"""Item list screen: shows the items inside a vault, with a live filter."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import events, work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, Input, Static

from pass_tui.cli import Item, PassCliError, Vault, list_items
from pass_tui.screens.base import BackScreen
from pass_tui.screens.item_detail import ItemDetailScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


def fuzzy_match(query: str, text: str) -> bool:
    """Case-insensitive subsequence match.

    Returns ``True`` when every character of ``query`` appears in ``text`` in
    order (not necessarily contiguously). An empty query matches everything.
    """
    query = query.lower()
    if not query:
        return True
    characters = iter(text.lower())
    return all(character in characters for character in query)


class ItemListScreen(BackScreen):
    """Lists the items in a single vault, filtered live by title."""

    BINDINGS = [
        Binding("slash", "focus_filter", "Filter"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault
        self._all_items: list[Item] = []
        self._items_by_key: dict[str, Item] = {}

    def compose_content(self) -> ComposeResult:
        yield Static(f"Vault: {self._vault.display_name}", id="item-vault")
        yield Input(placeholder="Filter items by title…", id="item-filter")
        yield DataTable(id="item-table", cursor_type="row", zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("", "Title", "Type")
        table.focus()
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

        self._all_items = items
        self._populate()

    def _populate(self) -> None:
        """Render the items whose title matches the current filter."""
        query = self.query_one("#item-filter", Input).value
        table = self.query_one(DataTable)
        table.clear()
        self._items_by_key.clear()
        for index, item in enumerate(self._all_items):
            if not fuzzy_match(query, item.display_title):
                continue
            key = item.item_id or str(index)
            self._items_by_key[key] = item
            table.add_row(
                item.type_icon,
                item.display_title,
                item.type_label,
                key=key,
            )

    def action_focus_filter(self) -> None:
        self.query_one("#item-filter", Input).focus()

    def action_refresh(self) -> None:
        self.load_items()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "item-filter":
            self._populate()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "item-filter":
            self.query_one(DataTable).focus()

    def on_key(self, event: events.Key) -> None:
        # Escape while filtering returns to the table instead of leaving.
        if event.key == "escape" and self.app.focused is self.query_one(
            "#item-filter", Input
        ):
            self.query_one(DataTable).focus()
            event.stop()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        # The selected item will drive the detail view in a later step.
        self.app.push_screen(ItemDetailScreen())
