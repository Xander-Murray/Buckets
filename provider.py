import platform
import subprocess
from functools import partial
from typing import TYPE_CHECKING, cast

from textual.command import DiscoveryHit, Hit, Hits, Provider
from textual.types import IgnoreReturnCallbackType

from Buckets.config import CONFIG, write_state
from Buckets.models.database.app import wipe_database, init_db

if TYPE_CHECKING:
    from textualrun import BucketsApp


class BucketsProvider(Provider):
    """Command palette provider for the Buckets terminal app."""

    @property
    def commands(
        self,
    ) -> tuple[tuple[str, IgnoreReturnCallbackType, str, bool], ...]:
        app = self.app

        commands_to_show = [
            ("app: quit", app.action_quit, "Quit the Buckets app", True),
            (
                "config: open file",
                self._action_open_config_file,
                "Open your Buckets config.yaml file in the default editor",
                True,
            ),
            (
                "config: toggle footer",
                self._action_toggle_footer,
                "Toggle footer visibility",
                True,
            ),
            (
                "database: reset",
                self._action_wipe_database,
                "Completely wipe and reinitialize the database",
                False,
            ),
            (
                "database: init",
                self._action_init_database,
                "Re-run database initialization (safe)",
                False,
            ),
            *self.get_theme_commands(),
        ]

        return tuple(commands_to_show)

    async def discover(self) -> Hits:
        """Show all available commands."""
        for name, runnable, help_text, show_discovery in self.commands:
            if show_discovery:
                yield DiscoveryHit(name, runnable, help=help_text)

    async def search(self, query: str) -> Hits:
        """Search for commands matching a query."""
        matcher = self.matcher(query)
        for name, runnable, help_text, _ in self.commands:
            if (match := matcher.match(name)) > 0:
                yield Hit(match, matcher.highlight(name), runnable, help=help_text)

    # ===== Theme Commands =====
    def get_theme_commands(
        self,
    ) -> tuple[tuple[str, IgnoreReturnCallbackType, str, bool], ...]:
        app = self.app
        return tuple(self.get_theme_command(theme) for theme in app.themes)

    def get_theme_command(
        self, theme_name: str
    ) -> tuple[str, IgnoreReturnCallbackType, str, bool]:
        return (
            f"theme: {theme_name}",
            partial(self.app.command_theme, theme_name),
            f"Change the theme to {theme_name}",
            True,
        )

    # ===== App Instance =====
    @property
    def app(self) -> "BucketsApp":
        return cast("BucketsApp", self.screen.app)

    # ===== Actions =====
    def _action_open_config_file(self) -> None:
        """Open the config file with the system's default editor."""
        try:
            file = "config.yaml"
            if platform.system() == "Darwin":
                subprocess.call(("open", file))
            elif platform.system() == "Windows":
                subprocess.call(("start", file), shell=True)
            else:
                subprocess.call(("xdg-open", file))
            self.app.notify("Opened config.yaml in your editor")
        except Exception as e:
            self.app.notify(f"Error opening config file: {e}", title="Error")

    def _action_toggle_footer(self) -> None:
        """Toggle footer visibility and save state."""
        cur = CONFIG.state.footer_visibility
        write_state("footer_visibility", not cur)
        self.app.refresh(layout=True, recompose=True)
        self.app.notify(f"Footer {'enabled' if not cur else 'hidden'}")

    def _action_wipe_database(self) -> None:
        """Completely drop all tables and recreate them."""
        wipe_database()
        self.app.refresh(layout=True, recompose=True)
        self.app.notify("Database wiped and recreated successfully")

    def _action_init_database(self) -> None:
        """Reinitialize the database safely (without wiping)."""
        init_db()
        self.app.notify("Database reinitialized successfully")
