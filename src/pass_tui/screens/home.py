"""Home screen shown once a pass-cli session is active."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from pass_tui.cli import SessionInfo

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


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
        border: round $primary;
    }
    #home-title {
        text-style: bold;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "logout", "Log out"),
    ]

    def __init__(self, session: SessionInfo) -> None:
        super().__init__()
        self._session = session

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="home-box"):
            yield Static(
                f"Signed in as [b]{escape(self._session.account_label)}[/b]",
                id="home-title",
            )
            yield Static(self._details(), id="home-details")
        yield Footer()

    def on_mount(self) -> None:
        self.app.sub_title = self._session.account_label

    def action_logout(self) -> None:
        """Log out of the active pass-cli session."""
        cast("PassTuiApp", self.app).perform_logout()

    def _details(self) -> str:
        session = self._session
        rows: list[str] = []
        if session.email:
            rows.append(f"Email:   {escape(session.email)}")
        if session.username:
            rows.append(f"User:    {escape(session.username)}")
        if session.user_id:
            rows.append(f"User ID: {escape(session.user_id)}")
        if session.release_track:
            rows.append(f"Track:   {escape(session.release_track)}")
        return "\n".join(rows) if rows else "No account details available."
