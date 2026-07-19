"""Login screen shown when there is no active pass-cli session."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static


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
    #login-error {
        color: $error;
        margin-top: 1;
    }
    """

    def __init__(self, error: str | None = None) -> None:
        super().__init__()
        self._error = error

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="login-box"):
            yield Static("No active Proton Pass session.", id="login-title")
            yield Static(
                "Log in with pass-cli to continue.",
                id="login-hint",
            )
            if self._error:
                yield Static(self._error, id="login-error")
        yield Footer()
