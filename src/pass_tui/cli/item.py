"""Item listing on top of ``pass-cli item list``.

The exact JSON key names emitted by ``pass-cli item list --output json`` are
not documented, so :class:`Item` is deliberately tolerant: it accepts a few
alias spellings and keeps any unknown keys instead of failing.
"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from pass_tui.cli.runner import PassCliError, run_pass_cli

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
