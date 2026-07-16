"""Tests for the pass-cli process runner.

The subprocess is mocked throughout, so these tests never spawn the real
binary and never depend on a Proton account.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from pass_tui.cli.runner import PASS_CLI_BINARY, PassCliError, run_pass_cli


class FakeProcess:
    """Stand-in for the object returned by create_subprocess_exec."""

    def __init__(
        self,
        *,
        stdout: bytes = b"",
        stderr: bytes = b"",
        returncode: int = 0,
    ) -> None:
        self._stdout = stdout
        self._stderr = stderr
        self.returncode = returncode

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr


def patch_exec(
    monkeypatch: pytest.MonkeyPatch,
    *,
    process: FakeProcess | None = None,
    raises: BaseException | None = None,
) -> list[tuple[str, ...]]:
    """Patch create_subprocess_exec; return a list that records call args."""
    calls: list[tuple[str, ...]] = []

    async def fake_exec(*args: str, **kwargs: Any) -> FakeProcess:
        calls.append(args)
        if raises is not None:
            raise raises
        assert process is not None
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    return calls


async def test_returns_parsed_object(monkeypatch: pytest.MonkeyPatch) -> None:
    process = FakeProcess(stdout=b'{"session": "active"}')
    calls = patch_exec(monkeypatch, process=process)

    result = await run_pass_cli("info", "--output", "json")

    assert result == {"session": "active"}
    assert calls == [(PASS_CLI_BINARY, "info", "--output", "json")]


async def test_returns_parsed_array(monkeypatch: pytest.MonkeyPatch) -> None:
    process = FakeProcess(stdout=b'[{"name": "Personal"}]')
    patch_exec(monkeypatch, process=process)

    result = await run_pass_cli("vault", "list", "--output", "json")

    assert result == [{"name": "Personal"}]


async def test_logs_on_stderr_do_not_break_parsing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = FakeProcess(stdout=b'{"ok": true}', stderr=b"INFO some log line\n")
    patch_exec(monkeypatch, process=process)

    result = await run_pass_cli("info")

    assert result == {"ok": True}


async def test_nonzero_exit_raises_with_stderr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = FakeProcess(stderr=b"not logged in", returncode=1)
    patch_exec(monkeypatch, process=process)

    with pytest.raises(PassCliError) as excinfo:
        await run_pass_cli("info")

    error = excinfo.value
    assert error.returncode == 1
    assert error.stderr == "not logged in"
    assert "not logged in" in str(error)


async def test_missing_binary_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_exec(monkeypatch, raises=FileNotFoundError())

    with pytest.raises(PassCliError) as excinfo:
        await run_pass_cli("info")

    assert PASS_CLI_BINARY in str(excinfo.value)


async def test_invalid_json_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    process = FakeProcess(stdout=b"not json at all")
    patch_exec(monkeypatch, process=process)

    with pytest.raises(PassCliError) as excinfo:
        await run_pass_cli("info")

    assert "valid JSON" in str(excinfo.value)


async def test_scalar_json_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    process = FakeProcess(stdout=b'"just a string"')
    patch_exec(monkeypatch, process=process)

    with pytest.raises(PassCliError) as excinfo:
        await run_pass_cli("info")

    assert "object or an array" in str(excinfo.value)
