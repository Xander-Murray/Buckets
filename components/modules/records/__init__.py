from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.events import DescendantBlur, DescendantFocus
from textual.reactive import reactive
from textual.widgets import Button, Input, Static, Switch

from textual.widgets import DataTable
from Buckets.components.indicators import EmptyIndicator
from Buckets.components.modules.records._cud import RecordCUD
from Buckets.components.modules.records._table_builder import RecordTableBuilder
from Buckets.config import CONFIG


class Records(RecordCUD, RecordTableBuilder, Static):
    """Records table (date view only) with add/edit/delete/transfer and filters."""

    DEFAULT_CSS = """\
Records .label-highlight-match {
    color: $accent-lighten-2;
    text-style: bold;
}
    """

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "label-highlight-match",
    }

    BINDINGS = [
        (CONFIG.hotkeys.new, "new", "Add"),
        (CONFIG.hotkeys.delete, "delete", "Delete"),
        (CONFIG.hotkeys.edit, "edit", "Edit"),
        (CONFIG.hotkeys.home.new_transfer, "new_transfer", "Transfer"),
        # removed: toggle_splits / display_by_person / display_by_date
    ]

    can_focus = True
    # removed: show_splits and displayMode
    FILTERS = {}
    FILTER_LABEL_TIPS = {
        "filter-category": "Shopping|Food|Dining",
        "filter-amount": ">=123.45",
        "filter-label": "Dinner with friends",
    }

    def __init__(self, parent: Static, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="records-container", classes="module-container"
        )
        super().__setattr__("border_title", "Records")
        self.page_parent = parent
        self.FILTERS = {
            "category": lambda: self.query_one("#filter-category").value,
            "amount": lambda: self.query_one("#filter-amount").value,
            "label": lambda: self.query_one("#filter-label").value,
            "enabled": lambda: self.query_one("#toggle-filter").value,
        }

    def on_mount(self) -> None:
        self.rebuild()

    # ---------- Callbacks ---------- #

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        current_row_index = event.cursor_row
        if event.row_key and event.row_key.value:
            self.current_row = event.row_key.value
            self.current_row_index = current_row_index
        else:
            self.current_row = None
            self.current_row_index = None

    # removed: watch_displayMode / action_toggle_splits / action_display_by_person / action_display_by_date

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # kept for future buttons if you re-add; currently no buttons in this view
        pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if self.FILTERS["enabled"]():
            self.rebuild(focus=False)

    def on_switch_changed(self, event: Switch.Changed) -> None:
        self.rebuild(focus=False)

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        if event.widget.id and event.widget.id.startswith("filter-"):
            event.widget.placeholder = self.FILTER_LABEL_TIPS.get(
                event.widget.id, event.widget.placeholder
            )

    def on_descendant_blur(self, event: DescendantBlur) -> None:
        if event.widget.id and event.widget.id.startswith("filter-"):
            event.widget.placeholder = "Filter " + event.widget.id.split("-")[1]

    # ---------- View ---------- #

    def compose(self) -> ComposeResult:
        with Container(classes="selectors"):
            # removed the display-mode selector; we are date-view only now
            with Container(classes="filtering", id="filter-container"):
                yield Input(id="filter-category", placeholder="Filter category")
                yield Input(
                    id="filter-amount",
                    placeholder="Filter amount",
                    restrict=r"^(>=|>|=|<=|<)?\d*\.?\d*$",
                )
                yield Input(id="filter-label", placeholder="Filter label")
                yield Switch(id="toggle-filter", animate=False)

        self.table = DataTable(
            id="records-table",
            cursor_type="row",
            cursor_foreground_priority=True,
            zebra_stripes=True,
        )
        yield self.table
        yield EmptyIndicator("No entries")

