"""Main Textual application for pass-tui."""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static


class PassTuiApp(App[None]):
    """Terminal UI for Proton Pass, layered over the official pass-cli."""

    TITLE = "pass-tui"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "pass-tui — a Proton Pass terminal UI (placeholder)",
            id="placeholder",
        )
        yield Footer()


def main() -> None:
    """Entry point for the ``pass-tui`` console script."""
    PassTuiApp().run()


if __name__ == "__main__":
    main()
