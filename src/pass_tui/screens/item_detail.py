"""Item detail screen: shows a single item's fields, secrets masked."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from rich.markup import escape
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.coordinate import Coordinate
from textual.timer import Timer
from textual.widgets import DataTable, ProgressBar, Static

from pass_tui.cli import Item, ItemDetail, ItemField, PassCliError, Vault, get_item
from pass_tui.screens.base import BackScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp

#: Fixed-width mask; deliberately hides the real length of the secret.
MASK = "••••••••"

#: How often the countdown progress bar is advanced, in seconds.
_PROGRESS_TICK = 0.25


class ItemDetailScreen(BackScreen):
    """Shows the fields of a single item, with sensitive values masked."""

    BINDINGS = [
        Binding("v", "toggle_reveal", "Reveal/hide"),
        Binding("c", "copy", "Copy field"),
    ]

    def __init__(self, item: Item, vault: Vault) -> None:
        super().__init__()
        self._item = item
        self._vault = vault
        self._detail: ItemDetail | None = None
        self._revealed = False
        self._progress_timer: Timer | None = None
        self._progress_left = 0.0

    def compose_content(self) -> ComposeResult:
        yield Static("Loading…", id="detail-title")
        yield DataTable(id="detail-table", cursor_type="row")
        yield Static("", id="detail-note")
        with Horizontal(id="clip-countdown"):
            yield Static("Clipboard clears in:", id="clip-label")
            yield ProgressBar(id="clip-bar", show_percentage=False)

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Field", "Value")
        self.query_one("#clip-countdown").display = False
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

        # The reveal binding only makes sense when there is a secret to reveal.
        self.refresh_bindings()

    def _display_value(self, field: ItemField) -> str:
        if field.sensitive and not self._revealed:
            return MASK
        return field.value or ""

    def _has_secrets(self) -> bool:
        return self._detail is not None and any(
            field.sensitive for field in self._detail.fields
        )

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool:
        if action == "toggle_reveal":
            return self._has_secrets()
        if action == "copy":
            return self._selected_field() is not None
        return True

    def _selected_field(self) -> ItemField | None:
        if self._detail is None or not self._detail.fields:
            return None
        row = self.query_one(DataTable).cursor_row
        if 0 <= row < len(self._detail.fields):
            return self._detail.fields[row]
        return None

    def action_copy(self) -> None:
        """Copy the selected field's real value and start the countdown."""
        field = self._selected_field()
        if field is None:
            return
        app = cast("PassTuiApp", self.app)
        if app.copy_with_autoclear(field.value, label=field.label):
            self._start_countdown(float(app.clipboard_clear_seconds))

    def _start_countdown(self, seconds: float) -> None:
        countdown = self.query_one("#clip-countdown")
        countdown.display = True
        bar = self.query_one("#clip-bar", ProgressBar)
        bar.update(total=seconds, progress=0.0)
        self._progress_left = seconds
        if self._progress_timer is not None:
            self._progress_timer.stop()
        self._progress_timer = self.set_interval(_PROGRESS_TICK, self._tick)

    def _tick(self) -> None:
        self._progress_left = max(0.0, self._progress_left - _PROGRESS_TICK)
        bar = self.query_one("#clip-bar", ProgressBar)
        bar.advance(_PROGRESS_TICK)
        if self._progress_left <= 0.0:
            self._stop_countdown()

    def _stop_countdown(self) -> None:
        if self._progress_timer is not None:
            self._progress_timer.stop()
            self._progress_timer = None
        self.query_one("#clip-countdown").display = False

    def action_toggle_reveal(self) -> None:
        """Toggle masking of sensitive fields, preserving the cursor."""
        if self._detail is None:
            return
        self._revealed = not self._revealed
        table = self.query_one(DataTable)
        for row, field in enumerate(self._detail.fields):
            if field.sensitive:
                table.update_cell_at(
                    Coordinate(row, 1), self._display_value(field)
                )
