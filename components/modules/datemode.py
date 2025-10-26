from datetime import datetime, timedelta

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widgets import Label, Static

from textual.widgets import Button
from Buckets.forms.form import Form, FormField
from Buckets.modals.input import InputModal
from Buckets.config import CONFIG


class DateMode(Static):
    can_focus = True

    BINDINGS = [
        Binding(CONFIG.hotkeys.home.datemode.go_to_day, "go_to_day", "Go to Day"),
    ]

    FORM = Form(
        fields=[
            FormField(
                type="dateAutoDay",
                key="date",
                title="Date",
                default_value=datetime.now().strftime("%d"),
            )
        ]
    )

    def __init__(self, parent: Static, *args, **kwargs) -> None:
        super().__init__(
            *args, **kwargs, id="datemode-container", classes="module-container"
        )
        super().__setattr__("border_title", "Period")
        super().__setattr__(
            "border_subtitle", f"← {CONFIG.hotkeys.home.cycle_offset_type} →"
        )
        self.page_parent = parent
        self.first_day_of_week = CONFIG.defaults.first_day_of_week

    def on_mount(self) -> None:
        self.rebuild()

    # region Builder
    # -------------- Builder ------------- #

    # cell classes:
    # today, not_current_month, target, target_week, target_month

    def _get_month_days(self, date: datetime) -> list[tuple[datetime, bool]]:
        """Returns list of (date, is_current_month) tuples for calendar"""
        # Get first day of month
        first_day = date.replace(day=1)

        # Calculate days before month starts to fill calendar
        days_before = (first_day.weekday() - self.first_day_of_week) % 7
        start_date = first_day - timedelta(days=days_before)

        # Generate 42 days (6 weeks)
        days = []
        for i in range(42):
            curr_date = start_date + timedelta(days=i)
            is_current = curr_date.month == date.month
            days.append((curr_date, is_current))

        return days

    def rebuild(self) -> None:
        """Builds the calendar.

        The calendar should always give cells the following classes:
        * Date of today: "today"
        * Days not in the specified filter month: "not-current-month"

        Target date is a day that should have the class "target". The following are the rules:
        - Week: The cell's first day of the week (must respect first_day_of_week) if offset is not 0, else target date is today.
        - Month: First day of month if offset is not 0, else today.
        - Year: Always today

        The calendar should give cells the classes based on the current offset_type:
        - Week: The cell row's container of the current week: class "target_week"
        - Month: Every day of the specified filter month: "target_month"
        - Year: No rules.
        """
        self.page_parent.filter["offset"]
        filter_offset_type = self.page_parent.filter["offset_type"]

        today = datetime.now()
        target_date = self.page_parent.get_target_date()

        # Get calendar days
        calendar_days = self._get_month_days(target_date)

        # Update calendar labels
        calendar_rows = self.query(".calendar-row")

        for row_idx, row in enumerate(calendar_rows):
            row.remove_class("target_week")
            for col_idx, label in enumerate(row.query("Label")):
                day_idx = row_idx * 7 + col_idx
                if day_idx >= len(calendar_days):
                    continue

                date, is_current = calendar_days[day_idx]

                # Set day number
                label.update(str(date.day))

                # Reset classes
                label.set_classes("")

                # Add not current month class
                if not is_current:
                    label.add_class("not_current_month")

                # Add today class
                if date.date() == today.date():
                    label.add_class("today")

                # Add target class
                if date.date() == target_date.date():
                    label.add_class("target")

                # Add type-specific classes
                match filter_offset_type:
                    case "week":
                        # Calculate week start based on first_day_of_week
                        days_to_first = (
                            target_date.weekday() - self.first_day_of_week
                        ) % 7
                        week_start = target_date - timedelta(days=days_to_first)
                        week_end = week_start + timedelta(days=6)
                        if week_start.date() <= date.date() <= week_end.date():
                            row.add_class("target_week")
                    case "month":
                        if is_current:
                            label.add_class("target_month")

        self.page_parent.update_filter_label(self.query_one(".current-filter-label"))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "prev-month":
            self.page_parent.action_dec_offset()
        elif event.button.id == "next-month":
            self.page_parent.action_inc_offset()
        self.rebuild()

    # region Callbacks
    # --------------- Callbacks --------------- #

    def action_go_to_day(self) -> None:
        def check_result(result) -> None:
            if result:
                self.page_parent.set_target_date(result["date"])

        self.app.push_screen(
            InputModal("Go to Day", form=self.FORM), callback=check_result
        )

    # region View
    # --------------- View --------------- #

    def compose(self) -> ComposeResult:
        with Container(classes="month-selector"):
            yield Button("<<<", id="prev-month")
            yield Label("Current Month", classes="current-filter-label")
            yield Button(">>>", id="next-month")

        with Static(classes="calendar"):
            # Create 6 rows of 7 days each for the calendar grid
            with Horizontal(classes="calendar-dotw-row"):
                days = ["M", "T", "W", "T", "F", "S", "S"]
                days = days[self.first_day_of_week :] + days[: self.first_day_of_week]
                for dotw in days:
                    yield Label(dotw)
            for _ in range(6):
                with Horizontal(classes="calendar-row"):
                    for _ in range(7):
                        yield Label("", classes="not_current_month")
