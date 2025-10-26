# Buckets/managers/utils.py
from __future__ import annotations

import re
from datetime import datetime, timedelta

from sqlalchemy.orm import sessionmaker
from textual.widget import Widget

from Buckets.config import CONFIG
from Buckets.models.category import Category
from Buckets.models.database.app import db_engine
from Buckets.models.record import Record

Session = sessionmaker(bind=db_engine)

# ---------------- UI helper ---------------- #

def try_method_query_one(widget: Widget, query: str, method: str, params) -> None:
    """Safely find a descendant widget and call a method on it (ignore errors)."""
    try:
        target = widget.query_one(query)
        getattr(target, method)(*params)
    except Exception:
        return

# ------------- period helpers -------------- #

def _get_start_end_of_year(offset: int = 0) -> tuple[datetime, datetime]:
    now = datetime.now()
    y = now.year + offset
    return datetime(y, 1, 1, 0, 0, 0), datetime(y, 12, 31, 23, 59, 59)

def _get_start_end_of_month(offset: int = 0) -> tuple[datetime, datetime]:
    now = datetime.now()
    month = now.month + offset
    year = now.year + (month - 1) // 12
    month = ((month - 1) % 12) + 1

    next_month = month + 1
    next_year = year + (next_month - 1) // 12
    next_month = ((next_month - 1) % 12) + 1

    start = datetime(year, month, 1, 0, 0, 0)
    end = datetime(next_year, next_month, 1, 0, 0, 0) - timedelta(seconds=1)
    return start, end

def _get_start_end_of_week(offset: int = 0) -> tuple[datetime, datetime]:
    now = datetime.now() + timedelta(weeks=offset)
    fdow = CONFIG.defaults.first_day_of_week
    start = (now - timedelta(days=(now.weekday() - fdow) % 7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59)
    return start, end

def _get_start_end_of_day(offset: int = 0) -> tuple[datetime, datetime]:
    now = datetime.now() + timedelta(days=offset)
    return (
        now.replace(hour=0, minute=0, second=0, microsecond=0),
        now.replace(hour=23, minute=59, second=59),
    )

def get_start_end_of_period(
    offset: int = 0, offset_type: str = "month"
) -> tuple[datetime, datetime]:
    if offset_type == "year":
        return _get_start_end_of_year(offset)
    if offset_type == "week":
        return _get_start_end_of_week(offset)
    if offset_type == "day":
        return _get_start_end_of_day(offset)
    # default month
    return _get_start_end_of_month(offset)

def get_period_figures(
    accountId: int | None = None,
    offset_type: str | None = None,
    offset: int | None = None,
    isIncome: bool | None = None,
    nature=None,
    session=None,
) -> float:
    """
    Total income/expense for a period.
    - Excludes transfers.
    - No split logic.
    """
    own_session = False
    if session is None:
        session = Session()
        own_session = True
    try:
        q = session.query(Record)
        if accountId is not None:
            q = q.filter(Record.accountId == accountId)
        if offset_type is not None and offset is not None:
            start, end = get_start_end_of_period(offset, offset_type)
            q = q.filter(Record.date >= start, Record.date < end)
        if nature is not None:
            q = q.join(Record.category).filter(Category.nature == nature)

        total = 0.0
        for r in q.all():
            if r.isTransfer:
                continue
            if isIncome is not None and r.isIncome != isIncome:
                continue
            total += r.amount if r.isIncome else -r.amount

        return abs(round(total, CONFIG.defaults.round_decimals))
    finally:
        if own_session:
            session.close()

# ----------------- averages ----------------- #

def _get_days_in_period(offset: int = 0, offset_type: str = "month") -> int:
    start, end = get_start_end_of_period(offset, offset_type)
    return max(1, (end - start).days + 1)

def get_period_average(
    net: float = 0.0, offset: int = 0, offset_type: str = "month"
) -> float:
    days = _get_days_in_period(offset, offset_type)
    return round(net / days, CONFIG.defaults.round_decimals)

# ------------ filter parsing helper ------------ #

def get_operator_amount(
    operator_amount: str | None = None,
) -> tuple[str | None, float | None]:
    """
    Parse '>=123.45', '<10', '=50', '42' -> (op, amount)
    """
    if not operator_amount:
        return None, None
    if re.match(r"^(>=|>|=|<=|<)?\d+(\.\d+)?$", operator_amount):
        if operator_amount[0].isdigit():
            op, amt = "=", operator_amount
        elif len(operator_amount) > 1 and operator_amount[1].isdigit():
            op, amt = operator_amount[:1], operator_amount[1:]
        else:
            op, amt = operator_amount[:2], operator_amount[2:]
        return op, float(amt)
    return None, None
