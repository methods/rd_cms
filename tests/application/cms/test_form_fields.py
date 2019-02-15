import enum
from lxml import html
from unittest import mock

from flask_wtf import FlaskForm
from werkzeug.datastructures import ImmutableMultiDict
from wtforms.validators import DataRequired
import pytest

from application.cms.form_fields import (
    _coerce_enum_to_text,
    RDUCheckboxField,
    RDURadioField,
    RDUStringField,
    RDUTextAreaField,
    RDUURLField,
)


class TestCoerceEnumToText:
    class EnumForTest(enum.Enum):
        ONE = 1
        TWO = 2
        THREE = 3

    def test_returns_function(self):
        assert type(_coerce_enum_to_text(self.EnumForTest)).__name__ == "function"

    def test_returned_function_returns_enum_names_if_input_is_an_enum(self):
        assert _coerce_enum_to_text(self.EnumForTest)(self.EnumForTest.ONE) == "ONE"

    def test_returned_function_returns_input_if_input_is_not_an_enum(self):
        assert _coerce_enum_to_text(self.EnumForTest)("other value") == "other value"


class TestRDUCheckboxField:
    class FormForTest(FlaskForm):
        class EnumForTest(enum.Enum):
            ONE = "one"
            TWO = "two"
            THREE = "three"

        checkbox_field = RDUCheckboxField(label="checkbox_field", choices=[(1, "one"), (2, "two"), (3, "three")])
        checkbox_field_invalid = RDUCheckboxField(
            label="checkbox_field",
            choices=[(1, 1), (2, 2), (3, 3)],
            validators=[DataRequired(message="failed validation")],
        )
        checkbox_field_enum = RDUCheckboxField(label="checkbox_field", enum=EnumForTest)
        other_field = RDUStringField(label="other_field")

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_legend_is_rendered(self):
        doc = html.fromstring(self.form.checkbox_field())

        assert doc.xpath("//legend")
        assert "checkbox_field" in doc.xpath("//legend")[0].text

    def test_checkbox_choices_are_rendered(self):
        doc = html.fromstring(self.form.checkbox_field())

        assert len(doc.xpath("//input[@type='checkbox']")) == 3

    def test_checkbox_choices_have_correct_values(self):
        doc = html.fromstring(self.form.checkbox_field())

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for i, checkbox in enumerate(checkboxes):
            assert checkbox.get("value") == str(self.form.checkbox_field.choices[i][0])

    def test_checkbox_can_render_choices_from_enum(self):
        doc = html.fromstring(self.form.checkbox_field_enum())

        assert len(doc.xpath("//input[@type='checkbox']")) == 3
        assert doc.xpath("//input[@type='checkbox']/following-sibling::label/text()") == ["one", "two", "three"]

    def test_checkbox_enum_choices_have_correct_values(self):
        doc = html.fromstring(self.form.checkbox_field_enum())

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for checkbox, e in zip(checkboxes, [e for e in self.form.EnumForTest]):
            assert checkbox.get("value") == e.name
            assert checkbox.xpath("following-sibling::label")[0].text == e.value

    def test_checkbox_labels_are_rendered(self):
        doc = html.fromstring(self.form.checkbox_field())

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for i, checkbox in enumerate(checkboxes):
            label = checkbox.xpath("following-sibling::label")[0]
            assert label.text == self.form.checkbox_field.choices[i][1]

    @pytest.mark.parametrize("disabled", [True, False])
    def test_render_field_with_disabled_causes_all_inputs_to_be_disabled(self, disabled):
        doc = html.fromstring(self.form.checkbox_field(disabled=disabled))

        checkboxes = doc.xpath("//input[@type='checkbox']")
        for checkbox in checkboxes:
            assert checkbox.get("disabled") == ("disabled" if disabled else None)


class TestRDURadioField:
    class FormForTest(FlaskForm):
        radio_field = RDURadioField(label="radio_field", choices=[(1, "one"), (2, "two"), (3, "three")])
        radio_field_invalid = RDURadioField(
            label="radio_field",
            choices=[(1, 1), (2, 2), (3, 3)],
            validators=[DataRequired(message="failed validation")],
        )
        other_field = RDUStringField(label="other_field")

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_legend_is_rendered(self):
        doc = html.fromstring(self.form.radio_field())

        assert doc.xpath("//legend")
        assert "radio_field" in doc.xpath("//legend")[0].text

    def test_radio_choices_are_rendered(self):
        doc = html.fromstring(self.form.radio_field())

        assert len(doc.xpath("//input[@type='radio']")) == 3

    def test_radio_choices_have_correct_values(self):
        doc = html.fromstring(self.form.radio_field())

        radios = doc.xpath("//input[@type='radio']")
        for i, radio in enumerate(radios):
            assert radio.get("value") == str(self.form.radio_field.choices[i][0])

    def test_radio_labels_are_rendered(self):
        doc = html.fromstring(self.form.radio_field())

        radios = doc.xpath("//input[@type='radio']")
        for i, radio in enumerate(radios):
            label = radio.xpath("following-sibling::label")[0]
            assert label.text == self.form.radio_field.choices[i][1]

    @pytest.mark.parametrize("disabled", [True, False])
    def test_render_field_with_disabled_causes_all_inputs_to_be_disabled(self, disabled):
        doc = html.fromstring(self.form.radio_field(disabled=disabled))

        radios = doc.xpath("//input[@type='radio']")
        for radio in radios:
            assert radio.get("disabled") == ("disabled" if disabled else None)

    def test_other_field_is_rendered(self):
        self.form.radio_field.set_other_field(self.form.other_field)
        doc = html.fromstring(self.form.radio_field())

        assert len(doc.xpath("//input[@type='text']")) == 1

    def test_other_field_includes_show_hide_script(self):
        self.form.radio_field.set_other_field(self.form.other_field)
        doc = html.fromstring(self.form.radio_field())

        assert "showHideControl" in doc.xpath("//script")[0].text


class TestRDUStringField:
    class FormForTest(FlaskForm):
        string_field = RDUStringField(label="string_field", hint="string_field hint")
        string_field_invalid = RDUStringField(
            label="string_field", hint="string_field hint", validators=[DataRequired(message="failed validation")]
        )
        string_field_strip = RDUStringField(label="string_field_strip", strip_whitespace=True)

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_label_is_rendered(self):
        doc = html.fromstring(self.form.string_field())

        assert doc.xpath("//label")

    def test_input_element_is_rendered(self):
        doc = html.fromstring(self.form.string_field())

        assert doc.xpath("//input[@type='text']")

    def test_hint_is_rendered_if_no_errors(self):
        doc = html.fromstring(self.form.string_field())

        assert not self.form.string_field.errors
        assert doc.xpath("//*[text()='string_field hint']")

    def test_hint_is_still_rendered_when_field_has_errors(self):
        self.form.validate()
        doc = html.fromstring(self.form.string_field_invalid())

        assert self.form.string_field_invalid.errors
        assert doc.xpath("//*[text()='string_field hint']")

    def test_error_message_rendered_if_field_fails_validation(self):
        self.form.validate()
        doc = html.fromstring(self.form.string_field_invalid())

        assert self.form.string_field_invalid.errors
        assert doc.xpath("//*[text()='failed validation']")

    def test_can_populate_object_with_data_from_field(self):
        formdata = ImmutableMultiDict({"string_field": "some data"})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.string_field == "some data"

    def test_populates_obj_with_none_if_value_is_empty_string(self):
        formdata = ImmutableMultiDict({"string_field": ""})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.string_field is None

    def test_can_strip_whitespace(self):
        formdata = ImmutableMultiDict({"string_field": "   blah   ", "string_field_strip": "   blah   "})
        self.form.process(formdata=formdata)

        assert self.form.string_field.data == "   blah   "
        assert self.form.string_field_strip.data == "blah"


class TestRDUURLField:
    class FormForTest(FlaskForm):
        url_field = RDUURLField(label="url_field", hint="url_field hint")
        url_field_invalid = RDUURLField(
            label="url_field", hint="url_field hint", validators=[DataRequired(message="failed validation")]
        )

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_label_is_rendered(self):
        doc = html.fromstring(self.form.url_field())

        assert doc.xpath("//label")

    def test_input_element_is_rendered(self):
        doc = html.fromstring(self.form.url_field())

        assert doc.xpath("//input[@type='url']")

    def test_hint_is_rendered_if_no_errors(self):
        doc = html.fromstring(self.form.url_field())

        assert not self.form.url_field.errors
        assert doc.xpath("//*[text()='url_field hint']")

    def test_hint_is_still_rendered_when_field_has_errors(self):
        self.form.validate()
        doc = html.fromstring(self.form.url_field_invalid())

        assert self.form.url_field_invalid.errors
        assert doc.xpath("//*[text()='url_field hint']")

    def test_error_message_rendered_if_field_fails_validation(self):
        self.form.validate()
        doc = html.fromstring(self.form.url_field_invalid())

        assert self.form.url_field_invalid.errors
        assert doc.xpath("//*[text()='failed validation']")

    def test_can_populate_object_with_data_from_field(self):
        formdata = ImmutableMultiDict({"url_field": "some data"})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.url_field == "some data"


class TestRDUTextAreaField:
    class FormForTest(FlaskForm):
        textarea_field = RDUTextAreaField(label="textarea_field", hint="textarea_field hint")
        textarea_field_invalid = RDUTextAreaField(
            label="textarea_field", hint="textarea_field hint", validators=[DataRequired(message="failed validation")]
        )

    def setup(self):
        self.form = self.FormForTest()

    def teardown(self):
        self.form = None

    def test_label_is_rendered(self):
        doc = html.fromstring(self.form.textarea_field())

        assert doc.xpath("//label")

    def test_input_element_is_rendered(self):
        doc = html.fromstring(self.form.textarea_field())

        assert doc.xpath("//textarea")

    def test_hint_is_rendered_if_no_errors(self):
        doc = html.fromstring(self.form.textarea_field())

        assert not self.form.textarea_field.errors
        assert doc.xpath("//*[text()='textarea_field hint']")

    def test_hint_is_still_rendered_when_field_has_errors(self):
        self.form.validate()
        doc = html.fromstring(self.form.textarea_field_invalid())

        assert self.form.textarea_field_invalid.errors
        assert doc.xpath("//*[text()='textarea_field hint']")

    def test_error_message_rendered_if_field_fails_validation(self):
        self.form.validate()
        doc = html.fromstring(self.form.textarea_field_invalid())

        assert self.form.textarea_field_invalid.errors
        assert doc.xpath("//*[text()='failed validation']")

    def test_can_populate_object_with_data_from_field(self):
        formdata = ImmutableMultiDict({"textarea_field": "some data"})
        self.form.process(formdata=formdata)
        obj = mock.Mock()

        self.form.populate_obj(obj)

        assert obj.textarea_field == "some data"
