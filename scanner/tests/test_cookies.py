"""Tests for scanner.capture.cookies (Plan 03, Task 1).

Covers the cookie-dismissal dispatcher: per-club strategy lookup, fallback to
GLOBAL_COOKIE_PRIORITIES, bounded retries, and post-click selector handling.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def test_global_priorities_has_20_entries():
    """Research §2.2 lists 20 strings. Port verbatim — drift is the acceptance criterion."""
    from scanner.capture.cookies import GLOBAL_COOKIE_PRIORITIES

    assert isinstance(GLOBAL_COOKIE_PRIORITIES, list)
    assert len(GLOBAL_COOKIE_PRIORITIES) == 20
    # Spot-check a few entries from each language group
    assert "accept all" in GLOBAL_COOKIE_PRIORITIES
    assert "acepto" in GLOBAL_COOKIE_PRIORITIES
    assert "akzeptieren" in GLOBAL_COOKIE_PRIORITIES
    assert "i agree" in GLOBAL_COOKIE_PRIORITIES


def test_mancity_strategy_prioritises_accept_all_cookies():
    from scanner.capture.cookies import MANCITY_STRATEGY

    # MANCITY_STRATEGY["priority"] must lead with "accept all cookies" per plan.
    assert MANCITY_STRATEGY["priority"][0].lower() == "accept all cookies"
    assert "accept all" in [p.lower() for p in MANCITY_STRATEGY["priority"]]


def test_strategies_dispatch_includes_mancity():
    from scanner.capture.cookies import STRATEGIES, MANCITY_STRATEGY

    assert "mancity" in STRATEGIES
    assert STRATEGIES["mancity"] is MANCITY_STRATEGY


def test_dismiss_cookies_returns_true_on_successful_click(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """JS evaluate returns True on first attempt → dismiss_cookies returns True."""
    from scanner.capture import cookies as cookies_mod

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())  # skip real sleeps

    result = cookies_mod.dismiss_cookies(mock_playwright_page, club="mancity")

    assert result is True
    mock_playwright_page.evaluate.assert_called()


def test_dismiss_cookies_uses_mancity_priority_for_mancity_club(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """dismiss_cookies(page, club='mancity') must pass MANCITY_STRATEGY['priority'], not global."""
    from scanner.capture import cookies as cookies_mod
    from scanner.capture.cookies import MANCITY_STRATEGY

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(mock_playwright_page, club="mancity")

    # page.evaluate(JS, priorities) — second positional arg is the priority list.
    call = mock_playwright_page.evaluate.call_args
    passed_priorities = call.args[1]
    assert passed_priorities == MANCITY_STRATEGY["priority"]


def test_dismiss_cookies_uses_global_priorities_for_none(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    from scanner.capture import cookies as cookies_mod
    from scanner.capture.cookies import GLOBAL_COOKIE_PRIORITIES

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(mock_playwright_page, club=None)

    passed_priorities = mock_playwright_page.evaluate.call_args.args[1]
    assert passed_priorities == GLOBAL_COOKIE_PRIORITIES


def test_dismiss_cookies_unknown_club_falls_back_to_global(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    from scanner.capture import cookies as cookies_mod
    from scanner.capture.cookies import GLOBAL_COOKIE_PRIORITIES

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(mock_playwright_page, club="NOT_A_REAL_CLUB")

    passed_priorities = mock_playwright_page.evaluate.call_args.args[1]
    assert passed_priorities == GLOBAL_COOKIE_PRIORITIES


def test_dismiss_cookies_returns_false_after_max_attempts(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    from scanner.capture import cookies as cookies_mod

    mock_playwright_page.evaluate = MagicMock(return_value=False)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    result = cookies_mod.dismiss_cookies(
        mock_playwright_page, club=None, max_attempts=3
    )

    assert result is False
    assert mock_playwright_page.evaluate.call_count == 3


def test_dismiss_cookies_swallows_evaluate_exceptions(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """Navigation races occasionally throw; the loop must keep retrying, not crash."""
    from scanner.capture import cookies as cookies_mod

    mock_playwright_page.evaluate = MagicMock(
        side_effect=[Exception("dom not ready"), Exception("still racing"), True]
    )
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    result = cookies_mod.dismiss_cookies(
        mock_playwright_page, club=None, max_attempts=3
    )

    assert result is True
    assert mock_playwright_page.evaluate.call_count == 3


def test_dismiss_cookies_runs_post_click_selectors_after_success(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """A strategy with post_click_selectors must click each after initial dismissal."""
    from scanner.capture import cookies as cookies_mod

    # Inject a fake strategy via monkeypatch (keeps STRATEGIES dict immutable per test)
    fake_strategy = {
        "priority": ["accept"],
        "post_click_selectors": ["[aria-label='Close']", ".promo-x"],
    }
    monkeypatch.setitem(cookies_mod.STRATEGIES, "faketestclub", fake_strategy)

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    mock_playwright_page.click = MagicMock()
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(mock_playwright_page, club="faketestclub")

    clicked = [c.args[0] for c in mock_playwright_page.click.call_args_list]
    assert "[aria-label='Close']" in clicked
    assert ".promo-x" in clicked


# -----------------------------------------------------------------------------
# Phase 2 Plan 02-04 — per-club cookie strategies for TOT/RMA/PSG/CHE
# -----------------------------------------------------------------------------


def test_tot_strategy_priority_starts_with_accept_all_cookies():
    """TOT_STRATEGY leads with 'accept all cookies' and has 3 lowercase entries."""
    from scanner.capture.cookies import TOT_STRATEGY

    priority = TOT_STRATEGY["priority"]
    assert priority[0].lower() == "accept all cookies"
    assert len(priority) == 3
    assert all(p == p.lower() for p in priority)


def test_rma_strategy_priority_starts_with_spanish():
    """RMA_STRATEGY leads with Spanish phrase, English fallback present."""
    from scanner.capture.cookies import RMA_STRATEGY

    priority = RMA_STRATEGY["priority"]
    assert priority[0].lower() == "aceptar todo"
    assert "accept all" in [p.lower() for p in priority]


def test_psg_strategy_priority_starts_with_french():
    """PSG_STRATEGY leads with French phrase, English fallback present."""
    from scanner.capture.cookies import PSG_STRATEGY

    priority = PSG_STRATEGY["priority"]
    assert priority[0].lower() == "tout accepter"
    assert "accept all" in [p.lower() for p in priority]


def test_che_strategy_priority_starts_with_accept_all_cookies():
    """CHE_STRATEGY leads with 'accept all cookies' (OneTrust convention)."""
    from scanner.capture.cookies import CHE_STRATEGY

    priority = CHE_STRATEGY["priority"]
    assert priority[0].lower() == "accept all cookies"


def test_strategies_dispatch_includes_all_5_pilot_clubs():
    """STRATEGIES dispatch must include every pilot-wave club slug."""
    from scanner.capture.cookies import STRATEGIES

    pilot = {"mancity", "tottenham", "realmadrid", "psg", "chelsea"}
    assert pilot.issubset(set(STRATEGIES.keys()))


def test_strategies_does_not_include_liverpool():
    """CLAUDE.md trap: Liverpool DO NOT TOUCH — no strategy in the dispatch dict."""
    from scanner.capture.cookies import STRATEGIES

    assert "liverpool" not in STRATEGIES


def test_dismiss_cookies_uses_psg_priority_for_psg_club(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """dismiss_cookies(page, club='psg') must pass PSG_STRATEGY['priority'], not global."""
    from scanner.capture import cookies as cookies_mod
    from scanner.capture.cookies import PSG_STRATEGY

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(mock_playwright_page, club="psg")

    passed_priorities = mock_playwright_page.evaluate.call_args.args[1]
    assert passed_priorities == PSG_STRATEGY["priority"]


def test_dismiss_cookies_uses_rma_priority_for_realmadrid_club(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """dismiss_cookies(page, club='realmadrid') must pass RMA_STRATEGY['priority']."""
    from scanner.capture import cookies as cookies_mod
    from scanner.capture.cookies import RMA_STRATEGY

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(mock_playwright_page, club="realmadrid")

    passed_priorities = mock_playwright_page.evaluate.call_args.args[1]
    assert passed_priorities == RMA_STRATEGY["priority"]


def test_global_cookie_priorities_unchanged():
    """User decision 2: GLOBAL_COOKIE_PRIORITIES stays at 20 entries (French stays per-club)."""
    from scanner.capture.cookies import GLOBAL_COOKIE_PRIORITIES

    assert len(GLOBAL_COOKIE_PRIORITIES) == 20


def test_mancity_strategy_unchanged():
    """Regression guard: Phase-1 MANCITY_STRATEGY priority list is not modified."""
    from scanner.capture.cookies import MANCITY_STRATEGY

    assert MANCITY_STRATEGY["priority"] == ["accept all cookies", "accept all"]


# -----------------------------------------------------------------------------
# Plan 02-08 — domain= kwarg dispatch (per-domain cookie priority overrides)
# -----------------------------------------------------------------------------


def test_dismiss_cookies_accepts_domain_kwarg_without_breaking(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """Plan 02-08 Test 7: dismiss_cookies(page, club='psg', domain='www.psg.fr')
    accepts the kwarg cleanly. With no domain-keyed STRATEGIES entry the
    behavior collapses to the pre-08 club-only path — assert the priority
    list passed to evaluate is exactly PSG_STRATEGY['priority']."""
    from scanner.capture import cookies as cookies_mod
    from scanner.capture.cookies import PSG_STRATEGY

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(
        mock_playwright_page,
        club="psg",
        domain="www.psg.fr",
    )

    passed_priorities = mock_playwright_page.evaluate.call_args.args[1]
    # No STRATEGIES['www.psg.fr'] yet → collapse to PSG_STRATEGY['priority'].
    assert passed_priorities == PSG_STRATEGY["priority"]


def test_dismiss_cookies_domain_strategy_takes_precedence(
    monkeypatch: pytest.MonkeyPatch, mock_playwright_page
):
    """Plan 02-08: when STRATEGIES contains a domain-keyed entry, its priority
    list is concatenated FIRST (then the club's, deduped). This proves the
    forward-compat hook works without needing to ship live broker entries."""
    from scanner.capture import cookies as cookies_mod
    from scanner.capture.cookies import PSG_STRATEGY

    fake_domain_strategy = {
        "priority": ["only on broker", "tout accepter"],  # second is shared with PSG
        "post_click_selectors": [],
    }
    monkeypatch.setitem(
        cookies_mod.STRATEGIES, "billetterie.example.com", fake_domain_strategy
    )

    mock_playwright_page.evaluate = MagicMock(return_value=True)
    monkeypatch.setattr(cookies_mod.time, "sleep", MagicMock())

    cookies_mod.dismiss_cookies(
        mock_playwright_page,
        club="psg",
        domain="billetterie.example.com",
    )

    passed = mock_playwright_page.evaluate.call_args.args[1]
    # Domain entries first, then PSG_STRATEGY entries appended (dedupe via
    # dict.fromkeys collapses the shared "tout accepter" to a single entry).
    assert passed[0] == "only on broker"
    assert "tout accepter" in passed
    # No duplicate tout accepter:
    assert passed.count("tout accepter") == 1
    # PSG-only entries follow:
    for psg_entry in PSG_STRATEGY["priority"]:
        assert psg_entry in passed
