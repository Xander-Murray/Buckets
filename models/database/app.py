from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from Buckets.models.account import Account
from Buckets.models.category import Category, Nature
from Buckets.models.database.db import Base
from Buckets.models.record import Record  # noqa: F401 (register table)
from Buckets.models.record_template import RecordTemplate  # noqa: F401
from Buckets.models.bucket import Bucket  # noqa: F401

# SQLite DB in project root
DB_PATH = Path("buckets.db").resolve()
db_engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
Session = sessionmaker(bind=db_engine)

def _create_outside_source_account(session):
    outside = session.query(Account).filter_by(name="Outside source").first()
    if not outside:
        outside = Account(
            name="Outside source",
            description="Default account for external transactions",
            beginningBalance=0.0,
            hidden=True,
        )
        session.add(outside)
        session.commit()

def _create_default_categories(session):
    if session.query(Category).count() > 0:
        return

    yaml_path = (
        Path(__file__).resolve().parents[2] / "default" / "default_categories.yaml"
    )

    with open(yaml_path, "r", encoding="utf-8") as file:
        default_categories = yaml.safe_load(file)

    for category in default_categories:
        parent = Category(
            name=category["name"],
            nature=getattr(Nature, category["nature"]),
            color=category["color"],
            parentCategoryId=None,
        )
        session.add(parent)
        session.commit()

        for subcategory in category["subcategories"]:
            child = Category(
                name=subcategory["name"],
                nature=getattr(Nature, subcategory["nature"]),
                color=category["color"],
                parentCategoryId=parent.id,
            )
            session.add(child)
            session.commit()

def _fix_dangling_categories(session):
    dangling_subcategories = (
        session.query(Category)
        .filter(
            Category.parentCategoryId.isnot(None),
            Category.deletedAt.is_(None),
            Category.parentCategoryId.in_(
                session.query(Category.id).filter(Category.deletedAt.isnot(None))
            ),
        )
        .all()
    )
    for subcategory in dangling_subcategories:
        subcategory.deletedAt = datetime.now()
        session.add(subcategory)
    session.commit()

def _sync_database_schema():
    try:
        inspector = inspect(db_engine)
        existing_tables = inspector.get_table_names()

        for table in Base.metadata.tables.values():
            if table.name not in existing_tables:
                table.create(db_engine)
            else:
                existing_columns = {
                    col["name"] for col in inspector.get_columns(table.name)
                }
                model_columns = {col.name for col in table.columns}

                for column_name in model_columns - existing_columns:
                    column = table.columns[column_name]
                    default_sql = ""
                    if column.default is not None:
                        try:
                            default_sql = f" DEFAULT {column.default.arg}"
                        except Exception:
                            pass
                    notnull_sql = " NOT NULL" if not column.nullable else ""
                    with db_engine.begin() as conn:
                        conn.execute(
                            text(
                                f'ALTER TABLE "{table.name}" ADD COLUMN "{column_name}" '
                                f"{column.type}{notnull_sql}{default_sql}"
                            )
                        )
    except Exception as e:
        raise Exception(f"Failed to sync database schema: {str(e)}")

def init_db():
    _sync_database_schema()
    Base.metadata.create_all(db_engine)
    session = Session()
    _create_outside_source_account(session)
    _create_default_categories(session)
    _fix_dangling_categories(session)
    session.close()
