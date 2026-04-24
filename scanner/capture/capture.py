"""Full-page capture orchestrator (Plan 03, Task 2).

The one function Plan 07's CLI and Plan 08's dry-run call. Coordinates
`scanner.capture.browser.create_browser`, cookie dismissal, lazy-load
scrolling, optional selector hiding (D-17), and the final full-page PNG.

**D-16 invariant:** this module contains no form dispatch. Form-fill lives
in `scanner.capture.form_dummy` and is purely `page.fill(...)` — never a
dispatch-button click. The grep-test in `tests/test_browser.py` enforces
that across the whole `scanner/capture/` tree.

**Output location (D-25, user decision 1):** writes to
`output_dir / 'fullpage' / '{club}_{step_name}.png'`. The caller chooses
`output_dir` — typically `scanner/output/evidence/{area}/` — NEVER `analysis/`.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

from scanner.capture.browser import create_browser, scroll_lazy
from scanner.capture.cookies import dismiss_cookies

logger = logging.getLogger(__name__)


def capture_page(
    url: str,
    club: str,
    area: str,
    step_name: str,
    output_dir: Path,
    *,
    headless: bool = False,
    hide_selectors: list[str] | None = None,
) -> Path:
    """Navigate, dismiss cookies, hide dynamic content, scroll lazy, screenshot.

    Parameters
    ----------
    url :
        Target page URL.
    club :
        Club slug — used for per-club cookie strategy dispatch and filename.
    area :
        Area slug — used for the persistent user-data dir (D-13).
    step_name :
        Flow-step name — appears in the output filename.
    output_dir :
        Parent dir. The PNG lands at `{output_dir}/fullpage/{club}_{step_name}.png`.
    headless :
        Defaults to False (headed). Passed through to `create_browser`.
    hide_selectors :
        Optional list of CSS selectors to hide via injected style tag (D-17).

    Returns
    -------
    Path
        Absolute path to the saved PNG. File is guaranteed non-empty on return.
    """
    out_file = output_dir / "fullpage" / f"{club}_{step_name}.png"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    pw, ctx = create_browser(club=club, area=area, headless=headless)
    try:
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_load_state("networkidle", timeout=30_000)
        time.sleep(2)  # settle for lazy-load images

        # Cookies FIRST per CLAUDE.md trap — before scroll, hide, or screenshot.
        dismiss_cookies(page, club=club)

        # Hide dynamic content (live chat, promo rotators) before scrolling so
        # injected CSS applies during the lazy-load walk too.
        if hide_selectors:
            css = "".join(
                f"{sel}{{display:none !important}}" for sel in hide_selectors
            )
            page.add_style_tag(content=css)

        scroll_lazy(page)

        png_bytes = page.screenshot(full_page=True)
        out_file.write_bytes(png_bytes)
        logger.info(
            f"Captured {club} {step_name} -> {out_file} ({len(png_bytes)} bytes)"
        )
        return out_file
    finally:
        ctx.close()
        pw.stop()


__all__ = ["capture_page"]
