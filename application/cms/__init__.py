from flask import Blueprint

cms_blueprint = Blueprint("cms", __name__, url_prefix="/cms")

from application.cms.views import create_measure_page  # noqa
import application.cms_autosave.views  # noqa
