"""Cookie-banner dismissal dispatcher (Plan 03, Task 1).

Per-club strategies override the global priority list; unknown clubs fall back to
`GLOBAL_COOKIE_PRIORITIES`. The strategy dict is open for Phase-2+ additions
(one entry per club that needs a hand-tuned priority). Man City is the only
populated entry in Phase 1 — it is the dry-run target and has the verified
"Accept All Cookies" wording that the generic list also matches.

IMPORTANT (CLAUDE.md Trap): the one-word club from Merseyside is intentionally
absent from this module. The project rule "DO NOT TOUCH" for that club applies
to the capture path as well as existing screenshots — do not add a strategy.
"""
from __future__ import annotations

import time
from typing import TypedDict

from playwright.sync_api import Page


class CookieStrategy(TypedDict, total=False):
    """Per-club override.

    Both fields are optional; unspecified fields fall back to the global default
    (empty `post_click_selectors`, `GLOBAL_COOKIE_PRIORITIES`).
    """

    priority: list[str]
    post_click_selectors: list[str]


# Verbatim port of research §2.2 / capture_elements.py line ~820.
# Order matters: earlier entries take precedence when a page has multiple
# matching buttons. "accept all" dominates over "accept" for a reason —
# we want the full-consent path (fewer cookie prompts later) when it's offered.
GLOBAL_COOKIE_PRIORITIES: list[str] = [
    "accept all", "accept", "agree", "consent", "got it", "ok",
    "reject all", "decline", "necessary only", "refuse", "deny all",
    "acepto", "acceptar", "aceptar", "akzeptieren", "aceitar",
    "allow all", "accetto", "i agree", "confirm",
]


# The one populated strategy in Phase 1 — dry-run target per D-22.
# "accept all cookies" is Man City's exact wording as of 2026-04-24.
MANCITY_STRATEGY: CookieStrategy = {
    "priority": ["accept all cookies", "accept all"],
    "post_click_selectors": [],
}


STRATEGIES: dict[str, CookieStrategy] = {
    "mancity": MANCITY_STRATEGY,
}


_DISMISS_JS = """(priorities) => {
    const btns = document.querySelectorAll(
        'button, a, [role="button"], span[role="button"]'
    );
    for (const p of priorities) {
        for (const b of btns) {
            const t = (b.textContent || '').toLowerCase().trim();
            if (t.includes(p)) { b.click(); return true; }
        }
    }
    if (window.__cmp) { window.__cmp('setConsent', 0); return true; }
    return false;
}"""


def dismiss_cookies(
    page: Page,
    club: str | None = None,
    max_attempts: int = 3,
) -> bool:
    """Dismiss the cookie/consent banner on `page`.

    Dispatches to `STRATEGIES[club]` when known, falling back to a generic
    `GLOBAL_COOKIE_PRIORITIES` sweep. Retries up to `max_attempts` times with
    a 1-second pause between attempts (banners sometimes render after initial
    `networkidle`). Post-click selectors (e.g. "Close" on a promo popup that
    appears only after the consent banner is dismissed) are clicked once, in
    order, after the first successful JS evaluation.

    Returns True when a click (or `__cmp` fallback) succeeded, False otherwise.
    Never raises — navigation races are swallowed per research §2.2.
    """
    strategy: CookieStrategy = STRATEGIES.get(club, {}) if club else {}
    priorities = strategy.get("priority", GLOBAL_COOKIE_PRIORITIES)
    post_click = strategy.get("post_click_selectors", [])

    for _attempt in range(max_attempts):
        try:
            dismissed = page.evaluate(_DISMISS_JS, priorities)
            if dismissed:
                time.sleep(1)
                for sel in post_click:
                    try:
                        page.click(sel)
                    except Exception:
                        # Post-click targets are best-effort — a missing promo-X
                        # button is normal.
                        pass
                return True
        except Exception:
            # Most common cause: navigation mid-evaluate. Retry.
            pass
        time.sleep(1)

    return False


__all__ = [
    "dismiss_cookies",
    "GLOBAL_COOKIE_PRIORITIES",
    "STRATEGIES",
    "MANCITY_STRATEGY",
    "CookieStrategy",
]
