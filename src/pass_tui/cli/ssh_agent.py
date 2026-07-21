"""ssh-agent integration on top of ``pass-cli ssh-agent``.

``ssh-agent load`` prints a plain-text summary (JSON support is not reliably
documented), so its counts are parsed from text. ``ssh-agent debug`` output is
shown verbatim.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from pass_tui.cli.runner import run_pass_cli_checked

_RE_LOADED = re.compile(r"successfully loaded\D*(\d+)", re.IGNORECASE)
_RE_SKIPPED = re.compile(r"already loaded\D*(\d+)", re.IGNORECASE)
_RE_TOTAL = re.compile(r"total keys\D*(\d+)", re.IGNORECASE)


@dataclass
class SshLoadSummary:
    """Parsed result of ``ssh-agent load``."""

    loaded: int | None
    skipped: int | None
    total: int | None
    raw: str

    def as_line(self) -> str:
        """A one-line summary, falling back to the raw output if unparsed."""
        parts: list[str] = []
        if self.loaded is not None:
            parts.append(f"loaded {self.loaded}")
        if self.skipped is not None:
            parts.append(f"already present {self.skipped}")
        if self.total is not None:
            parts.append(f"total {self.total}")
        if not parts:
            return self.raw.strip() or "Done."
        return "Keys: " + ", ".join(parts)


def _first_int(pattern: re.Pattern[str], text: str) -> int | None:
    match = pattern.search(text)
    return int(match.group(1)) if match else None


def parse_ssh_load_summary(text: str) -> SshLoadSummary:
    """Parse the loaded / already-present / total counts from load output."""
    return SshLoadSummary(
        loaded=_first_int(_RE_LOADED, text),
        skipped=_first_int(_RE_SKIPPED, text),
        total=_first_int(_RE_TOTAL, text),
        raw=text,
    )


async def ssh_agent_load(
    *,
    vault_name: str | None = None,
    share_id: str | None = None,
) -> SshLoadSummary:
    """Load a vault's SSH keys into the system agent via ``ssh-agent load``.

    Requires ``SSH_AUTH_SOCK`` to point at a running agent.

    Raises:
        PassCliError: if the command fails (e.g. no agent available).
    """
    args = ["ssh-agent", "load"]
    if share_id:
        args += ["--share-id", share_id]
    elif vault_name:
        args += ["--vault-name", vault_name]
    text = await run_pass_cli_checked(*args)
    return parse_ssh_load_summary(text)


async def ssh_agent_debug(
    *,
    vault_name: str | None = None,
    share_id: str | None = None,
    item_id: str | None = None,
    item_title: str | None = None,
) -> str:
    """Return the raw output of ``ssh-agent debug`` for display.

    Raises:
        PassCliError: if the command fails.
    """
    args = ["ssh-agent", "debug"]
    if share_id:
        args += ["--share-id", share_id]
    elif vault_name:
        args += ["--vault-name", vault_name]
    if item_id:
        args += ["--item-id", item_id]
    elif item_title:
        args += ["--item-title", item_title]
    return await run_pass_cli_checked(*args)
