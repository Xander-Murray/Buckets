"""
Textual App for the Buckets budgeting app (lean version).
- Uses Buckets' CONFIG
- Minimal: no theme plumbing, no extra CSS helpers
"""

from importlib.metadata import metadata, PackageNotFoundError

from textual import events, log, on
from textual.app import App as TextualApp, ComposeResult
from textual.command import CommandPalette
from textual.containers import Container
from textual.css.query import NoMatches
from textual.geometry import Size
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Footer, Label, Tab, Tabs

from Buckets.components.jump_overlay import JumpOverlay
from Buckets.components.jumper import Jumper
from Buckets.config import CONFIG, write_state
from Buckets.home import Home
from Buckets.buckets_page import BucketsPage
from Buckets.provider import BucketsProvider as AppProvider


PAGES = [
    {"name": "Home", "class": Home},
    {"name": "Buckets", "class": BucketsPage},
]


class App(TextualApp):
    CSS_PATH = [
        "styles/index.tcss",
        "styles/modals.tcss",
        "styles/home.tcss",
        "styles/home_modules.tcss",
        "styles/manager.tcss",
    ]

    BINDINGS = [
        (CONFIG.hotkeys.toggle_jump_mode, "toggle_jump_mode", "Jump Mode"),
        (CONFIG.hotkeys.home.cycle_tabs, "cycle_tabs", "Cycle tabs"),
        ("ctrl+q", "quit", "Quit"),
    ]
    COMMANDS = {AppProvider}

    layout: reactive[str] = reactive("h")
    _jumping: reactive[bool] = reactive(False, init=False, bindings=True)
    current_tab = 0

    def __init__(self, is_testing: bool = False) -> None:
        self.is_testing = is_testing
        super().__init__()

        try:
            meta = metadata("Buckets")
            name = meta.get("Name", "Buckets")
            version = meta.get("Version", "dev")
        except PackageNotFoundError:
            name, version = "Buckets", "dev"
        self.project_info = {"name": name, "version": version}

    def on_mount(self) -> None:
        # Keyboard "jumper" overlay mapping — jump directly to focusable widgets
        self.jumper = Jumper(
            {
                "accounts-container": "a",
                "buckets-container": "b",
                "categories-table": "k",
                "insights-container": "i",
                "records-container": "r",
                "templates-container": "t",
                "datemode-container": "p",
            },
            screen=self.screen,
        )

    # ----- Jump overlay -----
    def action_toggle_jump_mode(self) -> None:
        self._jumping = not self._jumping

    def watch__jumping(self, jumping: bool) -> None:
        focused_before = self.focused
        if focused_before is not None:
            self.set_focus(None, scroll_visible=False)

        def focus_first_focusable_within(w: Widget) -> bool:
            # Try common inner widgets first
            for selector in ("DataTable", "ListView", "Input", "Button"):
                try:
                    inner = w.query_one(selector)
                    if inner.focusable:
                        self.set_focus(inner)
                        return True
                except Exception:
                    pass
            # Fallback: any focusable descendant
            try:
                for child in w.walk_children(with_self=False):
                    if getattr(child, "focusable", False):
                        self.set_focus(child)
                        return True
            except Exception:
                pass
            return False

        def handle_jump_target(target: str | Widget | None) -> None:
            if isinstance(target, str):
                try:
                    target_widget = self.screen.query_one(f"#{target}")
                except NoMatches:
                    log.warning(f"Jump target #{target} not found on {self.screen!r}")
                    return
                # If target itself isn’t focusable, focus its best child (e.g., the DataTable)
                if target_widget.focusable:
                    self.set_focus(target_widget)
                else:
                    if (
                        not focus_first_focusable_within(target_widget)
                        and focused_before is not None
                    ):
                        self.set_focus(focused_before, scroll_visible=False)
            elif isinstance(target, Widget):
                self.set_focus(target)
            else:
                if focused_before is not None:
                    self.set_focus(focused_before, scroll_visible=False)

        self.clear_notifications()
        self.push_screen(JumpOverlay(self.jumper), callback=handle_jump_target)

    @on(CommandPalette.Opened)
    def palette_opened(self) -> None:
        pass

    @on(CommandPalette.OptionHighlighted)
    def palette_option_highlighted(
        self, event: CommandPalette.OptionHighlighted
    ) -> None:
        _ = event

    @on(CommandPalette.Closed)
    def palette_closed(self, event: CommandPalette.Closed) -> None:
        _ = event

    # ----- Tabs / layout -----
    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        if event.tab.id.startswith("tab-"):
            try:
                current = self.query_one(".content")
                current.remove()
            except NoMatches:
                pass
            page_class = next(
                page["class"]
                for page in PAGES
                if page["name"].lower() == event.tab.id.replace("tab-", "")
            )
            await self.mount(page_class(classes="content"))
            self.query_one(".content").set_classes(f"content {self.layout}")

    def on_resize(self, event: events.Resize) -> None:
        console_size: Size = event.size
        aspect_ratio = (console_size.width / 2) / console_size.height
        self.layout = "v" if aspect_ratio < 1 else "h"
        try:
            self.query_one(".content").set_classes(f"content {self.layout}")
        except Exception:
            pass

    # ----- Actions -----
    def action_goToTab(self, tab_number: int) -> None:
        tabs = self.query_one(Tabs)
        tabs.active = f"t{tab_number}"

    def action_quit(self) -> None:
        self.exit()

    def action_cycle_tabs(self) -> None:
        self.current_tab = (self.current_tab + 1) % len(PAGES)
        tab_id = f"tab-{PAGES[self.current_tab]['name'].lower()}"
        self.query_one(Tabs).active = tab_id

    def on_categories_dismissed(self, _) -> None:
        self.app.refresh(recompose=True)

    # ----- View -----
    def compose(self) -> ComposeResult:
        version = self.project_info["version"] if not self.is_testing else "vt"
        with Container(classes="header"):
            yield Label(f"↪ {self.project_info['name']}", classes="title")
            yield Label(version, classes="version")
            tabs = Tabs(
                *[
                    Tab(name, id=f"tab-{name.lower()}")
                    for name in [p["name"] for p in PAGES]
                ],
                classes="root-tabs",
            )
            tabs.can_focus = False
            yield tabs
            yield Label("Buckets", classes="path")
        if CONFIG.state.footer_visibility:
            yield Footer()
