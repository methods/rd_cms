import bleach
import json
import markdown
import jinja2
import re

from flask import Markup
from hurry.filesize import size, alternative
from slugify import slugify
from jinja2.runtime import Context
from mypy_extensions import NoReturn
from markupsafe import Markup
from typing import Any
from typing import Dict
from typing import List
from application.cms.models import TypeOfData


def render_markdown(string: str) -> Markup:
    return Markup(markdown.markdown(bleach.clean(string) if string else ""))


def filesize(string: str) -> str:
    try:
        return size(int(string), system=alternative)
    except TypeError:
        return string


def value_filter(value: str) -> Markup:

    icon_html = {
        "N/A": '<span class="not-applicable">N/A<sup>*</sup></span>',
        "?": __missing_data_icon("sample-too-small")
        + __icon_explanation("withheld because a small sample size makes it unreliable"),
        "!": __missing_data_icon("confidential") + __icon_explanation("withheld to protect confidentiality"),
        "-": __missing_data_icon("not-collected") + __icon_explanation("not collected"),
    }

    if value is not None and value.strip() in icon_html:
        return icon_html[value.strip()]
    else:
        return jinja2.escape(value)


def __missing_data_icon(class_name: str) -> str:
    return '<span class="missing-data ' + class_name + '"></span>'


def __icon_explanation(explanation: str) -> str:
    return '<span class="visually-hidden">' + explanation + "</span>"


def flatten(data: List[Dict[str, Any]]) -> List[str]:
    values = sum([d["values"] for d in data], [])
    return [v.strip() for v in values if v is not None]


def flatten_chart(chart: Dict[str, Any]) -> str:
    if chart:
        text = ""
        if chart["type"] == "panel_bar_chart":
            for panel in chart["panels"]:
                text = "%s%s" % (text, flatten_simple_chart(panel))
        elif chart["type"] == "bar" or chart["type"] == "simple_bar_chart":
            text = flatten_simple_chart(chart)
        return text
    else:
        return []


def flatten_simple_chart(chart: Dict[str, Any]) -> str:
    text = ""
    for series in chart["series"]:
        for value in series["data"]:
            try:
                if "text" in value:
                    text = "%s%s" % (text, value["text"])
            except TypeError:
                pass

    return text


@jinja2.contextfilter
def version_filter(context: Context, file_name: str) -> NoReturn:

    from flask import current_app

    base_dir = current_app.config["BASE_DIRECTORY"]

    if file_name.endswith(".css"):
        asset_directory = "%s/application/static/stylesheets" % base_dir
    elif file_name.endswith(".js"):
        asset_directory = "%s/application/static/javascripts" % base_dir
    else:
        return file_name

    manifest_path = "%s/rev-manifest.json" % asset_directory

    try:
        with open(manifest_path) as m:
            manifest = json.load(m)
            return manifest.get(file_name, file_name)
    except Exception as e:
        return file_name


def strip_trailing_slash(string: str) -> str:
    if string and string[-1] == "/":
        return string[0:-1]
    else:
        return string


def join_enum_display_names(enums: List[TypeOfData], joiner: str) -> str:
    enum_list = [item.name.lower() for item in enums]
    enum_list = [enum_list[0].capitalize()] + enum_list[1:]
    return joiner.join(enum_list)


def slugify_value(value: str) -> str:
    if value is not None:
        return slugify(value)
    else:
        return ""


def first_bullet(value: str) -> str:
    if value:
        regex = re.compile(r"\*\s[^\n]*")
        result = regex.search(value)
        if result:
            return result.group()
        else:
            return ""
    else:
        return ""
