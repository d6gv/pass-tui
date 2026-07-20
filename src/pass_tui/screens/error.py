"""Non-fatal error modal for surfacing pass-cli failures."""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ErrorModal(ModalScreen[None]):
    """Shows an error message over the current screen without crashing."""

    DEFAULT_CSS = """
    ErrorModal {
        align: center middle;
        background: $background 60%;
    }
    #error-box {
        width: 60;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        border: round $error;
        background: $surface;
    }
    #error-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    #error-dismiss {
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Dismiss"),
        Binding("enter", "close", "Dismiss", show=False),
    ]

    def __init__(self, message: str, *, title: str = "Error") -> None:
        super().__init__()
        self._message = message
        self._title = title

    def compose(self) -> ComposeResult:
        with Vertical(id="error-box"):
            yield Static(self._title, id="error-title")
            yield Static(escape(self._message), id="error-message")
            yield Button("Dismiss", id="error-dismiss", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "error-dismiss":
            self.action_close()

    def action_close(self) -> None:
        self.dismiss()
