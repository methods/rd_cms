from unittest import mock

from flask import session, request, current_app, flash, get_flashed_messages, url_for, render_template
from flask_wtf import FlaskForm
from lxml import html
import pytest
from wtforms.validators import DataRequired

from application.cms.forms import DataSourceForm, DataSource2Form
from application.cms.form_fields import RDUStringField
from application.cms.utils import copy_form_errors, flash_message_with_form_errors, get_data_source_forms


class TestCopyFormErrors:
    class FormForTest(FlaskForm):
        field = RDUStringField(label="field", validators=[DataRequired()])

    def test_copies_to_top_level_form_errors_attribute(self):
        form = self.FormForTest()
        clean_form = self.FormForTest()
        form.validate()
        assert form.errors
        assert not clean_form.errors

        copy_form_errors(from_form=form, to_form=clean_form)

        assert clean_form.errors

    def test_copies_to_field_level_errors_attribute(self):
        form = self.FormForTest()
        clean_form = self.FormForTest()
        form.validate()
        assert form.field.errors
        assert not clean_form.field.errors

        copy_form_errors(from_form=form, to_form=clean_form)

        assert clean_form.field.errors


class TestFlashMessageWithFormErrors:
    class FormForTest(FlaskForm):
        field = RDUStringField(label="field", validators=[DataRequired("invalid field")])

    def test_flash_message_inserted_into_session(self):
        form = self.FormForTest()
        form.validate()
        assert not session.get("_flashes")

        flash_message_with_form_errors(forms=[form])

        assert session.get("_flashes") == [("error", "Please see below errors:\n\n* [field](#field): invalid field\n")]


class TestGetDataSourceForms:
    def setup(self):
        self.saved_config = {**current_app.config}

    def teardown(self):
        current_app.config = {**self.saved_config}

    def test_returns_two_data_source_forms(self, stub_measure_page):
        form1, form2 = get_data_source_forms(request, stub_measure_page)

        assert isinstance(form1, DataSourceForm)
        assert isinstance(form2, DataSourceForm)

    def test_returned_forms_have_distinct_prefixes(self, stub_measure_page):
        form1, form2 = get_data_source_forms(request, stub_measure_page)

        assert form1._prefix == "data-source-1-"
        assert form2._prefix == "data-source-2-"

    @pytest.mark.parametrize("csrf_enabled", [True, False])
    def test_csrf_enabled_depending_on_app_config(self, stub_measure_page, csrf_enabled):
        current_app.config["WTF_CSRF_ENABLED"] = csrf_enabled

        form1, form2 = get_data_source_forms(request, stub_measure_page)

        assert form1.meta.csrf is csrf_enabled
        assert form2.meta.csrf is csrf_enabled

    def test_csrf_disabled_if_sending_to_review(self, stub_measure_page):
        assert current_app.config["WTF_CSRF_ENABLED"] is False

        form1, form2 = get_data_source_forms(request, stub_measure_page, sending_to_review=True)

        assert form1.meta.csrf is False
        assert form2.meta.csrf is False


class TestFlashMessages:
    def test_markdown_rendered_in_template(self, test_app_client, mock_logged_in_rdu_user):
        flash("text that should be markdown'd\n\n* a list item")

        doc = html.fromstring(render_template("base.html"))

        flash_message = doc.xpath("//div[@class='flash-message']")
        assert flash_message
        assert "text that should be markdown'd" in flash_message[0].text_content()
        assert flash_message[0].xpath("//li[contains(text(), 'a list item')]")
