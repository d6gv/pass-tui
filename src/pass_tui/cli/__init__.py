"""The layer that invokes pass-cli and parses its JSON output."""

from pass_tui.cli.auth import SessionInfo, fetch_session, logout
from pass_tui.cli.item import (
    Item,
    ItemDetail,
    ItemField,
    build_create_card_args,
    build_create_login_args,
    build_create_note_args,
    build_update_args,
    create_card_item,
    create_login_item,
    create_note_item,
    delete_item,
    get_item,
    list_items,
    parse_item_detail,
    update_item_fields,
)
from pass_tui.cli.runner import (
    PASS_CLI_BINARY,
    PassCliError,
    run_pass_cli,
    run_pass_cli_checked,
    run_pass_cli_interactive,
)
from pass_tui.cli.totp import (
    TOTP_PERIOD,
    get_totp_codes,
    period_index,
    seconds_remaining,
)
from pass_tui.cli.vault import Vault, list_vaults

__all__ = [
    "PASS_CLI_BINARY",
    "TOTP_PERIOD",
    "Item",
    "ItemDetail",
    "ItemField",
    "PassCliError",
    "SessionInfo",
    "Vault",
    "build_create_card_args",
    "build_create_login_args",
    "build_create_note_args",
    "build_update_args",
    "create_card_item",
    "create_login_item",
    "create_note_item",
    "delete_item",
    "fetch_session",
    "get_item",
    "get_totp_codes",
    "list_items",
    "list_vaults",
    "logout",
    "parse_item_detail",
    "period_index",
    "seconds_remaining",
    "update_item_fields",
    "run_pass_cli",
    "run_pass_cli_checked",
    "run_pass_cli_interactive",
]
