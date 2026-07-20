"""Item detail screen: shows a single item's fields, secrets masked."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.widgets import DataTable, Static

from pass_tui.cli import Item, ItemDetail, ItemField, PassCliError, Vault, get_item
from pass_tui.screens.base import BackScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp

#: Fixed-width mask; deliberately hides the real length of the secret.
MASK = "••••••••"


class ItemDetailScreen(BackScreen):
    """Shows the fields of a single item, with sensitive values masked."""

    def __init__(self, item: Item, vault: Vault) -> None:
        super().__init__()
        self._item = item
        self._vault = vault
        self._detail: ItemDetail | None = None
        self._revealed = False

    def compose_content(self) -> ComposeResult:
        yield Static("Loading…", id="detail-title")
        yield DataTable(id="detail-table", cursor_type="row")
        yield Static("", id="detail-note")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Field", "Value")
        self.load_detail()

    @work(exclusive=True, group="detail")
    async def load_detail(self) -> None:
        """Fetch the item detail from pass-cli and render it."""
        try:
            detail = await get_item(
                item_id=self._item.item_id,
                item_title=self._item.title,
                vault_name=self._vault.name,
                share_id=self._vault.share_id,
            )
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not load item"
            )
            return

        self._detail = detail
        self._render_detail()

    def _render_detail(self) -> None:
        detail = self._detail
        if detail is None:
            return

        title = self.query_one("#detail-title", Static)
        title.update(
            f"{self._item.type_icon} [b]{escape(detail.title)}[/b]  "
            f"[dim]({escape(detail.item_type)})[/dim]"
        )

        table = self.query_one(DataTable)
        table.clear()
        for field in detail.fields:
            table.add_row(field.label, self._display_value(field))

        note = self.query_one("#detail-note", Static)
        note.update(escape(detail.note) if detail.note else "")

    def _display_value(self, field: ItemField) -> str:
        if field.sensitive and not self._revealed:
            return MASK
        return field.value or ""
