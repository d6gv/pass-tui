"""TOTP dashboard: a terminal-authenticator view of all live codes."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Static

from pass_tui.cli import PassCliError, list_items, list_vaults
from pass_tui.screens.base import BackScreen
from pass_tui.widgets import TotpView

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class TotpDashboardScreen(BackScreen):
    """Shows every item's live TOTP code across all vaults.

    A ``TotpView`` is mounted per item; those without a TOTP hide themselves,
    so only items with codes remain visible. Codes refresh on their own 30s
    period. Note: this issues one ``item totp`` call per item on load.
    """

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    def compose_content(self) -> ComposeResult:
        yield Static("TOTP codes", id="totp-dash-title")
        yield Static(
            "Items without a TOTP are hidden.", id="totp-dash-hint"
        )
        yield VerticalScroll(id="totp-list")

    def on_screen_resume(self) -> None:
        self.load_codes()

    def action_refresh(self) -> None:
        self.load_codes()

    @work(exclusive=True, group="totp-dash")
    async def load_codes(self) -> None:
        """Gather all items and mount a TOTP view for each."""
        try:
            vaults = await list_vaults()
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not load vaults"
            )
            return

        container = self.query_one("#totp-list", VerticalScroll)
        await container.remove_children()

        for vault in vaults:
            try:
                items = await list_items(
                    vault_name=vault.name, share_id=vault.share_id
                )
            except PassCliError:
                # Skip a vault we cannot read rather than failing the whole view.
                continue
            for item in items:
                await container.mount(
                    TotpView(
                        item_id=item.item_id,
                        item_title=item.title,
                        vault_name=vault.name,
                        share_id=vault.share_id,
                        label=f"{item.display_title} — {vault.display_name}",
                    )
                )
