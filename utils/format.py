from __future__ import annotations

from datetime import datetime, timedelta
from Buckets.config import CONFIG


def parse_formula_expression(value: str) -> float:
    try:
        value = value.replace("+-", "-")
        # trim dangling operator at end
        if value and value[-1] in "+-*/.":
            value = value[:-1]
        return round(float(eval(value)), CONFIG.defaults.round_decimals)  # nosec
    except Exception:
        return 0.0


def format_date_to_readable(date) -> str:
    today = datetime.now().date()
    date = date.date() if isinstance(date, datetime) else date

    if date == today:
        return "Today"
    if date == today - timedelta(days=1):
        return "Yesterday"

    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    if start_of_week <= date <= end_of_week:
        return date.strftime("%A")
    return date.strftime(CONFIG.defaults.date_format)


def format_period_to_readable(filter: dict) -> str:
    """
    filter = {
        "offset": int,
        "offset_type": "day" | "week" | "month" | "year",
    }
    """
    offset = filter["offset"]
    offset_type = filter["offset_type"]
    first_day = CONFIG.defaults.first_day_of_week

    if offset_type == "day":
        return format_date_to_readable(datetime.now() + timedelta(days=offset))

    if offset == 0:
        return f"This {offset_type.title()}"
    if offset == -1:
        return f"Last {offset_type.title()}"

    now = datetime.now()

    if offset_type == "year":
        return f"{now.year + offset}"

    if offset_type == "month":
        target_month = now.month + offset
        target_year = now.year + (target_month - 1) // 12
        target_month = ((target_month - 1) % 12) + 1
        return f"{datetime(target_year, target_month, 1).strftime('%B %Y')}"

    if offset_type == "week":
        target_date = now + timedelta(weeks=offset)
        days_to_first = (target_date.weekday() - first_day) % 7
        start = target_date - timedelta(days=days_to_first)
        end = start + timedelta(days=6)
        return f"{start.strftime('%d %b')} - {end.strftime('%d %b')}"

    target_date = now + timedelta(days=offset)
    return f"{target_date.strftime('%d %B %Y')}"
