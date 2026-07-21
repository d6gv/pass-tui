"""SSH key management screen for a single vault."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widgets import DataTable, RichLog, Static

from pass_tui.cli import (
    Item,
    PassCliError,
    Vault,
    list_items,
    ssh_agent_debug,
    ssh_agent_load,
)
from pass_tui.screens.base import BackScreen
from pass_tui.screens.forms import SshKeyFormScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp

#: Normalized item type for SSH keys (from ``_normalize_type("ssh-key")``).
SSH_KEY_TYPE = "sshkey"


class SshScreen(BackScreen):
    """Lists the SSH-key items in a vault and manages the ssh-agent."""

    DEFAULT_CSS = """
    SshScreen #ssh-debug {
        height: 12;
        border: round $primary;
        display: none;
    }
    """

    BINDINGS = [
        Binding("l", "load", "Load into agent"),
        Binding("d", "debug", "Debug"),
        Binding("n", "new_key", "New key"),
        Binding("r", "refresh", "Refresh"),
    ]

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault
        self._keys_by_key: dict[str, Item] = {}

    def compose_content(self) -> ComposeResult:
        yield Static(f"SSH keys — {self._vault.display_name}", id="ssh-title")
        yield DataTable(id="ssh-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="ssh-summary")
        yield RichLog(id="ssh-debug", highlight=False, markup=False, wrap=True)

    def on_mount(self) -> None:
        self.query_one(DataTable).add_columns("Title")

    def on_screen_resume(self) -> None:
        self.load_keys()

    def action_refresh(self) -> None:
        self.load_keys()

    def action_new_key(self) -> None:
        self.app.push_screen(SshKeyFormScreen(self._vault))

    def action_load(self) -> None:
        self.load_into_agent()

    @work(exclusive=True, group="ssh-load")
    async def load_into_agent(self) -> None:
        """Load the vault's SSH keys into the system agent and show the summary."""
        summary_widget = self.query_one("#ssh-summary", Static)
        summary_widget.update("Loading keys into the agent…")
        try:
            summary = await ssh_agent_load(
                vault_name=self._vault.name, share_id=self._vault.share_id
            )
        except PassCliError as exc:
            summary_widget.update("")
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not load keys into the agent"
            )
            return
        summary_widget.update(summary.as_line())
        self.notify(summary.as_line(), title="ssh-agent")

    def action_debug(self) -> None:
        self.run_debug()

    @work(exclusive=True, group="ssh-debug")
    async def run_debug(self) -> None:
        """Run ``ssh-agent debug`` and show its output in the log panel."""
        log = self.query_one("#ssh-debug", RichLog)
        log.display = True
        log.clear()
        log.write("Running ssh-agent debug…")
        try:
            output = await ssh_agent_debug(
                vault_name=self._vault.name, share_id=self._vault.share_id
            )
        except PassCliError as exc:
            log.display = False
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="ssh-agent debug failed"
            )
            return
        log.clear()
        log.write(output.rstrip() or "(no output)")

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
