import datetime
import json
from unittest import mock
import re

import pytest
from bs4 import BeautifulSoup
from flask import url_for, current_app
from lxml import html
from werkzeug.datastructures import ImmutableMultiDict

from application.auth.models import TypeOfUser
from application.cms.forms import MeasureVersionForm
from application.cms.models import DataSource, TESTING_SPACE_SLUG, MeasureVersion
from application.cms.utils import get_data_source_forms
from application.sitebuilder.models import Build
from tests.models import (
    MeasureVersionFactory,
    SubtopicFactory,
    LowestLevelOfGeographyFactory,
    DataSourceFactory,
    MeasureVersionWithDimensionFactory,
    UserFactory,
)
from tests.utils import multidict_from_measure_version_and_kwargs, page_displays_error_matching_message


class TestGetCreateMeasurePage:
    def setup(self):
        self.saved_config = {**current_app.config}

    def teardown(self):
        current_app.config = {**self.saved_config}

    def test_create_measure_page(self, test_app_client, logged_in_rdu_user, stub_measure_data):
        LowestLevelOfGeographyFactory(name=stub_measure_data["lowest_level_of_geography_id"])
        subtopic = SubtopicFactory()
        form = MeasureVersionForm(is_minor_update=False, **stub_measure_data)

        response = test_app_client.post(
            url_for("cms.create_measure", topic_slug=subtopic.topic.slug, subtopic_slug=subtopic.slug),
            data=form.data,
            follow_redirects=True,
        )

        assert response.status_code == 200
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
        assert (
            page.find("div", class_="eff-flash-message__body").get_text(strip=True)
            == "Created page %s" % stub_measure_data["title"]
        )

    def test_create_measure_page_creates_data_source_entries(
        self, test_app_client, logged_in_rdu_user, stub_measure_data
    ):
        LowestLevelOfGeographyFactory(name=stub_measure_data["lowest_level_of_geography_id"])
        subtopic = SubtopicFactory()
        form = MeasureVersionForm(is_minor_update=False, **stub_measure_data)
        request_mock = mock.Mock()
        request_mock.method = "POST"
        data_source_form, data_source_2_form = get_data_source_forms(request_mock, None)
        data_source_form.title.data = "test"
        data_source_2_form.title.data = "test 2"
        form_data = ImmutableMultiDict(
            {
                **form.data,
                **{field.name: field.data for field in data_source_form},
                **{field.name: field.data for field in data_source_2_form},
            }
        )
        assert DataSource.query.count() == 0

        res = test_app_client.post(
            url_for("cms.create_measure", topic_slug=subtopic.topic.slug, subtopic_slug=subtopic.slug),
            data=form_data,
            follow_redirects=True,
        )

        assert res.status_code == 200
        assert DataSource.query.count() == 2

    def test_measure_pages_have_csrf_protection(self, test_app_client, logged_in_rdu_user, stub_measure_data):
        LowestLevelOfGeographyFactory(name=stub_measure_data["lowest_level_of_geography_id"])
        subtopic = SubtopicFactory()
        current_app.config["WTF_CSRF_ENABLED"] = True
        res = test_app_client.get(
            url_for("cms.create_measure", topic_slug=subtopic.topic.slug, subtopic_slug=subtopic.slug),
            follow_redirects=True,
        )
        doc = html.fromstring(res.get_data(as_text=True))

        assert doc.xpath("//*[@id='csrf_token']")
        assert doc.xpath("//*[@id='data-source-1-csrf_token']")
        assert doc.xpath("//*[@id='data-source-2-csrf_token']")


def test_can_not_send_to_review_without_a_data_source_uploaded(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(status="DRAFT", uploads=[])
    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "send-to-department-review"}),
        follow_redirects=True,
    )
    assert response.status_code == 400
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert "Upload the source data" in page.find("div", class_="govuk-error-summary").text


@pytest.mark.parametrize("cannot_reject_status", ("DRAFT", "APPROVED"))
def test_can_not_reject_page_if_not_under_review(test_app_client, logged_in_rdu_user, cannot_reject_status):
    measure_version = MeasureVersionFactory(status=cannot_reject_status)
    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "reject-measure"}),
        follow_redirects=True,
    )
    assert response.status_code == 400
    assert measure_version.status == cannot_reject_status


def test_can_reject_page_under_review(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")

    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "reject-measure"}),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert measure_version.status == "REJECTED"


def test_admin_user_can_publish_page_in_dept_review(test_app_client, logged_in_admin_user, mock_request_build):
    measure_version = MeasureVersionFactory(title="Test Measure Page", status="DEPARTMENT_REVIEW", latest=False)

    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "send-to-approved"}),
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").get_text(strip=True)
        == 'Sent page "Test Measure Page" to APPROVED'
    )

    assert measure_version.status == "APPROVED"
    assert measure_version.last_updated_by == logged_in_admin_user.email
    assert measure_version.published_by == logged_in_admin_user.email
    assert measure_version.published_at == datetime.date.today()
    assert measure_version.latest is True
    mock_request_build.assert_called_once()


@pytest.mark.parametrize("cannot_publish_status", ("DRAFT", "INTERNAL_REVIEW", "APPROVED", "REJECTED", "UNPUBLISH"))
def test_admin_user_can_not_publish_page_not_in_department_review(
    test_app_client, logged_in_admin_user, mock_request_build, cannot_publish_status
):
    measure_version = MeasureVersionFactory(status=cannot_publish_status)

    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "send-to-approved"}),
        follow_redirects=True,
    )

    assert response.status_code == 400
    assert measure_version.status == cannot_publish_status
    mock_request_build.assert_not_called()


def test_non_admin_user_can_not_publish_page_in_dept_review(test_app_client, logged_in_rdu_user, mock_request_build):
    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "send-to-approved"}),
        follow_redirects=True,
    )

    assert response.status_code == 403
    assert measure_version.status == "DEPARTMENT_REVIEW"
    mock_request_build.assert_not_called()


def test_admin_user_can_unpublish_page(test_app_client, logged_in_admin_user, mock_request_build):
    measure_version = MeasureVersionFactory(status="APPROVED")

    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "unpublish-measure"}),
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert measure_version.status == "UNPUBLISH"
    assert measure_version.unpublished_by == logged_in_admin_user.email
    mock_request_build.assert_called_once()


def test_non_admin_user_can_not_unpublish_page(test_app_client, logged_in_rdu_user, mock_request_build):
    measure_version = MeasureVersionFactory(status="APPROVED")

    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "unpublish-measure"}),
        follow_redirects=True,
    )

    assert response.status_code == 403
    assert measure_version.status == "APPROVED"
    mock_request_build.assert_not_called()


def test_admin_user_can_see_publish_unpublish_buttons_on_edit_page(test_app_client, logged_in_admin_user):
    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("button")[-1].text.strip().lower() == "approve for publishing"

    measure_version = MeasureVersionFactory(status="APPROVED")

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("button")[-1].text.strip().lower() == "unpublish"


def test_internal_user_can_not_see_publish_unpublish_buttons_on_edit_page(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW")
    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("button")[-1].text.strip().lower() == "reject"

    measure_version = MeasureVersionFactory(status="APPROVED")

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all("a", class_="govuk-button")[-1].text.strip() == "Update"


def test_order_measures_in_subtopic(test_app_client, logged_in_rdu_user):
    subtopic = SubtopicFactory()
    ids = [0, 1, 2, 3, 4]
    for id_ in ids:
        MeasureVersionFactory(
            id=id_, measure__position=id_, measure__id=id_, measure__subtopics=[subtopic], measure__slug=str(id_)
        )

    assert subtopic.measures[0].slug == "0"
    assert subtopic.measures[1].slug == "1"
    assert subtopic.measures[2].slug == "2"
    assert subtopic.measures[3].slug == "3"
    assert subtopic.measures[4].slug == "4"

    with test_app_client.session_transaction() as session:
        session["user_id"] = logged_in_rdu_user.id

    updates = []
    for position, id_ in enumerate(reversed(ids)):
        updates.append({"position": position, "measure_id": id_, "subtopic_id": subtopic.id})

    response = test_app_client.post(
        url_for("cms.set_measure_order"), data=json.dumps({"positions": updates}), content_type="application/json"
    )

    assert response.status_code == 200

    assert subtopic.measures[0].slug == "4"
    assert subtopic.measures[1].slug == "3"
    assert subtopic.measures[2].slug == "2"
    assert subtopic.measures[3].slug == "1"
    assert subtopic.measures[4].slug == "0"


def test_reorder_measures_triggers_build(test_app_client, logged_in_rdu_user):
    subtopic = SubtopicFactory()
    ids = [0, 1]
    reversed_ids = ids[::-1]
    for id_ in ids:
        MeasureVersionFactory(
            id=id_, measure__position=id_, measure__id=id_, measure__subtopics=[subtopic], measure__slug=str(id_)
        )

    builds = Build.query.all()

    assert len(builds) == 0

    updates = []
    for position, id in enumerate(reversed_ids):
        updates.append({"position": position, "measure_id": str(id), "subtopic_id": subtopic.id})

    response = test_app_client.post(
        url_for("cms.set_measure_order"), data=json.dumps({"positions": updates}), content_type="application/json"
    )

    assert response.status_code == 200

    builds = Build.query.all()

    assert len(builds) == 1


def test_view_edit_measure_page_subtopic_dropdown_includes_testing_space_topic(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(
        status="DRAFT",
        measure__subtopics__topic__slug=TESTING_SPACE_SLUG,
        measure__subtopics__topic__title="Testing space",
    )

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

    subtopic = page.find("select", attrs={"id": "subtopic"})
    assert subtopic.find("optgroup", label="Testing space")


def test_view_edit_measure_page(test_app_client, logged_in_rdu_user, stub_measure_data):
    data_source = DataSourceFactory.build(
        title="DWP Stats",
        type_of_data=["SURVEY"],
        source_url="http://dwp.gov.uk",
        publication_date="15th May 2017",
        note_on_corrections_or_updates="Note on corrections or updates",
        purpose="Purpose of data source",
    )
    measure_version = MeasureVersionFactory(status="DRAFT", data_sources=[data_source], **stub_measure_data)

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

    assert page.h1.text.strip() == "Edit page"

    title = page.find("input", attrs={"id": "title"})
    assert title
    assert title.attrs.get("value") == "Test Measure Page"

    subtopic = page.find("select", attrs={"id": "subtopic"})
    assert subtopic
    assert int(subtopic.find("option", selected=True).attrs.get("value")) == measure_version.measure.subtopic.id

    time_covered = page.find("input", attrs={"id": "time_covered"})
    assert time_covered
    assert time_covered.attrs.get("value") == "4 months"

    assert len(page.find_all("input", class_="country")) == 4

    # TODO lowest level of geography

    methodology_label = page.find("label", attrs={"for": "methodology"})
    methodology = page.find("textarea", attrs={"id": "methodology"})

    assert methodology_label.text.strip() == "Methodology"
    assert methodology.text == "how we measure unemployment"

    suppression_and_disclosure_label = page.find("label", attrs={"for": "suppression_and_disclosure"})
    suppression_and_disclosure = page.find("textarea", attrs={"id": "suppression_and_disclosure"})

    assert suppression_and_disclosure_label.text.strip() == "Suppression rules and disclosure control (optional)"
    assert suppression_and_disclosure.text == "Suppression rules and disclosure control"

    rounding_label = page.find("label", attrs={"for": "estimation"})
    rounding = page.find("textarea", attrs={"id": "estimation"})

    assert rounding_label.text.strip() == "Rounding (optional)"
    assert rounding.text == "X people are unemployed"

    # Data sources

    # TODO publisher/dept source

    sources = page.find("fieldset", class_="source")
    data_source_title_label = sources.find("label", attrs={"for": "data-source-1-title"})
    data_source_title_input = sources.find("input", attrs={"id": "data-source-1-title"})

    assert data_source_title_label.text.strip() == "Title of data source"
    assert data_source_title_input.attrs.get("value") == "DWP Stats"

    source_url = sources.find("input", attrs={"id": "data-source-1-source_url"})
    assert source_url.attrs.get("value") == "http://dwp.gov.uk"

    publication_date = page.find("input", attrs={"id": "data-source-1-publication_date"})
    assert publication_date
    assert publication_date.attrs.get("value") == "15th May 2017"

    note_on_corrections_or_updates_label = sources.find(
        "label", attrs={"for": "data-source-1-note_on_corrections_or_updates"}
    )
    note_on_corrections_or_updates = sources.find(
        "textarea", attrs={"id": "data-source-1-note_on_corrections_or_updates"}
    )

    assert note_on_corrections_or_updates_label.text.strip() == "Corrections or updates (optional)"
    assert note_on_corrections_or_updates.text == "Note on corrections or updates"

    # TODO frequency of release

    data_source_purpose_label = sources.find("label", attrs={"for": "data-source-1-purpose"})
    data_source_purpose = sources.find("textarea", attrs={"id": "data-source-1-purpose"})

    assert data_source_purpose_label.text.strip() == "Purpose of data source"
    assert data_source_purpose.text == "Purpose of data source"

    summary = page.find("textarea", attrs={"id": "summary"})
    assert summary
    assert summary.text == stub_measure_data["summary"]

    need_to_know = page.find("textarea", attrs={"id": "need_to_know"})
    assert need_to_know
    assert need_to_know.text == "Need to know this"

    measure_summary = page.find("textarea", attrs={"id": "measure_summary"})
    assert measure_summary
    assert measure_summary.text == "Unemployment measure summary"

    ethnicity_definition_summary = page.find("textarea", attrs={"id": "ethnicity_definition_summary"})
    assert ethnicity_definition_summary
    assert ethnicity_definition_summary.text == "This is a summary of ethnicity definitions"

    methodology = page.find("textarea", attrs={"id": "methodology"})
    assert methodology
    assert methodology.text == "how we measure unemployment"

    estimation = page.find("textarea", attrs={"id": "estimation"})
    assert estimation
    assert estimation.text == "X people are unemployed"

    related_publications = page.find("textarea", attrs={"id": "related_publications"})
    assert related_publications
    assert related_publications.text == "Related publications"

    qmi_url = page.find("input", attrs={"id": "qmi_url"})
    assert qmi_url
    assert qmi_url.attrs.get("value") == "http://www.quality-street.gov.uk"

    further_technical_information = page.find("textarea", attrs={"id": "further_technical_information"})
    assert further_technical_information
    assert further_technical_information.text == "Further technical information"


@pytest.mark.parametrize("measure_version, should_show_data_correction_radio", (("1.0", False), ("1.1", True)))
def test_view_edit_measure_page_for_minor_update_shows_data_correction_radio(
    test_app_client, logged_in_rdu_user, measure_version, should_show_data_correction_radio
):
    measure_version = MeasureVersionFactory(status="DRAFT", version=measure_version, update_corrects_data_mistake=None)

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

    assert page.h1.text.strip() == "Edit page"

    update_corrects_data_mistake = page.find("div", id="update_corrects_data_mistake")
    if should_show_data_correction_radio:
        legend = update_corrects_data_mistake.find("legend")
        labels = update_corrects_data_mistake.findAll("label")

        assert legend.text.strip() == "Are you correcting something that’s factually incorrect?"
        assert labels[0].text.strip() == "Yes"
        assert labels[1].text.strip() == "No"
        assert (
            update_corrects_data_mistake.findAll("input", {"type": "radio", "checked": True}) == []
        ), "One of the radio options is checked, but they should both be unchecked by default."

    else:
        assert update_corrects_data_mistake is None


def test_dept_user_should_not_be_able_to_delete_upload_if_page_not_shared(
    test_app_client, logged_in_dept_user, mock_delete_upload
):
    measure_version = MeasureVersionFactory(status="DRAFT", uploads__guid="test-download")

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert response.status_code == 403

    response = test_app_client.post(
        url_for(
            "cms.delete_upload",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            upload_guid="test-download",
        )
    )

    assert response.status_code == 403

    mock_delete_upload.assert_not_called()


def test_dept_user_should_be_able_to_delete_upload_from_shared_page(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionFactory(
        status="DRAFT",
        measure__shared_with=[logged_in_dept_user],
        uploads__guid="test-download",
        uploads__title="upload title",
    )

    response = test_app_client.post(
        url_for(
            "cms.delete_upload",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            upload_guid="test-download",
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find("div", class_="eff-flash-message__body").get_text(strip=True) == "Deleted upload ‘upload title’"
    assert len(measure_version.uploads) == 0


def test_dept_user_should_not_be_able_to_edit_upload_if_page_not_shared(
    test_app_client, logged_in_dept_user, mock_edit_upload
):
    measure_version = MeasureVersionFactory(
        status="DRAFT", uploads__guid="test-download", uploads__file_name="test-download.csv"
    )

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert response.status_code == 403

    response = test_app_client.get(
        url_for(
            "cms.edit_upload",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            upload_guid="test-download",
        )
    )

    assert response.status_code == 403

    mock_edit_upload.assert_not_called()


def test_dept_user_should_be_able_to_edit_upload_on_shared_page(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionFactory(
        status="DRAFT",
        measure__shared_with=[logged_in_dept_user],
        uploads__guid="test-download",
        uploads__title="upload title",
    )

    response = test_app_client.get(
        url_for(
            "cms.edit_upload",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            upload_guid="test-download",
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find("h1").string == "Edit source data"


def test_dept_user_should_be_able_to_edit_shared_page(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionFactory(
        status="DRAFT", measure__shared_with=[logged_in_dept_user], title="this will be updated"
    )

    data = {"title": "this is the update", "db_version_id": measure_version.db_version_id + 1}
    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=data,
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert (
        page.find("div", class_="eff-flash-message__body").get_text(strip=True) == 'Updated page "this is the update"'
    )
    assert measure_version.title == "this is the update"


@pytest.mark.parametrize("measure_version", ["1.0", "1.1", "2.0"])
def test_db_version_id_gets_incremented_after_an_update(test_app_client, logged_in_rdu_user, measure_version):
    measure_version: MeasureVersion = MeasureVersionFactory(
        status="DRAFT", title="this will be updated", db_version_id=1, version=measure_version
    )

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find("input", {"id": "db_version_id"}).attrs["value"] == "1"

    data = multidict_from_measure_version_and_kwargs(measure_version, title="this is the update")
    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=data,
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find("input", {"id": "db_version_id"}).attrs["value"] == "2"
    assert measure_version.title == "this is the update"


def test_edit_measure_page_updated_with_latest_db_version_id_when_posting_a_conflicting_update(
    db_session, test_app_client, logged_in_rdu_user
):
    measure_version: MeasureVersion = MeasureVersionFactory(status="DRAFT", title="initial title", version="2.0")
    assert measure_version.db_version_id == 1

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )
    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find("input", {"id": "db_version_id"}).attrs["value"] == "1"

    measure_version.title = "new title"
    db_session.session.commit()
    assert measure_version.db_version_id == 2

    data = multidict_from_measure_version_and_kwargs(measure_version, db_version_id="1", title="try new title")
    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=data,
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find("input", {"id": "db_version_id"}).attrs["value"] == "2"
    assert measure_version.title == "new title"
    assert page_displays_error_matching_message(
        response, message=f"‘Title’ has been updated by {measure_version.last_updated_by}"
    )
    assert len(page.findAll("div", class_="eff-diffs")) == 1
    assert (
        str(page.find("div", class_="eff-diffs"))
        == '<div class="govuk-body eff-diffs">\n<p class="govuk-body"> <ins>try</ins> new title</p>\n</div>'
    )


def test_dept_user_should_not_be_able_to_delete_dimension_if_page_not_shared(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionWithDimensionFactory(measure__shared_with=[])

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert response.status_code == 403

    response = test_app_client.post(
        url_for(
            "cms.delete_dimension",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            dimension_guid=measure_version.dimensions[0].guid,
        )
    )

    assert response.status_code == 403


def test_dept_cannot_publish_a_shared_page(test_app_client, logged_in_dept_user):
    measure_version = MeasureVersionFactory(status="DEPARTMENT_REVIEW", measure__shared_with=[logged_in_dept_user])

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        )
    )

    assert response.status_code == 200

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert not page.find("button", id="send-to-approved")

    response = test_app_client.post(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        data=ImmutableMultiDict({"measure-action": "send-to-approved"}),
        follow_redirects=True,
    )

    assert response.status_code == 403


@pytest.mark.parametrize(
    "user_type, can_see_copy_button",
    (
        (TypeOfUser.DEPT_USER, False),
        (TypeOfUser.RDU_USER, False),
        (TypeOfUser.ADMIN_USER, False),
        (TypeOfUser.DEV_USER, True),
    ),
)
def test_only_allowed_users_can_see_copy_measure_button_on_edit_page(test_app_client, user_type, can_see_copy_button):
    user = UserFactory(user_type=user_type)
    measure_version = MeasureVersionFactory()

    with test_app_client.session_transaction() as session:
        session["user_id"] = user.id

    response = test_app_client.get(
        url_for(
            "cms.edit_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    page_button_texts = [button.text.strip().lower() for button in page.find_all("button")]
    assert ("create a copy of this measure" in page_button_texts) is can_see_copy_button


def test_copy_measure_page(test_app_client, logged_in_dev_user):
    measure_version = MeasureVersionFactory(title="Test Measure Page", status="APPROVED")

    response = test_app_client.post(
        url_for(
            "cms.copy_measure_version",
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
        ),
        follow_redirects=True,
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

    assert page.find("h1").text == "Edit page"
    assert page.find("input", attrs={"name": "title"})["value"] == "COPY OF Test Measure Page"


def test_measure_version_history_page(test_app_client, logged_in_dev_user):
    measure_version_1_0 = MeasureVersionFactory(status="APPROVED", latest=False, version="1.0")
    measure_version_1_1 = MeasureVersionFactory(
        status="APPROVED", latest=True, version="1.1", measure=measure_version_1_0.measure
    )

    topic_slug = measure_version_1_0.measure.subtopic.topic.slug
    subtopic_slug = measure_version_1_0.measure.subtopic.slug
    measure_slug = measure_version_1_0.measure.slug

    response = test_app_client.get(
        url_for(
            "cms.list_measure_versions", topic_slug=topic_slug, subtopic_slug=subtopic_slug, measure_slug=measure_slug
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

    assert "Version history" in page.find("h1").text.strip()
    assert measure_version_1_1.title in page.find("h1").text.strip()

    view_form_links = page.findAll("a", text=re.compile(r"View\s+form"))
    view_form_hrefs = [element.attrs["href"] for element in view_form_links]

    assert view_form_hrefs == [
        f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/1.1/edit",
        f"/cms/{topic_slug}/{subtopic_slug}/{measure_slug}/1.0/edit",
    ]


def test_view_measure_version_by_measure_version_id_redirects(test_app_client, logged_in_rdu_user):
    measure_version = MeasureVersionFactory(id=345)
    response = test_app_client.get(url_for("cms.view_measure_version_by_measure_version_id", measure_version_id=345))

    assert response.status_code == 302
    assert response.location == url_for(
        "static_site.measure_version",
        topic_slug=measure_version.measure.subtopic.topic.slug,
        subtopic_slug=measure_version.measure.subtopic.slug,
        measure_slug=measure_version.measure.slug,
        version=measure_version.version,
        _external=True,
    )


def test_view_measure_version_by_measure_version_id_404_if_no_measure_version(test_app_client, logged_in_rdu_user):
    MeasureVersionFactory(id=345)
    response = test_app_client.get(url_for("cms.view_measure_version_by_measure_version_id", measure_version_id=456))

    assert response.status_code == 404


class _TestVisualisationBuilder:
    ROUTE_NAME = None

    def builder_url(self, measure_version):
        if not self.ROUTE_NAME:
            raise NotImplementedError

        return url_for(
            self.ROUTE_NAME,
            topic_slug=measure_version.measure.subtopic.topic.slug,
            subtopic_slug=measure_version.measure.subtopic.slug,
            measure_slug=measure_version.measure.slug,
            version=measure_version.version,
            dimension_guid=measure_version.dimensions[0].guid,
        )

    def test_custom_classification_select_populates_with_known_classification(
        self, test_app_client, logged_in_rdu_user
    ):
        measure_version = MeasureVersionWithDimensionFactory(version="1.0")
        response = test_app_client.get(self.builder_url(measure_version))

        assert response.status_code == 200
        page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
        classification_select = page.find("select", {"id": "custom_classification__selector"})
        classification_options = classification_select.find_all("option")
        assert len(classification_options) == 29
        assert {option.get_text(strip=True) for option in classification_options} == {
            "4 - Asian, Black, White, Other inc Mixed",
            "4 - Black, Mixed, White, Other inc Asian",
            "5 - Asian, Black, White British, White other, Other inc Mixed",
            "6 - Asian, Black African, Black Caribbean, Black other, White, Other",
            "6 - Asian, Black African, Black Caribbean, Black other, White, Other - Aggregates",
            "6 - Asian, Black, Mixed, White British, White other, Other",
            "6 - Asian, Black, Mixed, White British, White other, Other - Aggregates",
            "6 - Indian, Pakistani and Bangladeshi, Black, Mixed, White, Other",
            "7 - Asian, Black, Chinese, Mixed, White British, White other, Other",
            "7 - Asian, Black, Chinese, Mixed, White British, White other, Other - Aggregates",
            "8 - Indian, Pakistani and Bangladeshi, Asian other, Black, Mixed, White British, White other, Other",
            "8 - Indian, Pakistani and Bangladeshi, Asian other, Black, Mixed, White "
            "British, White other, Other - Aggregates",
            "APS detailed - 13",
            "APS detailed - 13 - Aggregates",
            "Annual population survey - 9",
            "DfE - 18+1",
            "DfE - 6+1",
            "Family resources survey - 10",
            "Longitudinal education outcomes - 10",
            "Longitudinal education outcomes - 10 - Aggregates",
            "Not applicable",
            "ONS 2001 - 16+1",
            "ONS 2001 - 5+1",
            "ONS 2011 - 18+1",
            "ONS 2011 - 5+1",
            "Please select",
            "Well-being survey - 12",
            "White British and Other",
            "White and Other",
        }  # TODO: Fix to use definitions/lookups from `test_data: https://trello.com/c/fwYpIWkD


class TestChartBuilder(_TestVisualisationBuilder):
    ROUTE_NAME = "cms.create_chart"


class TestTableBuilder(_TestVisualisationBuilder):
    ROUTE_NAME = "cms.create_table"
