"""The layer that invokes pass-cli and parses its JSON output."""

from pass_tui.cli.auth import SessionInfo, fetch_session, logout
from pass_tui.cli.item import (
    Item,
    ItemDetail,
    ItemField,
    build_create_login_args,
    create_login_item,
    get_item,
    list_items,
    parse_item_detail,
)
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
    "Item",
    "ItemDetail",
    "ItemField",
    "PassCliError",
    "SessionInfo",
    "Vault",
    "build_create_login_args",
    "create_login_item",
    "fetch_session",
    "get_item",
    "list_items",
    "list_vaults",
    "logout",
    "parse_item_detail",
    "run_pass_cli",
    "run_pass_cli_checked",
    "run_pass_cli_interactive",
]
