# __main__.py
import sys, os

sys.path.append(os.path.dirname(__file__))

"""
Entry point for the Buckets budgeting application.
When you run `python -m Buckets`, this will initialize the database
and start the Textual terminal interface.
"""

from time import sleep
from models.database.app import init_db
from textualrun import BucketsApp


def main():
    print("🚀 Starting Buckets...")
    init_db()
    sleep(0.5)
    BucketsApp().run()


if __name__ == "__main__":
    main()
