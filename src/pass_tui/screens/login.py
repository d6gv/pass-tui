"""Login screen shown when there is no active pass-cli session."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class LoginScreen(Screen[None]):
    """Landing screen for logged-out users."""

    DEFAULT_CSS = """
    LoginScreen {
        align: center middle;
    }
    #login-box {
        width: auto;
        height: auto;
        padding: 1 2;
    }
    #login-title {
        text-style: bold;
    }
    #login-button {
        margin-top: 1;
    }
    #login-error {
        color: $error;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("l", "login", "Log in"),
    ]

    def __init__(self, error: str | None = None) -> None:
        super().__init__()
        self._error = error

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="login-box"):
            yield Static("No active Proton Pass session.", id="login-title")
            yield Static(
                "Press [b]l[/b] (or the button) to log in with pass-cli.",
                id="login-hint",
            )
            yield Button("Log in", id="login-button", variant="primary")
            if self._error:
                yield Static(self._error, id="login-error")
        yield Footer()

    def on_mount(self) -> None:
        # Clear any account label left in the header by a previous session.
        self.app.sub_title = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-button":
            self.action_login()

    def action_login(self) -> None:
        """Delegate an interactive login to pass-cli."""
        cast("PassTuiApp", self.app).perform_interactive_login()
