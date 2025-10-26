from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database.db import Base

class Bucket(Base):
    __tablename__ = "bucket"

    createdAt = Column(DateTime, nullable=False, default=datetime.now)
    updatedAt = Column(
        DateTime, nullable=False, default=datetime.now, onupdate=datetime.now
    )
    deletedAt = Column(DateTime, nullable=True)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)

    accountId = Column(
        Integer, ForeignKey("account.id", ondelete="CASCADE"), nullable=False
    )

    account = relationship("Account", back_populates="buckets")
