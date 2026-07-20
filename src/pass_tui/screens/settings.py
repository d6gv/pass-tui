"""Settings screen (skeleton)."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static

from pass_tui.screens.base import BackScreen


class SettingsScreen(BackScreen):
    """Application and pass-cli settings."""

    def compose_content(self) -> ComposeResult:
        yield Static("Settings will appear here.", id="settings-placeholder")
