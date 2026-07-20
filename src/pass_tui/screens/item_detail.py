"""Item detail screen (skeleton)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from pass_tui.screens.base import BackScreen


class ItemDetailScreen(BackScreen):
    """Shows the fields of a single item."""

    def compose_content(self) -> ComposeResult:
        yield Static("Item details will appear here.", id="detail-placeholder")
