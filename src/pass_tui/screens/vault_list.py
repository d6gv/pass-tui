"""Vault list screen: the landing screen once a session is active."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import Static

from pass_tui.cli import SessionInfo
from pass_tui.screens.base import ChromeScreen
from pass_tui.screens.item_list import ItemListScreen
from pass_tui.screens.settings import SettingsScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class VaultListScreen(ChromeScreen):
    """Lists the user's vaults and is the root of the logged-in stack."""

    BINDINGS = [
        Binding("enter", "open_items", "Open"),
        Binding("s", "settings", "Settings"),
        Binding("ctrl+l", "logout", "Log out"),
    ]

    def __init__(self, session: SessionInfo) -> None:
        super().__init__()
        self._session = session

    def compose_content(self) -> ComposeResult:
        yield Static("Vaults will appear here.", id="vault-placeholder")

    def on_mount(self) -> None:
        self.app.sub_title = self._session.account_label

    def action_open_items(self) -> None:
        self.app.push_screen(ItemListScreen())

    def action_settings(self) -> None:
        self.app.push_screen(SettingsScreen())

    def action_logout(self) -> None:
        cast("PassTuiApp", self.app).perform_logout()
