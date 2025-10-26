from __future__ import annotations

from datetime import timedelta

from rich.text import Text

from textual.widgets import DataTable
from Buckets.components.indicators import EmptyIndicator
from Buckets.config import CONFIG
from Buckets.managers.records import get_records
from Buckets.utils.format import format_date_to_readable

class RecordTableBuilder:
    """
    Builds the Records table (date-based view only).
    - No splits
    - No people
    """

    def rebuild(self, focus: bool = True) -> None:
        if not hasattr(self, "table"):
            return

        table: DataTable = self.table
        empty_indicator: EmptyIndicator = self.query_one(".empty-indicator")

        self._initialize_table(table)
        records = self._fetch_records()

        self._build_date_view(table, records)

        # Restore cursor
        if hasattr(self, "current_row_index"):
            table.move_cursor(row=self.current_row_index)

        # Toggle empty indicator
        empty_indicator.display = not table.rows
        table.display = bool(table.rows)

        if focus:
            if table.display:
                table.focus()
            else:
                self.focus()

    # ---------------- Helpers ---------------- #

    def _fetch_records(self):
        return get_records(
            offset=self.page_parent.filter["offset"],
            offset_type=self.page_parent.filter["offset_type"],
        )

    def _initialize_table(self, table: DataTable) -> None:
        table.clear()
        table.columns.clear()
        table.add_columns(" ", "Category / Transfer", "Amount", "Label", "Account")

    def _get_label_string(self, text: str) -> Text | str:
        return text

    # ---------------- Date view ---------------- #

    def _build_date_view(self, table: DataTable, records: list) -> None:
        prev_group = None

        for record in records:
            flow_icon = self._flow_icon(record.isIncome)
            category_string, amount_string, account_string = self._format_record_fields(
                record, flow_icon
            )

            # Highlight label if filtering
            label_string = self._get_label_string(record.label)

            # Add group header based on current offset_type
            group_string = self._group_label_for_record(record)
            if group_string and prev_group != group_string:
                prev_group = group_string
                self._add_group_header_row(table, group_string)

            # Main record row
            table.add_row(
                " ",
                category_string,
                amount_string,
                label_string,
                account_string,
                key=f"r-{record.id}",
            )

    def _flow_icon(self, is_income: bool) -> str:
        pos = f"[green]{CONFIG.symbols.amount_positive}[/green]"
        neg = f"[red]{CONFIG.symbols.amount_negative}[/red]"
        return pos if is_income else neg

    def _format_record_fields(self, record, flow_icon: str) -> tuple[str, str, str]:
        """Returns (category_or_transfer, amount_str, account_str)."""
        if record.isTransfer:
            from_account = (
                f"[italic]{record.account.name}[/italic]"
                if record.account.hidden
                else record.account.name
            )
            to_account = (
                f"[italic]{record.transferToAccount.name}[/italic]"
                if record.transferToAccount and record.transferToAccount.hidden
                else (
                    record.transferToAccount.name if record.transferToAccount else "-"
                )
            )
            category_string = f"{from_account} → {to_account}"
            # For transfers, show raw amount without +/- since direction is implied
            amount_string = f"{record.amount}"
            account_string = "-"
        else:
            color_tag = (
                record.category.color.lower()
                if record.category and record.category.color
                else "white"
            )
            cat_name = record.category.name if record.category else "-"
            category_string = (
                f"[{color_tag}]{CONFIG.symbols.category_color}[/{color_tag}] {cat_name}"
            )
            amount_string = f"{flow_icon} {record.amount}"
            account_string = record.account.name if record.account else "-"

        return category_string, amount_string, account_string

    def _group_label_for_record(self, record) -> str | None:
        """Generates group header text based on current filter offset_type."""
        match self.page_parent.filter["offset_type"]:
            case "year":
                # Group by month
                return record.date.strftime("%B %Y")
            case "month":
                # Group by week (bounded to the same month)
                first_dow = CONFIG.defaults.first_day_of_week
                week_start = record.date - timedelta(
                    days=(record.date.weekday() - first_dow) % 7
                )
                week_end = week_start + timedelta(days=6)

                if week_start.month != record.date.month:
                    week_start = record.date.replace(day=1)
                if week_end.month != record.date.month:
                    last_day = (
                        record.date.replace(day=1) + timedelta(days=32)
                    ).replace(day=1) - timedelta(days=1)
                    week_end = last_day

                return f"{format_date_to_readable(week_start)} - {format_date_to_readable(week_end)}"
            case "week":
                # Group by day
                return format_date_to_readable(record.date)
            case "day":
                return None
        return None

    def _add_group_header_row(
        self, table: DataTable, string: str, key: str | None = None
    ) -> None:
        # Use dim/italic markup to visually separate group headers with the built-in DataTable
        table.add_row(
            "//", f"[dim][italic]{string}[/italic][/dim]", "", "", "", key=key
        )
