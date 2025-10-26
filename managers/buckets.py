from __future__ import annotations

from datetime import datetime
from typing import Optional

from Buckets.config import CONFIG
from Buckets.models.bucket import Bucket
from Buckets.models.database.app import Session


class BucketTransferError(Exception):
    """Raised when a bucket-to-bucket transfer is invalid."""

    pass


def create_bucket(data: dict) -> Bucket:
    """
    Create a bucket.

    Expected keys in `data`:
      - name (str, required)
      - amount (float, default 0.0)
      - accountId (int, required)
    """
    with Session() as s:
        bucket = Bucket(
            name=str(data["name"]),
            amount=round(
                float(data.get("amount", 0.0)), CONFIG.defaults.round_decimals
            ),
            accountId=int(data["accountId"]),
        )
        s.add(bucket)
        s.commit()
        s.refresh(bucket)
        s.expunge(bucket)
        return bucket


def get_bucket_by_id(bucket_id: int) -> Optional[Bucket]:
    with Session() as s:
        bucket = s.get(Bucket, int(bucket_id))
        if bucket and bucket.deletedAt is None:
            s.expunge(bucket)
            return bucket
        return None


def get_buckets_by_account(
    account_id: int, include_deleted: bool = False
) -> list[Bucket]:
    with Session() as s:
        q = s.query(Bucket).filter(Bucket.accountId == int(account_id))
        if not include_deleted:
            q = q.filter(Bucket.deletedAt.is_(None))
        buckets = q.order_by(Bucket.name.asc()).all()
        for b in buckets:
            s.expunge(b)
        return buckets


def get_all_buckets(include_deleted: bool = False) -> list[Bucket]:
    with Session() as s:
        q = s.query(Bucket)
        if not include_deleted:
            q = q.filter(Bucket.deletedAt.is_(None))
        buckets = q.order_by(Bucket.accountId.asc(), Bucket.name.asc()).all()
        for b in buckets:
            s.expunge(b)
        return buckets


def update_bucket(bucket_id: int, data: dict) -> Optional[Bucket]:
    """
    Update a bucket. Updatable keys: name, amount, accountId
    """
    with Session() as s:
        bucket = s.get(Bucket, int(bucket_id))
        if not bucket or bucket.deletedAt is not None:
            return None

        if "name" in data:
            bucket.name = str(data["name"])

        if "amount" in data:
            bucket.amount = round(float(data["amount"]), CONFIG.defaults.round_decimals)

        if "accountId" in data:
            bucket.accountId = int(data["accountId"])

        s.commit()
        s.refresh(bucket)
        s.expunge(bucket)
        return bucket


def delete_bucket(bucket_id: int) -> bool:
    with Session() as s:
        bucket = s.get(Bucket, int(bucket_id))
        if not bucket or bucket.deletedAt is not None:
            return False
        bucket.deletedAt = datetime.now()
        s.commit()
        return True


def transfer_between_buckets(
    from_bucket_id: int, to_bucket_id: int, amount: float
) -> bool:
    if from_bucket_id == to_bucket_id:
        raise BucketTransferError("Source and destination buckets must be different.")

    if amount is None:
        raise BucketTransferError("Amount is required.")

    amount = round(float(amount), CONFIG.defaults.round_decimals)
    if amount <= 0:
        raise BucketTransferError("Amount must be greater than 0.")

    with Session() as s:
        src = s.get(Bucket, int(from_bucket_id))
        dst = s.get(Bucket, int(to_bucket_id))

        if not src or src.deletedAt is not None:
            raise BucketTransferError("Source bucket not found.")
        if not dst or dst.deletedAt is not None:
            raise BucketTransferError("Destination bucket not found.")

        if src.accountId != dst.accountId:
            raise BucketTransferError("Buckets must belong to the same account.")

        if src.amount < amount:
            raise BucketTransferError("Insufficient funds in source bucket.")

        src.amount = round(src.amount - amount, CONFIG.defaults.round_decimals)
        dst.amount = round(dst.amount + amount, CONFIG.defaults.round_decimals)

        s.commit()
        return True
