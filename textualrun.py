from textual.app import App
from textual.containers import Container, VerticalScroll
from textual.widgets import Header, Footer, Label
from sqlalchemy.orm import sessionmaker

from models.database.app import db_engine
from models.account import Account


class BucketsApp(App):
    """Textual UI for Buckets Budget."""

    CSS_PATH = "styles/textual.tcss"
    TITLE = "💰 Buckets Budget"

    def on_mount(self) -> None:
        """Mount UI components."""
        Session = sessionmaker(bind=db_engine)
        self.session = Session()

        self.header = Header(show_clock=True)
        self.footer = Footer()
        self.body = VerticalScroll()

        # Mount UI elements first
        self.container = Container(self.header, self.body, self.footer)
        self.mount(self.container)

        # Then schedule refresh after mount
        self.call_after_refresh(self.refresh_view)

    def refresh_view(self) -> None:
        """Refresh the list of accounts and their buckets."""
        self.body.remove_children()

        accounts = self.session.query(Account).all()
        if not accounts:
            self.body.mount(Label("No accounts found."))
            return

        for account in accounts:
            self.body.mount(
                Label(f"🏦 {account.name} — ${account.beginningBalance:.2f}")
            )

            if hasattr(account, "buckets") and account.buckets:
                for bucket in account.buckets:
                    self.body.mount(Label(f"   📦 {bucket.name}: ${bucket.amount:.2f}"))
            else:
                self.body.mount(Label("   (no buckets)"))


if __name__ == "__main__":
    BucketsApp().run()

