"""Main Textual application for pass-tui."""

from __future__ import annotations

import json

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Static

from pass_tui.cli import PassCliError, run_pass_cli


class PassTuiApp(App[None]):
    """Terminal UI for Proton Pass, layered over the official pass-cli."""

    TITLE = "pass-tui"

    BINDINGS = [
        Binding("ctrl+d", "debug_info", "Debug: pass-cli info", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(
            "pass-tui — a Proton Pass terminal UI (placeholder)",
            id="placeholder",
        )
        yield Footer()

    async def action_debug_info(self) -> None:
        """Hidden command: dump `pass-cli info` JSON through the runner.

        Bound to ctrl+d. Proves the runner works from inside the app.
        """
        placeholder = self.query_one("#placeholder", Static)
        try:
            data = await run_pass_cli("info", "--output", "json")
        except PassCliError as exc:
            placeholder.update(f"pass-cli error:\n{exc}")
            return
        placeholder.update(json.dumps(data, indent=2))


def main() -> None:
    """Entry point for the ``pass-tui`` console script."""
    PassTuiApp().run()


if __name__ == "__main__":
    main()
