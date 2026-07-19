"""Main Textual application for pass-tui."""

from __future__ import annotations

from textual import work
from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from pass_tui.cli import PassCliError, fetch_session
from pass_tui.screens import HomeScreen, LoginScreen


class PassTuiApp(App[None]):
    """Terminal UI for Proton Pass, layered over the official pass-cli."""

    TITLE = "pass-tui"

    def compose(self) -> ComposeResult:
        yield Static("Checking for an active session…", id="loading")

    def on_mount(self) -> None:
        self.check_session()

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
            self._show_screen(HomeScreen(session))

    def _show_screen(self, screen: Screen[None]) -> None:
        """Route to ``screen``, replacing any current login/home screen.

        The first navigation happens over Textual's default screen, which
        ``switch_screen`` cannot replace, so it is pushed; later transitions
        swap the login/home screen in place.
        """
        if isinstance(self.screen, (LoginScreen, HomeScreen)):
            self.switch_screen(screen)
        else:
            self.push_screen(screen)


def main() -> None:
    """Entry point for the ``pass-tui`` console script."""
    PassTuiApp().run()


if __name__ == "__main__":
    main()
