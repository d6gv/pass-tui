"""Run the official ``pass-cli`` binary as a subprocess and parse its JSON.

pass-cli writes its logs to stderr, so stdout stays clean for JSON parsing.
This module never touches secure session storage; it only spawns the binary
and reads back what it prints.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any

#: Name of the pass-cli executable. Resolved on the PATH by the OS.
PASS_CLI_BINARY = "pass-cli"


class PassCliError(RuntimeError):
    """Raised when a pass-cli invocation fails or returns unparseable output.

    Attributes:
        command: The full argument vector that was run (binary included).
        returncode: The process exit code, if the process started.
        stderr: The captured stderr text, if any.
    """

    def __init__(
        self,
        message: str,
        *,
        command: list[str] | None = None,
        returncode: int | None = None,
        stderr: str | None = None,
    ) -> None:
        super().__init__(message)
        self.command = command
        self.returncode = returncode
        self.stderr = stderr


async def run_pass_cli(*args: str) -> dict[str, Any] | list[Any]:
    """Run ``pass-cli`` with ``args`` and return its stdout parsed as JSON.

    Args:
        *args: Arguments passed to the binary, e.g. ``"info", "--output", "json"``.

    Returns:
        The parsed JSON, which pass-cli emits as either an object or an array.

    Raises:
        PassCliError: if the binary is missing, exits non-zero, or emits output
            that is not a JSON object or array.
    """
    command = [PASS_CLI_BINARY, *args]
    printable = " ".join(command)

    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise PassCliError(
            f"Could not find the '{PASS_CLI_BINARY}' binary. Is pass-cli "
            "installed and on your PATH?",
            command=command,
        ) from exc

    stdout_bytes, stderr_bytes = await process.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")

    if process.returncode != 0:
        detail = stderr.strip() or stdout.strip() or "no error output"
        raise PassCliError(
            f"`{printable}` exited with code {process.returncode}: {detail}",
            command=command,
            returncode=process.returncode,
            stderr=stderr,
        )

    try:
        data = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise PassCliError(
            f"`{printable}` did not return valid JSON: {exc}",
            command=command,
            returncode=process.returncode,
            stderr=stderr,
        ) from exc

    if not isinstance(data, (dict, list)):
        raise PassCliError(
            f"`{printable}` returned JSON of type {type(data).__name__}, "
            "expected an object or an array.",
            command=command,
            returncode=process.returncode,
            stderr=stderr,
        )

    return data


def run_pass_cli_interactive(*args: str) -> int:
    """Run ``pass-cli`` with inherited stdio and return its exit code.

    For interactive commands such as ``login`` that must own the terminal.
    Call this only while the Textual app is suspended, so the terminal is free.
    Unlike :func:`run_pass_cli`, output is neither captured nor parsed.

    Raises:
        PassCliError: if the binary is missing.
    """
    command = [PASS_CLI_BINARY, *args]
    try:
        completed = subprocess.run(command)
    except FileNotFoundError as exc:
        raise PassCliError(
            f"Could not find the '{PASS_CLI_BINARY}' binary. Is pass-cli "
            "installed and on your PATH?",
            command=command,
        ) from exc
    return completed.returncode
