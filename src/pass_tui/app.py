"""Main Textual application for pass-tui."""

from __future__ import annotations

import pyperclip
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

from pass_tui.cli import (
    PassCliError,
    fetch_session,
    logout,
    run_pass_cli_interactive,
)
from pass_tui.screens import ErrorModal, HelpScreen, LoginScreen, VaultListScreen


class PassTuiApp(App[None]):
    """Terminal UI for Proton Pass, layered over the official pass-cli."""

    TITLE = "pass-tui"

    BINDINGS = [
        Binding("question_mark", "help", "Help"),
    ]

    #: Seconds before a copied secret is cleared from the clipboard.
    #: Configurable; will be sourced from config.py in a later phase.
    clipboard_clear_seconds: int = 15

    def __init__(self) -> None:
        super().__init__()
        self._clip_timer: Timer | None = None
        self._clip_value: str | None = None

    def compose(self) -> ComposeResult:
        yield Static("Checking for an active session…", id="loading")

    def on_mount(self) -> None:
        self.check_session()

    def copy_with_autoclear(self, value: str, *, label: str) -> bool:
        """Copy ``value`` and schedule it to be cleared after the timeout.

        Returns ``True`` on success. The clear timer lives on the app so the
        clipboard is wiped even if the user navigates away from the item.
        """
        try:
            pyperclip.copy(value)
        except pyperclip.PyperclipException as exc:
            self.show_error(str(exc), title="Clipboard unavailable")
            return False

        self._clip_value = value
        if self._clip_timer is not None:
            self._clip_timer.stop()
        self._clip_timer = self.set_timer(
            self.clipboard_clear_seconds, self._clear_clipboard
        )
        self.notify(
            f"Copied {label}; clipboard clears in "
            f"{self.clipboard_clear_seconds}s.",
            title="Clipboard",
        )
        return True

    def _clear_clipboard(self) -> None:
        """Clear the clipboard, but only if it still holds the copied value."""
        self._clip_timer = None
        value = self._clip_value
        self._clip_value = None
        if value is None:
            return
        try:
            if pyperclip.paste() == value:
                pyperclip.copy("")
        except pyperclip.PyperclipException:
            pass
        self.notify("Clipboard cleared.", title="Clipboard")

    def action_help(self) -> None:
        """Open the keyboard-shortcuts help overlay."""
        if isinstance(self.screen, HelpScreen):
            return
        self.push_screen(HelpScreen())

    def show_error(self, message: str, *, title: str = "Error") -> None:
        """Surface a non-fatal error in a modal instead of crashing."""
        self.push_screen(ErrorModal(message, title=title))

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
            self.show_error(str(exc), title="Login failed")
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
            self.show_error(str(exc), title="Logout failed")
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
