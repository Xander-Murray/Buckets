# Buckets/components/modules/buckets/__init__.py
from textual.app import ComposeResult
from textual.binding import Binding
from textual.css.query import NoMatches
from textual.widgets import Static

from textual.widgets import DataTable
from Buckets.components.indicators import EmptyIndicator
from Buckets.forms.bucket_forms import BucketForm, BucketTransferForm
from Buckets.managers.buckets import (
    create_bucket,
    update_bucket,
    delete_bucket,
    transfer_between_buckets,
)


class BucketsModule(Static):
    """Buckets CRUD + transfer list for the currently selected account (from page_parent.mode)."""

    BINDINGS = [
        Binding("a", "new", "Add"),
        Binding("e", "edit", "Edit"),
        Binding("d", "delete", "Delete"),
        Binding("t", "transfer", "Transfer"),
    ]

    def __init__(self, page_parent, *args, **kwargs):
        super().__init__(
            *args, **kwargs, id="buckets-container", classes="module-container"
        )
        self.page_parent = page_parent
        self.current_row: str | None = None
        self.current_row_index: int | None = None

    # ---------- Helpers ----------

    def _selected_account_id(self) -> int | None:
        # Mirrors Home/account mode convention
        try:
            return self.page_parent.mode["accountId"]["default_value"]
        except Exception:
            return None

    # ---------- Lifecycle ----------

    def on_mount(self) -> None:
        self.rebuild()

    # ---------- Building ----------

    def rebuild(self) -> None:
        try:
            table: DataTable = self.query_one("#buckets-table")
        except NoMatches:
            return  # not mounted yet

        # Build rows first so we can set visibility correctly
        rows: list[tuple[int, str, float]] = []
        acct_id = self._selected_account_id()
        if acct_id:
            from Buckets.managers.buckets import get_buckets_by_account

            for b in get_buckets_by_account(acct_id):
                rows.append((b.id, b.name, b.amount))

        table.clear()
        table.columns.clear()
        table.add_columns("Bucket", "Amount")
        for bid, name, amt in rows:
            table.add_row(name, amt, key=f"b-{bid}")

        # Toggle the empty state
        try:
            empty = self.query_one(EmptyIndicator)  # query by type
            empty.display = len(rows) == 0
        except NoMatches:
            pass

        table.display = len(rows) > 0
        if rows:
            table.move_cursor(row=0)

    # ---------- Selection tracking ----------

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self.current_row = event.row_key.value if event.row_key else None
        self.current_row_index = event.cursor_row

    # ---------- Actions ----------

    def action_new(self) -> None:
        acct_id = self._selected_account_id()
        form = BucketForm().get_form(default_account_id=acct_id)

        def done(data):
            if not data:
                return
            try:
                create_bucket(data)
                self.app.notify("Bucket created", severity="information", timeout=2)
                self.rebuild()
            except Exception as e:
                self.app.notify(f"{e}", title="Error", severity="error", timeout=5)

        from Buckets.modals.input import InputModal

        self.app.push_screen(InputModal("New Bucket", form), callback=done)

    def action_edit(self) -> None:
        if not self.current_row:
            self.app.notify("Select a bucket first", severity="warning", timeout=2)
            return
        _, bid = self.current_row.split("-", 1)

        form = BucketForm().get_filled_form(int(bid))

        def done(data):
            if not data:
                return
            try:
                update_bucket(int(bid), data)
                self.app.notify("Bucket updated", severity="information", timeout=2)
                self.rebuild()
            except Exception as e:
                self.app.notify(f"{e}", title="Error", severity="error", timeout=5)

        from Buckets.modals.input import InputModal

        self.app.push_screen(InputModal("Edit Bucket", form), callback=done)

    def action_delete(self) -> None:
        if not self.current_row:
            self.app.notify("Select a bucket first", severity="warning", timeout=2)
            return
        _, bid = self.current_row.split("-", 1)

        def confirm(ok: bool) -> None:
            if not ok:
                return
            try:
                delete_bucket(int(bid))
                self.app.notify("Bucket deleted", severity="information", timeout=2)
                self.rebuild()
            except Exception as e:
                self.app.notify(f"{e}", title="Error", severity="error", timeout=5)

        from Buckets.modals.confirmation import ConfirmationModal

        self.app.push_screen(ConfirmationModal("Delete this bucket?"), callback=confirm)

    def action_transfer(self) -> None:
        acct_id = self._selected_account_id()
        form = BucketTransferForm(acct_id).get_form()

        def done(data):
            if not data:
                return
            try:
                transfer_between_buckets(
                    int(data["fromBucketId"]),
                    int(data["toBucketId"]),
                    float(data["amount"]),
                )
                self.app.notify("Transfer complete", severity="information", timeout=2)
                self.rebuild()
            except Exception as e:
                self.app.notify(
                    f"{e}", title="Transfer error", severity="error", timeout=6
                )

        from Buckets.modals.input import InputModal

        self.app.push_screen(
            InputModal("Transfer Between Buckets", form), callback=done
        )

    # ---------- View ----------

    def compose(self) -> ComposeResult:
        self.border_title = "Buckets"
        yield DataTable(
            id="buckets-table",
            cursor_type="row",
            cursor_foreground_priority=True,
            zebra_stripes=True,
        )
        yield EmptyIndicator("No buckets")  # simple “no data” state
