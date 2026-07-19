"""The layer that invokes pass-cli and parses its JSON output."""

from pass_tui.cli.auth import SessionInfo, fetch_session, logout
from pass_tui.cli.runner import (
    PASS_CLI_BINARY,
    PassCliError,
    run_pass_cli,
    run_pass_cli_checked,
    run_pass_cli_interactive,
)

__all__ = [
    "PASS_CLI_BINARY",
    "PassCliError",
    "SessionInfo",
    "fetch_session",
    "logout",
    "run_pass_cli",
    "run_pass_cli_checked",
    "run_pass_cli_interactive",
]
