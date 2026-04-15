#!/usr/bin/env python3
"""Fix PSG and Man City captures — handle cookie walls and TreeWalker errors."""

import json
import os
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent  # analysis/homepage/
RESULTS = BASE / "results"
IMG_DIR = BASE / "crosscheck" / "img"

# Import locators from capture scripts
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from capture_elements import FEATURE_LOCATORS
from capture_batch1 import EXTRA_LOCATORS

ALL_LOCATORS = {**FEATURE_LOCATORS, **EXTRA_LOCATORS}


def get_true_features(club_id):
    path = RESULTS / f"{club_id}.json"
    with open(path) as f:
        data = json.load(f)
    return [k for k, v in data["features"].items() if v is True]


def safe_eval(page, expr):
    try:
        return page.evaluate(expr)
    except Exception as e:
        return None


def safe_screenshot(page, path, clip, full_page=True):
    try:
        page.screenshot(path=str(path), clip=clip, full_page=full_page, timeout=60000)
        return True
    except Exception as e:
        print(f"  [screenshot error] {e}")
        return False


def capture_feature(page, feature_key, club_id):
    locator = ALL_LOCATORS.get(feature_key)
    if not locator:
        print(f"  [NO LOCATOR] {feature_key}")
        return False

    out_path = IMG_DIR / f"{club_id}_{feature_key}.png"
    strategy = locator.get("strategy", "js")

    if strategy == "region":
        region = locator["region"]
        return safe_screenshot(page, out_path, {
            "x": region[0], "y": region[1],
            "width": region[2] - region[0], "height": region[3] - region[1]
        })

    if strategy == "same_as":
        ref_key = locator["same_as"]
        ref_path = IMG_DIR / f"{club_id}_{ref_key}.png"
        if ref_path.exists():
            shutil.copy2(ref_path, out_path)
            print(f"  [copy] {club_id}_{feature_key}.png (same as {ref_key})")
            return True

    # JS-based — wrap in safe body check
    js_code = locator.get("js", "null")
    # Wrap TreeWalker usage to handle null body
    safe_js = f"""() => {{
        if (!document.body) return null;
        try {{
            const el = (() => {{ {js_code} }})();
            if (!el) return null;
            const rect = el.getBoundingClientRect();
            const absY = rect.top + window.scrollY;
            return {{
                x: Math.max(0, rect.x),
                y: Math.max(0, absY),
                width: Math.min(rect.width, 1400),
                height: Math.min(rect.height, 900),
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
        pad = 10
        clip = {
            "x": max(0, el["x"] - pad),
            "y": max(0, el["y"] - pad),
            "width": clip_w + 2 * pad,
            "height": clip_h + 2 * pad,
        }
        if safe_screenshot(page, out_path, clip, full_page=True):
            print(f"  [js] {club_id}_{feature_key}.png ({int(clip['width'])}x{int(clip['height'])} @ y:{int(el['y'])})")
            return True

    fallback = locator.get("fallback_region")
    if fallback:
        if safe_screenshot(page, out_path, {
            "x": fallback[0], "y": fallback[1],
            "width": fallback[2] - fallback[0], "height": fallback[3] - fallback[1]
        }):
            print(f"  [fallback] {club_id}_{feature_key}.png")
            return True

    print(f"  [SKIP] {club_id}_{feature_key}")
    return False


def do_psg(browser):
    """PSG - handle cookie consent properly."""
    club_id = "psg"
    url = "https://www.psg.fr/en"
    print(f"\n{'='*60}")
    print(f"FIX: {club_id} ({url})")
    print(f"{'='*60}")

    true_features = get_true_features(club_id)
    print(f"TRUE features: {len(true_features)}")

    context = browser.new_context(
        viewport={"width": 1400, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    page = context.new_page()

    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    time.sleep(5)

    # PSG cookie handling - try multiple approaches
    for attempt in range(5):
        dismissed = safe_eval(page, """() => {
            try {
                // Didomi
                var btn = document.querySelector('button.didomi-dismiss-button, #didomi-notice-agree-button');
                if (btn) { btn.click(); return 'didomi'; }
            } catch(e) {}
            try {
                // Generic
                var btns = document.querySelectorAll('button, a, [role="button"]');
                for (var b of btns) {
                    try {
                        var txt = (b.textContent || '').toLowerCase().trim();
                        if (txt.includes('accept') || txt.includes('agree') || txt.includes('consent') || txt.includes('ok') || txt.includes('got it')) {
                            b.click(); return 'generic';
                        }
                    } catch(ex) {}
                }
            } catch(e) {}
            try {
                // Remove overlay elements
                document.querySelectorAll('[class*="consent"], [class*="cookie"], [class*="modal"], [class*="overlay"], [role="dialog"]').forEach(function(e) { try { e.remove(); } catch(ex) {} });
                return 'removed';
            } catch(e) {}
            return false;
        }""")
        print(f"  Cookie attempt {attempt+1}: {dismissed}")
        time.sleep(2)

        # Check page height
        height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
        if height > 3000:
            print(f"  Page unblocked! Height: {height}px")
            break

    # Scroll for lazy loading
    height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000
    print(f"  Page height: {height}px")

    for i in range(1, 7):
        safe_eval(page, f"window.scrollTo(0, {height * i // 6})")
        time.sleep(0.8)
    safe_eval(page, "window.scrollTo(0, 0)")
    time.sleep(2)

    final_height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
    print(f"  Final height: {final_height}px")

    captured = 0
    for feature in true_features:
        if capture_feature(page, feature, club_id):
            captured += 1

    print(f"  Result: {captured}/{len(true_features)}")
    context.close()
    return captured


def do_man_city(browser):
    """Man City - handle timeout."""
    club_id = "man_city"
    url = "https://www.mancity.com"
    print(f"\n{'='*60}")
    print(f"FIX: {club_id} ({url})")
    print(f"{'='*60}")

    true_features = get_true_features(club_id)
    print(f"TRUE features: {len(true_features)}")

    context = browser.new_context(
        viewport={"width": 1400, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    page = context.new_page()

    # Use domcontentloaded instead of networkidle to avoid timeout
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation partial: {e}")
    time.sleep(8)  # Extra wait for JS rendering

    # Cookie handling
    for attempt in range(5):
        dismissed = safe_eval(page, """() => {
            try {
                var btns = document.querySelectorAll('button, a, [role="button"]');
                for (var b of btns) {
                    try {
                        var txt = (b.textContent || '').toLowerCase().trim();
                        if (txt.includes('accept all') || txt.includes('accept') || txt.includes('agree') || txt.includes('ok') || txt.includes('got it')) {
                            b.click(); return txt;
                        }
                    } catch(ex) {}
                }
            } catch(e) {}
            try {
                document.querySelectorAll('[class*="consent"], [class*="cookie"], [class*="modal"], [class*="overlay"], [role="dialog"]').forEach(function(e) { try { e.remove(); } catch(ex) {} });
            } catch(e) {}
            return false;
        }""")
        print(f"  Cookie attempt {attempt+1}: {dismissed}")
        time.sleep(2)

        height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
        if height > 3000:
            print(f"  Page unblocked! Height: {height}px")
            break

    # Scroll
    height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000
    print(f"  Page height: {height}px")

    for i in range(1, 7):
        safe_eval(page, f"window.scrollTo(0, {height * i // 6})")
        time.sleep(0.8)
    safe_eval(page, "window.scrollTo(0, 0)")
    time.sleep(2)

    final_height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
    print(f"  Final height: {final_height}px")

    captured = 0
    for feature in true_features:
        if capture_feature(page, feature, club_id):
            captured += 1

    print(f"  Result: {captured}/{len(true_features)}")
    context.close()
    return captured


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        psg_count = do_psg(browser)
        city_count = do_man_city(browser)

        browser.close()

    print(f"\nFixes: PSG={psg_count}, Man City={city_count}")


if __name__ == "__main__":
    main()
