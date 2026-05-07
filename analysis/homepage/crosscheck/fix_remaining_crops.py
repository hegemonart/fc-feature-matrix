#!/usr/bin/env python3
"""Final fixes for the last few missed cropouts:

- wrexham paid_membership: target the eticketing.co.uk/Memberships/List link.
- barnsley b2b_partnerships: target the UNITING YOUR BUSINESS card specifically.
- barnsley secondary_editorial_strip_below_hero: target the row of 3 cards
  immediately below the hero.
"""

import time
from io import BytesIO
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

from capture_new_clubs import save_img, results, IMG_DIR, SCREENSHOTS_DIR


def kill_onetrust(page):
    page.evaluate("""
        const accept = document.getElementById('onetrust-accept-btn-handler');
        if (accept) accept.click();
        document.querySelectorAll('[class*="onetrust"], #onetrust-banner-sdk, #onetrust-consent-sdk, .onetrust-pc-dark-filter').forEach(e => e.remove());
    """)
    time.sleep(2)


def scroll_lazy(page):
    h = page.evaluate("document.body.scrollHeight")
    for i in range(min(h // 600, 25)):
        page.evaluate(f"window.scrollTo(0, {(i+1)*600})")
        time.sleep(0.35)
    time.sleep(1.5)
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(0.8)


def crop_and_save(page, full_png, club, feature, recipe_js, pad=8):
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
    x1 = max(0, int(box["x"]) - pad)
    y1 = max(0, int(box["y"]) - pad)
    x2 = min(fw, int(box["x"]) + int(box["width"]) + pad)
    y2 = min(fh, int(box["y"]) + int(box["height"]) + pad)
    if x2 - x1 < 30 or y2 - y1 < 20:
        print(f"    [TINY] {feature}: {x2-x1}x{y2-y1}")
        return False
    cropped = full_img.crop((x1, y1, x2, y2))
    buf = BytesIO()
    cropped.save(buf, format="PNG")
    return save_img(club, feature, buf.getvalue())


# Wrexham BE A MEMBER — find the eticketing memberships card.
WREXHAM_MEMBERSHIP = r"""
    (() => {
        const links = document.querySelectorAll('a[href*="Memberships"], a[href*="memberships"]');
        for (const a of links) {
            const href = a.href || '';
            if (/eticketing|memberships/i.test(href)) {
                const r = a.getBoundingClientRect();
                if (r.height > 100 && r.width > 100) {
                    return { x: r.left + scrollX, y: r.top + scrollY,
                             width: r.width, height: r.height };
                }
            }
        }
        return null;
    })()
"""


# Barnsley UNITING YOUR BUSINESS — find the card that contains an image
# whose alt OR a heading whose text mentions UNITING YOUR BUSINESS.
BARNSLEY_B2B = r"""
    (() => {
        // Try image alt first.
        const imgs = document.querySelectorAll('img');
        for (const img of imgs) {
            const alt = (img.alt || '').toLowerCase();
            if (/uniting|your business|with barnsley football/.test(alt)) {
                let card = img.closest('a, section, [class*="card"]');
                if (!card) card = img.parentElement;
                if (card) {
                    const r = card.getBoundingClientRect();
                    if (r.height > 100 && r.width > 200) {
                        return { x: r.left + scrollX, y: r.top + scrollY,
                                 width: r.width, height: r.height };
                    }
                }
            }
        }
        // Fallback: look for an <a> whose href contains business/sponsor/commercial.
        const links = document.querySelectorAll('a');
        for (const a of links) {
            const href = (a.href || '').toLowerCase();
            if (/sponsorship|commercial|business|partner|hospitality\/uniting/.test(href)) {
                const r = a.getBoundingClientRect();
                if (r.height > 200 && r.width > 200 && r.width < 800) {
                    return { x: r.left + scrollX, y: r.top + scrollY,
                             width: r.width, height: r.height };
                }
            }
        }
        return null;
    })()
"""


# Barnsley secondary editorial strip — 3 cards immediately below the hero.
# Look for a horizontal row of 3 card-like elements between Y=600 and Y=1300.
BARNSLEY_STRIP = r"""
    (() => {
        const candidates = document.querySelectorAll('section, div[class*="row" i], div[class*="grid" i]');
        for (const el of candidates) {
            const r = el.getBoundingClientRect();
            const top = r.top + scrollY;
            if (top > 600 && top < 1400 && r.width > 1000 && r.height > 100 && r.height < 500) {
                const cards = el.querySelectorAll('a, [class*="card" i]');
                let cardCount = 0;
                cards.forEach(c => {
                    const cr = c.getBoundingClientRect();
                    if (cr.width > 200 && cr.width < 600 && cr.height > 100) cardCount++;
                });
                if (cardCount >= 2 && cardCount <= 6) {
                    return { x: r.left + scrollX, y: top, width: r.width, height: r.height };
                }
            }
        }
        return null;
    })()
"""


def process_wrexham(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    try:
        print("\n--- WREXHAM ---")
        page.goto("https://www.wrexhamafc.co.uk/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6); kill_onetrust(page); time.sleep(1)
        scroll_lazy(page); kill_onetrust(page)
        png = page.screenshot(full_page=True)
        crop_and_save(page, png, "wrexham", "paid_membership", WREXHAM_MEMBERSHIP)
    finally:
        page.close()


def process_barnsley(browser):
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    try:
        print("\n--- BARNSLEY ---")
        page.goto("https://www.barnsleyfc.co.uk/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6); kill_onetrust(page); time.sleep(1)
        scroll_lazy(page); kill_onetrust(page)
        png = page.screenshot(full_page=True)
        crop_and_save(page, png, "barnsley", "b2b_partnerships", BARNSLEY_B2B)
        crop_and_save(page, png, "barnsley", "secondary_editorial_strip_below_hero",
                      BARNSLEY_STRIP)
    finally:
        page.close()


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            process_wrexham(browser)
            process_barnsley(browser)
        finally:
            browser.close()
    cap = sum(len(v) for v in results["captured"].values())
    fail = sum(len(v) for v in results["failed"].values())
    print(f"\nFINAL — captured: {cap}, failed: {fail}")
    for club, feats in results["failed"].items():
        if feats:
            print(f"  {club} failed: {feats}")


if __name__ == "__main__":
    main()
