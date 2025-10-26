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

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    beginningBalance = Column(Float, nullable=False, default=0.0)
    hidden = Column(Boolean, nullable=False, default=False)

    records = relationship(
        "Record",
        back_populates="account",
        foreign_keys="Record.accountId",
        cascade="all, delete-orphan",
    )

    transferFromRecords = relationship(
        "Record",
        back_populates="transferToAccount",
        foreign_keys="Record.transferToAccountId",
    )

    buckets = relationship(
        "Bucket",
        back_populates="account",
        cascade="all, delete-orphan",
    )
