# Buckets/managers/accounts.py
from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from sqlalchemy import func, select
from Buckets.config import CONFIG
from Buckets.models.database.app import Session
from Buckets.models.account import Account
from Buckets.models.record import Record

def create_account(data: dict) -> Account:
    """Create an account from a dict of fields."""
    session = Session()
    try:
        acc = Account(**data)
        session.add(acc)
        session.commit()
        session.refresh(acc)
        session.expunge(acc)
        return acc
    finally:
        session.close()

def _get_base_accounts_query(get_hidden: bool = False):
    stmt = select(Account).filter(Account.deletedAt.is_(None))
    if not get_hidden:
        stmt = stmt.filter(Account.hidden.is_(False))
    else:
        stmt = stmt.order_by(Account.hidden.asc(), Account.id.asc())
    return stmt

def get_all_accounts(get_hidden: bool = False) -> List[Account]:
    session = Session()
    try:
        stmt = _get_base_accounts_query(get_hidden)
        return session.scalars(stmt).all()
    finally:
        session.close()

def get_accounts_count(get_hidden: bool = False) -> int:
    session = Session()
    try:
        q = session.query(func.count(Account.id)).filter(Account.deletedAt.is_(None))
        if not get_hidden:
            q = q.filter(Account.hidden.is_(False))
        return int(q.scalar() or 0)
    finally:
        session.close()

def get_account_by_id(account_id: int) -> Optional[Account]:
    session = Session()
    try:
        return session.get(Account, account_id)
    finally:
        session.close()

def get_all_accounts_with_balance(get_hidden: bool = False) -> List[Account]:
    """Return accounts list where each item also has a transient `.balance` attr."""
    session = Session()
    try:
        stmt = _get_base_accounts_query(get_hidden)
        accounts = session.scalars(stmt).all()
        for acc in accounts:
            acc.balance = get_account_balance(acc.id, session)  # type: ignore[attr-defined]
        return accounts
    finally:
        session.close()

def get_account_balance_by_id(account_id: int) -> float:
    session = Session()
    try:
        return get_account_balance(account_id, session)
    finally:
        session.close()

def get_account_balance(account_id: int, session: Optional[Session] = None) -> float:
    own_session = False
    if session is None:
        session = Session()
        own_session = True

    try:
        acc = session.get(Account, account_id)
        if not acc:
            return 0.0

        balance = float(acc.beginningBalance or 0.0)

        origin_records = (
            session.query(Record).filter(Record.accountId == account_id).all()
        )
        for r in origin_records:
            if r.isTransfer:
                balance -= r.amount
            elif r.isIncome:
                balance += r.amount
            else:
                balance -= r.amount

        incoming_transfers = (
            session.query(Record)
            .filter(Record.isTransfer.is_(True))
            .filter(Record.transferToAccountId == account_id)
            .all()
        )
        for r in incoming_transfers:
            balance += r.amount

        return round(balance, CONFIG.defaults.round_decimals)
    finally:
        if own_session:
            session.close()

def update_account(account_id: int, data: dict) -> Optional[Account]:
    """Update fields on an account. Returns updated Account or None."""
    session = Session()
    try:
        acc = session.get(Account, account_id)
        if not acc:
            return None
        for key, val in data.items():
            if hasattr(acc, key):
                setattr(acc, key, val)
        session.commit()
        session.refresh(acc)
        session.expunge(acc)
        return acc
    finally:
        session.close()

def toggle_account_hidden(
    account_id: int, hidden: Optional[bool] = None
) -> Optional[Account]:
    """Toggle or explicitly set the hidden flag."""
    session = Session()
    try:
        acc = session.get(Account, account_id)
        if not acc:
            return None
        acc.hidden = (not acc.hidden) if hidden is None else bool(hidden)
        session.commit()
        session.refresh(acc)
        session.expunge(acc)
        return acc
    finally:
        session.close()

def delete_account(account_id: int) -> bool:
    """Soft-delete account by setting deletedAt."""
    session = Session()
    try:
        acc = session.get(Account, account_id)
        if not acc:
            return False
        acc.deletedAt = datetime.now()
        session.commit()
        return True
    finally:
        session.close()
