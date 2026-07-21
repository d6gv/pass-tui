"""Tests for CLI argument building and the create/update/delete wrappers.

``run_pass_cli_checked`` is mocked, so nothing spawns the real binary.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pass_tui.cli import item as item_module
from pass_tui.cli.item import (
    build_create_card_args,
    build_create_login_args,
    build_create_note_args,
    build_update_args,
    create_login_item,
    delete_item,
    update_item_fields,
)


def test_build_create_login_args_full() -> None:
    assert build_create_login_args(
        title="GitHub",
        username="me",
        email="me@x.com",
        password="pw",
        url="https://x",
        note="hi",
        share_id="s1",
    ) == [
        "item", "create", "login",
        "--title", "GitHub",
        "--username", "me",
        "--email", "me@x.com",
        "--password", "pw",
        "--url", "https://x",
        "--note", "hi",
        "--share-id", "s1",
    ]  # fmt: skip


def test_build_create_login_args_omits_empty_and_uses_vault_name() -> None:
    assert build_create_login_args(title="T", vault_name="Personal") == [
        "item", "create", "login",
        "--title", "T",
        "--vault-name", "Personal",
    ]  # fmt: skip


def test_build_update_args_repeats_field_flag() -> None:
    assert build_update_args(
        fields={"title": "T", "password": "p"},
        item_id="i1",
        share_id="s1",
    ) == [
        "item", "update",
        "--item-id", "i1",
        "--share-id", "s1",
        "--field", "title=T",
        "--field", "password=p",
    ]  # fmt: skip


def test_build_create_note_and_card_args() -> None:
    assert build_create_note_args(title="N", note="body", share_id="s1") == [
        "item", "create", "note", "--title", "N", "--note", "body",
        "--share-id", "s1",
    ]  # fmt: skip
    assert build_create_card_args(
        title="Visa", number="4111", expiry="2029-12", cvv="123", vault_name="P"
    ) == [
        "item", "create", "card",
        "--title", "Visa",
        "--number", "4111",
        "--expiry", "2029-12",
        "--cvv", "123",
        "--vault-name", "P",
    ]  # fmt: skip


async def test_create_login_item_invokes_checked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked = AsyncMock(return_value="")
    monkeypatch.setattr(item_module, "run_pass_cli_checked", checked)

    await create_login_item(title="T", username="u", share_id="s1")

    assert checked.await_args is not None
    assert checked.await_args.args == (
        "item", "create", "login",
        "--title", "T",
        "--username", "u",
        "--share-id", "s1",
    )  # fmt: skip


async def test_update_with_no_fields_does_nothing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked = AsyncMock(return_value="")
    monkeypatch.setattr(item_module, "run_pass_cli_checked", checked)

    await update_item_fields(fields={}, item_id="i1", share_id="s1")

    checked.assert_not_awaited()


async def test_delete_item_args(monkeypatch: pytest.MonkeyPatch) -> None:
    checked = AsyncMock(return_value="")
    monkeypatch.setattr(item_module, "run_pass_cli_checked", checked)

    await delete_item(share_id="s1", item_id="i1")

    assert checked.await_args is not None
    assert checked.await_args.args == (
        "item", "delete", "--share-id", "s1", "--item-id", "i1",
    )  # fmt: skip
