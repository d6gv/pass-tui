"""SSH key management screen for a single vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Static

from pass_tui.cli import Item, PassCliError, Vault, list_items
from pass_tui.screens.base import BackScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp

#: Normalized item type for SSH keys (from ``_normalize_type("ssh-key")``).
SSH_KEY_TYPE = "sshkey"


class SshScreen(BackScreen):
    """Lists the SSH-key items in a vault and manages the ssh-agent."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault
        self._keys_by_key: dict[str, Item] = {}

    def compose_content(self) -> ComposeResult:
        yield Static(f"SSH keys — {self._vault.display_name}", id="ssh-title")
        yield DataTable(id="ssh-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        self.query_one(DataTable).add_columns("Title")

    def on_screen_resume(self) -> None:
        self.load_keys()

    def action_refresh(self) -> None:
        self.load_keys()

    @work(exclusive=True, group="ssh")
    async def load_keys(self) -> None:
        """List the vault's items and keep only the SSH-key ones."""
        try:
            items = await list_items(
                vault_name=self._vault.name, share_id=self._vault.share_id
            )
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not load SSH keys"
            )
            return

        table = self.query_one(DataTable)
        table.clear()
        self._keys_by_key.clear()
        for index, item in enumerate(items):
            if item.type_label != SSH_KEY_TYPE:
                continue
            key = item.item_id or str(index)
            self._keys_by_key[key] = item
            table.add_row(item.display_title, key=key)
