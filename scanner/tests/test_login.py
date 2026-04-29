"""Tests for ``scanner.capture.login`` (Plan 02-10, Task 1).

The module is the per-club login helper consumed by the capture orchestrator
(``capture_flow``) before steps marked ``requires_credentials: true``.

Contract under test:

1. Happy path — both credentials present, selectors match, logged-in marker
   appears: ``login_to_club`` returns True and called the page primitives in
   the expected order (fill user → fill pass → click submit → wait for
   marker).

2. Missing credentials — when ``credentials.get_credential`` returns None
   for either field, ``login_to_club`` returns False without raising.

3. Per-club selector dispatch — ``LOGIN_SELECTORS`` carries entries for the
   five pilot clubs; an unknown club falls back to ``GENERIC_SELECTORS``.

4. Logged-in verification — after submit, the helper waits up to 5s for the
   logged-in marker; on timeout returns False.

5. No real network — every Playwright Page interaction is mocked.

6. Credential leak guard — neither the user nor the password value is ever
   logged via ``logging``. Caplog assert enforces this.

T-02-01-01 / T-02-01-02 invariants (no credential value in logs) extend to
this module by construction: the implementation must never reference the
resolved values in any log call.
"""
from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_page(
    *,
    fill_raises: bool = False,
    click_raises: bool = False,
    wait_marker_raises: bool = False,
) -> MagicMock:
    """Build a Page mock with configurable failure modes.

    Each toggle is a single call point: if ``fill_raises`` is True then the
    very next ``page.fill`` raises ``RuntimeError``; if ``click_raises``
    similar; ``wait_marker_raises`` triggers a timeout-style exception out of
    ``wait_for_selector``.
    """
    page = MagicMock(name="Page")
    page.fill = MagicMock(
        side_effect=RuntimeError("fill failed") if fill_raises else None
    )
    page.click = MagicMock(
        side_effect=RuntimeError("click failed") if click_raises else None
    )
    page.wait_for_selector = MagicMock(
        side_effect=TimeoutError("marker not found")
        if wait_marker_raises
        else None
    )
    return page


def _set_creds(monkeypatch: pytest.MonkeyPatch, club: str, user: str, pwd: str) -> None:
    monkeypatch.setenv(f"{club.upper()}_HOSPITALITY_USER", user)
    monkeypatch.setenv(f"{club.upper()}_HOSPITALITY_PASS", pwd)


def _clear_creds(monkeypatch: pytest.MonkeyPatch, club: str) -> None:
    monkeypatch.delenv(f"{club.upper()}_HOSPITALITY_USER", raising=False)
    monkeypatch.delenv(f"{club.upper()}_HOSPITALITY_PASS", raising=False)


# ---------------------------------------------------------------------------
# Test 1 — happy path
# ---------------------------------------------------------------------------


def test_login_to_club_happy_path_returns_true(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When both creds are set, fill + click + marker-wait all succeed,
    ``login_to_club`` returns True and called the primitives in order."""
    from scanner.capture.login import login_to_club

    _set_creds(monkeypatch, "tottenham", "alice@test", "p4ss")
    page = _make_page()

    result = login_to_club(page, "tottenham")

    assert result is True
    # Two fills (user, pass), one click, one wait_for_selector.
    assert page.fill.call_count == 2
    assert page.click.call_count == 1
    assert page.wait_for_selector.call_count == 1


# ---------------------------------------------------------------------------
# Test 2 — missing credentials → False, no raise
# ---------------------------------------------------------------------------


def test_login_to_club_missing_user_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If ``get_credential`` returns None for the user, helper returns False
    (no raise). No fill / click / wait should have happened."""
    from scanner.capture.login import login_to_club

    _clear_creds(monkeypatch, "psg")
    page = _make_page()

    result = login_to_club(page, "psg")

    assert result is False
    assert page.fill.call_count == 0
    assert page.click.call_count == 0


def test_login_to_club_missing_pass_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """User present but password missing → False, no submit attempted."""
    from scanner.capture.login import login_to_club

    monkeypatch.setenv("PSG_HOSPITALITY_USER", "alice@test")
    monkeypatch.delenv("PSG_HOSPITALITY_PASS", raising=False)
    page = _make_page()

    result = login_to_club(page, "psg")

    assert result is False
    # User-fill MAY have run before we discovered the missing pass — but we
    # require that submit was never attempted.
    assert page.click.call_count == 0


# ---------------------------------------------------------------------------
# Test 3 — per-club selector dispatch
# ---------------------------------------------------------------------------


def test_login_to_club_dispatches_per_club_selectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each pilot club's selector dict drives the fill calls for that club.

    We read the LOGIN_SELECTORS table directly and assert the helper used
    those selectors, not the generic fallback.
    """
    from scanner.capture import login as login_mod

    for club in ("mancity", "tottenham", "realmadrid", "psg", "chelsea"):
        _set_creds(monkeypatch, club, "u@x", "pw")
        sel = login_mod.LOGIN_SELECTORS[club]
        page = _make_page()

        result = login_mod.login_to_club(page, club)

        assert result is True, f"{club} login expected True"
        # Assert fill called with the user_field and pass_field selectors
        # from the per-club mapping.
        fill_selectors = [c.args[0] for c in page.fill.call_args_list]
        assert sel["user_field"] in fill_selectors, (
            f"{club} expected user_field={sel['user_field']!r} in {fill_selectors!r}"
        )
        assert sel["pass_field"] in fill_selectors, (
            f"{club} expected pass_field={sel['pass_field']!r} in {fill_selectors!r}"
        )


def test_login_to_club_unknown_club_falls_back_to_generic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An unknown club uses the GENERIC_SELECTORS table."""
    from scanner.capture import login as login_mod

    _set_creds(monkeypatch, "newcastle", "u@x", "pw")
    page = _make_page()

    result = login_mod.login_to_club(page, "newcastle")

    assert result is True
    fill_selectors = [c.args[0] for c in page.fill.call_args_list]
    assert login_mod.GENERIC_SELECTORS["user_field"] in fill_selectors
    assert login_mod.GENERIC_SELECTORS["pass_field"] in fill_selectors


# ---------------------------------------------------------------------------
# Test 4 — logged-in marker timeout returns False
# ---------------------------------------------------------------------------


def test_login_to_club_marker_timeout_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If wait_for_selector raises (no logged-in marker within 5s), the
    helper returns False — best-effort verification."""
    from scanner.capture.login import login_to_club

    _set_creds(monkeypatch, "chelsea", "u@x", "pw")
    page = _make_page(wait_marker_raises=True)

    result = login_to_club(page, "chelsea")

    assert result is False


def test_login_to_club_fill_failure_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If page.fill raises (selector miss, detached element), return False."""
    from scanner.capture.login import login_to_club

    _set_creds(monkeypatch, "mancity", "u@x", "pw")
    page = _make_page(fill_raises=True)

    result = login_to_club(page, "mancity")

    assert result is False
    assert page.click.call_count == 0  # never reached submit


def test_login_to_club_click_failure_returns_false(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If page.click raises (submit button missing), return False."""
    from scanner.capture.login import login_to_club

    _set_creds(monkeypatch, "mancity", "u@x", "pw")
    page = _make_page(click_raises=True)

    result = login_to_club(page, "mancity")

    assert result is False


# ---------------------------------------------------------------------------
# Test 5 — credential leak guard
# ---------------------------------------------------------------------------


def test_login_to_club_never_logs_credential_values(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Caplog must NOT contain either the user or the password value after
    a successful login. Sentinel values are unique strings so a substring
    match is reliable."""
    from scanner.capture.login import login_to_club

    user_sentinel = "secret_user_001@example.invalid"
    pass_sentinel = "do_not_log_this_password_AAA"
    _set_creds(monkeypatch, "mancity", user_sentinel, pass_sentinel)
    page = _make_page()

    caplog.set_level(logging.DEBUG, logger="scanner")
    caplog.set_level(logging.DEBUG, logger="scanner.capture.login")

    result = login_to_club(page, "mancity")

    assert result is True
    full_log = caplog.text
    assert user_sentinel not in full_log, (
        f"User sentinel {user_sentinel!r} leaked into logs:\n{full_log}"
    )
    assert pass_sentinel not in full_log, (
        f"Password sentinel {pass_sentinel!r} leaked into logs:\n{full_log}"
    )


def test_login_to_club_never_logs_credentials_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Failure-path log lines (any of: fill failed, marker timeout) must
    also NOT carry the credential value."""
    from scanner.capture.login import login_to_club

    user_sentinel = "fail_user_123@example.invalid"
    pass_sentinel = "fail_pass_xyz_marker"
    _set_creds(monkeypatch, "psg", user_sentinel, pass_sentinel)
    page = _make_page(wait_marker_raises=True)

    caplog.set_level(logging.DEBUG, logger="scanner")
    caplog.set_level(logging.DEBUG, logger="scanner.capture.login")

    result = login_to_club(page, "psg")

    assert result is False
    full_log = caplog.text
    assert user_sentinel not in full_log
    assert pass_sentinel not in full_log


# ---------------------------------------------------------------------------
# Test 6 — selector table covers all 5 pilot clubs
# ---------------------------------------------------------------------------


def test_login_selectors_covers_all_pilot_clubs() -> None:
    """The selector table MUST have an entry for every pilot club; this is
    a structural assertion guarding against typos or missing rollouts."""
    from scanner.capture.login import LOGIN_SELECTORS

    expected = {"mancity", "tottenham", "realmadrid", "psg", "chelsea"}
    assert expected.issubset(LOGIN_SELECTORS.keys()), (
        f"LOGIN_SELECTORS missing entries: {expected - set(LOGIN_SELECTORS.keys())}"
    )
    # Every entry must define the four required selector keys.
    required = {"user_field", "pass_field", "submit", "logged_in_marker"}
    for club, sel in LOGIN_SELECTORS.items():
        missing = required - set(sel.keys())
        assert not missing, f"{club} selector entry missing keys: {missing}"
