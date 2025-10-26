from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import joinedload, sessionmaker

from Buckets.models.account import Account
from Buckets.managers.utils import get_start_end_of_period
from Buckets.models.database.app import db_engine
from Buckets.models.record import Record
from Buckets.models.bucket import Bucket

Session = sessionmaker(bind=db_engine)

# ------------------------- Create ------------------------- #


def create_record(record_data: dict) -> Record:
    session = Session()
    try:
        record_data.setdefault("isInProgress", False)  # ✅ Fix here
        record = Record(**record_data)
        session.add(record)
        session.commit()
        session.refresh(record)
        session.expunge(record)
        return record
    finally:
        session.close()


# -------------------------- Read -------------------------- #


def get_record_by_id(record_id: int) -> Record | None:
    """Fetch a single record with category/account relations (no splits)."""
    session = Session()
    try:
        record = (
            session.query(Record)
            .options(
                joinedload(Record.category),
                joinedload(Record.account),
                joinedload(Record.transferToAccount),
            )
            .get(record_id)
        )
        return record
    finally:
        session.close()


def get_records(
    offset: int = 0,
    offset_type: str = "month",
) -> list[Record]:
    session = Session()
    try:
        query = session.query(Record).options(
            joinedload(Record.category),
            joinedload(Record.account),
            joinedload(Record.transferToAccount),
        )

        start_of_period, end_of_period = get_start_end_of_period(offset, offset_type)
        query = query.filter(
            Record.date >= start_of_period,
            Record.date < end_of_period,
        )

        created_at_col = getattr(Record, "createdAt")
        date_col = func.date(getattr(Record, "date"))
        query = query.order_by(date_col.desc(), created_at_col.desc())
        return query.all()
    finally:
        session.close()


# --------------------- Spending helpers ------------------- #


def _collect_expense_records(
    session, start_date: datetime, end_date: datetime
) -> list[Record]:
    """Expense records within range, excluding transfers."""
    return (
        session.query(Record)
        .filter(
            Record.isIncome == False,  # noqa: E712
            Record.isTransfer == False,  # noqa: E712
            Record.date >= start_date,
            Record.date < end_date,
        )
        .all()
    )


def _daily_sums(
    records: list[Record], start_date: datetime, end_date: datetime, cumulative: bool
) -> list[float]:
    """Build list of daily values (or cumulative) from start..end (clamped to today)."""
    per_day = {}
    for r in records:
        key = r.date.date()
        per_day[key] = per_day.get(key, 0.0) + float(r.amount)

    cur = start_date.date()
    end_d = end_date.date()
    today = datetime.today().date()
    out: list[float] = []
    running = 0.0

    while cur <= end_d:
        if cur <= today:
            val = per_day.get(cur, 0.0)
            if cumulative:
                running += val
                out.append(running)
            else:
                out.append(val)
        cur += timedelta(days=1)
    return out


def get_spending(start_date: datetime, end_date: datetime) -> list[float]:
    """Daily expense totals (no splits), excluding transfers."""
    session = Session()
    try:
        recs = _collect_expense_records(session, start_date, end_date)
        return _daily_sums(recs, start_date, end_date, cumulative=False)
    finally:
        session.close()


def get_spending_trend(start_date: datetime, end_date: datetime) -> list[float]:
    """Cumulative expense totals (no splits), excluding transfers."""
    session = Session()
    try:
        recs = _collect_expense_records(session, start_date, end_date)
        return _daily_sums(recs, start_date, end_date, cumulative=True)
    finally:
        session.close()


# --------------------- Balance timeline ------------------- #


def get_daily_balance(start_date: datetime, end_date: datetime) -> list[float]:
    """
    Daily total balance across all accounts.
    Rules:
      - Start with sum of beginning balances.
      - Add income amounts, subtract expense amounts.
      - Ignore transfers (net-zero within the system).
      - Iterate day-by-day from start_date to end_date (clamped to today).
    """
    session = Session()
    try:
        # Starting balance
        accounts = session.query(Account).filter(Account.deletedAt.is_(None)).all()
        total_balance = sum(float(a.beginningBalance or 0.0) for a in accounts)

        # Apply all records before start_date
        old_records = session.query(Record).filter(Record.date < start_date).all()

        def net_effect(r: Record) -> float:
            if r.isTransfer:
                return 0.0
            return float(r.amount) if r.isIncome else -float(r.amount)

        for r in old_records:
            total_balance += net_effect(r)

        # Build daily series
        results: list[float] = []
        cur = start_date
        today = datetime.today()

        while cur <= end_date:
            if cur > today:
                break
            day_records = (
                session.query(Record).filter(func.date(Record.date) == cur.date()).all()
            )
            day_delta = sum(net_effect(r) for r in day_records)
            total_balance += day_delta
            results.append(total_balance)
            cur += timedelta(days=1)

        return results
    finally:
        session.close()


# ------------------------- Update ------------------------- #


def update_record(record_id: int, updated_data: dict) -> Record | None:
    session = Session()
    try:
        record = session.query(Record).get(record_id)
        if record:
            payload = dict(updated_data)
            payload.pop("bucketId", None)  # ← prevent unexpected kw on setattr loop

            for k, v in payload.items():
                setattr(record, k, v)

            session.commit()
            session.refresh(record)
            session.expunge(record)
        return record
    finally:
        session.close()


# ------------------------- Delete ------------------------- #


def delete_record(record_id: int) -> Record | None:
    session = Session()
    try:
        record = session.query(Record).get(record_id)
        if record:
            session.delete(record)
            session.commit()
        return record
    finally:
        session.close()
