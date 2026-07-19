"""Home screen shown once a pass-cli session is active."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from pass_tui.cli import SessionInfo


class HomeScreen(Screen[None]):
    """Landing screen for logged-in users."""

    DEFAULT_CSS = """
    HomeScreen {
        align: center middle;
    }
    #home-box {
        width: auto;
        height: auto;
        padding: 1 2;
    }
    """

    def __init__(self, session: SessionInfo) -> None:
        super().__init__()
        self._session = session

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="home-box"):
            yield Static(
                "You have an active Proton Pass session.",
                id="home-title",
            )
        yield Footer()
