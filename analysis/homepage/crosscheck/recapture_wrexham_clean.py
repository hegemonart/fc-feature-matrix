#!/usr/bin/env python3
"""
Re-capture Wrexham homepage with proper OneTrust cookie dismissal AND
fixed recipes for previously-broken cropouts:

- social_links_in_footer: exclude EFL Together x.com/search badge (96x96)
  by filtering to small icon-sized links clustered on the same Y row.
- store_block / store_individual_products: target the "LATEST PRODUCTS"
  H1 instead of generic shop/store labels.
- paid_membership: target the "BE A MEMBER" promo card via image alt
  or surrounding link href.
- footer_sponsor_wall: target the "Principal Partners" / "Global Partners"
  / "Local Partners" trio in the footer.
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
    capture_feature,
    is_blank,
    results,
    IMG_DIR,
    SCREENSHOTS_DIR,
)

CLUB = {
    "id": "wrexham",
    "url": "https://www.wrexhamafc.co.uk/",
    "fullpage_filename": "38-wrexham.png",
}


def kill_onetrust(page):
    """Accept OneTrust cookies and remove the residual overlay/banner."""
    page.evaluate("""
        (() => {
            const accept = document.getElementById('onetrust-accept-btn-handler');
            if (accept) accept.click();
            if (typeof window.OneTrust !== 'undefined' && window.OneTrust.AllowAll) {
                try { window.OneTrust.AllowAll(); } catch (e) {}
            }
        })();
    """)
    time.sleep(2)
    page.evaluate("""
        document.querySelectorAll(
            '#onetrust-banner-sdk, #onetrust-consent-sdk, .onetrust-pc-dark-filter,'
            + ' #onetrust-pc-sdk, .ot-sdk-container, [class*="onetrust"]'
        ).forEach(e => e.remove());
    """)
    time.sleep(0.5)


# Fixed social_links recipe — excludes EFL Together x.com/search badge
# (which is 96x96, much bigger than the 24x24 real social icons).
SOCIAL_LINKS_FIXED = r"""
    (() => {
        const footer = document.querySelector('footer') || document.body;
        const sel = 'a[href*="facebook"], a[href*="instagram"], a[href*="twitter"],'
                  + ' a[href*="x.com"], a[href*="youtube"], a[href*="tiktok"],'
                  + ' a[href*="linkedin"]';
        const all = Array.from(footer.querySelectorAll(sel));
        // Filter: real social icons are small (<= 48px) and direct profile
        // links (not search URLs).
        const socials = all.filter(el => {
            const r = el.getBoundingClientRect();
            const href = el.href || '';
            if (r.width > 48 || r.height > 48) return false;
            if (/search\?|\?q=/.test(href)) return false;
            return true;
        });
        if (socials.length < 2) return null;
        // Cluster by Y coord — only keep links within 30px vertical of the
        // most-common Y. (Defends against scattered social links elsewhere
        // in the footer.)
        const ys = socials.map(s => Math.round(s.getBoundingClientRect().top + scrollY));
        const yMode = ys.sort((a, b) => ys.filter(v => Math.abs(v - a) < 30).length
                                       - ys.filter(v => Math.abs(v - b) < 30).length).pop();
        const cluster = socials.filter(s => Math.abs(s.getBoundingClientRect().top + scrollY - yMode) < 30);
        if (cluster.length < 2) return null;
        let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
        for (const s of cluster) {
            const r = s.getBoundingClientRect();
            minX = Math.min(minX, r.left + scrollX);
            minY = Math.min(minY, r.top + scrollY);
            maxX = Math.max(maxX, r.left + scrollX + r.width);
            maxY = Math.max(maxY, r.top + scrollY + r.height);
        }
        return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
    })()
"""


# "LATEST PRODUCTS" section — Wrexham's CMS-specific heading text.
LATEST_PRODUCTS = r"""
    (() => {
        const heads = document.querySelectorAll('h1, h2, h3, h4, [class*="title" i]');
        for (const h of heads) {
            const txt = (h.textContent || '').trim().toLowerCase();
            if (txt === 'latest products' || txt === 'products' || txt === 'shop'
                || txt === 'store' || txt === 'retail') {
                let sec = h.parentElement;
                for (let i = 0; i < 6 && sec; i++) {
                    const r = sec.getBoundingClientRect();
                    const imgs = sec.querySelectorAll('img').length;
                    if (r.height > 300 && r.width > 600 && imgs >= 1) {
                        return { x: r.left + scrollX, y: r.top + scrollY,
                                 width: r.width, height: Math.min(r.height, 1500) };
                    }
                    sec = sec.parentElement;
                }
            }
        }
        return null;
    })()
"""


# Wrexham's "BE A MEMBER" card — image alt or link href.
BE_A_MEMBER = r"""
    (() => {
        // Try links/buttons that mention BE A MEMBER or membership.
        const els = document.querySelectorAll('a, div, section, article');
        for (const el of els) {
            const txt = (el.textContent || '').trim();
            const aria = (el.getAttribute('aria-label') || '').toLowerCase();
            if (/be a member|wrexham story|find your place/i.test(txt)
                || /member/i.test(aria)) {
                const r = el.getBoundingClientRect();
                if (r.height > 100 && r.height < 700 && r.width > 200 && r.width < 800) {
                    return { x: r.left + scrollX, y: r.top + scrollY,
                             width: r.width, height: r.height };
                }
            }
        }
        // Fallback: image with alt containing "member" or "be a member".
        const imgs = document.querySelectorAll('img');
        for (const img of imgs) {
            const alt = (img.alt || '').toLowerCase();
            if (/member|membership|wrexham story/.test(alt)) {
                const r = img.getBoundingClientRect();
                if (r.height > 100 && r.width > 200) {
                    return { x: r.left + scrollX, y: r.top + scrollY,
                             width: r.width, height: r.height };
                }
            }
        }
        return null;
    })()
"""


# Wrexham footer — Principal Partners / Global Partners / Local Partners
# trio. Walk up from a "Principal Partners" heading to find the wrapper.
PARTNERS_FOOTER = r"""
    (() => {
        const heads = document.querySelectorAll('h1, h2, h3, h4, [class*="title" i]');
        let firstHead = null;
        for (const h of heads) {
            const txt = (h.textContent || '').trim().toLowerCase();
            if (txt.includes('principal partner')) {
                firstHead = h; break;
            }
        }
        if (!firstHead) {
            for (const h of heads) {
                const txt = (h.textContent || '').trim().toLowerCase();
                if (txt === 'partners' || txt.includes('our partners')) {
                    firstHead = h; break;
                }
            }
        }
        if (!firstHead) return null;
        let sec = firstHead.parentElement;
        for (let i = 0; i < 6 && sec; i++) {
            const r = sec.getBoundingClientRect();
            const imgs = sec.querySelectorAll('img').length;
            if (r.height > 200 && r.width > 600 && imgs >= 5) {
                return { x: r.left + scrollX, y: r.top + scrollY,
                         width: r.width, height: Math.min(r.height, 1200) };
            }
            sec = sec.parentElement;
        }
        // Final fallback: the union of all partner-region headings.
        const matches = Array.from(heads).filter(h =>
            /principal partner|global partner|local partner|partners/i.test(h.textContent || ''));
        if (matches.length === 0) return null;
        let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
        for (const h of matches) {
            const r = h.getBoundingClientRect();
            const containingSection = h.closest('section, div') || h;
            const cr = containingSection.getBoundingClientRect();
            minX = Math.min(minX, cr.left + scrollX);
            minY = Math.min(minY, cr.top + scrollY);
            maxX = Math.max(maxX, cr.left + scrollX + cr.width);
            maxY = Math.max(maxY, cr.top + scrollY + cr.height);
        }
        return { x: minX, y: minY, width: maxX - minX, height: Math.min(maxY - minY, 1200) };
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


# Standard recipes from RECIPES (still good for these features).
STANDARD_FEATURES = [
    "login_account", "search_input_in_header", "shop_shortcut_in_header",
    "tickets_shortcut_in_header", "persistent_bar_above_header",
    "secondary_editorial_strip_below_hero",
    "results_block", "standings_block",
    "dedicated_news_section", "news_rich_structure",
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
                scroll_lazy(page)
                kill_onetrust(page)

                full_png = capture_full_page(page, CLUB["id"], CLUB["fullpage_filename"])
                if not full_png:
                    return

                for feature in STANDARD_FEATURES:
                    capture_feature(page, full_png, CLUB["id"], feature)

                print("  --- targeted recipes ---")
                # Override the bad social_links cropout with the cluster-filtered version.
                crop_and_save(page, full_png, CLUB["id"], "social_links_in_footer", SOCIAL_LINKS_FIXED)
                crop_and_save(page, full_png, CLUB["id"], "store_block", LATEST_PRODUCTS)
                crop_and_save(page, full_png, CLUB["id"], "store_individual_products", LATEST_PRODUCTS)
                crop_and_save(page, full_png, CLUB["id"], "paid_membership", BE_A_MEMBER)
                crop_and_save(page, full_png, CLUB["id"], "footer_sponsor_wall", PARTNERS_FOOTER)
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
