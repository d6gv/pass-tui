"""The layer that invokes pass-cli and parses its JSON output."""

from pass_tui.cli.auth import SessionInfo, fetch_session, logout
from pass_tui.cli.runner import (
    PASS_CLI_BINARY,
    PassCliError,
    run_pass_cli,
    run_pass_cli_checked,
    run_pass_cli_interactive,
)
from pass_tui.cli.vault import Vault, list_vaults

__all__ = [
    "PASS_CLI_BINARY",
    "PassCliError",
    "SessionInfo",
    "Vault",
    "fetch_session",
    "list_vaults",
    "logout",
    "run_pass_cli",
    "run_pass_cli_checked",
    "run_pass_cli_interactive",
]
