"""Vault listing on top of ``pass-cli vault list``.

The exact JSON key names emitted by ``pass-cli vault list --output json`` are
not documented, so :class:`Vault` is deliberately tolerant: it accepts a few
alias spellings and keeps any unknown keys instead of failing.
"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from pass_tui.cli.runner import PassCliError, run_pass_cli


class Vault(BaseModel):
    """A single vault, parsed from ``pass-cli vault list --output json``."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    share_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("share_id", "shareId", "id", "ID"),
    )
    name: str | None = None
    description: str | None = None
    item_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "item_count", "itemCount", "items", "count", "item_number"
        ),
    )
    member_count: int | None = Field(
        default=None,
        validation_alias=AliasChoices("member_count", "memberCount", "members"),
    )
    shared: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("shared", "is_shared", "isShared"),
    )
    role: str | None = None

    @property
    def display_name(self) -> str:
        """A non-empty label for the vault."""
        return self.name or self.share_id or "(unnamed vault)"

    @property
    def item_count_display(self) -> str:
        """The item count as text, or ``"?"`` when unknown."""
        return str(self.item_count) if self.item_count is not None else "?"

    @property
    def is_shared(self) -> bool:
        """Best-effort guess at whether the vault is shared with others."""
        if self.shared is not None:
            return self.shared
        if self.member_count is not None:
            return self.member_count > 1
        if self.role is not None:
            return self.role.lower() != "owner"
        return False


async def list_vaults() -> list[Vault]:
    """Return the user's vaults via ``pass-cli vault list``.

    Raises:
        PassCliError: if the command fails or returns something other than a
            JSON array.
    """
    data = await run_pass_cli("vault", "list", "--output", "json")
    if not isinstance(data, list):
        raise PassCliError("`pass-cli vault list` did not return a JSON array.")
    return [Vault.model_validate(entry) for entry in data]
