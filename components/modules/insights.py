from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Label, Static

from Buckets.config import CONFIG
from Buckets.managers.categories import get_all_categories_records
from Buckets.managers.utils import get_period_average, get_period_figures


class Insights(Static):
    can_focus = True

    def __init__(self, parent: Static, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="insights-container", classes="module-container"
        )
        super().__setattr__("border_title", "Insights")
        super().__setattr__("border_subtitle", CONFIG.hotkeys.home.toggle_use_account)
        self.page_parent = parent
        self.use_account = False  # set in rebuild

    def on_mount(self) -> None:
        self.rebuild()

    # -------------- Builder ------------- #
    def rebuild(self) -> None:
        self.use_account = self.page_parent.filter["byAccount"]
        period_net = self._update_labels()
        self._update_top_categories(period_net)

    def _update_labels(self) -> int:
        current_filter_label = self.query_one(".current-filter-label")
        period_net_label = self.query_one(".period-net")
        period_average_label = self.query_one(".period-average")
        average_label = self.query_one(".average-label")

        is_income = self.page_parent.mode["isIncome"]
        label = "Income" if is_income else "Expense"

        # header text
        if self.use_account:
            current_filter_label.update(
                f"{self.page_parent.mode['accountId']['default_value_text']} {label} of {self.page_parent.get_filter_label()}"
            )
        else:
            current_filter_label.update(
                f"{label} of {self.page_parent.get_filter_label()}"
            )
        average_label.update(f"{label} per day")

        # fetch figures
        params = {
            "offset": self.page_parent.filter["offset"],
            "offset_type": self.page_parent.filter["offset_type"],
            "isIncome": is_income,
        }
        if self.use_account:
            params["accountId"] = self.page_parent.mode["accountId"]["default_value"]

        period_net = get_period_figures(**params)
        period_average = get_period_average(
            period_net,
            offset=self.page_parent.filter["offset"],
            offset_type=self.page_parent.filter["offset_type"],
        )
        period_net_label.update(str(period_net))
        period_average_label.update(str(period_average))

        return period_net

    def _fetch_category_records(self):
        """Return list of category records for current filter/mode."""
        params = {
            "offset": self.page_parent.filter["offset"],
            "offset_type": self.page_parent.filter["offset_type"],
            "is_income": self.page_parent.mode["isIncome"],
        }
        if self.use_account:
            params["account_id"] = self.page_parent.mode["accountId"]["default_value"]
        return get_all_categories_records(**params)

    def _update_top_categories(self, period_net: int, limit: int = 5) -> None:
        """Render a simple ranked list of top categories with percentages."""
        # ensure container exists
        container = self.query_one("#top-categories")
        # clear previous rows
        for child in list(container.children):
            child.remove()

        if not period_net:
            container.mount(Label("No data to display", classes="empty"))
            return

        records = self._fetch_category_records()

        # build top list (or “others” bucket)
        items = []
        if len(records) <= limit:
            for c in records:
                items.append((c.name, int(c.amount), c.color))
        else:
            for c in records[:limit]:
                items.append((c.name, int(c.amount), c.color))
            others_amount = int(sum(c.amount for c in records[limit:]))
            items.append(("Others", others_amount, "white"))

        # render rows: "● Category — 23% (123)"
        for name, amount, color in items:
            pct = round((amount / period_net) * 100) if period_net else 0
            # simple row: colored bullet + label + numbers
            row = Horizontal(classes="cat-row")
            row.compose_add_child(Label(f"[{color}]●[/{color}] {name}", classes="name"))
            row.compose_add_child(Label(f"{pct}% ({amount})", classes="pct"))
            container.mount(row)

    # --------------- View --------------- #
    def compose(self) -> ComposeResult:
        # top figures
        with Horizontal(classes="figures-container"):
            with Container(classes="net container"):
                yield Label(classes="current-filter-label title")  # dynamic
                yield Label("Loading...", classes="period-net amount")  # dynamic
            with Container(classes="average container"):
                yield Label("<> per day", classes="average-label title")  # dynamic
                yield Label("Loading...", classes="period-average amount")  # dynamic

        # simple list for top categories (replaces PercentageBar)
        yield Container(id="top-categories", classes="top-categories")
