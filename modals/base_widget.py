# Buckets/modals/base_widget.py

from textual.app import ComposeResult
from textual.containers import Container, ScrollableContainer, Horizontal
from textual.widgets import Footer, Static, Button

class ModalContainer(ScrollableContainer):
    """Minimal modal wrapper: content scrolls, close button on top, footer on bottom."""

    can_focus = False

    def __init__(self, *content, custom_classes: str = "wrapper base-modal"):
        super().__init__(classes=custom_classes, id="modal-container")
        self.content = content

    def compose(self) -> ComposeResult:
        with Horizontal(classes="modal-header"):
            yield Button("×", id="modal-close")  # click to close
            yield Static("")  # spacer / keep layout simple

        with Container(classes="container"):
            for widget in self.content:
                yield widget

        yield Footer(show_command_palette=False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "modal-close":
            self.app.pop_screen()
