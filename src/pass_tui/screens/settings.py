"""Settings screen: pass-cli default vault and output format."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Button, Input, Label, Select, Static

from pass_tui.cli import (
    OUTPUT_FORMATS,
    SETTING_DEFAULT_FORMAT,
    SETTING_DEFAULT_VAULT,
    PassCliError,
    get_setting,
    list_vaults,
    set_setting,
)
from pass_tui.config import Config
from pass_tui.screens.base import BackScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class SettingsScreen(BackScreen):
    """View and change pass-cli's default vault and output format."""

    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
    ]

    def compose_content(self) -> ComposeResult:
        with VerticalScroll(id="settings-box"):
            yield Static("pass-cli", id="settings-cli-title")
            yield Label("Default vault")
            yield Select[str]([], id="set-vault")
            yield Label("Default output format")
            yield Select[str](
                [(fmt, fmt) for fmt in OUTPUT_FORMATS], id="set-format"
            )
            yield Static("pass-tui", id="settings-tui-title")
            yield Label("Clipboard clear (seconds)")
            yield Input(id="set-clip", type="integer")
            yield Label("Theme")
            yield Select[str]([], id="set-theme")
            yield Button("Save", id="settings-save", variant="primary")

    def on_screen_resume(self) -> None:
        self.load_settings()

    def on_mount(self) -> None:
        # Local pass-tui config is available immediately (no CLI needed).
        app = cast("PassTuiApp", self.app)
        self.query_one("#set-clip", Input).value = str(
            app.config.clipboard_clear_seconds
        )
        theme_select = self.query_one("#set-theme", Select)
        theme_select.set_options(
            (name, name) for name in sorted(app.available_themes)
        )
        if app.config.theme in app.available_themes:
            theme_select.value = app.config.theme

    @work(exclusive=True, group="settings")
    async def load_settings(self) -> None:
        """Populate the vault options and reflect the current defaults."""
        try:
            vaults = await list_vaults()
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not load settings"
            )
            return

        names = [vault.display_name for vault in vaults]
        vault_select = self.query_one("#set-vault", Select)
        vault_select.set_options((name, name) for name in names)

        current_vault = await get_setting(SETTING_DEFAULT_VAULT)
        if current_vault in names:
            vault_select.value = current_vault

        current_format = await get_setting(SETTING_DEFAULT_FORMAT)
        if current_format in OUTPUT_FORMATS:
            self.query_one("#set-format", Select).value = current_format

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "settings-save":
            self.action_save()

    def action_save(self) -> None:
        app = cast("PassTuiApp", self.app)

        # Local pass-tui config (applied immediately and persisted to disk).
        raw_clip = self.query_one("#set-clip", Input).value
        try:
            clip = max(1, int(raw_clip))
        except ValueError:
            clip = app.config.clipboard_clear_seconds
        theme_value = self.query_one("#set-theme", Select).value
        theme = (
            cast("str", theme_value)
            if theme_value is not Select.BLANK
            else app.config.theme
        )
        app.apply_config(
            Config(
                clipboard_clear_seconds=clip,
                theme=theme,
                keybindings=app.config.keybindings,
            )
        )

        # pass-cli settings (applied via the CLI).
        vault_value = self.query_one("#set-vault", Select).value
        format_value = self.query_one("#set-format", Select).value
        vault = vault_value if vault_value is not Select.BLANK else None
        fmt = format_value if format_value is not Select.BLANK else None
        self.save_settings(
            cast("str | None", vault), cast("str | None", fmt)
        )

    @work(exclusive=True, group="settings")
    async def save_settings(self, vault: str | None, fmt: str | None) -> None:
        try:
            if vault is not None:
                await set_setting(SETTING_DEFAULT_VAULT, vault)
            if fmt is not None:
                await set_setting(SETTING_DEFAULT_FORMAT, fmt)
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not save settings"
            )
            return
        self.notify("Settings saved.", title="pass-tui")
        self.dismiss()
