from __future__ import annotations

from typing import ClassVar

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.events import DescendantBlur, DescendantFocus
from textual.widgets import DataTable, Static

from Buckets.components.indicators import EmptyIndicator
from Buckets.components.modules.records._cud import RecordCUD
from Buckets.components.modules.records._table_builder import RecordTableBuilder
from Buckets.config import CONFIG

class Records(RecordCUD, RecordTableBuilder, Static):
    """Records table (date view only) with add/edit/delete/transfer; no filters."""

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
    ]

    can_focus = True

    def __init__(self, parent: Static, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="records-container", classes="module-container"
        )
        super().__setattr__("border_title", "Records")
        self.page_parent = parent

        self.FILTERS = {
            "enabled": lambda: False,
            "label": lambda: "",
            "amount": lambda: "",
            "category": lambda: "",
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

    # Keep focus helpers if you reintroduce filter inputs later; otherwise harmless.
    def on_descendant_focus(self, event: DescendantFocus) -> None:
        pass

    def on_descendant_blur(self, event: DescendantBlur) -> None:
        pass

    # ---------- View ---------- #

    def compose(self) -> ComposeResult:
        with Container(classes="selectors"):
            pass

        self.table = DataTable(
            id="records-table",
            cursor_type="row",
            cursor_foreground_priority=True,
            zebra_stripes=True,
        )
        yield self.table
        yield EmptyIndicator("No entries")
        # No selectors / filters UI
