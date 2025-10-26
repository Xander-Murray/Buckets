from datetime import datetime

from rich.text import Text
from sqlalchemy import desc, func, select
from sqlalchemy.orm import joinedload, sessionmaker

from Buckets.managers.utils import get_start_end_of_period
from Buckets.models.category import Category
from Buckets.models.database.app import db_engine
from Buckets.models.record import Record

Session = sessionmaker(bind=db_engine)

# region Get
def get_categories_count() -> int:
    """Count all categories excluding deleted ones."""
    session = Session()
    try:
        stmt = select(Category).filter(Category.deletedAt.is_(None))
        return len(session.scalars(stmt).all())
    finally:
        session.close()

def get_all_categories_tree() -> list[tuple[Category, Text, int]]:
    """Retrieve all categories in a hierarchical tree format."""
    session = Session()
    try:
        stmt = (
            select(Category)
            .options(joinedload(Category.parentCategory))
            .order_by(Category.id)
            .filter(Category.deletedAt.is_(None))
        )
        categories = session.scalars(stmt).all()

        def is_last(cat, parent_id):
            siblings = [c for c in categories if c.parentCategoryId == parent_id]
            return cat == siblings[-1] if siblings else True

        def build_category_tree(parent_id=None, depth=0):
            result = []
            for category in categories:
                if category.parentCategoryId == parent_id:
                    if depth == 0:
                        node = Text("●", style=category.color)
                    else:
                        node = Text(
                            " " * (depth - 1)
                            + ("└" if is_last(category, parent_id) else "├"),
                            style=category.color,
                        )
                    result.append((category, node, depth))
                    result.extend(build_category_tree(category.id, depth + 1))
            return result

        return build_category_tree()
    finally:
        session.close()

def get_all_categories_by_freq():
    """Retrieve all categories ordered by the frequency of their usage in records."""
    session = Session()
    try:
        stmt = (
            select(Category, func.count(Category.records).label("record_count"))
            .outerjoin(Category.records)
            .group_by(Category.id)
            .order_by(desc("record_count"))
            .options(joinedload(Category.parentCategory))
            .filter(Category.deletedAt.is_(None))
        )
        return session.execute(stmt).all()
    finally:
        session.close()

def get_category_by_id(category_id: int) -> Category | None:
    """Retrieve a category by its ID."""
    session = Session()
    try:
        stmt = (
            select(Category)
            .filter_by(id=category_id)
            .filter(Category.deletedAt.is_(None))
            .options(joinedload(Category.parentCategory))
        )
        return session.scalars(stmt).first()
    finally:
        session.close()

def get_all_categories_records(
    offset: int = 0,
    offset_type: str = "month",
    is_income: bool = True,
    subcategories: bool = False,
    account_id: int | None = None,
):
    session = Session()
    try:
        start_of_period, end_of_period = get_start_end_of_period(offset, offset_type)

        stmt = (
            select(Record)
            .options(joinedload(Record.category))
            .filter(
                Record.date >= start_of_period,
                Record.date < end_of_period,
                Record.isIncome == is_income,
                Record.isTransfer == False,  # exclude transfers
            )
        )
        if account_id is not None:
            stmt = stmt.filter(Record.accountId == account_id)

        category_totals: dict[int, float] = {}
        records = session.scalars(stmt).all()

        for record in records:
            if record.category is None:
                continue

            # Amount = raw record amount (no split adjustments)
            record_amount = record.amount

            # Roll up to parent if requested
            category_id = (
                record.category.parentCategoryId
                if (not subcategories and record.category.parentCategoryId)
                else record.categoryId
            )

            category_totals[category_id] = (
                category_totals.get(category_id, 0.0) + record_amount
            )

        if not category_totals:
            return []

        cats_stmt = (
            select(Category)
            .filter(
                Category.id.in_(category_totals.keys()),
                Category.deletedAt.is_(None),
            )
            .options(joinedload(Category.parentCategory))
        )
        categories = session.scalars(cats_stmt).all()

        # Attach computed total for convenience on objects
        for category in categories:
            category.amount = category_totals.get(category.id, 0.0)

        # Drop zero totals, sort by amount desc
        categories = [c for c in categories if c.amount != 0]
        categories.sort(key=lambda c: c.amount, reverse=True)

        return categories
    finally:
        session.close()

# region Create
def create_category(data: dict) -> Category:
    """Create a new category."""
    session = Session()
    try:
        new_category = Category(**data)
        session.add(new_category)
        session.commit()
        session.refresh(new_category)
        session.expunge(new_category)
        return new_category
    finally:
        session.close()

# region Update
def update_category(category_id: int, data: dict) -> Category | None:
    """Update a category by its ID."""
    session = Session()
    try:
        category = session.get(Category, category_id)
        if category:
            for key, value in data.items():
                setattr(category, key, value)
            session.commit()
            session.refresh(category)
            session.expunge(category)
        return category
    finally:
        session.close()

# region Delete
def delete_category(category_id: int) -> bool:
    """Soft-delete a category and its subcategories."""
    session = Session()
    try:
        category = session.get(Category, category_id)
        if not category:
            return False

        now = datetime.now()
        category.deletedAt = now

        # Soft-delete direct children too
        subcategories = (
            session.query(Category).filter_by(parentCategoryId=category_id).all()
        )
        for sub in subcategories:
            sub.deletedAt = now

        session.commit()
        session.refresh(category)
        session.expunge(category)
        return True
    finally:
        session.close()
