from datetime import datetime
from rich.text import Text
from Buckets.forms.form import Form, FormField, Option, Options
from Buckets.managers.record_templates import get_transfer_templates
from Buckets.models.record import Record

_TRANSFER_FORM = Form(
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
            title="Amount",
            key="amount",
            type="number",
            placeholder="0.00",
            min=0,
            is_required=True,
        ),
        FormField(
            title="Date", key="date", type="dateAutoDay", placeholder="dd (mm) (yy)"
        ),
    ]
)

_TRANSFER_TEMPLATE_FORM = Form(
    fields=[
        FormField(
            title="Label",
            key="label",
            type="string",
            placeholder="Label",
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
    ]
)

class TransferForm:
    def __init__(self, isTemplate: bool = False, defaultDate: str | None = None):
        self.isTemplate = isTemplate
        self.defaultDate = defaultDate

    def _template_options(self) -> Options:
        templates = get_transfer_templates()
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

    def _base(self) -> Form:
        f = (_TRANSFER_TEMPLATE_FORM if self.isTemplate else _TRANSFER_FORM).clone()
        if not self.isTemplate:
            f.fields[0].options = self._template_options()
            f.fields[2].default_value = self.defaultDate
        return f

    def get_form(self, hidden_fields: dict = {}):
        f = self._base()
        for field in f.fields:
            if field.key in hidden_fields:
                field.type = "hidden"
                v = hidden_fields[field.key]
                if isinstance(v, dict):
                    field.default_value = v.get("default_value")
                    field.default_value_text = v.get("default_value_text")
                else:
                    field.default_value = v
        return f

    def get_filled_form(self, record: Record) -> Form:
        f = self._base()
        if not record.isTransfer:
            return f
        for field in f.fields:
            k = field.key
            v = getattr(record, k)
            match k:
                case "date":
                    field.default_value = (
                        v.strftime("%d")
                        if v.month == datetime.now().month
                        else v.strftime("%d %m %y")
                    )
                case "label":
                    field.default_value = "" if v is None else str(v)
                    field.type = "string"  # disable autocomplete
                case _:
                    field.default_value = "" if v is None else str(v)
        return f
