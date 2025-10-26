from textual import events
from textual.app import ComposeResult
from textual.containers import Container
from textual.screen import ModalScreen
from textual.widgets import (
    Label,
)

class ConfirmationModal(ModalScreen):
    def __init__(self, message: str, *args, **kwargs):
        super().__init__(id="confirmation-modal-screen", *args, **kwargs)
        self.message = message

    def compose(self) -> ComposeResult:
        dialog = Container(classes="dialog")
        dialog.border_title = "Alert"
        with dialog:
            yield Label(self.message)

    def on_key(self, event: events.Key):
        if event.key == "enter":
            self.dismiss(True)
        elif event.key == "escape":
            self.dismiss(False)
