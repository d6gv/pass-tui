"""Rendering tests for the vault list screen, driven by Pilot with mock data.

``fetch_session`` and ``list_vaults`` are stubbed, so no real process runs.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from textual.pilot import Pilot
from textual.widgets import DataTable

import pass_tui.app as app_module
import pass_tui.screens.vault_list as vault_list_module
from pass_tui.app import PassTuiApp
from pass_tui.cli import SessionInfo, Vault
from pass_tui.cli.runner import PassCliError
from pass_tui.screens import ErrorModal, VaultListScreen

SESSION = SessionInfo(email="me@proton.me")


def _make_app(
    monkeypatch: pytest.MonkeyPatch,
    *,
    vaults: list[Vault] | None = None,
    error: Exception | None = None,
) -> tuple[PassTuiApp, AsyncMock]:
    monkeypatch.setattr(
        app_module, "fetch_session", AsyncMock(return_value=SESSION)
    )
    if error is not None:
        list_mock = AsyncMock(side_effect=error)
    else:
        list_mock = AsyncMock(return_value=vaults or [])
    monkeypatch.setattr(vault_list_module, "list_vaults", list_mock)
    return PassTuiApp(), list_mock


async def _settle(pilot: Pilot[None]) -> None:
    for _ in range(4):
        await pilot.pause()


async def test_renders_vault_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    vaults = [
        Vault(name="Personal", item_count=12, shared=False),
        Vault(name="Team", item_count=5, member_count=3),
    ]
    app, _ = _make_app(monkeypatch, vaults=vaults)
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert isinstance(app.screen, VaultListScreen)
        table = app.screen.query_one(DataTable)
        assert table.row_count == 2
        assert table.get_row_at(0) == ["Personal", "12", ""]
        assert table.get_row_at(1) == ["Team", "5", "yes"]


async def test_unknown_item_count_renders_question_mark(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, _ = _make_app(monkeypatch, vaults=[Vault(name="Legacy")])
    async with app.run_test() as pilot:
        await _settle(pilot)
        table = app.screen.query_one(DataTable)
        assert table.get_row_at(0) == ["Legacy", "?", ""]


async def test_keyboard_navigation_moves_cursor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vaults = [
        Vault(name="A", item_count=1),
        Vault(name="B", item_count=2),
    ]
    app, _ = _make_app(monkeypatch, vaults=vaults)
    async with app.run_test() as pilot:
        await _settle(pilot)
        table = app.screen.query_one(DataTable)
        assert table.cursor_row == 0
        await pilot.press("down")
        await pilot.pause()
        assert table.cursor_row == 1


async def test_refresh_reloads_vaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, list_mock = _make_app(monkeypatch, vaults=[Vault(name="A")])
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert list_mock.await_count == 1
        await pilot.press("r")
        await _settle(pilot)
        assert list_mock.await_count == 2


async def test_cli_error_shows_error_modal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, _ = _make_app(monkeypatch, error=PassCliError("network unreachable"))
    async with app.run_test() as pilot:
        await _settle(pilot)
        assert isinstance(app.screen, ErrorModal)
        assert app.is_running  # non-fatal: the app keeps running
