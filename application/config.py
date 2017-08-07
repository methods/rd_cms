import ast
import os
import logging
from os.path import join, dirname
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Note this will fail with warnings, not exception
# if file does not exist. Therefore the config classes
# below will break. For CI env variables are set in circle.yml
# In Heroku, well... they are set in Heroku.

from application.utils import get_bool

p = Path(dirname(__file__))
dotenv_path = join(str(p.parent), '.env')
load_dotenv(dotenv_path)


class Config:
    DEBUG = False
    LOG_LEVEL = logging.INFO
    ENVIRONMENT = os.environ.get('ENVIRONMENT', 'PROD')
    SECRET_KEY = os.environ['SECRET_KEY']
    PROJECT_NAME = "rd_cms"
    BASE_DIRECTORY = dirname(dirname(os.path.abspath(__file__)))
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True

    GITHUB_ACCESS_TOKEN = os.environ['GITHUB_ACCESS_TOKEN']
    HTML_CONTENT_REPO = 'rd_html'
    GITHUB_URL = os.environ.get('RDU_GITHUB_URL', 'github.com/methods')
    STATIC_SITE_REMOTE_REPO = "https://{}:x-oauth-basic@{}.git".format(GITHUB_ACCESS_TOKEN,
                                                                       '/'.join((GITHUB_URL,
                                                                                HTML_CONTENT_REPO)))

    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=int(os.environ.get('PERMANENT_SESSION_LIFETIME_MINS', 360)))
    SECURITY_PASSWORD_SALT = SECRET_KEY
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_URL_PREFIX = '/auth'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESEARCH = get_bool(os.environ.get('RESEARCH', False))

    SECURITY_FLASH_MESSAGES = False
    STATIC_BUILD_DIR = os.environ['STATIC_BUILD_DIR']
    BETA_PUBLICATION_STATES = ['APPROVED']

    FILE_SERVICE = os.environ.get('FILE_SERVICE', 'Local')
    S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
    S3_REGION = os.environ.get('S3_REGION', 'eu-west-2')
    LOCAL_ROOT = os.environ.get('LOCAL_ROOT', None)

    HARMONISER_ENABLED = get_bool(os.environ.get('HARMONISER_ENABLED', False))
    HARMONISER_FILE = os.environ.get('HARMONISER_FILE', './application/data/ethnicity_lookup.csv')

    SIMPLE_CHART_BUILDER = get_bool(os.environ.get('SIMPLE_CHART_BUILDER', False))
    RDU_SITE = os.environ.get('RDU_SITE', 'https://ethnicity-facts-and-figures.herokuapp.com')

    BUILD_SITE = get_bool(os.environ.get('BUILD_SITE', False))
    PUSH_SITE = get_bool(os.environ.get('PUSH_SITE', False))


class DevConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG
    PUSH_ENABLED = False
    FETCH_ENABLED = False
    ENVIRONMENT = 'DEV'
    SESSION_COOKIE_SECURE = False


class TestConfig(DevConfig):
    if os.environ['ENVIRONMENT'] == 'CI':
        SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://localhost/rdcms_test')
    LOGIN_DISABLED = False
    WORK_WITH_REMOTE = False
    FILE_SERVICE = 'Local'

    HARMONISER_ENABLED = True
    HARMONISER_FILE = 'tests/test_data/test_lookups/test_lookup.csv'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
