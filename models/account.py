# Buckets/models/account.py
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from .database.db import Base


class Account(Base):
    __tablename__ = "account"

    # timestamps
    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    # fields
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    beginningBalance = Column(Float, nullable=False, default=0.0)
    hidden = Column(Boolean, nullable=False, default=False)
    # repaymentDate = Column(Integer, nullable=True)  # keep if you use it

    # ---- relationships ----
    # Matches Record.account (back_populates="account")
    records = relationship(
        "Record",
        back_populates="account",
        foreign_keys="Record.accountId",
        cascade="all, delete-orphan",
    )

    # Matches Record.transferToAccount (back_populates="transferToAccount")
    transferFromRecords = relationship(
        "Record",
        back_populates="transferToAccount",
        foreign_keys="Record.transferToAccountId",
    )

    # NEW: matches Bucket.account (back_populates="account")
    buckets = relationship(
        "Bucket",
        back_populates="account",
        cascade="all, delete-orphan",
    )

