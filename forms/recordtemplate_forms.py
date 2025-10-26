from rich.text import Text
from Buckets.managers.accounts import get_all_accounts_with_balance
from Buckets.managers.categories import get_all_categories_by_freq
from Buckets.managers.record_templates import get_template_by_id
from Buckets.forms.form import Form, FormField, Option, Options

_RECORD_TEMPLATE_FORM = Form(
    fields=[
        FormField(
            placeholder="Template label",
            title="Label",
            key="label",
            type="string",
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
    ]
)


class RecordTemplateForm:
    def _account_options(self) -> Options:
        accounts = get_all_accounts_with_balance()
        return Options(
            items=[
                Option(
                    text=acc.name,
                    value=acc.id,
                    postfix=Text(f"{acc.balance}", style="yellow"),
                )
                for acc in accounts
            ]
        )

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
                for c, _ in categories
            ]
        )

    def _base(self) -> Form:
        f = _RECORD_TEMPLATE_FORM.clone()
        f.fields[3].options = self._account_options()
        f.fields[1].options = self._category_options()
        return f

    def get_form(self) -> Form:
        return self._base()

    def get_filled_form(self, templateId: int) -> Form:
        f = self._base()
        template = get_template_by_id(templateId)
        for field in f.fields:
            k = field.key
            v = getattr(template, k)
            match k:
                case "isIncome":
                    field.default_value = bool(v)
                case "categoryId":
                    field.default_value = template.category.id
                    field.default_value_text = template.category.name
                case "accountId":
                    field.default_value = template.account.id
                    field.default_value_text = template.account.name
                case _:
                    field.default_value = "" if v is None else str(v)
        return f
