# buckets_page.py
from datetime import datetime
from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static

from Buckets.components.modules.accountmode import AccountMode
from Buckets.components.modules.categories import Categories
from Buckets.components.modules.buckets import BucketsModule
from Buckets.managers.accounts import get_all_accounts


class BucketsPage(Static):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, id="buckets-page")

        self.accounts_module = AccountMode(parent=self)
        self.categories_module = Categories()
        self.buckets_module = BucketsModule(page_parent=self)

        accounts = get_all_accounts()
        self.accounts = accounts
        self.accounts_indices = {"index": 0, "count": len(accounts)}

        self.mode = {
            "isIncome": False,
            "date": datetime.now(),
            "accountId": {
                "default_value": None,
                "default_value_text": "Select account",
            },
        }
        if accounts:
            self.mode["accountId"]["default_value"] = accounts[0].id
            self.mode["accountId"]["default_value_text"] = accounts[0].name

    def on_mount(self) -> None:
        self.rebuild()

    def rebuild(self) -> None:
        self.accounts_module.rebuild()
        self.buckets_module.rebuild()
        self.categories_module.rebuild()

    # ---------- selection helpers ----------

    def _select_account(self, dir: int = 0, id: int | None = None) -> None:
        if id is not None:
            # select by id
            for index, account in enumerate(self.accounts):
                if account.id == int(id):
                    self.accounts_indices["index"] = index
                    self.mode["accountId"]["default_value"] = account.id
                    self.mode["accountId"]["default_value_text"] = account.name
                    break
        elif self.accounts_indices["count"] > 0:
            # rotate by direction
            new_index = (self.accounts_indices["index"] + dir) % self.accounts_indices[
                "count"
            ]
            self.accounts_indices["index"] = new_index
            sel = self.accounts[new_index]
            self.mode["accountId"]["default_value"] = sel.id
            self.mode["accountId"]["default_value_text"] = sel.name

        self.accounts_module.rebuild()
        self.buckets_module.rebuild()
        self.categories_module.rebuild()

    def action_select_account(self, account_id: int) -> None:
        self._select_account(id=account_id)

    def action_select_prev_account(self) -> None:
        self._select_account(-1)

    def action_select_next_account(self) -> None:
        self._select_account(1)

    # ---------- view ----------

    def compose(self) -> ComposeResult:
        with Static(classes="manager-modules-container"):
            with Container(classes="left"):
                yield self.accounts_module
                yield self.buckets_module
            with Container(classes="right"):
                yield self.categories_module
