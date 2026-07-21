"""Tests for the client-side password generator."""

from __future__ import annotations

import string

from pass_tui.password import generate_password


def test_length_is_respected() -> None:
    assert len(generate_password(32)) == 32
    assert len(generate_password(0)) == 1  # clamped to a minimum of 1


def test_excludes_unselected_categories() -> None:
    password = generate_password(
        40, use_symbols=False, use_upper=False, use_digits=True
    )
    assert not any(character in string.ascii_uppercase for character in password)
    assert not any(character in "!@#$%^&*" for character in password)
    assert any(character in string.digits for character in password)


def test_includes_one_of_each_selected_category() -> None:
    password = generate_password(
        4, use_lower=True, use_upper=True, use_digits=True, use_symbols=True
    )
    assert any(c in string.ascii_lowercase for c in password)
    assert any(c in string.ascii_uppercase for c in password)
    assert any(c in string.digits for c in password)
    assert any(not c.isalnum() for c in password)


def test_falls_back_to_lowercase_when_nothing_selected() -> None:
    password = generate_password(
        12,
        use_lower=False,
        use_upper=False,
        use_digits=False,
        use_symbols=False,
    )
    assert len(password) == 12
    assert all(character in string.ascii_lowercase for character in password)
