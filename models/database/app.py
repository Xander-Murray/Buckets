from datetime import datetime
from pathlib import Path

import yaml
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# create the import
from models.account import Account
from models.category import Category, Nature
from models.database.db import Base
from models.record import Record
from models.record_template import RecordTemplate
from models.bucket import Bucket

db_engine = create_engine("sqlite:///buckets.db", echo=False)
Session = sessionmaker(bind=db_engine)


def _create_default_categories(session):
    category_account = session.query(Category).count()
    if category_account > 0:
        return

    yaml_path = (
        Path(__file__).parent.parent.parent / "default" / "default_categories.yaml"
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
                    with db_engine.begin() as conn:
                        conn.execute(
                            text(
                                f'ALTER TABLE {table.name} ADD COLUMN "{column_name}" '
                                f"{column.type} "
                                f"{'NOT NULL' if not column.nullable else ''} "
                                f"{'DEFAULT ' + str(column.default.arg) if column.default is not None else ''}"
                            )
                        )
    except Exception as e:
        raise Exception(f"Failed to sync database schema: {str(e)}")


def init_db():
    _sync_database_schema()
    Base.metadata.create_all(db_engine)
    session = Session()
    _create_default_categories(session)
    _fix_dangling_categories(session)
    session.close()


def wipe_database():
    Base.metadata.drop_all(db_engine)
    _sync_database_schema()
    Base.metadata.create_all(db_engine)
    session = Session()
    _create_default_categories(session)
    session.close()
