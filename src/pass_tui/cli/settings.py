"""pass-cli persistent settings on top of ``pass-cli settings get/set``."""

from __future__ import annotations

from pass_tui.cli.runner import PassCliError, run_pass_cli_checked

#: Setting key for the vault used when none is specified.
SETTING_DEFAULT_VAULT = "default-vault"
#: Setting key for the default output format.
SETTING_DEFAULT_FORMAT = "default-format"
#: Output formats pass-cli commands accept.
OUTPUT_FORMATS = ("json", "yaml", "text")


async def get_setting(key: str) -> str:
    """Return a pass-cli setting value, or ``""`` if it is unset.

    A failure (e.g. the key has never been set) is treated as unset rather than
    raising, so it can be shown as "no default".
    """
    try:
        text = await run_pass_cli_checked("settings", "get", key)
    except PassCliError:
        return ""
    return text.strip()


async def set_setting(key: str, value: str) -> None:
    """Set a pass-cli setting via ``pass-cli settings set``.

    Raises:
        PassCliError: if the command fails.
    """
    await run_pass_cli_checked("settings", "set", key, value)
