import traceback
import uuid
from contextlib import contextmanager
from datetime import datetime

import boto3
import shutil

import os
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker

from application.cms.page_service import page_service
from application.cms.file_service import S3FileSystem
from application.sitebuilder.models import Build
from application import db
from application.sitebuilder.build import do_it, get_static_dir

YEAR_IN_SECONDS = 60 * 60 * 24 * 365
HOUR_IN_SECONDS = 60 * 60
FIFTEEN_MINUTES_IN_SECONDS = 60 * 15


def request_build():
    build = Build()
    build.id = str(uuid.uuid4())
    db.session.add(build)
    db.session.commit()


def build_site(app):
    Session = sessionmaker(db.engine)
    with make_session_scope(Session) as session:
        builds = session.query(Build).filter(Build.status == "PENDING").order_by(desc(Build.created_at)).all()
        if not builds:
            print("No pending builds at", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
            return
        superseded = []
        for i, build in enumerate(builds):
            if build.status == "PENDING":
                _start_build(app, build, session)
                superseded.extend(builds[i + 1 :])
                break
        for b in superseded:
            _mark_build_superseded(b, session)


def s3_deployer(app, build_dir, deletions=[]):
    _delete_files_not_needed_for_deploy(build_dir)

    site_bucket_name = app.config["S3_STATIC_SITE_BUCKET"]
    s3 = S3FileSystem(site_bucket_name, region=app.config["S3_REGION"])
    resource = boto3.resource("s3")
    bucket = resource.Bucket(site_bucket_name)

    for page in deletions:
        version = "latest" if page.latest else page.version
        subtopic = page_service.get_page(page.parent_guid)
        topic = page_service.get_page(subtopic.parent_guid)
        prefix = "%s/%s/%s/%s" % (topic.uri, subtopic.uri, page.uri, version)
        to_delete = list(bucket.objects.filter(Prefix=prefix))

        for d in to_delete:
            resource.Object(bucket.name, key=d.key).delete()

    # Ensure static assets (css, JavaScripts, etc) are uploaded before the rest of the site
    _upload_dir_to_s3(build_dir, s3, specific_subdirectory=get_static_dir())

    # Upload the whole site now the updated static assets are in place
    _upload_dir_to_s3(build_dir, s3)


def _upload_dir_to_s3(source_dir, s3, specific_subdirectory=None):
    target_dir = os.path.join(source_dir, specific_subdirectory) if specific_subdirectory else source_dir

    for root, dirs, files in os.walk(target_dir):
        for file_ in files:
            file_path = os.path.join(root, file_)

            # this is temp hack to work around that static site on s3 not
            # actually enabled for hosting static site and therefore
            # index files in sub directories do not work.
            # therefore use directory name as bucket key and index file contents
            # as bucket content
            bucket_key = file_path.replace(source_dir + os.path.sep, "")
            bucket_key = bucket_key.replace("/index.html", "")

            if _is_versioned_asset(file_):
                s3.write(file_path, bucket_key, max_age_seconds=YEAR_IN_SECONDS, strict=False)
            elif _measure_related(file_):
                s3.write(file_path, bucket_key, max_age_seconds=FIFTEEN_MINUTES_IN_SECONDS, strict=False)
            else:
                s3.write(file_path, bucket_key, max_age_seconds=HOUR_IN_SECONDS, strict=False)


def _delete_files_not_needed_for_deploy(build_dir):
    to_delete = [".git", "README.md", ".gitignore"]
    for file in to_delete:
        path = os.path.join(build_dir, file)
        if os.path.isdir(path):
            shutil.rmtree(path)
        elif os.path.isfile(path):
            os.remove(path)


def _start_build(app, build, session):
    try:
        _mark_build_started(build, session)
        do_it(app, build)
        build.status = "DONE"
        build.succeeded_at = datetime.utcnow()
        session.add(build)
    except Exception as e:
        build.status = "FAILED"
        build.failed_at = datetime.utcnow()
        build.failure_reason = traceback.format_exc()
    finally:
        session.add(build)


def _is_versioned_asset(file):
    import re

    match = re.search(r"(application|all|charts)-(\w+).(css|js)$", file)
    if match:
        return match.group(1) in ["application", "all", "charts"]
    return False


def _measure_related(file):
    return file.split(".")[-1] in ["html", "json", "csv"]


def _mark_build_started(build, session):
    build.status = "STARTED"
    session.add(build)
    session.commit()


def _mark_build_superseded(build, session):
    if build.status == "PENDING":
        build.status = "SUPERSEDED"
        session.add(build)


@contextmanager
def make_session_scope(Session):
    session = Session()
    session.expire_on_commit = False
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
