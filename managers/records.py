from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import joinedload, sessionmaker

from Buckets.managers.utils import get_operator_amount, get_start_end_of_period
from Buckets.models.account import Account
from Buckets.models.category import Category
from Buckets.models.database.app import db_engine
from Buckets.models.record import Record
from Buckets.models.bucket import Bucket

Session = sessionmaker(bind=db_engine)


# ------------------------- Create ------------------------- #


def create_record(record_data: dict) -> Record:
    if record_data.get("isIncome"):
        record_data.pop("bucketId", None)  # ← no bucket for income
    session = Session()
    try:
        payload = dict(record_data)  # ← copy
        bucket_id = payload.pop("bucketId", None)  # ← strip unknown kw

        # create the record (no bucketId on the model)
        record = Record(**payload)
        session.add(record)

        # If you want to decrement the bucket on EXPENSE create:
        if (
            bucket_id
            and not payload.get("isIncome", False)
            and not payload.get("isTransfer", False)
        ):
            bucket = session.query(Bucket).get(int(bucket_id))
            if bucket is not None:
                # subtract the expense amount from the bucket
                bucket.amount = float(bucket.amount or 0) - float(payload["amount"])

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
    account_id: int | None = None,
    category_piped_names: str | None = None,
    operator_amount: str | None = None,
    label: str | None = None,
) -> list[Record]:
    """
    Fetch records for a period with optional filters.
    - Excludes nothing by default (caller can decide to ignore transfers).
    - No split/person joins.
    """
    session = Session()
    try:
        query = session.query(Record).options(
            joinedload(Record.category),
            joinedload(Record.account),
            joinedload(Record.transferToAccount),
        )

        # Period filter
        start_of_period, end_of_period = get_start_end_of_period(offset, offset_type)
        query = query.filter(
            Record.date >= start_of_period,
            Record.date < end_of_period,
        )

        # Optional filters
        if account_id not in (None, ""):
            query = query.filter(Record.accountId == account_id)

        if category_piped_names not in (None, ""):
            category_names = [
                s.strip() for s in category_piped_names.split("|") if s.strip()
            ]
            if category_names:
                query = query.join(Record.category).filter(
                    Category.name.in_(category_names)
                )

        if operator_amount not in (None, ""):
            operator, amount = get_operator_amount(operator_amount)
            if operator and amount is not None:
                query = query.filter(Record.amount.op(operator)(amount))

        if label not in (None, ""):
            query = query.filter(Record.label.ilike(f"%{label}%"))

        # Stable ordering: newest date, then newest created
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
