#! /usr/bin/env python
import sys

import os
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Server
from flask_security import SQLAlchemyUserDatastore
from sqlalchemy import desc, func

from application.admin.forms import is_gov_email
from application.auth.models import *
from application.cms.classification_service import classification_service
from application.cms.models import *
from application.config import Config, DevConfig
from application.data.ethnicity_classification_synchroniser import EthnicityClassificationSynchroniser
from application.factory import create_app
from application.redirects.models import *
from application.sitebuilder.models import *
from application.sitebuilder.build import build_and_upload_error_pages
from application.utils import create_and_send_activation_email, send_email

if os.environ.get("ENVIRONMENT", "DEVELOPMENT").lower().startswith("dev"):
    app = create_app(DevConfig)
else:
    app = create_app(Config)

manager = Manager(app)
manager.add_command("server", Server())

migrate = Migrate(app, db)
manager.add_command("db", MigrateCommand)

# Note not using Flask-Security Role model
user_datastore = SQLAlchemyUserDatastore(db, User, None)


@manager.option("--email", dest="email")
@manager.option("--user-type", dest="user_type", default="RDU_USER")
def create_local_user_account(email, user_type):
    if is_gov_email(email):
        user = user_datastore.find_user(email=email)
        if user:
            print("User %s already exists" % email)
        else:
            user = User(email=email)
            if user_type == TypeOfUser.DEPT_USER.name:
                user.user_type = TypeOfUser.DEPT_USER
                user.capabilities = CAPABILITIES[TypeOfUser.DEPT_USER]
            elif user_type == TypeOfUser.RDU_USER.name:
                user.user_type = TypeOfUser.RDU_USER
                user.capabilities = CAPABILITIES[TypeOfUser.RDU_USER]
            elif user_type == TypeOfUser.DEV_USER.name:
                user.user_type = TypeOfUser.DEV_USER
                user.capabilities = CAPABILITIES[TypeOfUser.DEV_USER]
            else:
                print("Only DEPT_USER, RDU_USER or DEV_USER user types can be created with this command")
                sys.exit(-1)

            db.session.add(user)
            db.session.commit()
            confirmation_url = create_and_send_activation_email(email, app, devmode=True)
            print("User account created. To complete process go to %s" % confirmation_url)
    else:
        print("email is not a gov.uk email address and has not been whitelisted")


@manager.command
def build_static_site():
    if app.config["BUILD_SITE"]:
        from application.sitebuilder.build_service import build_site

        build_site(app)
    else:
        print("Build is disabled at the moment. Set BUILD_SITE to true to enable")


@manager.command
def request_static_build():
    if app.config["BUILD_SITE"]:
        from application.sitebuilder.build_service import request_build

        request_build()
        print("A build has been requested. It could be up to ten minutes before the request is processed")
    else:
        print("Build is disabled at the moment. Set BUILD_SITE to true to enable")


@manager.command
def force_build_static_site():
    if app.config["BUILD_SITE"]:
        from application.sitebuilder.build_service import request_build
        from application.sitebuilder.build_service import build_site

        request_build()
        print("An immediate build has been requested")
        build_site(app)
    else:
        print("Build is disabled at the moment. Set BUILD_SITE to true to enable")


@manager.command
def pull_prod_data():
    environment = os.environ.get("ENVIRONMENT", "PRODUCTION")
    if environment == "PRODUCTION":
        print("It looks like you are running this in production or some unknown environment.")
        print("Do not run this command in this environment as it deletes data")
        sys.exit(-1)

    prod_db = os.environ.get("PROD_DB_URL")
    if prod_db is None:
        print("You need to set an environment variable 'PROD_DB_URL' with value of production postgres url")
        sys.exit(-1)

    import subprocess
    import shlex

    out_file = "/tmp/data.dump"
    command = "scripts/get_data.sh %s %s" % (prod_db, out_file)
    subprocess.call(shlex.split(command))

    db.session.execute("DELETE FROM ethnicity_in_classification;")
    db.session.execute("DELETE FROM parent_ethnicity_in_classification;")
    db.session.execute("DELETE FROM ethnicity;")
    db.session.execute("DELETE FROM dimension_categorisation;")
    db.session.execute("DELETE FROM classification;")
    db.session.execute("DELETE FROM dimension;")
    db.session.execute("DELETE FROM upload;")
    db.session.execute("DELETE FROM page;")
    db.session.execute("DELETE FROM frequency_of_release;")
    db.session.execute("DELETE FROM lowest_level_of_geography;")
    db.session.execute("DELETE FROM organisation;")
    db.session.execute("DELETE FROM type_of_statistic;")
    db.session.commit()

    command = "pg_restore -d %s %s" % (app.config["SQLALCHEMY_DATABASE_URI"], out_file)
    subprocess.call(shlex.split(command))

    import contextlib

    with contextlib.suppress(FileNotFoundError):
        os.remove(out_file)

    print("Loaded data to", app.config["SQLALCHEMY_DATABASE_URI"])

    if os.environ.get("PROD_UPLOAD_BUCKET_NAME"):
        #  Copy upload files from production to the upload bucket for the current environment
        import boto3

        s3 = boto3.resource("s3")
        source = s3.Bucket(os.environ.get("PROD_UPLOAD_BUCKET_NAME"))
        destination = s3.Bucket(os.environ.get("S3_UPLOAD_BUCKET_NAME"))

        # Clear out destination folder
        destination.objects.all().delete()

        print(f"Copying upload files from bucket {source.name}")
        for key in source.objects.all():
            print(f"  Copying file {key.key}")
            destination.copy(CopySource={"Bucket": source.name, "Key": key.key}, Key=key.key)
        print("Finished copying upload files")


@manager.command
def delete_old_builds():
    from datetime import date

    a_week_ago = date.today() - timedelta(days=7)
    out = db.session.query(Build).filter(Build.created_at < a_week_ago).delete()
    db.session.commit()
    print("Deleted %d old builds" % out)


@manager.command
def report_broken_build():
    from datetime import date

    yesterday = date.today() - timedelta(days=1)
    failed = (
        db.session.query(Build)
        .filter(Build.status == "FAILED", Build.created_at > yesterday)
        .order_by(desc(Build.created_at))
        .first()
    )
    if failed:
        message = "Build failure in application %s. Build id %s created at %s\n\n%s" % (
            app.config["ENVIRONMENT"],
            failed.id,
            failed.created_at,
            failed.failure_reason,
        )
        subject = "Build failure in application %s on %s" % (app.config["ENVIRONMENT"], date.today())
        recipients = db.session.query(User).filter(User.user_type == TypeOfUser.DEV_USER.name).all()
        for r in recipients:
            send_email(app.config["RDU_EMAIL"], r.email, message, subject)
        print(message)
    else:
        print("No failed builds today")


@manager.command
def report_stalled_build():
    from datetime import date

    half_an_hour_ago = datetime.now() - timedelta(minutes=30)
    stalled = (
        db.session.query(Build)
        .filter(
            Build.status == "STARTED", func.DATE(Build.created_at) == date.today(), Build.created_at <= half_an_hour_ago
        )
        .order_by(desc(Build.created_at))
        .first()
    )

    if stalled:
        message = "Build stalled for more than 30 minutes in application %s. Build id %s created at %s" % (
            app.config["ENVIRONMENT"],
            stalled.id,
            stalled.created_at,
        )
        subject = "Build stalled in application %s on %s" % (app.config["ENVIRONMENT"], date.today())
        recipients = db.session.query(User).filter(User.user_type == TypeOfUser.DEV_USER.name).all()
        for r in recipients:
            send_email(app.config["RDU_EMAIL"], r.email, message, subject)
        print(message)
    else:
        print("No stalled builds")


@manager.command
def refresh_materialized_views():
    from application.dashboard.view_sql import refresh_all_dashboard_helper_views

    db.session.execute(refresh_all_dashboard_helper_views)
    db.session.commit()
    print("Refreshed data for MATERIALIZED VIEWS")


@manager.command
def drop_and_create_materialized_views():
    from application.dashboard.view_sql import (
        drop_all_dashboard_helper_views,
        latest_published_pages_view,
        pages_by_geography_view,
        ethnic_groups_by_dimension_view,
        categorisations_by_dimension,
    )

    db.session.execute(drop_all_dashboard_helper_views)
    db.session.execute(latest_published_pages_view)
    db.session.execute(pages_by_geography_view)
    db.session.execute(ethnic_groups_by_dimension_view)
    db.session.execute(categorisations_by_dimension)
    db.session.commit()
    print("Drop and create MATERIALIZED VIEWS done")


# Build stalled or failed emails continue until status is updated using
# this command.
@manager.option("--build_id", dest="build_id")
def acknowledge_build_issue(build_id):
    try:
        build = db.session.query(Build).filter(Build.id == build_id).one()
        build.status = "SUPERSEDED"
        db.session.add(build)
        db.session.commit()
        print("Build id", build_id, "set to superseded")
    except sqlalchemy.orm.exc.NoResultFound:
        print("No build found with id", build_id)


@manager.command
def run_data_migration(migration=None):
    data_migrations_folder = os.path.join("scripts", "data_migrations")

    if migration is None:
        migrations = os.listdir(data_migrations_folder)
        print("The following data migrationas are available:")
        for migration in migrations:
            print(f' * {os.path.basename(migration).replace(".sql", "")}')

    else:
        migration_filename = os.path.join(data_migrations_folder, f"{migration}.sql")
        try:
            with open(migration_filename, "r") as migration_file:
                migration_sql = migration_file.read()

        except Exception as e:
            print(f"Unable to load data migration from {migration}: {e}")

        else:
            try:
                db.session.execute(migration_sql)
                db.session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                print(f"Unable to apply data migration: {e}")
            else:
                print(f"Applied data migration: {migration}")


# Add a redirect rule
@manager.option("--from_uri", dest="from_uri")
@manager.option("--to_uri", dest="to_uri")
def add_redirect_rule(from_uri, to_uri):
    created = datetime.utcnow()
    redirect = Redirect(created=created, from_uri=from_uri, to_uri=to_uri)

    db.session.add(redirect)
    db.session.commit()
    print("Redirect from", from_uri, "to", to_uri, "added")


# Remove a redirect rule
@manager.option("--from_uri", dest="from_uri")
def delete_redirect_rule(from_uri):
    try:
        redirect = Redirect.query.filter_by(from_uri=from_uri).one()
        db.session.delete(redirect)
        db.session.commit()
        print("Redirect rule with from_uri", from_uri, "deleted")
    except NoResultFound as e:
        print("Could not delete a redirect rule with from_uri ", from_uri)


@manager.command
def refresh_error_pages():
    build_and_upload_error_pages(app)


@manager.command
def synchronise_classifications():
    synchroniser = EthnicityClassificationSynchroniser(classification_service=classification_service)
    synchroniser.synchronise_classifications(app.classification_finder.get_classification_collection())


if __name__ == "__main__":
    manager.run()
