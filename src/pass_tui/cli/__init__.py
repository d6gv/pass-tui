"""The layer that invokes pass-cli and parses its JSON output."""

from pass_tui.cli.runner import PASS_CLI_BINARY, PassCliError, run_pass_cli

__all__ = ["PASS_CLI_BINARY", "PassCliError", "run_pass_cli"]
