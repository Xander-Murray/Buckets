# Buckets/forms/validation.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Tuple
from textual.widget import Widget

from Buckets.utils.format import parse_formula_expression

def _validate_number(
    value: str, field, is_float: bool = False
) -> Tuple[bool, str | None, Any]:
    if not value:
        return (
            (False, "Required", None)
            if getattr(field, "is_required", False)
            else (True, None, None)
        )

    num_val = parse_formula_expression(value) if is_float else int(value)

    if getattr(field, "min", None) is not None:
        min_val = float(field.min) if is_float else int(field.min)
        if num_val <= min_val:
            return False, f"Must be greater than {field.min}", None

    if getattr(field, "max", None) is not None:
        max_val = float(field.max) if is_float else int(field.max)
        if num_val > max_val:
            return False, f"Must be less than {field.max}", None

    return True, None, num_val

def _validate_date(
    value: str, field, auto_day: bool = False
) -> Tuple[datetime | None, str | None]:
    if not value:
        return (
            (None, "Required") if getattr(field, "is_required", False) else (None, None)
        )

    try:
        if auto_day and value.isdigit():
            this_month = datetime.now().strftime("%m")
            this_year = datetime.now().strftime("%y")
            return datetime.strptime(
                f"{value} {this_month} {this_year}", "%d %m %y"
            ), None
        return datetime.strptime(value, "%d %m %y"), None
    except ValueError:
        return None, (
            "Must be in dd (mm) (yy) format."
            if auto_day
            else "Must be in dd mm yy format"
        )

def _validate_autocomplete(
    value: str, held_value: str, field
) -> Tuple[bool, str | None]:
    if not value and not held_value:
        return (
            (False, "Must be selected")
            if getattr(field, "is_required", False)
            else (True, None)
        )

    items = getattr(getattr(field, "options", None), "items", None)
    if not items:
        return True, None

    if getattr(items[0], "text", None):
        matches = [item for item in items if item.text == value]
        if not matches:
            return False, "Invalid selection"
        return (
            (True, None)
            if any(str(item.value) == str(held_value) for item in matches)
            else (False, "Invalid selection")
        )
    else:
        return (
            (True, None)
            if held_value in [str(item.value) for item in items]
            else (False, "Invalid selection")
        )

def validateForm(
    formComponent: Widget, formData
) -> Tuple[Dict[str, Any], Dict[str, str], bool]:
    """
    Returns (result_dict, errors_dict, is_valid)
    Expects formData.fields list with .key, .type, .is_required, etc.
    """
    result: Dict[str, Any] = {}
    errors: Dict[str, str] = {}
    isValid = True

    for field in formData.fields:
        key = field.key
        fieldWidget = formComponent.query_one(f"#field-{key}")
        fieldValue = (
            getattr(fieldWidget, "heldValue", None)
            if hasattr(fieldWidget, "heldValue")
            else getattr(fieldWidget, "value", None)
        )

        error = None

        match field.type:
            case "integer":
                ok, error, num_val = _validate_number(fieldValue, field, is_float=False)
                if ok and num_val is not None:
                    result[key] = num_val
            case "number":
                ok, error, num_val = _validate_number(fieldValue, field, is_float=True)
                if ok and num_val is not None:
                    result[key] = num_val
            case "date":
                date, error = _validate_date(fieldValue, field, auto_day=False)
                if date:
                    result[key] = date
            case "dateAutoDay":
                date, error = _validate_date(fieldValue, field, auto_day=True)
                if date:
                    result[key] = date
            case "autocomplete":
                if getattr(field, "autocomplete_selector", False):
                    ok, error = _validate_autocomplete(
                        fieldWidget.value, fieldValue, field
                    )
                    if ok and fieldValue:
                        result[key] = fieldValue
                else:
                    if not fieldWidget.value and getattr(field, "is_required", False):
                        error = "Required"
                    else:
                        result[key] = fieldWidget.value
            case _:
                if not fieldValue and getattr(field, "is_required", False):
                    error = "Required"
                else:
                    result[key] = fieldValue

        if error:
            errors[key] = error
            isValid = False

    return result, errors, isValid
