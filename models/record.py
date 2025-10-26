from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship, validates

from Buckets.config import CONFIG
from .database.db import Base


class Record(Base):
    __tablename__ = "record"

    # timestamps
    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )

    # fields
    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, nullable=False)
    amount = Column(Float, CheckConstraint("amount > 0"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.now)

    accountId = Column(Integer, ForeignKey("account.id"), nullable=False)
    categoryId = Column(Integer, ForeignKey("category.id"), nullable=True)

    isIncome = Column(Boolean, nullable=False, default=False)
    isTransfer = Column(
        Boolean,
        CheckConstraint("(isTransfer = FALSE) OR (isIncome = FALSE)"),
        nullable=False,
        default=False,
    )
    transferToAccountId = Column(Integer, ForeignKey("account.id"), nullable=True)

    account = relationship(
        "Account",
        back_populates="records",
        foreign_keys=[accountId],
    )
    transferToAccount = relationship(
        "Account",
        back_populates="transferFromRecords",
        foreign_keys=[transferToAccountId],
    )
    category = relationship("Category", back_populates="records")

    @validates("amount")
    def validate_amount(self, key, value):
        if value is not None:
            return round(value, CONFIG.defaults.round_decimals)
        return value
