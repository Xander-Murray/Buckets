from Buckets.managers.accounts import get_account_by_id
from Buckets.forms.form import Form, FormField

# blueprint (never mutated)
_ACCOUNT_FORM = Form(
    fields=[
        FormField(
            placeholder="My Account",
            title="Name",
            key="name",
            type="string",
            is_required=True,
        ),
        FormField(
            placeholder="0.00",
            title="Beginning Balance",
            key="beginningBalance",
            type="number",
            default_value="0",
            is_required=True,
        ),
        FormField(
            placeholder="(Optional) Number, purpose etc.",
            title="Description",
            key="description",
            type="string",
        ),
    ]
)

class AccountForm:
    """Stateless factory wrapper to match existing call sites."""

    def get_form(self) -> Form:
        return _ACCOUNT_FORM.clone()

    def get_filled_form(self, accountId: int) -> Form:
        form = _ACCOUNT_FORM.clone()
        account = get_account_by_id(accountId)
        if not account:
            return form
        for field in form.fields:
            value = getattr(account, field.key)
            field.default_value = "" if value is None else str(value)
        return form
