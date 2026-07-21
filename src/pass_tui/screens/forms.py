"""Item create/edit forms."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.widgets import Button, Input, Label, Static

from pass_tui.cli import (
    Item,
    PassCliError,
    Vault,
    create_login_item,
    update_item_fields,
)
from pass_tui.screens.base import BackScreen
from pass_tui.widgets import PasswordGenerator

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


class LoginFormScreen(BackScreen):
    """Form for creating or editing a login item in a vault.

    Passing ``item`` switches the form to edit mode: fields are pre-filled from
    ``initial`` and submitting runs ``item update`` instead of ``item create``.
    In edit mode the password is left blank and only sent when the user types a
    new one, so the existing secret is not round-tripped or cleared by mistake.
    """

    BINDINGS = [
        Binding("ctrl+s", "submit", "Save"),
    ]

    def __init__(
        self,
        vault: Vault,
        *,
        item: Item | None = None,
        initial: dict[str, str] | None = None,
    ) -> None:
        super().__init__()
        self._vault = vault
        self._item = item
        self._initial = initial or {}

    @property
    def _is_edit(self) -> bool:
        return self._item is not None

    def compose_content(self) -> ComposeResult:
        with VerticalScroll(id="form-box"):
            yield Static(
                "Edit login item" if self._is_edit else "New login item",
                id="form-title",
            )
            yield Label("Title")
            yield Input(self._initial.get("title", ""), id="f-title")
            yield Label("Username")
            yield Input(self._initial.get("username", ""), id="f-username")
            yield Label("Password")
            yield Input(
                id="f-password",
                password=True,
                placeholder=(
                    "Leave blank to keep current" if self._is_edit else ""
                ),
            )
            yield PasswordGenerator(id="f-password-generator")
            yield Label("URL")
            yield Input(self._initial.get("url", ""), id="f-url")
            yield Label("Note")
            yield Input(self._initial.get("note", ""), id="f-note")
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

    def on_password_generator_generated(
        self, event: PasswordGenerator.Generated
    ) -> None:
        self.query_one("#f-password", Input).value = event.password

    def action_submit(self) -> None:
        values = self._gather()
        if not values["title"]:
            self.notify("Title is required.", severity="warning")
            return
        if self._is_edit:
            self.update_item(values)
        else:
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

    @work(exclusive=True, group="form")
    async def update_item(self, values: dict[str, str]) -> None:
        assert self._item is not None
        fields = {
            "title": values["title"],
            "username": values["username"],
            "url": values["url"],
            "note": values["note"],
        }
        # Only change the password when a new one was entered.
        if values["password"]:
            fields["password"] = values["password"]
        try:
            await update_item_fields(
                fields=fields,
                item_id=self._item.item_id,
                item_title=self._item.title,
                vault_name=self._vault.name,
                share_id=self._vault.share_id,
            )
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not update item"
            )
            return
        self.notify("Login item updated.", title="pass-tui")
        self.dismiss()
