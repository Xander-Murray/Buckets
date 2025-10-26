# Buckets/forms/record_forms.py
from __future__ import annotations

import copy
from datetime import datetime

from rich.text import Text

from Buckets.forms.form import Form, FormField, Option, Options
from Buckets.managers.accounts import get_all_accounts_with_balance
from Buckets.managers.categories import get_all_categories_by_freq
from Buckets.managers.record_templates import get_record_templates
from Buckets.managers.records import get_record_by_id


class RecordForm:
    """Form builder for creating / editing a Record (no splits / people)."""

    _instance: "RecordForm | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ------------ Blueprint ------------ #

    FORM = Form(
        fields=[
            FormField(
                placeholder="Label",
                title="Label / Template name",
                key="label",
                type="autocomplete",
                options=Options(),
                autocomplete_selector=False,
                is_required=True,
            ),
            FormField(
                title="Category",
                key="categoryId",
                type="autocomplete",
                options=Options(),
                is_required=True,
                placeholder="Select Category",
            ),
            FormField(
                placeholder="0.00",
                title="Amount",
                key="amount",
                type="number",
                min=0,
                is_required=True,
            ),
            FormField(
                title="Account",
                key="accountId",
                type="autocomplete",
                options=Options(),
                is_required=True,
                placeholder="Select Account",
            ),
            FormField(
                title="Type",
                key="isIncome",
                type="boolean",
                labels=["Expense", "Income"],
                default_value=False,
            ),
            FormField(
                placeholder="dd (mm) (yy)",
                title="Date",
                key="date",
                type="dateAutoDay",
                default_value=datetime.now().strftime("%d"),
            ),
        ]
    )

    # --------------- Init --------------- #

    def __init__(self) -> None:
        self._populate_form_options()

    # -------------- Helpers ------------- #

    def _populate_form_options(self) -> None:
        """Populate autocomplete options for templates, accounts, categories."""
        # Templates for label autocomplete (value = template.id)
        templates = get_record_templates()
        self.FORM.fields[0].options = Options(
            items=[
                Option(
                    text=template.label,
                    value=template.id,
                    postfix=Text(f"{template.amount}", style="yellow"),
                )
                for template in templates
            ]
        )

        # Accounts (with current balance)
        accounts = get_all_accounts_with_balance()
        self.FORM.fields[3].options = Options(
            items=[
                Option(
                    text=account.name,
                    value=account.id,
                    postfix=Text(f"{account.balance}", style="yellow"),
                )
                for account in accounts
            ]
        )
        if accounts:
            self.FORM.fields[3].default_value = accounts[0].id
            self.FORM.fields[3].default_value_text = accounts[0].name

        # Categories (sorted by usage frequency)
        categories = get_all_categories_by_freq()
        self.FORM.fields[1].options = Options(
            items=[
                Option(
                    text=category.name,
                    value=category.id,
                    prefix=Text("●", style=category.color),
                    postfix=(
                        Text(
                            f"↪ {category.parentCategory.name}",
                            style=category.parentCategory.color,
                        )
                        if category.parentCategory
                        else ""
                    ),
                )
                for category, _ in categories
            ]
        )

    # -------------- Builders ------------ #

    def get_filled_form(self, recordId: int):
        """
        Return a copy of the form filled with values from the record.

        Note: We return `(filled_form, Form())` to keep compatibility with
        any legacy callers that previously expected `(form, split_form)`.
        """
        filled_form = copy.deepcopy(self.FORM)
        record = get_record_by_id(recordId)

        for field in filled_form.fields:
            key = field.key
            value = getattr(record, key)

            match key:
                case "date":
                    if value and value.month == datetime.now().month:
                        field.default_value = value.strftime("%d")
                    else:
                        field.default_value = value.strftime("%d %m %y")
                case "isIncome":
                    field.default_value = bool(value)
                case "categoryId":
                    if record.category:
                        field.default_value = record.category.id
                        field.default_value_text = record.category.name
                case "accountId":
                    if record.account:
                        field.default_value = record.account.id
                        field.default_value_text = record.account.name
                case "label":
                    field.default_value = str(value) if value is not None else ""
                    field.type = "string"  # disable autocomplete when editing
                case _:
                    field.default_value = str(value) if value is not None else ""

        # No splits support anymore; return empty secondary form for compatibility.
        return filled_form, Form()

    def get_form(self, default_values: dict):
        form = copy.deepcopy(self.FORM)

        if not default_values:
            return form

        for field in form.fields:
            match field.key:
                case "date":
                    value = default_values["date"]
                    if value.month == datetime.now().month:
                        field.default_value = value.strftime("%d")
                    else:
                        field.default_value = value.strftime("%d %m %y")
                case "isIncome":
                    field.default_value = bool(default_values["isIncome"])
                case "accountId":
                    field.default_value = default_values["accountId"]["default_value"]
                    field.default_value_text = default_values["accountId"][
                        "default_value_text"
                    ]
        return form
