"""Unit tests for session detection and logout in the auth layer.

``run_pass_cli`` is mocked, so nothing spawns the real binary or depends on a
Proton account.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pass_tui.cli import auth
from pass_tui.cli.auth import SessionInfo, fetch_session, logout
from pass_tui.cli.runner import PassCliError


async def test_fetch_session_parses_account(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auth,
        "run_pass_cli",
        AsyncMock(return_value={"email": "me@proton.me", "id": "abc"}),
    )

    session = await fetch_session()

    assert isinstance(session, SessionInfo)
    assert session.email == "me@proton.me"
    assert session.user_id == "abc"
    assert session.account_label == "me@proton.me"


async def test_fetch_session_none_when_not_logged_in(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auth,
        "run_pass_cli",
        AsyncMock(side_effect=PassCliError("not logged in", returncode=1)),
    )

    assert await fetch_session() is None


async def test_fetch_session_reraises_missing_binary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # returncode=None means the process never started (e.g. binary missing).
    monkeypatch.setattr(
        auth,
        "run_pass_cli",
        AsyncMock(side_effect=PassCliError("not found", returncode=None)),
    )

    with pytest.raises(PassCliError):
        await fetch_session()


async def test_fetch_session_rejects_array(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(auth, "run_pass_cli", AsyncMock(return_value=[]))

    with pytest.raises(PassCliError):
        await fetch_session()


async def test_account_label_falls_back_to_username() -> None:
    assert SessionInfo(username="me").account_label == "me"
    assert SessionInfo().account_label == "unknown account"


async def test_logout_invokes_pass_cli_logout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked = AsyncMock(return_value="")
    monkeypatch.setattr(auth, "run_pass_cli_checked", checked)

    await logout()

    checked.assert_awaited_once_with("logout")
