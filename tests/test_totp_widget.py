"""Tests for the TotpView widget: display and period-driven refresh."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from textual.app import App, ComposeResult

import pass_tui.widgets.totp as totp_widget
from pass_tui.cli.runner import PassCliError
from pass_tui.widgets import TotpView


class _Clock:
    """A controllable stand-in for the ``time`` module."""

    def __init__(self, value: float) -> None:
        self.value = value

    def time(self) -> float:
        return self.value


class _Host(App[None]):
    def __init__(self, view: TotpView) -> None:
        super().__init__()
        self._view = view

    def compose(self) -> ComposeResult:
        yield self._view


async def test_view_shows_code_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        totp_widget, "get_totp_codes", AsyncMock(return_value={"totp": "123456"})
    )
    view = TotpView(item_id="i1", share_id="s1")
    app = _Host(view)
    async with app.run_test() as pilot:
        for _ in range(3):
            await pilot.pause()
        assert view.display is True
        assert view.primary_code() == "123456"


async def test_view_hides_without_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        totp_widget,
        "get_totp_codes",
        AsyncMock(side_effect=PassCliError("no totp")),
    )
    view = TotpView(item_id="i1", share_id="s1")
    app = _Host(view)
    async with app.run_test() as pilot:
        for _ in range(3):
            await pilot.pause()
        assert view.display is False
        assert view.primary_code() is None


async def test_code_refetched_on_period_rollover(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clock = _Clock(0.0)
    monkeypatch.setattr(totp_widget, "time", clock)
    fetch = AsyncMock(return_value={"totp": "111111"})
    monkeypatch.setattr(totp_widget, "get_totp_codes", fetch)

    view = TotpView(item_id="i1", share_id="s1")
    app = _Host(view)
    async with app.run_test() as pilot:
        for _ in range(3):
            await pilot.pause()
        # Initial fetch on mount.
        assert fetch.await_count == 1

        # Same period: a tick must not re-fetch.
        clock.value = 15.0
        view._tick()
        for _ in range(2):
            await pilot.pause()
        assert fetch.await_count == 1

        # New period: the tick re-fetches exactly once.
        clock.value = 30.0
        view._tick()
        for _ in range(3):
            await pilot.pause()
        assert fetch.await_count == 2
