"""Session detection on top of ``pass-cli info``.

The exact JSON key names emitted by ``pass-cli info --output json`` are not
documented, so :class:`SessionInfo` is deliberately tolerant: it accepts a few
alias spellings and keeps any unknown keys instead of failing.
"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from pass_tui.cli.runner import PassCliError, run_pass_cli


class SessionInfo(BaseModel):
    """The active account, parsed from ``pass-cli info --output json``."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    email: str | None = None
    username: str | None = None
    user_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("user_id", "id", "userId", "ID"),
    )
    release_track: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "release_track", "releaseTrack", "release", "track"
        ),
    )

    @property
    def account_label(self) -> str:
        """A human-friendly label for the signed-in account."""
        return self.email or self.username or "unknown account"


async def fetch_session() -> SessionInfo | None:
    """Return the active session, or ``None`` if there is no active session.

    ``pass-cli info`` exiting non-zero is treated as "not logged in" and yields
    ``None``. Any other failure (missing binary, unparseable output) re-raises
    as :class:`PassCliError`, since it points at a real problem rather than a
    logged-out state.
    """
    try:
        data = await run_pass_cli("info", "--output", "json")
    except PassCliError as exc:
        if exc.returncode is not None and exc.returncode != 0:
            return None
        raise

    if not isinstance(data, dict):
        raise PassCliError(
            "`pass-cli info` returned a JSON array; expected an object."
        )
    return SessionInfo.model_validate(data)
