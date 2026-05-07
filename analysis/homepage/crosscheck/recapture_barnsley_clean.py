#!/usr/bin/env python3
"""
Re-capture Barnsley homepage with proper OneTrust cookie dismissal.

Previous capture left the OneTrust banner + 1440x900 dark-filter overlay
on screen, which blocked the standings/results column inside the hero and
broke the recipes for store_block / store_individual_products /
footer_sponsor_wall / etc.

Strategy:
1. Click #onetrust-accept-btn-handler (the actual OneTrust accept button).
2. Remove the residual #onetrust-pc-dark-filter and #onetrust-banner-sdk
   nodes so they cannot leak through.
3. Verify cookie nodes are gone before capturing.
4. Use targeted recipes for Wrexham/Barnsley CMS quirks (LATEST PRODUCTS,
   RETAIL, OUR PARTNERS).
"""

import time
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

from capture_new_clubs import (
    RECIPES,
    scroll_lazy,
    capture_full_page,
    save_img,
    is_blank,
    results,
    IMG_DIR,
    SCREENSHOTS_DIR,
)

CLUB = {
    "id": "barnsley",
    "url": "https://www.barnsleyfc.co.uk/",
    "fullpage_filename": "40-barnsley.png",
}


def kill_onetrust(page):
    """Accept OneTrust cookies and remove the residual overlay/banner."""
    page.evaluate("""
        (() => {
            // Try clicking the accept button
            const accept = document.getElementById('onetrust-accept-btn-handler');
            if (accept) accept.click();
            // Optanon API fallback
            if (typeof window.OneTrust !== 'undefined' && window.OneTrust.AllowAll) {
                try { window.OneTrust.AllowAll(); } catch (e) {}
            }
            if (typeof window.Optanon !== 'undefined' && window.Optanon.AllowAll) {
                try { window.Optanon.AllowAll(); } catch (e) {}
            }
        })();
    """)
    time.sleep(2)
    # Force-remove any leftover OneTrust DOM nodes (the dark filter is the
    # critical one — it covers the full viewport at z-index 2147483645 and
    # blocks every recipe from finding elements in the hero).
    page.evaluate("""
        document.querySelectorAll(
            '#onetrust-banner-sdk, #onetrust-consent-sdk, .onetrust-pc-dark-filter,'
            + ' #onetrust-pc-sdk, .ot-sdk-container, [class*="onetrust"]'
        ).forEach(e => e.remove());
    """)
    time.sleep(0.5)


def verify_clean(page):
    found = page.evaluate("""
        document.querySelectorAll(
            '#onetrust-banner-sdk, .onetrust-pc-dark-filter, #onetrust-consent-sdk'
        ).length
    """)
    print(f"  OneTrust nodes remaining: {found}")
    return found == 0


# Targeted RETAIL section recipe — Barnsley CMS uses an h2 "RETAIL" label.
def recipe_barnsley_retail():
    return r"""
        (() => {
            const heads = document.querySelectorAll('h1, h2, h3, [class*="title" i]');
            for (const h of heads) {
                const txt = (h.textContent || '').trim().toLowerCase();
                if (txt === 'retail' || txt === 'shop' || txt === 'store') {
                    let sec = h.parentElement;
                    for (let i = 0; i < 5 && sec; i++) {
                        const r = sec.getBoundingClientRect();
                        if (r.height > 250 && r.width > 600) {
                            return { x: r.left + scrollX, y: r.top + scrollY,
                                     width: r.width, height: Math.min(r.height, 900) };
                        }
                        sec = sec.parentElement;
                    }
                }
            }
            return null;
        })()
    """


# Targeted "OUR PARTNERS" recipe — Barnsley + Wrexham both label the
# footer sponsor wall this way. We grab the labelled section, not the full
# footer.
def recipe_partner_section():
    return r"""
        (() => {
            const heads = document.querySelectorAll('h1, h2, h3, h4, [class*="title" i]');
            for (const h of heads) {
                const txt = (h.textContent || '').trim().toLowerCase();
                if (txt.includes('our partners') || txt.includes('principal partner')
                    || txt.includes('sponsors') || txt.includes('partners')) {
                    let sec = h.parentElement;
                    for (let i = 0; i < 5 && sec; i++) {
                        const r = sec.getBoundingClientRect();
                        const imgs = sec.querySelectorAll('img').length;
                        if (r.height > 100 && r.width > 600 && imgs >= 3) {
                            return { x: r.left + scrollX, y: r.top + scrollY,
                                     width: r.width, height: Math.min(r.height, 900) };
                        }
                        sec = sec.parentElement;
                    }
                }
            }
            return null;
        })()
    """


# Targeted "Previous Result" recipe (BAR 1-3 STP card).
def recipe_previous_result():
    return r"""
        (() => {
            const cards = document.querySelectorAll('div, section, article');
            for (const el of cards) {
                const txt = (el.textContent || '').trim();
                if (/previous result/i.test(txt) && txt.length < 400) {
                    const r = el.getBoundingClientRect();
                    if (r.height > 80 && r.height < 600 && r.width > 200) {
                        return { x: r.left + scrollX, y: r.top + scrollY,
                                 width: r.width, height: r.height };
                    }
                }
            }
            return null;
        })()
    """


def crop_and_save(page, full_png, club, feature, recipe_js):
    try:
        box = page.evaluate(recipe_js)
    except Exception as e:
        print(f"    [JS-ERR] {feature}: {e}")
        return False
    if not box:
        print(f"    [MISS] {feature}: not found")
        return False
    full_img = Image.open(BytesIO(full_png))
    fw, fh = full_img.size
    x1 = max(0, int(box["x"]) - 8)
    y1 = max(0, int(box["y"]) - 8)
    x2 = min(fw, int(box["x"]) + int(box["width"]) + 8)
    y2 = min(fh, int(box["y"]) + int(box["height"]) + 8)
    if x2 - x1 < 30 or y2 - y1 < 20:
        print(f"    [TINY] {feature}: {x2-x1}x{y2-y1}")
        return False
    cropped = full_img.crop((x1, y1, x2, y2))
    buf = BytesIO()
    cropped.save(buf, format="PNG")
    return save_img(club, feature, buf.getvalue())


# Standard recipe set (from RECIPES) for the rest of the features.
STANDARD_FEATURES = [
    "login_account", "search_input_in_header", "shop_shortcut_in_header",
    "tickets_shortcut_in_header", "persistent_bar_above_header",
    "secondary_editorial_strip_below_hero",
    "standings_block",
    "dedicated_news_section", "news_rich_structure",
    "tickets_block",
    "social_links_in_footer",
]


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
                time.sleep(6)
                kill_onetrust(page)
                if not verify_clean(page):
                    print("  WARN: OneTrust still present, retrying ...")
                    kill_onetrust(page)
                scroll_lazy(page)
                # Re-kill after scroll (OneTrust sometimes reattaches).
                kill_onetrust(page)

                full_png = capture_full_page(page, CLUB["id"], CLUB["fullpage_filename"])
                if not full_png:
                    return

                # Standard recipes from RECIPES.
                from capture_new_clubs import capture_feature
                for feature in STANDARD_FEATURES:
                    capture_feature(page, full_png, CLUB["id"], feature)

                # Targeted recipes.
                print("  --- targeted recipes ---")
                crop_and_save(page, full_png, CLUB["id"], "results_block",
                              recipe_previous_result())
                crop_and_save(page, full_png, CLUB["id"], "store_block",
                              recipe_barnsley_retail())
                crop_and_save(page, full_png, CLUB["id"], "store_individual_products",
                              recipe_barnsley_retail())
                crop_and_save(page, full_png, CLUB["id"], "footer_sponsor_wall",
                              recipe_partner_section())
                # b2b_partnerships recipe — "UNITING YOUR BUSINESS" promo.
                crop_and_save(page, full_png, CLUB["id"], "b2b_partnerships", r"""
                    (() => {
                        const all = document.querySelectorAll('div, section, a');
                        for (const el of all) {
                            const txt = (el.textContent || '').trim();
                            if (/uniting your business|become a partner|become a sponsor|partner with/i.test(txt)
                                && txt.length < 500) {
                                const r = el.getBoundingClientRect();
                                if (r.height > 100 && r.height < 700 && r.width > 300) {
                                    return { x: r.left + scrollX, y: r.top + scrollY,
                                             width: r.width, height: r.height };
                                }
                            }
                        }
                        return null;
                    })()
                """)
            finally:
                page.close()
        finally:
            browser.close()

    cap = sum(len(v) for v in results["captured"].values())
    fail = sum(len(v) for v in results["failed"].values())
    print("\n" + "=" * 60)
    print(f"  CAPTURED: {cap}")
    print(f"  FAILED  : {fail}")
    print("=" * 60)
    for club, feats in results["failed"].items():
        if feats:
            print(f"  {club} failed: {feats}")


if __name__ == "__main__":
    main()
