"""A self-refreshing TOTP code widget with a 30-second countdown."""

from __future__ import annotations

import math
import time

from textual import work
from textual.app import ComposeResult
from textual.message import Message
from textual.widget import Widget
from textual.widgets import ProgressBar, Static

from pass_tui.cli import (
    TOTP_PERIOD,
    PassCliError,
    get_totp_codes,
    period_index,
    seconds_remaining,
)


class TotpView(Widget):
    """Shows an item's live TOTP code(s) and a depleting period countdown.

    The code is fetched via ``pass-cli item totp`` and re-fetched only when the
    period rolls over; the countdown is driven purely by ``set_interval``. The
    widget hides itself when the item has no TOTP.
    """

    DEFAULT_CSS = """
    TotpView {
        height: auto;
        padding: 0 1;
    }
    TotpView .totp-label {
        color: $text-muted;
    }
    TotpView .totp-codes {
        text-style: bold;
    }
    TotpView .totp-bar {
        width: 20;
    }
    """

    class Changed(Message):
        """Posted after the set of codes changes (including first load)."""

    def __init__(
        self,
        *,
        item_id: str | None = None,
        item_title: str | None = None,
        vault_name: str | None = None,
        share_id: str | None = None,
        label: str | None = None,
        id: str | None = None,
    ) -> None:
        super().__init__(id=id)
        self._item_id = item_id
        self._item_title = item_title
        self._vault_name = vault_name
        self._share_id = share_id
        self._label = label
        self._codes: dict[str, str] = {}
        self._period: int | None = None

    def compose(self) -> ComposeResult:
        if self._label:
            yield Static(self._label, classes="totp-label")
        yield Static("", classes="totp-codes")
        yield ProgressBar(
            total=TOTP_PERIOD,
            show_percentage=False,
            show_eta=False,
            classes="totp-bar",
        )

    def on_mount(self) -> None:
        self.display = False  # stay hidden until we know there is a code
        self._period = period_index(time.time())
        self.set_interval(0.5, self._tick)
        self.refresh_codes()

    def _tick(self) -> None:
        now = time.time()
        self.query_one(ProgressBar).update(progress=seconds_remaining(now))
        current = period_index(now)
        if current != self._period:
            self._period = current
            self.refresh_codes()

    @work(exclusive=True, group="totp")
    async def refresh_codes(self) -> None:
        try:
            codes = await get_totp_codes(
                item_id=self._item_id,
                item_title=self._item_title,
                vault_name=self._vault_name,
                share_id=self._share_id,
            )
        except PassCliError:
            codes = {}
        self._codes = codes
        self.display = bool(codes)
        self.query_one(".totp-codes", Static).update(self._format_codes())
        self.post_message(self.Changed())

    def _format_codes(self) -> str:
        if not self._codes:
            return ""
        if len(self._codes) == 1:
            return next(iter(self._codes.values()))
        return "  ".join(f"{name}: {code}" for name, code in self._codes.items())

    def primary_code(self) -> str | None:
        """The first available code, for copying, or ``None``."""
        return next(iter(self._codes.values()), None)

    def remaining_seconds(self) -> int:
        """Whole seconds left in the current period (for display/tests)."""
        return int(math.ceil(seconds_remaining(time.time())))
