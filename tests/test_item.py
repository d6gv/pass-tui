"""Unit tests for the Item model, item detail parsing, and CLI arg building.

``run_pass_cli`` is mocked, so nothing spawns the real binary.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest

from pass_tui.cli import item as item_module
from pass_tui.cli.item import (
    Item,
    ItemDetail,
    ItemField,
    get_item,
    list_items,
    parse_item_detail,
)


def _field(detail: ItemDetail, label: str) -> ItemField | None:
    return next((f for f in detail.fields if f.label == label), None)


def test_item_type_icon_and_label() -> None:
    assert Item(item_type="login").type_icon == "🔑"
    assert Item(item_type="creditCard").type_label == "creditcard"
    assert Item(item_type="creditCard").type_icon == "💳"
    assert Item(item_type="wifi").type_icon == "•"  # unknown type
    assert Item().type_label == "unknown"


def test_display_title_fallback() -> None:
    assert Item(title="GitHub").display_title == "GitHub"
    assert Item().display_title == "(untitled)"


def test_parse_login_flattens_known_fields() -> None:
    raw = {
        "title": "GitHub",
        "type": "login",
        "content": {
            "content": {
                "Login": {
                    "username": "me@x.com",
                    "password": "s3cr3t",
                    "urls": ["https://github.com"],
                    "totp": "otpauth://x",
                }
            }
        },
    }

    detail = parse_item_detail(raw)

    assert detail.title == "GitHub"
    assert detail.item_type == "login"
    username = _field(detail, "Username")
    password = _field(detail, "Password")
    totp = _field(detail, "TOTP")
    assert username is not None and username.value == "me@x.com"
    assert username.sensitive is False
    assert password is not None and password.value == "s3cr3t"
    assert password.sensitive is True
    assert totp is not None and totp.sensitive is True
    assert _field(detail, "URLs") is not None


def test_parse_custom_sections_marks_hidden_sensitive() -> None:
    raw = {
        "title": "Server",
        "type": "custom",
        "note": "prod box",
        "content": {
            "content": {
                "Custom": {
                    "sections": [
                        {
                            "section_fields": [
                                {"name": "Host", "content": {"Text": "1.2.3.4"}},
                                {"name": "API Key", "content": {"Hidden": "abc"}},
                            ]
                        }
                    ]
                }
            }
        },
    }

    detail = parse_item_detail(raw)

    assert detail.note == "prod box"
    host = _field(detail, "Host")
    api_key = _field(detail, "API Key")
    assert host is not None and host.sensitive is False
    assert api_key is not None and api_key.value == "abc"
    assert api_key.sensitive is True


def test_parse_flags_sensitive_by_field_name() -> None:
    raw = {
        "title": "T",
        "type": "custom",
        "content": {
            "content": {
                "Custom": {
                    "sections": [
                        {
                            "section_fields": [
                                # Plain "Text" content, but the name implies a secret.
                                {
                                    "name": "Recovery Token",
                                    "content": {"Text": "xyz"},
                                }
                            ]
                        }
                    ]
                }
            }
        },
    }

    detail = parse_item_detail(raw)

    token = _field(detail, "Recovery Token")
    assert token is not None and token.sensitive is True


def test_parse_unwraps_item_key() -> None:
    raw = {"item": {"title": "Wrapped", "type": "note", "content": {}}}

    detail = parse_item_detail(raw)

    assert detail.title == "Wrapped"
    assert detail.item_type == "note"


def test_parse_degrades_on_unknown_shape() -> None:
    detail = parse_item_detail({"weird": True})

    assert detail.title == "(untitled)"
    assert detail.item_type == "unknown"
    assert detail.fields == []


async def test_list_items_prefers_share_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    run = AsyncMock(return_value=[])
    monkeypatch.setattr(item_module, "run_pass_cli", run)

    await list_items(vault_name="Personal", share_id="s1")

    assert run.await_args is not None
    assert run.await_args.args == (
        "item",
        "list",
        "--share-id",
        "s1",
        "--output",
        "json",
    )


async def test_get_item_requests_secrets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw: dict[str, Any] = {"title": "X", "type": "login", "content": {}}
    run = AsyncMock(return_value=raw)
    monkeypatch.setattr(item_module, "run_pass_cli", run)

    await get_item(item_id="i1", share_id="s1")

    assert run.await_args is not None
    assert run.await_args.args == (
        "item",
        "get",
        "--item-id",
        "i1",
        "--share-id",
        "s1",
        "--show-secrets",
        "--output",
        "json",
    )
