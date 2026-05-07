#!/usr/bin/env python3
"""
Re-capture Barnsley homepage. Initial capture in capture_may7.py landed on
an article page because the generic cookie banner dismissal accidentally
clicked a 'Confirm' button on an in-page CTA. This script uses a tighter
cookie dismissal that only matches explicit cookie-banner text.
"""

import time
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from capture_new_clubs import (
    RECIPES,
    scroll_lazy,
    capture_full_page,
    capture_feature,
    results,
    IMG_DIR,
    SCREENSHOTS_DIR,
)

CLUB = {
    "id": "barnsley",
    "url": "https://www.barnsleyfc.co.uk/",
    "fullpage_filename": "40-barnsley.png",
}

FEATURES_TO_CAPTURE = [
    "login_account", "search_input_in_header", "shop_shortcut_in_header",
    "tickets_shortcut_in_header", "persistent_bar_above_header",
    "secondary_editorial_strip_below_hero",
    "results_block", "standings_block",
    "dedicated_news_section", "news_rich_structure",
    "tickets_block",
    "store_block", "store_individual_products",
    "footer_sponsor_wall", "social_links_in_footer",
]


def safe_dismiss_cookies(page):
    """Tighter cookie dismissal — only match 'accept all' / 'reject all'
    buttons inside elements that look like cookie banners (avoid clicking
    a generic 'Confirm' CTA on the page)."""
    try:
        page.evaluate("""
            const banners = document.querySelectorAll(
                '[class*="cookie" i], [id*="cookie" i], [class*="consent" i], '
                + '[id*="consent" i], [class*="gdpr" i]'
            );
            for (const banner of banners) {
                const btns = banner.querySelectorAll('button, a, [role="button"]');
                for (const b of btns) {
                    const txt = (b.textContent || '').toLowerCase().trim();
                    if (txt === 'accept all' || txt === 'accept' || txt === 'allow all'
                        || txt === 'reject all' || txt === 'reject') {
                        b.click(); return;
                    }
                }
            }
        """)
        time.sleep(1.5)
        # Then nuke any leftover banner/modal overlays.
        page.evaluate("""
            document.querySelectorAll(
                '[class*="cookie" i], [class*="consent" i], [id*="cookie" i], '
                + '[id*="consent" i], [class*="gdpr" i]'
            ).forEach(e => {
                if (e.getBoundingClientRect().height > 50) e.remove();
            });
        """)
    except Exception:
        pass


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            try:
                print(f"\nLoading {CLUB['url']} ...")
                page.goto(CLUB["url"], timeout=60000, wait_until="domcontentloaded")
                time.sleep(5)
                safe_dismiss_cookies(page)
                time.sleep(1)
                # Verify we're on the homepage by checking the URL didn't navigate.
                current_url = page.url
                print(f"  URL after dismiss: {current_url}")
                if "/news/" in current_url or "/article/" in current_url:
                    print("  WARNING: Navigated away from homepage. Reloading.")
                    page.goto(CLUB["url"], timeout=60000, wait_until="domcontentloaded")
                    time.sleep(5)
                scroll_lazy(page)

                full_png = capture_full_page(page, CLUB["id"], CLUB["fullpage_filename"])
                if not full_png:
                    return

                for feature in FEATURES_TO_CAPTURE:
                    capture_feature(page, full_png, CLUB["id"], feature)
            finally:
                page.close()
        finally:
            browser.close()

    print("\n" + "=" * 60)
    print(f"  CAPTURED: {sum(len(v) for v in results['captured'].values())}")
    print(f"  FAILED  : {sum(len(v) for v in results['failed'].values())}")
    print("=" * 60)
    for club, feats in results["failed"].items():
        if feats:
            print(f"  {club} failed: {feats}")


if __name__ == "__main__":
    main()
