"""Vault list screen: the landing screen once a session is active."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable

from pass_tui.cli import PassCliError, SessionInfo, Vault, list_vaults
from pass_tui.screens.base import ChromeScreen
from pass_tui.screens.item_list import ItemListScreen
from pass_tui.screens.settings import SettingsScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class VaultListScreen(ChromeScreen):
    """Lists the user's vaults and is the root of the logged-in stack."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("s", "settings", "Settings"),
        Binding("ctrl+l", "logout", "Log out"),
    ]

    def __init__(self, session: SessionInfo) -> None:
        super().__init__()
        self._session = session
        self._vaults_by_key: dict[str, Vault] = {}

    def compose_content(self) -> ComposeResult:
        yield DataTable(id="vault-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        self.app.sub_title = self._session.account_label
        table = self.query_one(DataTable)
        table.add_columns("Vault", "Items", "Shared")
        self.load_vaults()

    @work(exclusive=True, group="vaults")
    async def load_vaults(self) -> None:
        """Fetch vaults from pass-cli and populate the table."""
        try:
            vaults = await list_vaults()
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not load vaults"
            )
            return

        table = self.query_one(DataTable)
        table.clear()
        self._vaults_by_key.clear()
        for index, vault in enumerate(vaults):
            key = vault.share_id or str(index)
            self._vaults_by_key[key] = vault
            table.add_row(
                vault.display_name,
                vault.item_count_display,
                "yes" if vault.is_shared else "",
                key=key,
            )

    def action_refresh(self) -> None:
        self.load_vaults()

    def action_settings(self) -> None:
        self.app.push_screen(SettingsScreen())

    def action_logout(self) -> None:
        cast("PassTuiApp", self.app).perform_logout()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        key = event.row_key.value
        if key is None:
            return
        vault = self._vaults_by_key.get(key)
        if vault is not None:
            self.app.push_screen(ItemListScreen(vault))
