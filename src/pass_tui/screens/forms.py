"""Item create/edit forms."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, cast

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.validation import Function, Validator
from textual.widgets import Button, Input, Label, Static, TextArea

from pass_tui.cli import (
    Item,
    PassCliError,
    Vault,
    create_card_item,
    create_login_item,
    create_note_item,
    update_item_fields,
)
from pass_tui.screens.base import BackScreen
from pass_tui.widgets import PasswordGenerator

if TYPE_CHECKING:
    from pass_tui.app import PassTuiApp


def required(message: str = "This field is required") -> Validator:
    """A validator that rejects empty/whitespace-only values."""
    return Function(lambda value: bool(value.strip()), message)


def optional_pattern(pattern: str, message: str) -> Validator:
    """A validator that accepts an empty value or a full regex match."""
    regex = re.compile(pattern)
    return Function(
        lambda value: value == "" or regex.fullmatch(value) is not None,
        message,
    )


class FormScreen(BackScreen):
    """Base for item forms: save binding plus input validation."""

    BINDINGS = [
        Binding("ctrl+s", "submit", "Save"),
    ]

    def _check(self, *field_ids: str) -> bool:
        """Validate the named inputs; notify and focus the first invalid one."""
        first_invalid: Input | None = None
        message = ""
        for field_id in field_ids:
            field = self.query_one(field_id, Input)
            result = field.validate(field.value)
            if result is not None and not result.is_valid and first_invalid is None:
                first_invalid = field
                message = result.failure_descriptions[0]
        if first_invalid is not None:
            self.notify(message, severity="warning")
            first_invalid.focus()
            return False
        return True

    def action_submit(self) -> None:  # pragma: no cover - overridden
        raise NotImplementedError


class LoginFormScreen(FormScreen):
    """Form for creating or editing a login item in a vault.

    Passing ``item`` switches the form to edit mode: fields are pre-filled from
    ``initial`` and submitting runs ``item update`` instead of ``item create``.
    In edit mode the password is left blank and only sent when the user types a
    new one, so the existing secret is not round-tripped or cleared by mistake.
    """

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
            yield Input(
                self._initial.get("title", ""),
                id="f-title",
                validators=[required("Title is required")],
            )
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
            yield Input(
                self._initial.get("url", ""),
                id="f-url",
                validators=[
                    optional_pattern(
                        r"https?://\S+", "Enter a valid http(s) URL"
                    )
                ],
            )
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
        if not self._check("#f-title", "#f-url"):
            return
        values = self._gather()
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


class NoteFormScreen(FormScreen):
    """Form for creating a note item in a vault."""

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault

    def compose_content(self) -> ComposeResult:
        with VerticalScroll(id="form-box"):
            yield Static("New note item", id="form-title")
            yield Label("Title")
            yield Input(id="n-title", validators=[required("Title is required")])
            yield Label("Note")
            yield TextArea(id="n-note")
            yield Button("Save", id="form-save", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "form-save":
            self.action_submit()

    def action_submit(self) -> None:
        if not self._check("#n-title"):
            return
        title = self.query_one("#n-title", Input).value.strip()
        self.create_item(title, self.query_one("#n-note", TextArea).text)

    @work(exclusive=True, group="form")
    async def create_item(self, title: str, note: str) -> None:
        try:
            await create_note_item(
                title=title,
                note=note,
                vault_name=self._vault.name,
                share_id=self._vault.share_id,
            )
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not create item"
            )
            return
        self.notify("Note item created.", title="pass-tui")
        self.dismiss()


class CardFormScreen(FormScreen):
    """Form for creating a card item in a vault."""

    def __init__(self, vault: Vault) -> None:
        super().__init__()
        self._vault = vault

    def compose_content(self) -> ComposeResult:
        with VerticalScroll(id="form-box"):
            yield Static("New card item", id="form-title")
            yield Label("Title")
            yield Input(id="c-title", validators=[required("Title is required")])
            yield Label("Cardholder name")
            yield Input(id="c-cardholder")
            yield Label("Card number")
            yield Input(
                id="c-number",
                validators=[
                    optional_pattern(
                        r"[\d ]+", "Card number must be digits"
                    )
                ],
            )
            yield Label("Expiry (YYYY-MM)")
            yield Input(
                id="c-expiry",
                placeholder="2029-12",
                validators=[
                    optional_pattern(r"\d{4}-\d{2}", "Use the YYYY-MM format")
                ],
            )
            yield Label("CVV")
            yield Input(
                id="c-cvv",
                password=True,
                validators=[optional_pattern(r"\d{3,4}", "CVV must be 3-4 digits")],
            )
            yield Label("PIN")
            yield Input(
                id="c-pin",
                password=True,
                validators=[optional_pattern(r"\d{3,12}", "PIN must be digits")],
            )
            yield Label("Note")
            yield Input(id="c-note")
            yield Button("Save", id="form-save", variant="primary")

    def _gather(self) -> dict[str, str]:
        def value(field_id: str) -> str:
            return self.query_one(field_id, Input).value

        return {
            "title": value("#c-title").strip(),
            "cardholder": value("#c-cardholder"),
            "number": value("#c-number"),
            "expiry": value("#c-expiry"),
            "cvv": value("#c-cvv"),
            "pin": value("#c-pin"),
            "note": value("#c-note"),
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "form-save":
            self.action_submit()

    def action_submit(self) -> None:
        if not self._check(
            "#c-title", "#c-number", "#c-expiry", "#c-cvv", "#c-pin"
        ):
            return
        self.create_item(self._gather())

    @work(exclusive=True, group="form")
    async def create_item(self, values: dict[str, str]) -> None:
        try:
            await create_card_item(
                title=values["title"],
                cardholder=values["cardholder"],
                number=values["number"],
                expiry=values["expiry"],
                cvv=values["cvv"],
                pin=values["pin"],
                note=values["note"],
                vault_name=self._vault.name,
                share_id=self._vault.share_id,
            )
        except PassCliError as exc:
            cast("PassTuiApp", self.app).show_error(
                str(exc), title="Could not create item"
            )
            return
        self.notify("Card item created.", title="pass-tui")
        self.dismiss()
