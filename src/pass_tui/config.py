"""pass-tui's own configuration file (separate from pass-cli settings).

Stored as TOML at a platform-appropriate location, e.g.
``~/.config/pass-tui/config.toml`` on Linux.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import platformdirs
import tomli_w
from pydantic import BaseModel, ConfigDict, Field

_APP_NAME = "pass-tui"


class Config(BaseModel):
    """User preferences for the TUI itself."""

    model_config = ConfigDict(extra="ignore")

    #: Seconds before a copied secret is cleared from the clipboard.
    clipboard_clear_seconds: int = 15
    #: Textual theme name (e.g. "textual-dark", "nord").
    theme: str = "textual-dark"
    #: Optional keybinding overrides, ``action -> key`` (reserved for later use).
    keybindings: dict[str, str] = Field(default_factory=dict)


def config_path() -> Path:
    """Return the path to the config file (which may not exist yet)."""
    return Path(platformdirs.user_config_dir(_APP_NAME)) / "config.toml"


def load_config(path: Path | None = None) -> Config:
    """Load the config, returning defaults when the file is missing or invalid."""
    path = path or config_path()
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (FileNotFoundError, tomllib.TOMLDecodeError, OSError):
        return Config()
    return Config.model_validate(data)


def save_config(config: Config, path: Path | None = None) -> None:
    """Write the config to disk, creating the parent directory if needed."""
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        tomli_w.dump(config.model_dump(), handle)
