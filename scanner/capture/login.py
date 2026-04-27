"""Per-club Playwright login helper (Plan 02-10, Task 1).

Best-effort, fail-soft authentication helper consumed by the capture
orchestrator (``capture_flow``) before steps marked
``requires_credentials: true``.

Contract
========

``login_to_club(page, club) -> bool``

- Resolves credentials via :func:`scanner.capture.credentials.get_credential`
  using env-var convention ``{CLUB}_{AREA}_{FIELD}``. Area is ``"hospitality"``
  for the back-half pilot — Plan 02-10 only authenticates against hospitality
  flows.
- Returns ``False`` when:
  - either ``user`` or ``pass`` env var is unset;
  - any Playwright primitive (fill / click / wait_for_selector) raises;
  - the logged-in marker is not seen within 5 s.
- Returns ``True`` only when the full sequence (fill user → fill pass →
  click submit → marker observed) completes.
- **Never raises.** Mirrors the ``dismiss_cookies`` invariant from Phase 1:
  caller decides what to do with the result. The orchestrator records a
  ``missing-credentials`` step status when this returns False.

Security invariants (T-02-01-01 / T-02-01-02 / T-10-02)
=======================================================

- The resolved user / pass values are passed directly to ``page.fill`` and
  are never referenced in any logging call. The only logged information is
  the boolean outcome and the club slug.
- The selector dispatch table (``LOGIN_SELECTORS``) is committed source —
  no data values flow through it. Per-club entries are best-known selectors
  at execute time; a generic fallback covers unknown clubs.

D-21 deviation note
===================

This module is a *new sibling* under ``scanner/capture/`` — it does not
modify ``capture.py``, ``browser.py``, or ``cookies.py``. The deviation
covers the additive ``capture_flow`` orchestrator alongside this helper;
see ``.planning/phases/02-hospitality-pilot/02-10-PLAN.md``.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from scanner.capture import credentials

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import Page

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Selector dispatch tables
# ---------------------------------------------------------------------------
#
# Per-club best-known selectors at execute time. Entries are deliberately
# comma-joined so Playwright's ``page.fill`` resolves to the first matching
# DOM node (most permissive).
#
# Sources:
# - mancity: hospitality enquiry portal uses email/password input names.
# - tottenham: My Spurs login form (input#email / input#password).
# - realmadrid: areavip login (Spanish locale variant; also accepts EN).
# - psg: PSG billetterie account form.
# - chelsea: Chelsea hospitality account portal.
#
# The fallback ``GENERIC_SELECTORS`` covers any club not present here, using
# broad type/name attribute matchers that work on most modern login forms.

LOGIN_SELECTORS: dict[str, dict[str, str]] = {
    "mancity": {
        "user_field": "input[name='email'], input#email, input[type='email']",
        "pass_field": "input[name='password'], input#password, input[type='password']",
        "submit": "button[type='submit'], button:has-text('Sign in')",
        "logged_in_marker": "[data-testid='user-menu'], a[href*='/account/dashboard'], a[href*='logout']",
    },
    "tottenham": {
        "user_field": "input[name='email'], input#email, input[type='email']",
        "pass_field": "input[name='password'], input#password, input[type='password']",
        "submit": "button[type='submit'], button:has-text('Sign in'), button:has-text('Log in')",
        "logged_in_marker": "[data-testid='user-menu'], a[href*='/account'], button:has-text('Log out')",
    },
    "realmadrid": {
        "user_field": "input[name='email'], input#email, input[type='email'], input[name='username']",
        "pass_field": "input[name='password'], input#password, input[type='password']",
        "submit": "button[type='submit'], button:has-text('Iniciar sesi'), button:has-text('Log in')",
        "logged_in_marker": "[data-testid='user-menu'], a[href*='/areavip/'], a[href*='logout'], a[href*='cerrar-sesion']",
    },
    "psg": {
        "user_field": "input[name='email'], input#email, input[type='email'], input[name='username']",
        "pass_field": "input[name='password'], input#password, input[type='password']",
        "submit": "button[type='submit'], button:has-text('Se connecter'), button:has-text('Sign in')",
        "logged_in_marker": "[data-testid='user-menu'], a[href*='/account'], a[href*='/mon-compte'], a[href*='deconnexion']",
    },
    "chelsea": {
        "user_field": "input[name='email'], input#email, input[type='email']",
        "pass_field": "input[name='password'], input#password, input[type='password']",
        "submit": "button[type='submit'], button:has-text('Sign in'), button:has-text('Log in')",
        "logged_in_marker": "[data-testid='user-menu'], a[href*='/account'], a[href*='logout']",
    },
}

GENERIC_SELECTORS: dict[str, str] = {
    "user_field": "input[type='email'], input[name='email'], input[name='username']",
    "pass_field": "input[type='password'], input[name='password']",
    "submit": "button[type='submit']",
    "logged_in_marker": "[data-testid*='user'], a[href*='account'], a[href*='logout']",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def login_to_club(page: "Page", club: str) -> bool:
    """Best-effort hospitality login flow for ``club``.

    Returns ``True`` only when the full sequence succeeded AND the
    logged-in marker was observed within 5 s. Returns ``False`` on any
    failure (missing creds, selector miss, timeout). Never raises.

    The function does not log credential values — only the boolean outcome
    and the club slug appear in logs.
    """
    selectors = LOGIN_SELECTORS.get(club.lower(), GENERIC_SELECTORS)

    # Resolve credentials. ``get_credential`` returns None when env unset.
    user = credentials.get_credential(club, "user")
    if user is None:
        # Do NOT log the env var name as missing here — that is the
        # orchestrator's job (it already constructs the env-var key for the
        # run-log). This module silently fails-soft.
        logger.debug("login_to_club: user credential unset for %s", club)
        return False
    pwd = credentials.get_credential(club, "pass")
    if pwd is None:
        logger.debug("login_to_club: pass credential unset for %s", club)
        return False

    # Fill the user field.
    try:
        page.fill(selectors["user_field"], user)
    except Exception:
        logger.debug("login_to_club: user fill failed for %s", club)
        return False

    # Fill the password field.
    try:
        page.fill(selectors["pass_field"], pwd)
    except Exception:
        logger.debug("login_to_club: pass fill failed for %s", club)
        return False

    # Click submit.
    try:
        page.click(selectors["submit"])
    except Exception:
        logger.debug("login_to_club: submit click failed for %s", club)
        return False

    # Verify the logged-in marker appears within 5 s.
    try:
        page.wait_for_selector(selectors["logged_in_marker"], timeout=5000)
    except Exception:
        logger.debug("login_to_club: logged-in marker timeout for %s", club)
        return False

    logger.info("login_to_club: success for %s", club)
    return True


__all__ = ["login_to_club", "LOGIN_SELECTORS", "GENERIC_SELECTORS"]
