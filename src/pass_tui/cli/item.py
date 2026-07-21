"""Item listing and detail on top of ``pass-cli item list`` / ``item get``.

The exact JSON key names emitted by pass-cli are not documented, so both the
:class:`Item` summary model and the :func:`parse_item_detail` normalizer are
deliberately tolerant: they accept several alias spellings and degrade
gracefully on unexpected shapes instead of failing.

The detail JSON is known (from third-party usage) to be deeply nested along
``content.content.<Type>.sections[].section_fields[]`` with per-field content
tagged as ``Text`` (plain) or ``Hidden`` (secret). :func:`parse_item_detail`
flattens that — and simpler login-style shapes — into a list of
:class:`ItemField`. It is best-effort against an unverified schema; adjust the
helpers here once the real output is confirmed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from pass_tui.cli.runner import PassCliError, run_pass_cli, run_pass_cli_checked

#: Icon shown per normalized item type. Falls back to ``_DEFAULT_ICON``.
_TYPE_ICONS = {
    "login": "🔑",
    "note": "📝",
    "card": "💳",
    "creditcard": "💳",
    "alias": "📧",
    "sshkey": "🔐",
    "identity": "🪪",
    "custom": "🧩",
}
_DEFAULT_ICON = "•"

#: Field names that imply a secret value even when not tagged as hidden.
_SENSITIVE_NAME = re.compile(
    r"password|secret|token|cvv|pin|passphrase|private", re.IGNORECASE
)


def _normalize_type(item_type: str | None) -> str:
    """Reduce a type string to lowercase alphanumerics for lookup."""
    if not item_type:
        return ""
    return "".join(ch for ch in item_type.lower() if ch.isalnum())


class Item(BaseModel):
    """A single item summary, from ``pass-cli item list --output json``."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    item_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("item_id", "itemId", "id", "ID"),
    )
    share_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("share_id", "shareId"),
    )
    title: str | None = Field(
        default=None,
        validation_alias=AliasChoices("title", "name"),
    )
    item_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("item_type", "itemType", "type"),
    )

    @property
    def display_title(self) -> str:
        """A non-empty label for the item."""
        return self.title or "(untitled)"

    @property
    def type_label(self) -> str:
        """The normalized type name, or ``"unknown"``."""
        return _normalize_type(self.item_type) or "unknown"

    @property
    def type_icon(self) -> str:
        """An icon representing the item type."""
        return _TYPE_ICONS.get(_normalize_type(self.item_type), _DEFAULT_ICON)


@dataclass(frozen=True)
class ItemField:
    """One presentable field of an item's detail."""

    label: str
    value: str
    sensitive: bool = False


@dataclass
class ItemDetail:
    """The normalized, presentable detail of a single item."""

    title: str
    item_type: str
    fields: list[ItemField] = field(default_factory=list)
    note: str | None = None


async def list_items(
    *,
    vault_name: str | None = None,
    share_id: str | None = None,
) -> list[Item]:
    """Return the items in a vault via ``pass-cli item list``.

    A ``share_id`` is preferred when available because it identifies the vault
    unambiguously; otherwise the vault name is used.

    Raises:
        PassCliError: if the command fails or returns something other than a
            JSON array.
    """
    args = ["item", "list"]
    if share_id:
        args += ["--share-id", share_id]
    elif vault_name:
        args += ["--vault-name", vault_name]
    args += ["--output", "json"]

    data = await run_pass_cli(*args)
    if not isinstance(data, list):
        raise PassCliError("`pass-cli item list` did not return a JSON array.")
    return [Item.model_validate(entry) for entry in data]


async def get_item(
    *,
    item_id: str | None = None,
    item_title: str | None = None,
    vault_name: str | None = None,
    share_id: str | None = None,
) -> ItemDetail:
    """Return the detail of a single item via ``pass-cli item get``.

    ``--show-secrets`` is passed so that hidden values are present in the JSON;
    the UI is responsible for masking them until the user reveals them.

    Raises:
        PassCliError: if the command fails or returns something other than a
            JSON object.
    """
    args = ["item", "get"]
    if item_id:
        args += ["--item-id", item_id]
    elif item_title:
        args += ["--item-title", item_title]
    if share_id:
        args += ["--share-id", share_id]
    elif vault_name:
        args += ["--vault-name", vault_name]
    args += ["--show-secrets", "--output", "json"]

    data = await run_pass_cli(*args)
    if not isinstance(data, dict):
        raise PassCliError("`pass-cli item get` did not return a JSON object.")
    return parse_item_detail(data)


def _vault_args(vault_name: str | None, share_id: str | None) -> list[str]:
    """Vault identification args, preferring the unambiguous share id."""
    if share_id:
        return ["--share-id", share_id]
    if vault_name:
        return ["--vault-name", vault_name]
    return []


def build_create_login_args(
    *,
    title: str,
    username: str = "",
    email: str = "",
    password: str = "",
    url: str = "",
    note: str = "",
    vault_name: str | None = None,
    share_id: str | None = None,
) -> list[str]:
    """Build the argv for ``pass-cli item create login``.

    Only non-empty optional fields are included. Note: pass-cli's create uses
    named flags (``--username`` etc.), not ``--field``.
    """
    args = ["item", "create", "login", "--title", title]
    for flag, value in (
        ("--username", username),
        ("--email", email),
        ("--password", password),
        ("--url", url),
        ("--note", note),
    ):
        if value:
            args += [flag, value]
    args += _vault_args(vault_name, share_id)
    return args


async def create_login_item(
    *,
    title: str,
    username: str = "",
    email: str = "",
    password: str = "",
    url: str = "",
    note: str = "",
    vault_name: str | None = None,
    share_id: str | None = None,
) -> None:
    """Create a login item via ``pass-cli item create login``.

    Raises:
        PassCliError: if the command fails.
    """
    args = build_create_login_args(
        title=title,
        username=username,
        email=email,
        password=password,
        url=url,
        note=note,
        vault_name=vault_name,
        share_id=share_id,
    )
    await run_pass_cli_checked(*args)


def build_update_args(
    *,
    fields: dict[str, str],
    item_id: str | None = None,
    item_title: str | None = None,
    vault_name: str | None = None,
    share_id: str | None = None,
) -> list[str]:
    """Build the argv for ``pass-cli item update``.

    Each entry in ``fields`` becomes a repeated ``--field name=value``.
    """
    args = ["item", "update"]
    if item_id:
        args += ["--item-id", item_id]
    elif item_title:
        args += ["--item-title", item_title]
    args += _vault_args(vault_name, share_id)
    for name, value in fields.items():
        args += ["--field", f"{name}={value}"]
    return args


async def update_item_fields(
    *,
    fields: dict[str, str],
    item_id: str | None = None,
    item_title: str | None = None,
    vault_name: str | None = None,
    share_id: str | None = None,
) -> None:
    """Update fields of an item via ``pass-cli item update``.

    Does nothing when ``fields`` is empty.

    Raises:
        PassCliError: if the command fails.
    """
    if not fields:
        return
    args = build_update_args(
        fields=fields,
        item_id=item_id,
        item_title=item_title,
        vault_name=vault_name,
        share_id=share_id,
    )
    await run_pass_cli_checked(*args)


async def delete_item(*, share_id: str, item_id: str) -> None:
    """Delete an item via ``pass-cli item delete``.

    Both the share id and the item id are required by pass-cli, and the
    deletion is permanent.

    Raises:
        PassCliError: if the command fails.
    """
    await run_pass_cli_checked(
        "item", "delete", "--share-id", share_id, "--item-id", item_id
    )


def _looks_sensitive(name: str) -> bool:
    return bool(_SENSITIVE_NAME.search(name))


def _coerce_str(value: Any) -> str:
    """Render a JSON value as a single display string."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(_coerce_str(entry) for entry in value if entry)
    if isinstance(value, dict):
        return ", ".join(_coerce_str(entry) for entry in value.values() if entry)
    return str(value)


def _first_str(node: dict[str, Any], *keys: str) -> str:
    """Return the first key present in ``node`` as a non-empty string."""
    for key in keys:
        if key in node:
            text = _coerce_str(node[key])
            if text:
                return text
    return ""


def _extract_field_content(content: Any) -> tuple[str, bool]:
    """Return ``(value, sensitive)`` from a possibly type-tagged content."""
    if isinstance(content, dict):
        for tag, sensitive in (("Hidden", True), ("Totp", True), ("Text", False)):
            if tag in content:
                return _coerce_str(content[tag]), sensitive
        if len(content) == 1:
            (key, value), = content.items()
            return _coerce_str(value), _looks_sensitive(str(key))
    return _coerce_str(content), False


def _unwrap_typed(typed: Any) -> tuple[Any, str | None]:
    """Unwrap a single-key ``{"Login": {...}}``-style envelope."""
    if isinstance(typed, dict) and len(typed) == 1:
        (key, value), = typed.items()
        if isinstance(value, dict) and key[:1].isupper():
            return value, key
    return typed, None


def _collect_known_fields(body: dict[str, Any], fields: list[ItemField]) -> None:
    """Pull well-known login-style fields out of ``body``."""
    known: list[tuple[tuple[str, ...], str, bool]] = [
        (("username", "user"), "Username", False),
        (("email",), "Email", False),
        (("password", "pass"), "Password", True),
        (("totp", "totpUri", "totp_uri"), "TOTP", True),
    ]
    for keys, label, sensitive in known:
        value = _first_str(body, *keys)
        if value:
            fields.append(ItemField(label, value, sensitive))

    urls = body.get("urls") or body.get("url")
    url_text = _coerce_str(urls)
    if url_text:
        fields.append(ItemField("URLs", url_text, False))


def _collect_sections(body: dict[str, Any], fields: list[ItemField]) -> None:
    """Pull custom section fields out of ``body``."""
    sections = body.get("sections")
    if not isinstance(sections, list):
        return
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_fields = section.get("section_fields") or section.get("fields")
        if not isinstance(section_fields, list):
            continue
        for entry in section_fields:
            if not isinstance(entry, dict):
                continue
            name = _first_str(entry, "name", "label") or "Field"
            content = entry.get("content", entry.get("value"))
            value, sensitive = _extract_field_content(content)
            fields.append(
                ItemField(name, value, sensitive or _looks_sensitive(name))
            )


def parse_item_detail(raw: dict[str, Any]) -> ItemDetail:
    """Normalize the raw ``item get`` JSON into an :class:`ItemDetail`.

    Best-effort against an unverified, deeply nested schema; unknown shapes
    degrade to empty fields rather than raising.
    """
    node = raw["item"] if isinstance(raw.get("item"), dict) else raw

    title = _first_str(node, "title", "name") or "(untitled)"
    item_type = _first_str(node, "item_type", "itemType", "type")
    note = _first_str(node, "note")
    fields: list[ItemField] = []

    content = node.get("content")
    typed = content
    if isinstance(content, dict) and isinstance(content.get("content"), dict):
        typed = content["content"]

    body, type_from_body = _unwrap_typed(typed)
    if type_from_body and not item_type:
        item_type = type_from_body

    if isinstance(body, dict):
        if not note:
            note = _first_str(body, "note", "content")
        _collect_known_fields(body, fields)
        _collect_sections(body, fields)

    return ItemDetail(
        title=title,
        item_type=_normalize_type(item_type) or "unknown",
        fields=fields,
        note=note or None,
    )
