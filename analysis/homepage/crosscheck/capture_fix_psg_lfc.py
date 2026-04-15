#!/usr/bin/env python3
"""
Fix captures for PSG and Liverpool using Playwright with stealth settings.
PSG blocks standard Playwright — we override navigator.webdriver and use a real user agent.
Liverpool needs extra wait time for JS rendering.
"""

import json
import os
import sys
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent  # analysis/homepage/
RESULTS = BASE / "results"
IMG_DIR = BASE / "crosscheck" / "img"
IMG_DIR.mkdir(exist_ok=True)

MIN_BODY_Y = 500

HEADER_FEATURES = {
    "language_switcher_in_header", "login_account", "search_input_in_header",
    "shop_shortcut_in_header", "tickets_shortcut_in_header", "sponsor_lockup_in_header",
    "persistent_bar_above_header",
}
HERO_FEATURES = {
    "hero_carousel", "secondary_editorial_strip_below_hero", "brand_sponsor_highlighted_in_hero",
}

# Import LOCATORS from the batch1 script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capture_batch1 import LOCATORS


def get_true_features(club_id):
    path = RESULTS / f"{club_id}.json"
    with open(path) as f:
        data = json.load(f)
    return [k for k, v in data["features"].items() if v is True]


def safe_eval(page, expr):
    try:
        return page.evaluate(expr)
    except Exception:
        return None


def safe_screenshot(page, path, clip, full_page=True):
    try:
        if clip["width"] <= 0 or clip["height"] <= 0:
            return False
        clip["x"] = max(0, clip["x"])
        clip["y"] = max(0, clip["y"])
        page.screenshot(path=str(path), clip=clip, full_page=full_page, timeout=60000)
        return True
    except Exception as e:
        print(f"    [screenshot error] {str(e)[:100]}")
        return False


def dismiss_cookies_psg(page):
    """PSG uses Didomi consent. Try multiple strategies."""
    for attempt in range(8):
        result = safe_eval(page, """() => {
            // Try Didomi specific buttons
            var btns = [
                document.getElementById('didomi-notice-agree-button'),
                document.querySelector('button.didomi-dismiss-button'),
                document.querySelector('#didomi-popup .didomi-continue-without-agreeing'),
                document.querySelector('[aria-label="Agree"]'),
            ];
            for (var b of btns) {
                if (b) { b.click(); return 'didomi-' + b.id; }
            }
            // Try generic consent buttons
            var all = document.querySelectorAll('button, a, [role="button"]');
            for (var b of all) {
                try {
                    var txt = (b.textContent || '').toLowerCase().trim();
                    if (txt.includes('accept') || txt.includes('agree') || txt === 'ok' || txt.includes('consent') || txt.includes('continue without')) {
                        b.click(); return 'generic: ' + txt.substring(0, 30);
                    }
                } catch(e) {}
            }
            return false;
        }""")
        print(f"    Cookie attempt {attempt+1}: {result}")
        time.sleep(2)

        height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
        if height > 3000:
            print(f"    Page unblocked! Height: {height}px")
            return True

    # Force remove all overlays
    safe_eval(page, """() => {
        document.querySelectorAll('#didomi-host, [id*="didomi"], [class*="consent"], [class*="cookie"], [class*="modal"], [class*="overlay"], [role="dialog"], [class*="backdrop"]').forEach(e => { try { e.remove(); } catch(x) {} });
        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';
        // Remove fixed position overlays
        document.querySelectorAll('div, section').forEach(e => {
            try {
                var s = window.getComputedStyle(e);
                if ((s.position === 'fixed' || s.position === 'sticky') && parseInt(s.zIndex) > 100) {
                    var r = e.getBoundingClientRect();
                    if (r.width > 300 && r.height > 300) e.remove();
                }
            } catch(x) {}
        });
    }""")
    time.sleep(1)
    height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
    print(f"    After force-remove: {height}px")
    return height > 3000


def dismiss_cookies_liverpool(page):
    """Liverpool has a standard cookie banner."""
    for attempt in range(5):
        result = safe_eval(page, """() => {
            var btns = document.querySelectorAll('button, a, [role="button"]');
            for (var b of btns) {
                try {
                    var txt = (b.textContent || '').toLowerCase().trim();
                    if (txt.includes('accept all') || txt.includes('accept') || txt.includes('agree') || txt === 'ok' || txt.includes('got it')) {
                        b.click(); return txt.substring(0, 30);
                    }
                } catch(e) {}
            }
            return false;
        }""")
        print(f"    Cookie attempt {attempt+1}: {result}")
        time.sleep(2)

        height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
        if height > 3000:
            print(f"    Page unblocked! Height: {height}px")
            return True

    # Force remove
    safe_eval(page, """() => {
        document.querySelectorAll('[class*="consent"], [class*="cookie"], [class*="modal"], [class*="overlay"], [role="dialog"], [class*="backdrop"]').forEach(e => { try { e.remove(); } catch(x) {} });
        document.body.style.overflow = 'auto';
        document.documentElement.style.overflow = 'auto';
    }""")
    time.sleep(1)
    height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
    print(f"    After force-remove: {height}px")
    return height > 3000


def scroll_lazy_load(page):
    """Scroll incrementally to trigger lazy loading."""
    height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000
    for i in range(1, 9):
        safe_eval(page, f"window.scrollTo(0, {height * i // 8})")
        time.sleep(0.7)
    new_height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000
    if new_height > height + 500:
        for i in range(1, 5):
            safe_eval(page, f"window.scrollTo(0, {new_height * i // 4})")
            time.sleep(0.5)
    safe_eval(page, "window.scrollTo(0, 0)")
    time.sleep(2)
    return safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0


def capture_feature(page, feature_key, club_id):
    """Capture a screenshot for one feature."""
    locator = LOCATORS.get(feature_key)
    if not locator:
        print(f"    [NO LOCATOR] {feature_key}")
        return False

    out_path = IMG_DIR / f"{club_id}_{feature_key}.png"

    # PSG-specific locators for features that need custom handling
    psg_specific = get_psg_specific_locator(feature_key, club_id)
    if psg_specific:
        locator = psg_specific

    # Region-based (fixed crop)
    if "region" in locator:
        r = locator["region"]
        if safe_screenshot(page, out_path, {"x": r[0], "y": r[1], "width": r[2]-r[0], "height": r[3]-r[1]}):
            print(f"    [region] {feature_key}")
            return True
        return False

    # Same-as (copy from another feature)
    if "same_as" in locator:
        ref = locator["same_as"]
        ref_path = IMG_DIR / f"{club_id}_{ref}.png"
        if ref_path.exists():
            shutil.copy2(ref_path, out_path)
            print(f"    [copy] {feature_key} (= {ref})")
            return True
        ref_locator = LOCATORS.get(ref, {})
        if "js" in ref_locator:
            locator = ref_locator
        else:
            print(f"    [SKIP] {feature_key} (ref {ref} not found)")
            return False

    # JS-based element location
    js_code = locator["js"].replace("{min_y}", str(MIN_BODY_Y))

    safe_js = f"""() => {{
        if (!document.body) return null;
        try {{
            var el = (function() {{ {js_code} }})();
            if (!el) return null;
            var rect = el.getBoundingClientRect();
            var absY = rect.top + window.scrollY;
            return {{
                x: Math.max(0, Math.round(rect.x)),
                y: Math.max(0, Math.round(absY)),
                width: Math.round(Math.min(rect.width, 1400)),
                height: Math.round(Math.min(rect.height, 900)),
            }};
        }} catch(e) {{ return null; }}
    }}"""

    el = safe_eval(page, safe_js)

    if el and el["width"] > 5 and el["height"] > 5:
        clip_h = min(el["height"], 800)
        clip_w = min(el["width"], 1400)
        if clip_w < 200:
            clip_w = 600
            el["x"] = max(0, el["x"] - 200)
        pad = 15
        clip = {
            "x": max(0, el["x"] - pad),
            "y": max(0, el["y"] - pad),
            "width": clip_w + 2 * pad,
            "height": clip_h + 2 * pad,
        }
        if safe_screenshot(page, out_path, clip, full_page=True):
            print(f"    [js] {feature_key} ({clip['width']}x{clip['height']} @ y:{el['y']})")
            return True

    # Fallback
    fb = locator.get("fallback")
    if fb:
        if safe_screenshot(page, out_path, {"x": fb[0], "y": fb[1], "width": fb[2]-fb[0], "height": fb[3]-fb[1]}):
            print(f"    [fallback] {feature_key}")
            return True

    print(f"    [SKIP] {feature_key}")
    return False


def get_psg_specific_locator(feature_key, club_id):
    """PSG-specific locator overrides based on live page analysis."""
    if club_id != "psg":
        return None

    # PSG page section positions (from live Chrome analysis):
    # Header: 0-60, Hero: 60-700, Fixtures: ~760, News: ~1165
    # Post game interviews: ~1730, PSG TV: ~2766, Men/Women/Handball: ~3013
    # Podcasts: ~3510, Communities/Stadium: ~3826, Footer: ~4500+
    psg_overrides = {
        "next_match_block": {"region": [0, 700, 1400, 1100]},
        "next_match_feature_rich": {"same_as": "next_match_block"},
        "results_block": {"region": [0, 700, 1400, 1100]},
        "dedicated_news_section": {"region": [0, 1100, 1400, 1700]},
        "news_rich_structure": {"same_as": "dedicated_news_section"},
        "press_conference_block": {"region": [0, 1680, 1400, 2200]},
        "homepage_video_block": {"region": [0, 2700, 1400, 3200]},
        "video_thumbnails_inline": {"same_as": "homepage_video_block"},
        "podcast_audio": {"region": [0, 3450, 1400, 3850]},
        "womens_team_featured": {"region": [0, 2950, 1400, 3500]},
        "charity_csr_block": {"region": [0, 3770, 1400, 4100]},
        "stadium_tours_block": {"region": [0, 3770, 1400, 4200]},
        "heritage_past_content": {"region": [0, 2950, 1400, 3500]},
        "multi_sport_tickets": {"region": [0, 2950, 1400, 3200]},
        "app_store_badges": {
            "js": """
                var els = document.querySelectorAll('a[href*="apps.apple"], a[href*="play.google"], a[href*="itunes"], img[alt*="App Store"], img[alt*="Google Play"], img[alt*="app-store"], img[alt*="google-play"]');
                for (var el of els) {
                    if (el.getBoundingClientRect().height > 5) return el.closest('div[class], section, footer') || el;
                }
                return null;
            """,
        },
    }
    return psg_overrides.get(feature_key)


def process_club(page, club_id, url, cookie_handler):
    """Navigate to club and capture all TRUE features."""
    print(f"\n{'='*60}")
    print(f"CLUB: {club_id} ({url})")
    print(f"{'='*60}")

    true_features = get_true_features(club_id)
    print(f"  TRUE features: {len(true_features)}: {', '.join(true_features)}")

    # Navigate
    print(f"  Navigating...")
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation warning: {str(e)[:80]}")

    # Wait longer for JS-heavy sites
    wait_time = 8 if club_id == "liverpool" else 6
    print(f"  Waiting {wait_time}s for JS rendering...")
    time.sleep(wait_time)

    # Dismiss cookies
    print(f"  Dismissing cookies...")
    cookie_handler(page)

    # Scroll for lazy loading
    height = scroll_lazy_load(page)
    print(f"  Final page height: {height}px")

    if height < 2000:
        print(f"  ⚠️  WARNING: Page very short ({height}px) — captures may fail")
        # Try one more reload
        try:
            page.reload(wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        time.sleep(5)
        cookie_handler(page)
        height = scroll_lazy_load(page)
        print(f"  After reload: {height}px")

    # Capture features
    captured = 0
    skipped = []
    for feature in true_features:
        if capture_feature(page, feature, club_id):
            captured += 1
        else:
            skipped.append(feature)

    print(f"\n  Result: {captured}/{len(true_features)} captured")
    if skipped:
        print(f"  Skipped: {', '.join(skipped)}")
    return captured, len(true_features)


def main():
    with sync_playwright() as p:
        # Launch with stealth settings
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )

        # Override navigator.webdriver to avoid bot detection
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)

        page = context.new_page()

        # Process PSG first
        psg_captured, psg_total = process_club(
            page, "psg", "https://www.psg.fr/en", dismiss_cookies_psg
        )

        # Then Liverpool
        lfc_captured, lfc_total = process_club(
            page, "liverpool", "https://www.liverpoolfc.com", dismiss_cookies_liverpool
        )

        context.close()
        browser.close()

    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  PSG: {psg_captured}/{psg_total}")
    print(f"  Liverpool: {lfc_captured}/{lfc_total}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
