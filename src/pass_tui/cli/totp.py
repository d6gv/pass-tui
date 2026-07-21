"""TOTP codes on top of ``pass-cli item totp``.

The command returns a ``{field_name: code}`` mapping with no timing metadata,
so the UI derives the countdown from the wall clock: TOTP codes use a fixed
30-second period, and a code changes when the period index rolls over.
"""

from __future__ import annotations

from typing import Any

from pass_tui.cli.runner import PassCliError, run_pass_cli

#: The standard TOTP period, in seconds.
TOTP_PERIOD = 30


def seconds_remaining(now: float, period: int = TOTP_PERIOD) -> float:
    """Seconds left in the current TOTP period at time ``now``."""
    return period - (now % period)


def period_index(now: float, period: int = TOTP_PERIOD) -> int:
    """The index of the TOTP period containing ``now``.

    The value changes exactly when a new code becomes valid, which is what the
    UI watches to decide when to re-fetch.
    """
    return int(now // period)


async def get_totp_codes(
    *,
    item_id: str | None = None,
    item_title: str | None = None,
    vault_name: str | None = None,
    share_id: str | None = None,
) -> dict[str, str]:
    """Return the current TOTP codes for an item as a ``{name: code}`` map.

    Raises:
        PassCliError: if the command fails (e.g. the item has no TOTP) or
            returns something other than a JSON object.
    """
    args = ["item", "totp"]
    if item_id:
        args += ["--item-id", item_id]
    elif item_title:
        args += ["--item-title", item_title]
    if share_id:
        args += ["--share-id", share_id]
    elif vault_name:
        args += ["--vault-name", vault_name]
    args += ["--output", "json"]

    data = await run_pass_cli(*args)
    if not isinstance(data, dict):
        raise PassCliError("`pass-cli item totp` did not return a JSON object.")
    return {
        str(name): str(code)
        for name, code in data.items()
        if isinstance(code, (str, int)) and _coerce_code(code)
    }


def _coerce_code(code: Any) -> str:
    return str(code).strip()
