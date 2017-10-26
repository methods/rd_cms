#! /usr/bin/env python
import os
import json
import shutil

import sys
from flask_script import Manager, Server

from flask_security import SQLAlchemyUserDatastore
from flask_security.utils import encrypt_password

from flask_migrate import (
    Migrate,
    MigrateCommand
)
from slugify import slugify

from application.cms.page_service import page_service
from application.factory import create_app
from application.config import Config, DevConfig
from application.auth.models import *
from application.cms.models import *
from application.sitebuilder.models import *

env = os.environ.get('ENVIRONMENT', 'DEV')
# if env.lower() == 'dev':
#     app = create_app(DevConfig)
# else:
#     app = create_app(Config)
app = create_app(DevConfig)

manager = Manager(app)
manager.add_command("server", Server())

migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)


@manager.option('--email', dest='email')
@manager.option('--password', dest='password')
def create_internal_user(email, password):
    if not user_datastore.find_user(email=email):
        user = user_datastore.create_user(
            email=email,
            password=encrypt_password(password),
            roles=['INTERNAL_USER'])
        db.session.add(user)
        db.session.commit()
        return user


@manager.option('--email', dest='email')
@manager.option('--password', dest='password')
def create_departmental_user(email, password):
    if not user_datastore.find_user(email=email):
        user = user_datastore.create_user(
            email=email,
            password=encrypt_password(password),
            roles=['DEPARTMENTAL_USER'])
        db.session.add(user)
        db.session.commit()
        return user


@manager.option('--email', dest='email')
@manager.option('--role', dest='role')
def add_role_to_user(email, role):
    user = user_datastore.find_user(email=email)
    role = Role.query.filter_by(name=role.upper()).first()
    user.roles.append(role)
    db.session.add(user)
    db.session.commit()


@manager.command
def create_roles():
    for role in [('ADMIN', 'Application administrator'),
                 ('INTERNAL_USER', 'A user in the RDU team who can add, edit and view all pages'),
                 ('DEPARTMENTAL_USER', 'A user that can view pages that have a status of departmental review'),
                 ]:
        role = user_datastore.create_role(name=role[0], description=role[1])
        db.session.add(role)
        db.session.commit()


@manager.option('--email', dest='email')
@manager.option('--newpass', dest='new_password')
def update_password(email, new_password):
    user = user_datastore.find_user(email=email)
    if user is not None:
        user.password = encrypt_password(new_password.strip())
        db.session.add(user)
        db.session.commit()
        print('password updated')
    else:
        print('Could not find user with email %s', email)


def set_dimension_source_data(page_dict, root):
    for d in page_dict.get('dimensions', []):
        source_dir = os.path.join(root, 'source', d['guid'])
        chart_source = os.path.join(source_dir, 'chart.json')
        if os.path.isfile(chart_source):
            with open(chart_source) as chart_source_file:
                chart_source_data = json.load(chart_source_file)
                d['chart_source_data'] = chart_source_data

        table_source = os.path.join(source_dir, 'table.json')
        if os.path.isfile(table_source):
            with open(table_source) as table_source_file:
                table_source_data = json.load(table_source_file)
                d['table_source_data'] = table_source_data


@manager.command
def build_static_site():
    if app.config['BUILD_SITE']:
        from application.sitebuilder.build_service import build_site
        build_site(app)
    else:
        print('Build is disabled at the moment. Set BUILD_SITE to true to enable')


@manager.command
def request_static_build():
    if app.config['BUILD_SITE']:
        from application.sitebuilder.build_service import request_build
        request_build()
        print('A build has been requested. It could be up to ten minutes before the request is processed')
    else:
        print('Build is disabled at the moment. Set BUILD_SITE to true to enable')


@manager.command
def force_build_static_site():
    if app.config['BUILD_SITE']:
        from application.sitebuilder.build_service import request_build
        from application.sitebuilder.build_service import build_site
        request_build()
        build_site(app)
        print('An immediate build has been requested')
    else:
        print('Build is disabled at the moment. Set BUILD_SITE to true to enable')


@manager.option('--measure-id', dest='measure_id')
@manager.option('--from-subtopic', dest='from_subtopic')
@manager.option('--to-subtopic', dest='to_subtopic')
def move_measure(measure_id, from_subtopic, to_subtopic):
    page = DbPage.query.filter_by(guid=measure_id, parent_guid=from_subtopic).one()
    subtopic = DbPage.query.filter_by(guid=to_subtopic).one()
    page.parent_guid = subtopic.guid
    db.session.add(page)
    db.session.commit()
    print('Moved', measure_id, 'from', from_subtopic, 'to', to_subtopic)


@manager.option('--page-id', dest='page_id')
@manager.option('--position', dest='position')
def set_page_position(page_id, position):
    page = DbPage.query.filter_by(guid=page_id).one()
    page.position = position
    db.session.add(page)
    db.session.commit()
    print('Set page', page_id, 'to postion', position)


@manager.option('--old-title', dest='old_title')
@manager.option('--new-title', dest='new_title')
@manager.option('--page-type', dest='page_type')
def rename_page(old_title, new_title, page_type):

    if page_type not in ['topic', 'subtopic']:
        print('This can only be used to rename topic and subtopic pages')
        return

    page = DbPage.query.filter_by(title=old_title, page_type=page_type).one()

    renamed_page = DbPage()

    renamed_page.title = new_title
    renamed_page.uri = slugify(renamed_page.title)
    renamed_page.guid = '%s_%s' % (page_type, renamed_page.uri.replace('-', ''))
    renamed_page.status = page.status
    renamed_page.version = page.version
    renamed_page.description = page.description
    renamed_page.parent_guid = page.parent_guid
    renamed_page.parent_version = page.parent_version
    renamed_page.subtopics = page.subtopics
    renamed_page.page_type = page.page_type

    if page.page_type == 'subtopic':
        parent = DbPage.query.filter_by(guid=page.parent_guid, version=page.parent_version).one()
        subtopics = [st for st in parent.subtopics if st != page.guid]
        subtopics.append(renamed_page.guid)
        subtopics = sorted(subtopics)
        parent.subtopics = subtopics
        db.session.add(parent)

    for c in page.children:
        renamed_page.children.append(c)

    db.session.add(renamed_page)
    db.session.commit()

    db.session.delete(page)
    db.session.commit()

    print('Renamed', old_title, 'to', new_title)


if __name__ == '__main__':
    manager.run()
