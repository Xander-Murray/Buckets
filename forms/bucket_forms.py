from rich.text import Text
from Buckets.forms.form import Form, FormField, Option, Options
from Buckets.managers.accounts import get_all_accounts_with_balance
from Buckets.managers.buckets import get_bucket_by_id, get_buckets_by_account

# blueprint (never mutated)
_BUCKET_BASE = Form(
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

class BucketForm:
    """Stateless: options populated per-call."""

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

    def get_form(self, default_account_id: int | None = None) -> Form:
        f = _BUCKET_BASE.clone()
        f.fields[2].options = self._account_options()
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
        if not b:
            return f
        for field in f.fields:
            if field.key == "accountId":
                field.default_value = b.accountId
                field.default_value_text = next(
                    (
                        opt.text
                        for opt in field.options.items
                        if opt.value == b.accountId
                    ),
                    "Account",
                )
            else:
                val = getattr(b, field.key)
                field.default_value = "" if val is None else str(val)
        return f

class BucketTransferForm:
    """Transfer funds between buckets within the selected account."""

    _FORM = Form(
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
        self.account_id = account_id

    def get_form(self) -> Form:
        f = self._FORM.clone()
        buckets = get_buckets_by_account(self.account_id) if self.account_id else []
        opts = Options(items=[Option(text=b.name, value=b.id) for b in buckets])
        f.fields[0].options = opts
        f.fields[1].options = opts
        return f
