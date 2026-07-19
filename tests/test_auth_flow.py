"""Screen-transition tests for the login/logout flow, driven by Pilot.

Every pass-cli call is stubbed, so no real process is launched: session
detection, the interactive login, and logout are all replaced with fakes.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from textual.pilot import Pilot
from textual.widgets import Static

import pass_tui.app as app_module
from pass_tui.app import PassTuiApp
from pass_tui.cli import SessionInfo
from pass_tui.cli.runner import PassCliError
from pass_tui.screens import HomeScreen, LoginScreen

SESSION = SessionInfo(email="me@proton.me", username="me")


async def _settle(pilot: Pilot[None]) -> None:
    """Let workers run and the resulting screen switch be processed."""
    for _ in range(3):
        await pilot.pause()


async def test_startup_without_session_shows_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(app_module, "fetch_session", AsyncMock(return_value=None))

    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert isinstance(app.screen, LoginScreen)


async def test_startup_with_session_shows_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_module, "fetch_session", AsyncMock(return_value=SESSION)
    )

    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert isinstance(app.screen, HomeScreen)
        assert app.sub_title == "me@proton.me"
        details = str(app.screen.query_one("#home-details", Static).render())
        assert "me@proton.me" in details


async def test_startup_cli_error_shows_login_with_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_module,
        "fetch_session",
        AsyncMock(side_effect=PassCliError("pass-cli exploded")),
    )

    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert isinstance(app.screen, LoginScreen)
        error = str(app.screen.query_one("#login-error", Static).render())
        assert "pass-cli exploded" in error


async def test_login_success_transitions_to_home(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No session at startup, an active session after login completes.
    monkeypatch.setattr(
        app_module,
        "fetch_session",
        AsyncMock(side_effect=[None, SESSION]),
    )
    # Stub the suspend + subprocess with a successful exit code.
    monkeypatch.setattr(PassTuiApp, "_suspend_and_login", lambda self: 0)

    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert isinstance(app.screen, LoginScreen)
        await pilot.press("l")
        await _settle(pilot)
        assert isinstance(app.screen, HomeScreen)


async def test_login_failure_stays_on_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(app_module, "fetch_session", AsyncMock(return_value=None))
    # Non-zero exit: login was cancelled or failed.
    monkeypatch.setattr(PassTuiApp, "_suspend_and_login", lambda self: 1)

    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _settle(pilot)
        await pilot.press("l")
        await _settle(pilot)
        assert isinstance(app.screen, LoginScreen)


async def test_logout_transitions_back_to_login(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        app_module, "fetch_session", AsyncMock(return_value=SESSION)
    )
    logout_mock = AsyncMock(return_value=None)
    monkeypatch.setattr(app_module, "logout", logout_mock)

    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert isinstance(app.screen, HomeScreen)
        await pilot.press("ctrl+l")
        await _settle(pilot)
        assert isinstance(app.screen, LoginScreen)
        logout_mock.assert_awaited_once()
        assert app.sub_title == ""
