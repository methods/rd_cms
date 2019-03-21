"""
This module extends a number of WTForm fields and widgets to provide custom integration with how RDU displays these
elements. We don't explicitly define HTML in this module; instead, we hook into templated fragments representing
the elements in the `application/templates/forms/` directory.
"""

from enum import Enum
from functools import partial


from flask import render_template
from markupsafe import Markup
from wtforms.fields import SelectMultipleField, RadioField, StringField
from wtforms.widgets import HTMLString, html_params


class _ChoiceInputs(Enum):
    CHECKBOX = "checkbox"
    RADIO = "radio"


def _coerce_enum_to_text(enum):
    def coerce(instance):
        return instance.name if isinstance(instance, enum) else instance

    return coerce


def _coerce_none_to_blank_string(value):
    return value or ""


def _coerce_string_none_to_python_none(value):
    return None if value == "None" else value


def _strip_whitespace(value):
    if value is not None and hasattr(value, "strip"):
        return value.strip()
    return value


class _FormFieldTemplateRenderer:
    def __call__(self, field, id_, name, class_, diffs, disabled, render_params, field_params):
        if disabled:
            field_params["disabled"] = True

        return HTMLString(
            render_template(
                self.TEMPLATE,
                field=field,
                id_=id_,
                name=name,
                class_=class_,
                errors=field.errors,
                diffs=diffs,
                disabled=disabled,  # This needs to be sent both to the template and to the field (for choice inputs)
                **render_params,
                field_params=HTMLString(html_params(**field_params)),
            )
        )


class _RDUTextInput(_FormFieldTemplateRenderer):
    TEMPLATE = "forms/_text_input.html"
    input_type = "text"

    def __call__(self, field, class_="", diffs=None, disabled=False, textarea=False, **kwargs):
        value = {"value": field.data}

        field_params = {} if textarea else {"type": self.input_type}
        field_params = {**field_params, **kwargs}

        return super().__call__(
            field=field,
            id_=field.id,
            name=field.name,
            class_=class_,
            diffs=diffs,
            disabled=disabled,
            render_params={"textarea": textarea, **value},
            field_params=field_params,
        )


class _RDUPasswordInput(_RDUTextInput):
    input_type = "password"


class _RDUTextAreaInput(_RDUTextInput):
    def __call__(self, field, class_="", diffs=None, disabled=False, rows=10, cols=100, **kwargs):
        if rows:
            kwargs["rows"] = rows
        if cols:
            kwargs["cols"] = cols

        return super().__call__(field=field, diffs=diffs, disabled=disabled, class_=class_, textarea=True, **kwargs)


class _RDUURLInput(_RDUTextInput):
    input_type = "url"


class _RDUChoiceInput(_FormFieldTemplateRenderer):
    TEMPLATE = "forms/_choice_input.html"

    def __init__(self, field_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_type = field_type

    def __call__(self, field, class_="", diffs=None, disabled=False, **kwargs):
        if getattr(field, "checked", field.data):
            kwargs["checked"] = True

        return super().__call__(
            field=field,
            id_=field.id,
            name=field.name,
            class_=class_,
            diffs=diffs,
            disabled=disabled,
            render_params={"value": field.data, "field_type": self.field_type.value},
            field_params={**kwargs},
        )


class _FormGroup(_FormFieldTemplateRenderer):
    TEMPLATE = "forms/_form_group.html"

    def __init__(self, field_type: _ChoiceInputs, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.field_type = field_type
        self.other_field = None

    def __call__(
        self, field, class_="", fieldset_class="", legend_class="", field_class="", diffs=None, disabled=False, **kwargs
    ):
        subfields = [subfield for subfield in field]

        return super().__call__(
            field=field,
            id_=field.id,
            name=field.name,
            class_=class_,
            diffs=diffs,
            disabled=disabled,
            render_params={
                "fields": subfields,
                "other_field": self.other_field,
                "fieldset_class": fieldset_class,
                "legend_class": legend_class,
                "field_class": field_class,
                "field_type": self.field_type.value,
            },
            field_params={**kwargs},
        )

    def set_other_field(self, other_field):
        self.other_field = other_field


class RDUCheckboxField(SelectMultipleField):
    widget = _FormGroup(field_type=_ChoiceInputs.CHECKBOX)
    option_widget = _RDUChoiceInput(field_type=widget.field_type)

    def __init__(self, label=None, validators=None, enum=None, hint=None, **kwargs):
        if enum:
            if kwargs.get("choices") or kwargs.get("coerce"):
                raise ValueError(
                    f"Cannot initialise {self.__cls__}: mutually exclusive arguments: (enum,) vs (choices, coerce)"
                )
            kwargs["choices"] = tuple([(e.name, e.value) for e in enum])
            kwargs["coerce"] = _coerce_enum_to_text(enum)

        self.hint = hint
        super().__init__(label, validators, **kwargs)


class RDURadioField(RadioField):
    """
    A radio-button field that supports showing/hiding a different field based on whether the last radio has been
    selected - the current limitation/expectation being that the last field is an "other" selection.
    """

    _widget_class = partial(_FormGroup, field_type=_ChoiceInputs.RADIO)
    widget = _widget_class()
    option_widget = _RDUChoiceInput(field_type=widget.field_type)

    def __init__(self, label=None, validators=None, hint=None, **kwargs):
        kwargs["filters"] = kwargs.get("filters", [])
        if _coerce_string_none_to_python_none not in kwargs["filters"]:
            kwargs["filters"].append(_coerce_string_none_to_python_none)

        super().__init__(label, validators, **kwargs)
        self.hint = hint

    def set_other_field(self, other_field):
        # Create a new instance of the widget in order to store instance-level attributes on it without attaching them
        # to the class-level widget.
        self.widget = self._widget_class()
        self.widget.set_other_field(other_field)


class RDUStringField(StringField):
    widget = _RDUTextInput()

    def __init__(
        self,
        label=None,
        validators=None,
        hint=None,
        extended_hint=None,
        strip_whitespace=False,
        character_count_limit=None,
        **kwargs,
    ):
        # Automatically coalesce `None` values to blank strings
        # If we get null values from the database, we don't want to render these as 'None' strings in form fields.
        kwargs["filters"] = kwargs.get("filters", [])
        if _coerce_none_to_blank_string not in kwargs["filters"]:
            kwargs["filters"].append(_coerce_none_to_blank_string)

        if strip_whitespace and _strip_whitespace not in kwargs["filters"]:
            kwargs["filters"].append(_strip_whitespace)
        elif not strip_whitespace and _strip_whitespace in kwargs["filters"]:
            kwargs["filters"].remove(_strip_whitespace)

        super().__init__(label, validators, **kwargs)
        self.hint = hint
        self.character_count_limit = character_count_limit
        self.extended_hint = Markup(render_template(f"forms/extended_hints/{extended_hint}")) if extended_hint else None

    def populate_obj(self, obj, name):
        """
        If the user enters a blank string into the field, we'll store it as a null in the database.
        Primarily this avoids a FK constraint error on `data_source.publisher_id`, where we get a blank string back
        if the user leaves the 'please select' default option selected.
        """

        setattr(obj, name, self.data if self.data else None)


class RDUTextAreaField(RDUStringField):
    widget = _RDUTextAreaInput()


class RDUPasswordField(RDUStringField):
    widget = _RDUPasswordInput()


class RDUURLField(RDUStringField):
    widget = _RDUURLInput()
