from textual.app import ComposeResult
from textual.widgets import Static

class EmptyIndicator(Static):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        yield Static(self.message, classes="empty-indicator")
