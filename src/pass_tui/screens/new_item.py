"""Modal for choosing which kind of item to create."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class NewItemModal(ModalScreen[str | None]):
    """Asks which item type to create; dismisses the chosen kind or ``None``."""

    DEFAULT_CSS = """
    NewItemModal {
        align: center middle;
        background: $background 60%;
    }
    #new-item-box {
        width: 40;
        max-width: 90%;
        height: auto;
        padding: 1 2;
        border: round $primary;
        background: $surface;
    }
    #new-item-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #new-item-box Button {
        width: 100%;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="new-item-box"):
            yield Static("Create item", id="new-item-title")
            yield Button("Login", id="kind-login", variant="primary")
            yield Button("Note", id="kind-note")
            yield Button("Card", id="kind-card")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id and event.button.id.startswith("kind-"):
            self.dismiss(event.button.id.removeprefix("kind-"))

    def action_cancel(self) -> None:
        self.dismiss(None)
