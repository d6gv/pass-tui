"""Item list screen: shows the items inside a vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Static

from pass_tui.cli import Item, PassCliError, Vault, list_items
from pass_tui.screens.base import BackScreen
from pass_tui.screens.item_detail import ItemDetailScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class ItemListScreen(BackScreen):
    """Lists the items in a single vault."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault
        self._items_by_key: dict[str, Item] = {}

    def compose_content(self) -> ComposeResult:
        yield Static(f"Vault: {self._vault.display_name}", id="item-vault")
        yield DataTable(id="item-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("", "Title", "Type")
        self.load_items()

    @work(exclusive=True, group="items")
    async def load_items(self) -> None:
        """Fetch items for the vault from pass-cli and populate the table."""
        try:
            items = await list_items(
                vault_name=self._vault.name, share_id=self._vault.share_id
            )
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not load items"
            )
            return

        table = self.query_one(DataTable)
        table.clear()
        self._items_by_key.clear()
        for index, item in enumerate(items):
            key = item.item_id or str(index)
            self._items_by_key[key] = item
            table.add_row(
                item.type_icon,
                item.display_title,
                item.type_label,
                key=key,
            )

    def action_refresh(self) -> None:
        self.load_items()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # The selected item will drive the detail view in a later step.
        self.app.push_screen(ItemDetailScreen())
