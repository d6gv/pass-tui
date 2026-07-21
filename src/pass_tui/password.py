"""Client-side password generation using the ``secrets`` module."""

from __future__ import annotations

import secrets
import string

_SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"


def generate_password(
    length: int = 20,
    *,
    use_lower: bool = True,
    use_upper: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """Return a cryptographically-random password.

    At least one character from each selected category is included when the
    length allows. If no category is selected, lowercase letters are used as a
    safe fallback. ``length`` is clamped to a minimum of 1.
    """
    pools: list[str] = []
    if use_lower:
        pools.append(string.ascii_lowercase)
    if use_upper:
        pools.append(string.ascii_uppercase)
    if use_digits:
        pools.append(string.digits)
    if use_symbols:
        pools.append(_SYMBOLS)
    if not pools:
        pools.append(string.ascii_lowercase)

    length = max(1, length)
    alphabet = "".join(pools)

    chars: list[str] = []
    if length >= len(pools):
        chars.extend(secrets.choice(pool) for pool in pools)
    while len(chars) < length:
        chars.append(secrets.choice(alphabet))

    rng = secrets.SystemRandom()
    rng.shuffle(chars)
    return "".join(chars[:length])
