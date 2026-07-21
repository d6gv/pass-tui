"""Tests for form validators and that invalid submits are blocked."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from textual.widgets import Input

import pass_tui.app as app_module
import pass_tui.screens.forms as forms_module
from pass_tui.app import PassTuiApp
from pass_tui.cli import Vault
from pass_tui.screens.forms import LoginFormScreen, optional_pattern, required


def test_required_validator() -> None:
    validator = required("needed")
    assert validator.validate("hello").is_valid is True
    assert validator.validate("   ").is_valid is False
    assert validator.validate("").is_valid is False


def test_optional_pattern_allows_empty_but_checks_format() -> None:
    validator = optional_pattern(r"https?://\S+", "bad url")
    assert validator.validate("").is_valid is True
    assert validator.validate("https://example.com").is_valid is True
    assert validator.validate("not a url").is_valid is False


async def test_login_form_blocks_invalid_submit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    create = AsyncMock(return_value=None)
    monkeypatch.setattr(forms_module, "create_login_item", create)
    monkeypatch.setattr(
        app_module, "fetch_session", AsyncMock(return_value=None)
    )

    app = PassTuiApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        await app.push_screen(LoginFormScreen(Vault(name="P", share_id="v1")))
        for _ in range(3):
            await pilot.pause()

        # Empty title: blocked.
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert create.await_count == 0

        # Title present but invalid URL: still blocked.
        app.screen.query_one("#f-title", Input).value = "GitHub"
        app.screen.query_one("#f-url", Input).value = "not-a-url"
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert create.await_count == 0

        # Valid: submits.
        app.screen.query_one("#f-url", Input).value = "https://github.com"
        await pilot.press("ctrl+s")
        for _ in range(3):
            await pilot.pause()
        assert create.await_count == 1
