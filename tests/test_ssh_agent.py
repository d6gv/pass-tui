"""Tests for ssh-agent output parsing and command building."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from pass_tui.cli import ssh_agent as ssh_module
from pass_tui.cli.ssh_agent import (
    parse_ssh_load_summary,
    ssh_agent_debug,
    ssh_agent_load,
)


def test_parse_full_summary() -> None:
    text = (
        "Successfully loaded: 3\n"
        "Already loaded (skipped): 2\n"
        "Total keys: 5\n"
    )
    summary = parse_ssh_load_summary(text)

    assert (summary.loaded, summary.skipped, summary.total) == (3, 2, 5)
    assert summary.as_line() == "Keys: loaded 3, already present 2, total 5"


def test_parse_is_case_insensitive_and_order_independent() -> None:
    text = "TOTAL KEYS: 4\nsuccessfully loaded: 4\nalready loaded (skipped): 0"
    summary = parse_ssh_load_summary(text)

    assert (summary.loaded, summary.skipped, summary.total) == (4, 0, 4)


def test_parse_partial_summary() -> None:
    summary = parse_ssh_load_summary("Total keys: 7")

    assert summary.loaded is None
    assert summary.skipped is None
    assert summary.total == 7
    assert summary.as_line() == "Keys: total 7"


def test_parse_unrecognized_falls_back_to_raw() -> None:
    summary = parse_ssh_load_summary("  unexpected output  ")

    assert (summary.loaded, summary.skipped, summary.total) == (None, None, None)
    assert summary.as_line() == "unexpected output"


def test_parse_empty_output() -> None:
    assert parse_ssh_load_summary("").as_line() == "Done."


async def test_ssh_agent_load_builds_args_and_parses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked = AsyncMock(return_value="Successfully loaded: 1\nTotal keys: 1")
    monkeypatch.setattr(ssh_module, "run_pass_cli_checked", checked)

    summary = await ssh_agent_load(vault_name="Personal")

    assert summary.loaded == 1
    assert checked.await_args is not None
    assert checked.await_args.args == (
        "ssh-agent", "load", "--vault-name", "Personal",
    )  # fmt: skip


async def test_ssh_agent_load_prefers_share_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked = AsyncMock(return_value="")
    monkeypatch.setattr(ssh_module, "run_pass_cli_checked", checked)

    await ssh_agent_load(vault_name="Personal", share_id="s1")

    assert checked.await_args is not None
    assert checked.await_args.args == ("ssh-agent", "load", "--share-id", "s1")


async def test_ssh_agent_debug_returns_raw_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checked = AsyncMock(return_value="prod: Ed25519 valid\n")
    monkeypatch.setattr(ssh_module, "run_pass_cli_checked", checked)

    output = await ssh_agent_debug(share_id="s1", item_title="prod")

    assert output == "prod: Ed25519 valid\n"
    assert checked.await_args is not None
    assert checked.await_args.args == (
        "ssh-agent", "debug", "--share-id", "s1", "--item-title", "prod",
    )  # fmt: skip
