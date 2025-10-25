from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database.db import Base


class Bucket(Base):
    """
    Represents a sub-allocation of funds inside an Account — like Ally's buckets.
    Each bucket belongs to exactly one account and has its own balance, goal,
    and metadata (name, color, etc.)
    """

    __tablename__ = "bucket"

    # ---------- Common Timestamps ---------- #
    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    # ---------- Core Columns ---------- #
    id = Column(Integer, primary_key=True, index=True)

    # Link this bucket to a parent account
    accountId = Column(Integer, ForeignKey("account.id"), nullable=False)

    # Display / management fields
    name = Column(String, nullable=False)  # e.g. "Vacation", "Rent", "Emergency Fund"
    description = Column(String, nullable=True)
    color = Column(String, nullable=True, default="#9b59b6")  # default purple color

    # Financial attributes
    allocatedAmount = Column(
        Float, nullable=False, default=0.0
    )  # how much money is currently in this bucket
    goalAmount = Column(Float, nullable=False, default=0.0)  # optional target goal
    hidden = Column(
        Boolean, nullable=False, default=False
    )  # allows user to hide unused buckets

    # ---------- Relationships ---------- #
    account = relationship("Account", back_populates="buckets")

    # Optional: link records if you want to track bucket-specific transactions later
    records = relationship(
        "Record", back_populates="bucket", cascade="all, delete-orphan"
    )
