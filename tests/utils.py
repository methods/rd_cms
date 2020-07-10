from lxml import html
from werkzeug.datastructures import ImmutableMultiDict

from application.cms.models import MeasureVersion


class GeneralTestException(Exception):
    pass


class UnmockedRequestException(GeneralTestException):
    pass


class UnexpectedMockInvocationException(GeneralTestException):
    pass


def get_page_with_title(title):
    return MeasureVersion.query.filter_by(title=title).one()


def assert_strings_match_ignoring_whitespace(string_1, string_2):
    assert "".join(string_1.split()) == "".join(string_2.split())


def page_displays_error_matching_message(response, message: str) -> bool:
    doc = html.fromstring(response.get_data(as_text=True))

    error_summary = doc.xpath(
        "//div[contains(@class, 'govuk-error-summary')]//a[normalize-space(text())=$message]", message=message
    )

    return True if error_summary else False


def multidict_from_measure_version_and_kwargs(measure_version: MeasureVersion, **kwargs) -> ImmutableMultiDict:
    return ImmutableMultiDict(
        {
            "template_version": measure_version.template_version,
            "title": measure_version.title,
            "description": measure_version.description,
            "measure_summary": measure_version.measure_summary,
            "summary": measure_version.summary,
            "lowest_level_of_geography": measure_version.lowest_level_of_geography_id,
            "area_covered": [area_covered.name for area_covered in measure_version.area_covered],
            "time_covered": measure_version.time_covered,
            "need_to_know": measure_version.need_to_know,
            "ethnicity_definition_summary": measure_version.ethnicity_definition_summary,
            "related_publications": measure_version.related_publications,
            "methodology": measure_version.methodology,
            "suppression_and_disclosure": measure_version.suppression_and_disclosure,
            "estimation": measure_version.estimation,
            "qmi_url": measure_version.qmi_url,
            "further_technical_information": measure_version.further_technical_information,
            "update_corrects_data_mistake": measure_version.update_corrects_data_mistake,
            "update_corrects_measure_version": measure_version.update_corrects_measure_version,
            "db_version_id": measure_version.db_version_id,
            **kwargs,
        }
    )


def details_tag_with_summary(dom_node, summary_text):

    summary_tags = dom_node.find_all("summary")

    summary_tags_with_matching_text = list(filter(lambda x: x.get_text().strip() == summary_text, summary_tags))

    if len(summary_tags_with_matching_text) > 0:
        return summary_tags_with_matching_text[0].parent
    else:
        return None


def find_link_with_text(dom_node, link_text):

    return dom_node.find("a", string=link_text)


def find_input_for_label_with_text(dom_node, label_text):

    label_tags = dom_node.find_all("label")

    label_tags_with_matching_text = list(filter(lambda x: x.get_text().strip() == label_text, label_tags))

    number_of_matching_label_tags = len(label_tags_with_matching_text)

    if number_of_matching_label_tags == 1:

        id_label_is_for = label_tags_with_matching_text[0]["for"]

        input_element = dom_node.select('input[id="' + id_label_is_for + '"]')

        if len(input_element) == 1:
            return input_element[0]
        else:
            raise Exception(f"No input found with the id '{id_label_is_for}'")

    elif number_of_matching_label_tags > 1:
        raise Exception(f"{number_of_matching_label_tags} labels found with the text '{label_text}'")
    else:
        raise Exception(f"No label not found with the text '{label_text}'")
