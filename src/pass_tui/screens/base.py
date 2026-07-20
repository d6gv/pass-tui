"""Shared screen chrome for pass-tui screens."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Footer, Header


class ChromeScreen(Screen[None]):
    """A screen with the standard header and footer.

    Subclasses provide their body by overriding :meth:`compose_content`.
    """

    def compose(self) -> ComposeResult:
        yield Header()
        yield from self.compose_content()
        yield Footer()

    def compose_content(self) -> ComposeResult:
        yield from ()


class BackScreen(ChromeScreen):
    """A pushed screen that pops itself off the stack on Escape."""

    BINDINGS = [
        Binding("escape", "back", "Back"),
    ]

    def action_back(self) -> None:
        self.dismiss()
