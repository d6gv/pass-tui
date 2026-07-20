"""Main Textual application for pass-tui."""

from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Static

from pass_tui.cli import (
    PassCliError,
    fetch_session,
    logout,
    run_pass_cli_interactive,
)
from pass_tui.screens import HelpScreen, LoginScreen, VaultListScreen


class PassTuiApp(App[None]):
    """Terminal UI for Proton Pass, layered over the official pass-cli."""

    TITLE = "pass-tui"

    BINDINGS = [
        Binding("question_mark", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Static("Checking for an active session…", id="loading")

    def on_mount(self) -> None:
        self.check_session()

    def action_help(self) -> None:
        """Open the keyboard-shortcuts help overlay."""
        if isinstance(self.screen, HelpScreen):
            return
        self.push_screen(HelpScreen())

    @work(exclusive=True, group="session")
    async def check_session(self) -> None:
        """Detect an active pass-cli session and route to the right screen."""
        try:
            session = await fetch_session()
        except PassCliError as exc:
            self._show_screen(LoginScreen(error=str(exc)))
            return

        if session is None:
            self._show_screen(LoginScreen())
        else:
            self._show_screen(VaultListScreen(session))

    def perform_interactive_login(self) -> None:
        """Suspend the TUI, run ``pass-cli login``, then re-check the session."""
        try:
            exit_code = self._suspend_and_login()
        except PassCliError as exc:
            self.notify(str(exc), title="pass-cli", severity="error")
            return

        if exit_code == 0:
            self.check_session()
        else:
            self.notify(
                "Login was cancelled or did not complete.",
                title="pass-cli",
                severity="warning",
            )

    def _suspend_and_login(self) -> int:
        """Hand the terminal to ``pass-cli login`` while the TUI is suspended.

        Isolated so tests can stub it without a real terminal or subprocess.
        """
        with self.suspend():
            return run_pass_cli_interactive("login")

    @work(exclusive=True, group="session")
    async def perform_logout(self) -> None:
        """Log out via ``pass-cli logout`` and return to the login screen."""
        try:
            await logout()
        except PassCliError as exc:
            self.notify(str(exc), title="pass-cli", severity="error")
            return
        self.notify("Logged out.", title="pass-cli")
        self._show_screen(LoginScreen())

    def _show_screen(self, screen: Screen[None]) -> None:
        """Route to ``screen``, replacing any current login/home screen.

        The first navigation happens over Textual's default screen, which
        ``switch_screen`` cannot replace, so it is pushed; later transitions
        swap the login/home screen in place.
        """
        if isinstance(self.screen, (LoginScreen, VaultListScreen)):
            self.switch_screen(screen)
        else:
            self.push_screen(screen)


def main() -> None:
    """Entry point for the ``pass-tui`` console script."""
    PassTuiApp().run()


if __name__ == "__main__":
    main()
