"""Unit tests for TOTP timing helpers and code fetching."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pass_tui.cli import totp as totp_module
from pass_tui.cli.runner import PassCliError
from pass_tui.cli.totp import (
    get_totp_codes,
    period_index,
    seconds_remaining,
)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (0.0, 30.0),
        (5.0, 25.0),
        (29.0, 1.0),
        (30.0, 30.0),
        (59.0, 1.0),
    ],
)
def test_seconds_remaining(now: float, expected: float) -> None:
    assert seconds_remaining(now) == expected


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (0.0, 0),
        (29.9, 0),
        (30.0, 1),
        (61.0, 2),
    ],
)
def test_period_index(now: float, expected: int) -> None:
    assert period_index(now) == expected


def test_period_index_changes_exactly_at_boundary() -> None:
    # A code is valid within a period and changes when the index increments.
    assert period_index(29.999) == period_index(0.0)
    assert period_index(30.0) == period_index(0.0) + 1


async def test_get_totp_codes_builds_args_and_parses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = AsyncMock(return_value={"totp": "152470", "TOTP 1": "119533"})
    monkeypatch.setattr(totp_module, "run_pass_cli", run)

    codes = await get_totp_codes(item_id="i1", share_id="s1")

    assert codes == {"totp": "152470", "TOTP 1": "119533"}
    assert run.await_args is not None
    assert run.await_args.args == (
        "item", "totp",
        "--item-id", "i1",
        "--share-id", "s1",
        "--output", "json",
    )  # fmt: skip


async def test_get_totp_codes_drops_empty_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        totp_module,
        "run_pass_cli",
        AsyncMock(return_value={"totp": "123456", "empty": ""}),
    )

    assert await get_totp_codes(item_title="X", vault_name="V") == {
        "totp": "123456"
    }


async def test_get_totp_codes_rejects_non_object(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        totp_module, "run_pass_cli", AsyncMock(return_value=["nope"])
    )

    with pytest.raises(PassCliError):
        await get_totp_codes(item_id="i1", share_id="s1")
