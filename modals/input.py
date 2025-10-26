from textual import events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, Switch  # ← add Switch

from Buckets.components.fields import Fields
from Buckets.modals.base_widget import ModalContainer
from Buckets.forms.form import Form
from Buckets.utils.validation import validateForm


class InputModal(ModalScreen):
    def __init__(self, title: str, form: Form, *args, **kwargs):
        super().__init__(classes="modal-screen", *args, **kwargs)
        self.title = title
        self.form = form

    # --------------- Hooks -------------- #
    def on_mount(self) -> None:
        self._sync_bucket_visibility()

    def on_key(self, event: events.Key):
        if event.key == "down":
            self.screen.focus_next()
        elif event.key == "up":
            self.screen.focus_previous()
        elif event.key == "enter":
            self.action_submit()
        elif event.key == "escape":
            self.dismiss(None)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        if event.switch.id == "field-isIncome":
            self._sync_bucket_visibility()

    def _sync_bucket_visibility(self) -> None:
        """Hide the Bucket row when isIncome is True. Show when False."""
        is_income = False
        try:
            is_income = self.query_one("#field-isIncome", Switch).value
        except Exception:
            return

        try:
            bucket_row = self.query_one("#row-field-bucketId")
        except Exception:
            return

        bucket_row.display = not is_income

        if is_income:
            try:
                bucket_widget = self.query_one("#field-bucketId")
                if hasattr(bucket_widget, "heldValue"):
                    bucket_widget.heldValue = None
                if hasattr(bucket_widget, "value"):
                    bucket_widget.value = ""
            except Exception:
                pass

    def set_title(self, title: str):
        self.title = title

    def action_submit(self):
        resultForm, errors, isValid = validateForm(self, self.form)
        if isValid:
            self.dismiss(resultForm)
        else:
            previousErrors = self.query(".error")
            for error in previousErrors:
                error.remove()
            for key, value in errors.items():
                field = self.query_one(f"#row-field-{key}")
                field.mount(Label(value, classes="error"))

    def compose(self) -> ComposeResult:
        yield ModalContainer(Fields(self.form))
