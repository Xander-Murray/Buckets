from textual import events
from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import (
    Label,
)

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

    def on_key(self, event: events.Key):
        if event.key == "down":
            self.screen.focus_next()
        elif event.key == "up":
            self.screen.focus_previous()
        elif event.key == "enter":
            self.action_submit()
        elif event.key == "escape":
            self.dismiss(None)

    # ------------- Callbacks ------------ #

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

    # -------------- Compose ------------- #

    def compose(self) -> ComposeResult:
        yield ModalContainer(Fields(self.form))
