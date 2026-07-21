"""Item create/edit forms."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Button, Input, Label, Static

from pass_tui.cli import PassCliError, Vault, create_login_item
from pass_tui.screens.base import BackScreen

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class LoginFormScreen(BackScreen):
    """Form for creating a login item in a vault."""

    BINDINGS = [
        Binding("ctrl+s", "submit", "Save"),
    ]

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault

    def compose_content(self) -> ComposeResult:
        with VerticalScroll(id="form-box"):
            yield Static("New login item", id="form-title")
            yield Label("Title")
            yield Input(id="f-title")
            yield Label("Username")
            yield Input(id="f-username")
            yield Label("Password")
            yield Input(id="f-password", password=True)
            yield Label("URL")
            yield Input(id="f-url")
            yield Label("Note")
            yield Input(id="f-note")
            yield Button("Save", id="form-save", variant="primary")

    def _gather(self) -> dict[str, str]:
        def value(field_id: str) -> str:
            return self.query_one(field_id, Input).value

        return {
            "title": value("#f-title").strip(),
            "username": value("#f-username"),
            "password": value("#f-password"),
            "url": value("#f-url"),
            "note": value("#f-note"),
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "form-save":
            self.action_submit()

    def action_submit(self) -> None:
        values = self._gather()
        if not values["title"]:
            self.notify("Title is required.", severity="warning")
            return
        self.create_item(values)

    @work(exclusive=True, group="form")
    async def create_item(self, values: dict[str, str]) -> None:
        try:
            await create_login_item(
                title=values["title"],
                username=values["username"],
                password=values["password"],
                url=values["url"],
                note=values["note"],
                vault_name=self._vault.name,
                share_id=self._vault.share_id,
            )
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not create item"
            )
            return
        self.notify("Login item created.", title="pass-tui")
        self.dismiss()
