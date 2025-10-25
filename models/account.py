from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean
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
    name = Column(String, nullable=False)
    description = Column(String)
    beginningBalance = Column(Float, nullable=False)
    repaymentDate = Column(Integer)

    hidden = Column(Boolean, nullable=False, default=False)

    records = relationship(
        "Record", back_populates="account", foreign_keys="[Record.accountId]"
    )
    transferFromRecords = relationship(
        "Record",
        back_populates="transferToAccount",
        foreign_keys="[Record.transferToAccountId]",
    )

    # New relationship: an account can have multiple buckets
    buckets = relationship(
        "Bucket", back_populates="account", cascade="all, delete-orphan"
    )
