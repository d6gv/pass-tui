"""A small inline password generator widget."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Button, Checkbox, Input

from pass_tui.password import generate_password

_DEFAULT_LENGTH = 20


class PasswordGenerator(Widget):
    """Generates a password from configurable options.

    Posts a :class:`PasswordGenerator.Generated` message so a parent form can
    fill its password field without this widget knowing about the form.
    """

    DEFAULT_CSS = """
    PasswordGenerator {
        height: auto;
    }
    PasswordGenerator > Horizontal {
        height: auto;
        align: left middle;
    }
    PasswordGenerator #pw-length {
        width: 8;
    }
    PasswordGenerator Checkbox {
        width: auto;
        margin: 0 1;
    }
    """

    class Generated(Message):
        """Emitted when a new password has been generated."""

        def __init__(self, password: str) -> None:
            super().__init__()
            self.password = password

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Input(
                value=str(_DEFAULT_LENGTH),
                id="pw-length",
                type="integer",
            )
            yield Checkbox("Symbols", value=True, id="pw-symbols")
            yield Checkbox("Digits", value=True, id="pw-digits")
            yield Checkbox("Upper", value=True, id="pw-upper")
            yield Button("Generate", id="pw-generate")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "pw-generate":
            event.stop()
            self.post_message(self.Generated(self._generate()))

    def _generate(self) -> str:
        raw_length = self.query_one("#pw-length", Input).value
        try:
            length = int(raw_length)
        except ValueError:
            length = _DEFAULT_LENGTH
        return generate_password(
            length,
            use_upper=self.query_one("#pw-upper", Checkbox).value,
            use_digits=self.query_one("#pw-digits", Checkbox).value,
            use_symbols=self.query_one("#pw-symbols", Checkbox).value,
        )
