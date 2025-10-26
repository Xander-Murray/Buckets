# forms/bucket_forms.py
import copy
from rich.text import Text

from Buckets.forms.form import Form, FormField, Option, Options
from Buckets.managers.accounts import get_all_accounts_with_balance
from Buckets.managers.buckets import get_bucket_by_id, get_buckets_by_account


class BucketForm:
    """Create/Edit bucket form."""

    BASE = Form(
        fields=[
            FormField(
                title="Name",
                key="name",
                type="string",
                placeholder="My Bucket",
                is_required=True,
            ),
            FormField(
                title="Amount",
                key="amount",
                type="number",
                placeholder="0.00",
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
        ]
    )

    def __init__(self) -> None:
        # populate account options
        accounts = get_all_accounts_with_balance()
        self.BASE.fields[2].options = Options(
            items=[
                Option(
                    text=acc.name,
                    value=acc.id,
                    postfix=Text(f"{acc.balance}", style="yellow"),
                )
                for acc in accounts
            ]
        )

    def get_form(self, default_account_id: int | None = None) -> Form:
        f = copy.deepcopy(self.BASE)
        if default_account_id:
            f.fields[2].default_value = default_account_id
            for opt in f.fields[2].options.items:
                if opt.value == default_account_id:
                    f.fields[2].default_value_text = opt.text
                    break
        return f

    def get_filled_form(self, bucket_id: int) -> Form:
        b = get_bucket_by_id(bucket_id)
        f = self.get_form(default_account_id=b.accountId if b else None)
        if b:
            for field in f.fields:
                match field.key:
                    case "accountId":
                        field.default_value = b.accountId
                        field.default_value_text = next(
                            (
                                opt.text
                                for opt in field.options.items
                                if opt.value == b.accountId
                            ),
                            "Account",
                        )
                    case _:
                        field.default_value = (
                            str(getattr(b, field.key))
                            if getattr(b, field.key) is not None
                            else ""
                        )
        return f


class BucketTransferForm:
    """Transfer funds between buckets within the selected account."""

    BASE = Form(
        fields=[
            FormField(
                title="From",
                key="fromBucketId",
                type="autocomplete",
                options=Options(),
                is_required=True,
                placeholder="Select source bucket",
            ),
            FormField(
                title="To",
                key="toBucketId",
                type="autocomplete",
                options=Options(),
                is_required=True,
                placeholder="Select destination bucket",
            ),
            FormField(
                title="Amount",
                key="amount",
                type="number",
                placeholder="0.00",
                min=0,
                is_required=True,
            ),
        ]
    )

    def __init__(self, account_id: int | None) -> None:
        buckets = get_buckets_by_account(account_id) if account_id else []
        opts = Options(items=[Option(text=b.name, value=b.id) for b in buckets])
        self.BASE.fields[0].options = opts
        self.BASE.fields[1].options = opts

    def get_form(self) -> Form:
        return copy.deepcopy(self.BASE)
