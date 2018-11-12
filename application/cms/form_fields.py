"""
This module extends a number of WTForm fields and widgets to provide custom integration with how RDU displays these
elements. We don't explicitly define HTML in this module; instead, we hook into templated fragments representing
the elements in the `application/templates/forms/` directory.
"""

from enum import Enum

from flask import render_template
from wtforms.fields import SelectMultipleField, RadioField, StringField, SelectField
from wtforms.widgets import HTMLString, TextInput, html_params


class _ChoiceInputs(Enum):
    CHECKBOX = "checkbox"
    RADIO = "radio"


def _coerce_enum_to_text(enum):
    def coerce(instance):
        return instance.name if isinstance(instance, enum) else instance

    return coerce


class _RDUTextInput(TextInput):
    TEXT_INPUT_TEMPLATE = "forms/_text_input.html"

    def __call__(self, field, textarea=False, diffs=None, **kwargs):
        return HTMLString(
            render_template(
                self.TEXT_INPUT_TEMPLATE, field=field, textarea=textarea, field_params=HTMLString(html_params(**kwargs))
            )
        )


class _RDUTextAreaInput(_RDUTextInput):
    def __call__(self, field, rows=10, cols=100, **kwargs):
        return super().__call__(field=field, textarea=True, rows=rows, cols=cols, **kwargs)


class _RDUURLInput(_RDUTextInput):
    input_type = "url"


class _RDUChoiceInput:
    CHOICE_INPUT_TEMPLATE = "forms/_choice_input.html"

    def __init__(self, type_: _ChoiceInputs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = type_.name

    def __call__(self, field, **kwargs):
        if getattr(field, "checked", field.data):
            kwargs["checked"] = True

        return HTMLString(
            render_template(
                self.CHOICE_INPUT_TEMPLATE, field=field, type=self.type, field_params=HTMLString(html_params(**kwargs))
            )
        )


class _FormGroup:
    FORM_GROUP_TEMPLATE = "forms/_form_group.html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.other_field = None

    def __call__(self, field, **kwargs):
        return HTMLString(
            render_template(
                self.FORM_GROUP_TEMPLATE,
                id=field.id,
                legend=field.label.text,
                fields=[subfield for subfield in field],
                errors=field.errors,
                disabled=kwargs.get("disabled", False),
                other_field=self.other_field,
                field_params=HTMLString(html_params(**kwargs)),
            )
        )

    def set_other_field(self, other_field):
        self.other_field = other_field


class RDUCheckboxField(SelectMultipleField):
    widget = _FormGroup()
    option_widget = _RDUChoiceInput(type_=_ChoiceInputs.CHECKBOX)

    def __init__(self, label=None, validators=None, enum=None, **kwargs):
        if enum:
            if kwargs.get("choices") or kwargs.get("coerce"):
                raise ValueError(
                    f"Cannot initialise {self.__cls__}: mutually exclusive arguments: (enum,) vs (choices, coerce)"
                )
            kwargs["choices"] = tuple([(e.name, e.value) for e in enum])
            kwargs["coerce"] = _coerce_enum_to_text(enum)

        super().__init__(label, validators, **kwargs)


class RDURadioField(RadioField):
    """
    A radio-button field that supports showing/hiding a different field based on whether the last radio has been
    selected - the current limitation/expectation being that the last field is an "other" selection.
    """

    _widget_class = _FormGroup
    widget = _widget_class()
    option_widget = _RDUChoiceInput(type_=_ChoiceInputs.RADIO)

    def set_other_field(self, other_field):
        # Create a new instance of the widget in order to store instance-level attributes on it without attaching them
        # to the class-level widget.
        self.widget = self._widget_class()
        self.widget.set_other_field(other_field)


class RDUStringField(StringField):
    widget = _RDUTextInput()

    def __init__(self, label=None, validators=None, hint=None, **kwargs):
        kwargs["filters"] = kwargs.get("filters", [])

        # Automatically coalesce `None` values to blank strings
        kwargs["filters"].append(lambda x: x or "")

        super().__init__(label, validators, **kwargs)
        self.hint = hint

    def populate_obj(self, obj, name):
        """
        If the user enters a blank string into the field, we'll store it as a null in the database.
        Pri marily this avoids a FK constraint error on `data_source.publisher_id`, where we get a blank string back
        if the user leaves the 'please select' default option selected.
        """

        setattr(obj, name, self.data if self.data else None)


class RDUTextAreaField(RDUStringField):
    widget = _RDUTextAreaInput()


class RDUURLField(RDUStringField):
    widget = _RDUURLInput()