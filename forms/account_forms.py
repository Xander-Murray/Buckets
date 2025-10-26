import copy
from Buckets.managers.accounts import get_account_by_id
from Buckets.forms.form import Form, FormField


class AccountForm:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    FORM = Form(
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

    def get_filled_form(self, accountId: int):
        form = copy.deepcopy(self.FORM)
        account = get_account_by_id(accountId)
        for field in form.fields:
            value = getattr(account, field.key)
            field.default_value = str(value) if value is not None else ""
        return form

    def get_form(self):
        return copy.deepcopy(self.FORM)
