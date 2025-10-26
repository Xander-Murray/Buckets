from typing import TYPE_CHECKING

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Center
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Label

from Buckets.config import CONFIG

if TYPE_CHECKING:
    from Buckets.components.jumper import Jumper

class JumpOverlay(ModalScreen[str | Widget | None]):
    DEFAULT_CSS = """\
    JumpOverlay {
        background: black 25%;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss_overlay", "Dismiss", show=False),
    ]

    def __init__(
        self,
        jumper: "Jumper",
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.jumper: Jumper = jumper
        self.keys_to_widgets: dict[str, Widget | str] = {}
        self._resize_counter = 0

    def on_key(self, key_event: events.Key) -> None:
        if key_event.key in [
            "tab",
            "shift+tab",
            CONFIG.hotkeys.new,
            CONFIG.hotkeys.edit,
            CONFIG.hotkeys.delete,
            CONFIG.hotkeys.home.new_transfer,
        ]:
            key_event.stop()
            key_event.prevent_default()

        if self.is_active:
            # If they press a key corresponding to a jump target,
            # then we jump to it.
            target = self.keys_to_widgets.get(key_event.key)
            if target is not None:
                self.dismiss(target)
                return

    def action_dismiss_overlay(self) -> None:
        self.dismiss(None)

    async def on_resize(self) -> None:
        self._resize_counter += 1
        if self._resize_counter == 1:
            return
        await self.recompose()

    def _sync(self) -> None:
        self.overlays = self.jumper.get_overlays()
        self.keys_to_widgets = {v.key: v.widget for v in self.overlays.values()}

    def compose(self) -> ComposeResult:
        self._sync()
        for offset, jump_info in self.overlays.items():
            key, _widget = jump_info
            label = Label(key, classes="textual-jump-label")
            label.styles.offset = offset
            yield label
        with Center(id="textual-jump-info"):
            yield Label("Press a key to jump")
        with Center(id="textual-jump-dismiss"):
            yield Label("[b]ESC[/] to dismiss")
