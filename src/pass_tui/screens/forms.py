"""Create/edit form screen (skeleton)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from pass_tui.screens.base import BackScreen


class FormScreen(BackScreen):
    """Form for creating or editing an item."""

    def compose_content(self) -> ComposeResult:
        yield Static("Form will appear here.", id="form-placeholder")
