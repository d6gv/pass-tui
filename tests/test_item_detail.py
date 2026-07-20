"""Tests for item detail masking/reveal and the clipboard auto-clear timer.

``get_item`` and ``pyperclip`` are stubbed, so no process or real clipboard is
touched.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from textual.pilot import Pilot
from textual.widgets import DataTable

import pass_tui.app as app_module
import pass_tui.screens.item_detail as item_detail_module
from pass_tui.app import PassTuiApp
from pass_tui.cli import Item, ItemDetail, ItemField, Vault
from pass_tui.screens.item_detail import MASK, ItemDetailScreen

ITEM = Item(item_id="i1", title="GitHub", item_type="login")
VAULT = Vault(name="Personal", share_id="v1")


class FakeClipboard:
    """A stand-in for the pyperclip module."""

    class PyperclipException(Exception):
        pass

    def __init__(self) -> None:
        self.value = ""

    def copy(self, text: str) -> None:
        self.value = text

    def paste(self) -> str:
        return self.value


@pytest.fixture(autouse=True)
def _no_session(monkeypatch: pytest.MonkeyPatch) -> None:
    # Land on the login screen so startup never touches the real CLI; the
    # detail screen is pushed on top explicitly in each test.
    monkeypatch.setattr(
        app_module, "fetch_session", AsyncMock(return_value=None)
    )


@pytest.fixture
def clipboard(monkeypatch: pytest.MonkeyPatch) -> FakeClipboard:
    fake = FakeClipboard()
    monkeypatch.setattr(app_module, "pyperclip", fake)
    return fake


def _stub_detail(monkeypatch: pytest.MonkeyPatch, detail: ItemDetail) -> None:
    monkeypatch.setattr(
        item_detail_module, "get_item", AsyncMock(return_value=detail)
    )


async def _open_detail(pilot: Pilot[None]) -> None:
    await pilot.pause()
    await pilot.app.push_screen(ItemDetailScreen(ITEM, VAULT))
    for _ in range(3):
        await pilot.pause()


def _login_detail() -> ItemDetail:
    return ItemDetail(
        title="GitHub",
        item_type="login",
        fields=[
            ItemField("Username", "me@x.com", sensitive=False),
            ItemField("Password", "s3cr3t", sensitive=True),
        ],
    )


async def test_sensitive_masked_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_detail(monkeypatch, _login_detail())
    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _open_detail(pilot)
        table = app.screen.query_one(DataTable)
        assert table.get_row_at(0) == ["Username", "me@x.com"]
        assert table.get_row_at(1) == ["Password", MASK]


async def test_reveal_and_hide_toggle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _stub_detail(monkeypatch, _login_detail())
    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _open_detail(pilot)
        table = app.screen.query_one(DataTable)
        await pilot.press("v")
        await pilot.pause()
        assert table.get_row_at(1) == ["Password", "s3cr3t"]
        await pilot.press("v")
        await pilot.pause()
        assert table.get_row_at(1) == ["Password", MASK]


async def test_reveal_binding_hidden_without_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    detail = ItemDetail(
        title="Note",
        item_type="note",
        fields=[ItemField("Body", "hello", sensitive=False)],
    )
    _stub_detail(monkeypatch, detail)
    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _open_detail(pilot)
        actions = {
            ab.binding.action for ab in app.screen.active_bindings.values()
        }
        assert "toggle_reveal" not in actions


async def test_copy_sets_clipboard_and_shows_countdown(
    monkeypatch: pytest.MonkeyPatch,
    clipboard: FakeClipboard,
) -> None:
    _stub_detail(monkeypatch, _login_detail())
    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _open_detail(pilot)
        await pilot.press("down")  # select the Password row
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        assert clipboard.value == "s3cr3t"
        assert app.screen.query_one("#clip-countdown").display is True


async def test_copy_schedules_clear_that_wipes_clipboard(
    monkeypatch: pytest.MonkeyPatch,
    clipboard: FakeClipboard,
) -> None:
    _stub_detail(monkeypatch, _login_detail())
    app = PassTuiApp()
    async with app.run_test() as pilot:
        await _open_detail(pilot)
        await pilot.press("down")
        await pilot.pause()
        await pilot.press("c")
        await pilot.pause()
        # A clear timer is scheduled...
        assert app._clip_timer is not None
        # ...and when it fires it wipes the copied value.
        app._clear_clipboard()
        assert clipboard.value == ""


async def test_clear_leaves_foreign_clipboard_untouched(
    monkeypatch: pytest.MonkeyPatch,
    clipboard: FakeClipboard,
) -> None:
    app = PassTuiApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.copy_with_autoclear("s3cr3t", label="Password") is True
        # The user copies something else before the timer fires.
        clipboard.value = "unrelated"
        app._clear_clipboard()
        assert clipboard.value == "unrelated"
