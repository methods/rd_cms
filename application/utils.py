import csv
import hashlib
import json
import sys
import os
import logging
from datetime import date
import time

from flask_mail import Message
from functools import wraps

from io import StringIO
from flask import abort, current_app, url_for, render_template, flash
from flask_login import current_user
from itsdangerous import TimestampSigner, SignatureExpired, URLSafeTimedSerializer
from slugify import slugify

from application import mail


def setup_module_logging(logger, level):
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(log_format)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    if len(logger.handlers) > 1:
        logger.warning("The same logger may have been initialised multiple times.")

    return logger


def get_bool(param):
    if str(param).lower().strip() in ["true", "t", "yes", "y", "on", "1"]:
        return True
    elif str(param).lower().strip() in ["false", "f", "no", "n", "off", "0"]:
        return False
    return False


# This should be placed after login_required decorator as it needs authenticated user
def user_has_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        measure_id = kwargs.get("measure")
        if current_user.is_authenticated and measure_id is not None and current_user.can_access(measure_id):
            return f(*args, **kwargs)
        else:
            return abort(403)

    return decorated_function


# This should be placed after login_required decorator as it needs authenticated user
def user_can(capabilibity):
    def can_decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.is_authenticated and current_user.can(capabilibity):
                return f(*args, **kwargs)
            else:
                return abort(403)

        return decorated_function

    return can_decorator


class DateEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, date):
            return o.isoformat()

        return json.JSONEncoder.default(self, o)


def get_content_with_metadata(filename, page):
    source = os.environ.get("RDU_SITE", "https://www.ethnicity-facts-figures.service.gov.uk")
    metadata = [
        ["Title", page.title],
        ["Location", page.format_area_covered()],
        ["Time period", page.time_covered],
        ["Data source", page.department_source.name if page.department_source is not None else ""],
        ["Data source link", page.source_url],
        ["Source", source],
        ["Last updated", page.publication_date],
    ]

    rows = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                rows.append(row)

    except UnicodeDecodeError as e:
        with open(filename, "r", encoding="iso-8859-1") as f:
            reader = csv.reader(f, delimiter=",")
            for row in reader:
                rows.append(row)

    except Exception as e:
        message = "error with file %s" % filename
        print(message, e)
        raise e

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")

        for m in metadata:
            writer.writerow(m)

        for row in rows:
            writer.writerow(row)

        return output.getvalue()


def generate_token(email, app):
    signer = TimestampSigner(app.config["SECRET_KEY"])
    return signer.sign(email).decode("utf8")


def check_token(token, app):
    signer = TimestampSigner(app.config["SECRET_KEY"])
    try:
        email = signer.unsign(token, max_age=app.config["TOKEN_MAX_AGE_SECONDS"])
        if isinstance(email, bytes):
            email = email.decode("utf-8")
        return email
    except SignatureExpired as e:
        current_app.logger.info("token expired %s" % e)
        return None


def create_and_send_activation_email(email, app, devmode=False):
    token = generate_token(email, app)
    confirmation_url = url_for("register.confirm_account", token=token, _external=True)

    if devmode:
        return confirmation_url

    html = render_template("admin/confirm_account.html", confirmation_url=confirmation_url, user=current_user)
    try:
        send_email(
            app.config["RDU_EMAIL"], email, html, "Access to the Ethnicity Facts and Figures content management system"
        )
        flash("User account invite sent to: %s." % email)
    except Exception as ex:
        flash("Failed to send invite to: %s" % email, "error")
        app.logger.error(ex)


def send_email(sender, email, message, subject):
    msg = Message(html=message, subject=subject, sender=sender, recipients=[email])
    mail.send(msg)


def write_dimension_csv(dimension):
    if "table" in dimension:
        source_data = dimension["table"]["data"]
    elif "chart" in dimension:
        source_data = dimension["chart"]["data"]
    else:
        source_data = [[]]

    metadata = get_dimension_metadata(dimension)
    csv_columns = source_data[0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow("")
        writer.writerow(csv_columns)
        for row in source_data[1:]:
            writer.writerow(row)

        return output.getvalue()


def write_dimension_tabular_csv(dimension):
    if "tabular" in dimension:
        source_data = dimension["tabular"]["data"]
    else:
        source_data = [[]]

    metadata = get_dimension_metadata(dimension)

    csv_columns = source_data[0]

    with StringIO() as output:
        writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)
        for m in metadata:
            writer.writerow(m)
        writer.writerow("")
        writer.writerow(csv_columns)
        for row in source_data[1:]:
            writer.writerow(row)

        return output.getvalue()


def get_dimension_metadata(dimension):
    source = os.environ.get("RDU_SITE", "")

    if dimension["context"]["publication_date"] != "":
        date = dimension["context"]["publication_date"]
    else:
        date = ""

    return [
        ["Title", dimension["context"]["dimension"]],
        ["Location", dimension["context"]["location"]],
        ["Time period", dimension["context"]["time_period"]],
        ["Data source", dimension["context"]["source_text"]],
        ["Data source link", dimension["context"]["source_url"]],
        ["Source", source],
        ["Last updated", date],
    ]


def generate_review_token(page_id, page_version):
    key = os.environ.get("SECRET_KEY")
    serializer = URLSafeTimedSerializer(key)
    token = "%s|%s" % (page_id, page_version)
    return serializer.dumps(token)


def decode_review_token(token, config):
    key = config["SECRET_KEY"]
    serializer = URLSafeTimedSerializer(key)
    seconds_in_day = 24 * 60 * 60
    max_age_seconds = seconds_in_day * config.get("PREVIEW_TOKEN_MAX_AGE_DAYS")
    decoded_token = serializer.loads(token, max_age=max_age_seconds)
    page_id, page_version = decoded_token.split("|")
    return page_id, page_version


def get_token_age(token, config):
    key = config["SECRET_KEY"]
    serializer = URLSafeTimedSerializer(key)
    token_created = serializer.loads(token, return_timestamp=True)[1]
    return token_created


def create_guid(value):
    hash = hashlib.sha1()
    hash.update("{}{}".format(str(time.time()), slugify(value)).encode("utf-8"))
    return hash.hexdigest()
