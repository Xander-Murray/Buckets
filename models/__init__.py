# Ensure models are imported so SQLAlchemy sees all tables before mapping
from .database.db import Base  # noqa: F401
from .account import Account  # noqa: F401
from .bucket import Bucket  # noqa: F401
from .category import Category  # noqa: F401
from .record import Record  # noqa: F401
from .record_template import RecordTemplate  # noqa: F401

