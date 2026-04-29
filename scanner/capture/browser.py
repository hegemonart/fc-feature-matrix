"""Playwright persistent-context factory for the scanner (Plan 03, Task 1).

Ports the browser-setup patterns from `analysis/homepage/crosscheck/capture_elements.py`
(viewport, user-agent, sandbox args) and `recapture_round5.py::scroll_lazy` (bounded
lazy-load scroll). Generalises them into area- and club-parameterised helpers.

Invariants (D-12, D-13, user decision 2):
 - Viewport is locked to 1440×900 with `device_scale_factor=2` (full-page PNG at 2× DPR).
 - One persistent user-data dir per (area, club) — cookies/session survive across
   scanner invocations but never leak between areas (prevents hospitality session
   bleeding into ticket captures when Phase 4/5 ship).
 - `headless=False` is the DEFAULT — the pilot dry-run is a headed visual check.
   CI and Phase-2+ batch runs pass `headless=True` explicitly.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from playwright.sync_api import sync_playwright

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import BrowserContext, Playwright


USER_DATA_ROOT: Path = Path.home() / ".scanner" / "user-data"

# Plan 02-19 — Patchright engine literal. Patchright is a stealth-patched
# fork of Playwright that ships with aggressive Chromium-level patches
# (TLS fingerprinting, JS challenge evasion, CDP leak prevention) targeting
# Cloudflare Turnstile pages where playwright-stealth still trips. We keep
# both code paths because Patchright is additive — defaults preserve Plan
# 02-15 Wave A behavior (Playwright + playwright-stealth).
BrowserEngine = Literal["playwright", "patchright"]

# Plan 02-15 Wave A — anti-bot fingerprint masks. Imported lazily inside
# create_browser() so test_browser tests that monkeypatch sync_playwright
# don't require the real package at import time, and so import failures
# fall back to a no-op stealth path (D-21 backward compat).
def _apply_stealth_sync(context) -> None:
    """Apply playwright-stealth fingerprint masks to a BrowserContext.

    No-op on import / apply failure (logged at WARNING). Stealth is a
    cosmetic enhancement — the existing capture pipeline must keep working
    even if playwright-stealth is uninstalled or its API changes.
    """
    try:
        from playwright_stealth import Stealth  # type: ignore[import-not-found]
        Stealth().apply_stealth_sync(context)
    except Exception:  # pragma: no cover — defensive only
        import logging
        logging.getLogger(__name__).warning(
            "playwright-stealth not applied (install missing or API drift); "
            "continuing without fingerprint masks",
        )

# Chrome UA matching research §2.1 — stable across Mac / Linux / Windows headless.
_USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def create_browser(
    club: str,
    area: str,
    *,
    headless: bool = False,
    stealth: bool = True,
    engine: BrowserEngine = "playwright",
) -> tuple["Playwright", "BrowserContext"]:
    """Launch a persistent Chromium context for the given (area, club) pair.

    Returns a `(playwright_instance, context)` tuple. The caller is responsible
    for closing the context and stopping the Playwright instance (see
    `scanner.capture.capture.capture_page` for the canonical teardown pattern).

    Parameters
    ----------
    club :
        Club slug (e.g. "mancity"). Used to segment the user-data directory.
    area :
        Area slug (e.g. "hospitality"). Segments the user-data directory at a
        higher level than `club` to prevent cross-area session leak (D-13).
    headless :
        Defaults to `False` per user decision 2. Pilot dry-runs should be
        headed so a human can visually inspect popups; batch runs pass `True`.
    stealth :
        Plan 02-15 Wave A. Defaults to ``True`` — applies playwright-stealth
        fingerprint masks (navigator.webdriver, chrome.runtime, plugins,
        WebGL vendor, etc.) so headless Chromium passes the cheap bot checks
        that triggered Cloudflare Turnstile interstitials in Plan 02-11.
        Set ``stealth=False`` to reproduce pre-v2 behavior or to debug
        whether stealth is masking a real selector miss.

        With ``engine="patchright"`` we deliberately skip applying
        playwright-stealth even when ``stealth=True`` — Patchright already
        ships its own stealth patches and double-applying causes API drift
        warnings.
    engine :
        Plan 02-19. ``"playwright"`` (default) preserves the Plan 02-15
        Wave A behavior (regular Playwright + playwright-stealth fingerprint
        masks). ``"patchright"`` swaps the underlying driver for the
        stealth-patched Patchright fork — same Playwright API, but with
        Chromium-level patches that bypass Cloudflare Turnstile pages where
        playwright-stealth's runtime-level masks still leak. Use this engine
        only when stealth on the regular driver has been verified to fail
        (see ``scanner.scripts.recapture.stealth_probe``).
    """
    user_data_dir = USER_DATA_ROOT / area / club
    user_data_dir.mkdir(parents=True, exist_ok=True)

    if engine == "patchright":
        # Lazy import — keeps test_browser tests that monkeypatch
        # ``sync_playwright`` at the module top from needing patchright at
        # import time, and lets imports fail loudly only when the engine is
        # actually requested (D-21 backward compat).
        from patchright.sync_api import sync_playwright as patchright_sync
        pw = patchright_sync().start()
    elif engine == "playwright":
        pw = sync_playwright().start()
    else:  # pragma: no cover — defensive only
        raise ValueError(f"Unknown browser engine: {engine!r}")

    ctx = pw.chromium.launch_persistent_context(
        str(user_data_dir),
        headless=headless,
        viewport={"width": 1440, "height": 900},  # D-12
        device_scale_factor=2,  # D-12 (DPR=2 full-page PNG)
        user_agent=_USER_AGENT,
        args=["--no-sandbox"],
    )
    # Patchright already provides stealth patches at the Chromium level —
    # double-applying playwright-stealth on top is redundant and emits a
    # stealth-already-applied UserWarning. Keep the regular Playwright path
    # using playwright-stealth as before.
    if stealth and engine == "playwright":
        _apply_stealth_sync(ctx)
    return pw, ctx


def scroll_lazy(page, step_px: int = 600, settle_ms: int = 400) -> None:
    """Bounded scroll-to-bottom loop to trigger lazy-load images + sections.

    Port of `analysis/homepage/crosscheck/recapture_round5.py::scroll_lazy` —
    marked "most reliable" in CLAUDE.md. Capped at 15 steps so a buggy infinite-
    scroll page (T-03-04) cannot hang the capture loop.

    Parameters
    ----------
    step_px :
        Scroll increment in CSS pixels. 600 matches the ported original.
    settle_ms :
        Pause between scroll steps for lazy-load hydration (in milliseconds).
    """
    import time  # local import keeps module top clean for monkeypatching in tests

    try:
        h = page.evaluate("document.body.scrollHeight")
    except Exception:
        return

    settle_s = settle_ms / 1000.0
    try:
        steps = min(int(h) // step_px, 15) if h else 0
        for i in range(steps):
            page.evaluate(f"window.scrollTo(0, {(i + 1) * step_px})")
            time.sleep(settle_s)
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
    except Exception:
        # Scroll failures are non-fatal — the full-page screenshot still captures
        # whatever did render. Let the caller proceed.
        pass


__all__ = ["create_browser", "scroll_lazy", "USER_DATA_ROOT", "_apply_stealth_sync"]
