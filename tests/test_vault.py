"""Unit tests for the Vault model and vault listing.

``run_pass_cli`` is mocked, so nothing spawns the real binary.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pass_tui.cli import vault as vault_module
from pass_tui.cli.runner import PassCliError
from pass_tui.cli.vault import Vault, list_vaults


def test_vault_parses_alias_spellings() -> None:
    vault = Vault.model_validate(
        {"shareId": "s1", "name": "Personal", "itemCount": 4}
    )

    assert vault.share_id == "s1"
    assert vault.name == "Personal"
    assert vault.item_count == 4
    assert vault.display_name == "Personal"
    assert vault.item_count_display == "4"


def test_display_name_falls_back() -> None:
    assert Vault(share_id="s1").display_name == "s1"
    assert Vault().display_name == "(unnamed vault)"


def test_item_count_display_unknown() -> None:
    assert Vault().item_count_display == "?"


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"shared": True}, True),
        ({"shared": False}, False),
        ({"shared": False, "member_count": 5}, False),  # explicit flag wins
        ({"member_count": 3}, True),
        ({"member_count": 1}, False),
        ({"role": "Viewer"}, True),
        ({"role": "Owner"}, False),
        ({}, False),
    ],
)
def test_is_shared(kwargs: dict[str, object], expected: bool) -> None:
    assert Vault.model_validate(kwargs).is_shared is expected


async def test_list_vaults_parses_array(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vault_module,
        "run_pass_cli",
        AsyncMock(return_value=[{"name": "A"}, {"name": "B"}]),
    )

    vaults = await list_vaults()

    assert [vault.name for vault in vaults] == ["A", "B"]


async def test_list_vaults_rejects_non_array(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        vault_module, "run_pass_cli", AsyncMock(return_value={"name": "A"})
    )

    with pytest.raises(PassCliError):
        await list_vaults()
