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
from Buckets.managers.buckets import get_buckets_by_account  # ← fix import

# blueprint (never mutated)
_RECORD_FORM = Form(
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
        FormField(  # ← bucket is optional; used for expenses to subtract from
            title="Bucket",
            key="bucketId",
            type="autocomplete",
            options=Options(),
            is_required=False,
            placeholder="Select Bucket",
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

class RecordForm:
    """Stateless; options are populated per call."""

    # ---------- options builders ---------- #

    def _template_options(self) -> Options:
        templates = get_record_templates()
        return Options(
            items=[
                Option(
                    text=t.label,
                    value=t.id,
                    postfix=Text(f"{t.amount}", style="yellow"),
                )
                for t in templates
            ]
        )

    def _account_options(self) -> Options:
        accounts = get_all_accounts_with_balance()
        return Options(
            items=[
                Option(
                    text=a.name,
                    value=a.id,
                    postfix=Text(f"{a.balance}", style="yellow"),
                )
                for a in accounts
            ]
        )

    def _bucket_options(self, account_id: int | None) -> Options:
        """Buckets are scoped to the chosen account; empty list if none."""
        if not account_id:
            return Options(items=[])
        buckets = get_buckets_by_account(account_id)
        return Options(items=[Option(text=b.name, value=b.id) for b in buckets])

    def _category_options(self) -> Options:
        categories = get_all_categories_by_freq()
        return Options(
            items=[
                Option(
                    text=c.name,
                    value=c.id,
                    prefix=Text("●", style=c.color),
                    postfix=(
                        Text(f"↪ {c.parentCategory.name}", style=c.parentCategory.color)
                        if c.parentCategory
                        else ""
                    ),
                )
                for c, _freq in categories
            ]
        )

    # ---------- base form ---------- #

    def _base_form_with_options(self) -> Form:
        # deep copy to keep the blueprint immutable
        f = copy.deepcopy(_RECORD_FORM)

        # label (templates), category, account get populated now
        f.fields[0].options = self._template_options()
        f.fields[1].options = self._category_options()
        f.fields[4].options = self._account_options()  # index 4 = accountId

        # pick a default account if available
        acc_items = f.fields[4].options.items
        if acc_items:
            f.fields[4].default_value = acc_items[0].value
            f.fields[4].default_value_text = acc_items[0].text
            # populate bucket list for that default account
            f.fields[3].options = self._bucket_options(
                acc_items[0].value
            )  # index 3 = bucketId
        else:
            f.fields[3].options = Options(items=[])

        return f

    # ---------- public builders ---------- #

    def get_form(self, default_values: dict) -> Form:
        """
        Build a new-record form. Buckets are filled from the chosen/default account.
        """
        f = self._base_form_with_options()

        if default_values:
            for field in f.fields:
                match field.key:
                    case "date":
                        value = default_values["date"]
                        field.default_value = (
                            value.strftime("%d")
                            if value.month == datetime.now().month
                            else value.strftime("%d %m %y")
                        )
                    case "isIncome":
                        field.default_value = bool(default_values["isIncome"])
                    case "accountId":
                        field.default_value = default_values["accountId"][
                            "default_value"
                        ]
                        field.default_value_text = default_values["accountId"][
                            "default_value_text"
                        ]
                        # refresh bucket options for the *selected* account
                        f.fields[3].options = self._bucket_options(field.default_value)

        return f

    def get_filled_form(self, recordId: int):
        """
        Build an edit form pre-filled with the record's values.
        Returns (form, empty_secondary_form) for legacy compatibility.
        """
        f = self._base_form_with_options()
        record = get_record_by_id(recordId)

        # If the record has an account, refill bucket options based on that account
        if record.account:
            f.fields[3].options = self._bucket_options(record.account.id)

        for field in f.fields:
            key = field.key
            value = getattr(record, key, None)

            match key:
                case "date":
                    if value:
                        field.default_value = (
                            value.strftime("%d")
                            if value.month == datetime.now().month
                            else value.strftime("%d %m %y")
                        )
                case "bucketId":
                    if getattr(record, "bucket", None):
                        field.default_value = record.bucket.id
                        field.default_value_text = record.bucket.name
                case "isIncome":
                    field.default_value = bool(value)
                case "categoryId":
                    if getattr(record, "category", None):
                        field.default_value = record.category.id
                        field.default_value_text = record.category.name
                case "accountId":
                    if getattr(record, "account", None):
                        field.default_value = record.account.id
                        field.default_value_text = record.account.name
                case "label":
                    field.default_value = "" if value is None else str(value)
                    # disable autocomplete when editing label
                    field.type = "string"
                case _:
                    field.default_value = "" if value is None else str(value)

        # return an extra empty Form() as some callers still expect a tuple
        return f, Form()
