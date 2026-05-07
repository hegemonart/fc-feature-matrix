#!/usr/bin/env python3
"""
Capture full-page screenshots and per-feature crops for the 3 new entries
added on 2026-05-07: Wrexham AFC, NFL, Barnsley FC.

Reuses RECIPES, helpers, and capture flow from capture_new_clubs.py — the
proven full-page-screenshot + JS-bbox + PIL-crop pipeline.
"""

import time
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

# Reuse the recipe library + helpers from the previous-batch script.
from capture_new_clubs import (
    RECIPES,
    dismiss_cookies,
    scroll_lazy,
    capture_full_page,
    capture_feature,
    save_img,
    is_blank,
    results,
    IMG_DIR,
    SCREENSHOTS_DIR,
)

CLUBS = [
    {
        "id": "wrexham",
        "url": "https://www.wrexhamafc.co.uk/",
        "fullpage_filename": "38-wrexham.png",
    },
    {
        "id": "nfl",
        "url": "https://www.nfl.com/",
        "fullpage_filename": "39-nfl.png",
    },
    {
        "id": "barnsley",
        "url": "https://www.barnsleyfc.co.uk/",
        "fullpage_filename": "40-barnsley.png",
    },
]

# Per-club override list: features marked TRUE in the JSON that have a recipe
# in RECIPES — these are the ones we attempt to crop. Features without a
# recipe (or marked FALSE) are skipped.
CLUB_FEATURES = {
    "wrexham": [
        "login_account", "search_input_in_header", "shop_shortcut_in_header",
        "tickets_shortcut_in_header", "persistent_bar_above_header",
        "secondary_editorial_strip_below_hero",
        "results_block", "standings_block",
        "dedicated_news_section", "news_rich_structure",
        "store_block", "store_individual_products",
        "paid_membership",
        "footer_sponsor_wall", "social_links_in_footer",
    ],
    "nfl": [
        "login_account", "tickets_shortcut_in_header",
        "persistent_bar_above_header", "brand_sponsor_highlighted_in_hero",
        "dedicated_news_section", "news_rich_structure",
        "homepage_video_block", "episodic_docu_series",
        "paid_membership",
        "heritage_past_content",
        "player_roster_preview", "individual_player_cards",
        "in_content_sponsor", "app_store_badges", "club_tv_app_promo",
        "social_links_in_footer",
    ],
    "barnsley": [
        "login_account", "search_input_in_header", "shop_shortcut_in_header",
        "tickets_shortcut_in_header", "persistent_bar_above_header",
        "secondary_editorial_strip_below_hero",
        "results_block", "standings_block",
        "dedicated_news_section", "news_rich_structure",
        "tickets_block",
        "store_block", "store_individual_products",
        "footer_sponsor_wall", "social_links_in_footer",
    ],
}


def process_club(browser, club_def):
    cid = club_def["id"]
    url = club_def["url"]
    fullpage_filename = club_def["fullpage_filename"]

    print("\n" + "=" * 60)
    print(f"  {cid} ({url})")
    print("=" * 60)

    page = browser.new_page(viewport={"width": 1440, "height": 900})
    try:
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        time.sleep(5)
        dismiss_cookies(page)
        time.sleep(1)
        scroll_lazy(page)

        full_png = capture_full_page(page, cid, fullpage_filename)
        if not full_png:
            return

        for feature in CLUB_FEATURES.get(cid, []):
            capture_feature(page, full_png, cid, feature)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for club in CLUBS:
                process_club(browser, club)
        finally:
            browser.close()

    summary = {
        "captured_total": sum(len(v) for v in results["captured"].values()),
        "failed_total": sum(len(v) for v in results["failed"].values()),
        "captured": results["captured"],
        "failed": results["failed"],
    }
    print("\n" + "=" * 60)
    print(f"  CAPTURED: {summary['captured_total']}")
    print(f"  FAILED  : {summary['failed_total']}")
    print("=" * 60)
    for club, feats in results["failed"].items():
        if feats:
            print(f"  {club} failed: {feats}")


if __name__ == "__main__":
    main()
