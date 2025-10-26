from textual.app import ComposeResult
from textual.widgets import Static

from textual.widgets import Button
from Buckets.config import CONFIG


class IncomeMode(Static):
    def __init__(self, parent: Static, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="incomemode-container", classes="module-container"
        )
        super().__setattr__("border_title", "View and add")
        super().__setattr__("border_subtitle", CONFIG.hotkeys.home.toggle_income_mode)
        self.page_parent = parent

    def on_mount(self) -> None:
        self.rebuild()

    # region Builder
    # -------------- Builder ------------- #

    def rebuild(self) -> None:
        expense_label: Button = self.query_one("#expense-label")
        income_label: Button = self.query_one("#income-label")
        current_is_income = self.page_parent.mode["isIncome"]
        expense_label.classes = "selected" if not current_is_income else ""
        income_label.classes = "selected" if current_is_income else ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.page_parent.action_toggle_income_mode()

    # region View
    # --------------- View --------------- #

    def compose(self) -> ComposeResult:
        yield Button("Expense", id="expense-label")
        yield Button("Income", id="income-label")
