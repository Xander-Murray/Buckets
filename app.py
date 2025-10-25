"""
Main entry point for the Buckets budgeting app.
Handles database initialization and basic CLI inspection.
"""

from models.database.app import init_db, Session
from models.account import Account
from models.bucket import Bucket
from models.category import Category
from models.record import Record
from models.record_template import RecordTemplate


def main():
    print("Initializing Buckets database...")
    init_db()

    # Start a session
    session = Session()

    # Display some simple data overview
    accounts = session.query(Account).all()
    print(f"\n🧾 Found {len(accounts)} accounts:")
    for acc in accounts:
        print(f" - {acc.name} (${acc.beginningBalance:.2f})")

        buckets = session.query(Bucket).filter_by(accountId=acc.id).all()
        for b in buckets:
            print(f"    ├─ {b.name}: ${b.amount:.2f}")

    print("\n✅ Database loaded successfully.")
    print("Use:  python textualrun.py  to open the Textual terminal interface.")
    session.close()


if __name__ == "__main__":
    main()
