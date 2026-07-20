"""Modal help screen listing keyboard shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

_HELP_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "General",
        [
            ("?", "Toggle this help"),
            ("Ctrl+C", "Quit pass-tui"),
        ],
    ),
    (
        "Vault list",
        [
            ("Up / Down", "Move between vaults"),
            ("Enter", "Open the selected vault"),
            ("r", "Refresh the vault list"),
            ("s", "Open settings"),
            ("Ctrl+L", "Log out"),
        ],
    ),
    (
        "Navigation",
        [
            ("Esc", "Go back"),
        ],
    ),
]


class HelpScreen(ModalScreen[None]):
    """An overlay listing the available keyboard shortcuts."""

    DEFAULT_CSS = """
    HelpScreen {
        align: center middle;
        background: $background 60%;
    }
    #help-box {
        width: 60;
        max-width: 90%;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        border: round $primary;
        background: $surface;
    }
    #help-title {
        text-style: bold;
        margin-bottom: 1;
    }
    .help-section {
        text-style: bold;
        color: $secondary;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "close", "Close"),
        Binding("question_mark", "close", "Close", show=False),
    ]

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="help-box"):
            yield Static("pass-tui — keyboard shortcuts", id="help-title")
            for title, rows in _HELP_SECTIONS:
                yield Static(title, classes="help-section")
                for key, description in rows:
                    yield Static(f"  [b]{key:<10}[/b] {description}")

    def action_close(self) -> None:
        self.dismiss()
