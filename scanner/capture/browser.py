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
from typing import TYPE_CHECKING

from playwright.sync_api import sync_playwright

if TYPE_CHECKING:  # pragma: no cover
    from playwright.sync_api import BrowserContext, Playwright


USER_DATA_ROOT: Path = Path.home() / ".scanner" / "user-data"

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
    """
    user_data_dir = USER_DATA_ROOT / area / club
    user_data_dir.mkdir(parents=True, exist_ok=True)

    pw = sync_playwright().start()
    ctx = pw.chromium.launch_persistent_context(
        str(user_data_dir),
        headless=headless,
        viewport={"width": 1440, "height": 900},  # D-12
        device_scale_factor=2,  # D-12 (DPR=2 full-page PNG)
        user_agent=_USER_AGENT,
        args=["--no-sandbox"],
    )
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


__all__ = ["create_browser", "scroll_lazy", "USER_DATA_ROOT"]
