"""Double-confirmation modal for destructive actions."""

from __future__ import annotations

from rich.markup import escape
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Static


class ConfirmDeleteModal(ModalScreen[bool]):
    """Confirm a permanent delete via two deliberate actions.

    The user must both tick the acknowledgement checkbox and press Delete, so
    an accidental keypress cannot destroy an item. Dismisses ``True`` only on
    an acknowledged delete, ``False`` otherwise.
    """

    DEFAULT_CSS = """
    ConfirmDeleteModal {
        align: center middle;
        background: $background 60%;
    }
    #confirm-box {
        width: 60;
        max-width: 90%;
        height: auto;
        padding: 1 2;
        border: round $error;
        background: $surface;
    }
    #confirm-title {
        text-style: bold;
        color: $error;
        margin-bottom: 1;
    }
    #confirm-check {
        margin: 1 0;
    }
    #confirm-buttons {
        height: auto;
        align: right middle;
    }
    #confirm-buttons Button {
        margin-left: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(self, item_title: str) -> None:
        super().__init__()
        self._item_title = item_title

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-box"):
            yield Static("Delete item", id="confirm-title")
            yield Static(
                f"Permanently delete [b]{escape(self._item_title)}[/b]? "
                "This cannot be undone."
            )
            yield Checkbox(
                "I understand this cannot be undone", id="confirm-check"
            )
            with Horizontal(id="confirm-buttons"):
                yield Button("Cancel", id="confirm-cancel")
                yield Button(
                    "Delete", id="confirm-delete", variant="error", disabled=True
                )

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        self.query_one("#confirm-delete", Button).disabled = not event.value

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-delete":
            self.dismiss(True)
        elif event.button.id == "confirm-cancel":
            self.dismiss(False)

    def action_cancel(self) -> None:
        self.dismiss(False)
