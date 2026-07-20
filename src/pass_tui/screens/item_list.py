"""Item list screen (skeleton)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from pass_tui.screens.base import BackScreen
from pass_tui.screens.item_detail import ItemDetailScreen


class ItemListScreen(BackScreen):
    """Lists the items in a vault."""

    BINDINGS = [
        Binding("enter", "open_detail", "Open"),
    ]

    def compose_content(self) -> ComposeResult:
        yield Static("Items will appear here.", id="item-placeholder")

    def action_open_detail(self) -> None:
        self.app.push_screen(ItemDetailScreen())
