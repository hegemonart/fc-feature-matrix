#!/usr/bin/env python3
"""
Capture PSG and Liverpool using Playwright with pre-warmed cookies.
These sites block headless automation, so we use headless=False and
handle cookies more aggressively.
"""

import json
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
RESULTS = BASE / "results"
IMG_DIR = BASE / "crosscheck" / "img"
MIN_BODY_Y = 500


def get_true_features(club_id):
    with open(RESULTS / f"{club_id}.json") as f:
        data = json.load(f)
    return [k for k, v in data["features"].items() if v is True]


def safe_eval(page, expr):
    try:
        return page.evaluate(expr)
    except:
        return None


def safe_screenshot(page, path, clip):
    try:
        if clip["width"] <= 0 or clip["height"] <= 0:
            return False
        clip["x"] = max(0, clip["x"])
        clip["y"] = max(0, clip["y"])
        page.screenshot(path=str(path), clip=clip, full_page=True, timeout=60000)
        return True
    except Exception as e:
        print(f"    [error] {str(e)[:80]}")
        return False


# PSG-specific section mapping (y-positions from live page)
PSG_SECTIONS = {
    "language_switcher_in_header": {"region": [1350, 0, 1400, 50]},
    "login_account": {"region": [1100, 0, 1250, 50]},
    "shop_shortcut_in_header": {"region": [1250, 0, 1400, 50]},
    "tickets_shortcut_in_header": {"region": [1150, 0, 1300, 50]},
    "hero_carousel": {"region": [0, 50, 1400, 700]},
    "next_match_block": {"y": 759, "h": 350},
    "next_match_feature_rich": {"same": "next_match_block"},
    "results_block": None,  # Need to verify
    "dedicated_news_section": {"y": 1165, "h": 500},
    "news_rich_structure": {"same": "dedicated_news_section"},
    "homepage_video_block": {"y": 1732, "h": 400},
    "video_thumbnails_inline": {"same": "homepage_video_block"},
    "podcast_audio": {"y": 3510, "h": 300},
    "press_conference_block": {"y": 1732, "h": 400},
    "stadium_tours_block": {"y": 3826, "h": 300},
    "heritage_past_content": None,
    "womens_team_featured": {"y": 3013, "h": 200},
    "charity_csr_block": {"y": 3826, "h": 300},
    "app_store_badges": None,  # Check footer
}


def capture_psg(page):
    """Capture PSG features using known section positions."""
    club_id = "psg"
    true_features = get_true_features(club_id)
    print(f"  TRUE features: {len(true_features)}")

    captured = 0
    for feature in true_features:
        out_path = IMG_DIR / f"{club_id}_{feature}.png"
        info = PSG_SECTIONS.get(feature)

        if info is None:
            print(f"    [SKIP] {feature} — no position data")
            continue

        if "same" in info:
            ref = info["same"]
            ref_path = IMG_DIR / f"{club_id}_{ref}.png"
            if ref_path.exists():
                shutil.copy2(ref_path, out_path)
                print(f"    [copy] {feature} (= {ref})")
                captured += 1
            continue

        if "region" in info:
            r = info["region"]
            if safe_screenshot(page, out_path, {"x": r[0], "y": r[1], "width": r[2]-r[0], "height": r[3]-r[1]}):
                print(f"    [region] {feature}")
                captured += 1
            continue

        if "y" in info:
            y = info["y"]
            h = info.get("h", 400)
            if safe_screenshot(page, out_path, {"x": 0, "y": max(0, y - 20), "width": 1400, "height": h}):
                print(f"    [section] {feature} (y={y}, h={h})")
                captured += 1
            continue

    # Try to find app_store_badges in footer
    el = safe_eval(page, """() => {
        var els = document.querySelectorAll('a[href*="apps.apple"], a[href*="play.google"]');
        if (els.length > 0) {
            var container = els[0].closest('div') || els[0].parentElement;
            var r = container.getBoundingClientRect();
            return {x: Math.round(r.x), y: Math.round(r.top + window.scrollY), w: Math.round(r.width), h: Math.round(r.height)};
        }
        return null;
    }""")
    if el:
        out_path = IMG_DIR / f"{club_id}_app_store_badges.png"
        if safe_screenshot(page, out_path, {"x": max(0, el["x"]-10), "y": max(0, el["y"]-10), "width": max(el["w"]+20, 300), "height": el["h"]+20}):
            print(f"    [js] app_store_badges")
            captured += 1

    return captured


LIVERPOOL_SECTIONS = {
    "language_switcher_in_header": {"region": [0, 0, 1400, 50]},
    "login_account": {"region": [1100, 0, 1400, 50]},
    "search_input_in_header": {"region": [1000, 0, 1400, 50]},
    "shop_shortcut_in_header": {"region": [500, 0, 1000, 50]},
    "tickets_shortcut_in_header": {"region": [400, 0, 800, 50]},
    "sponsor_lockup_in_header": {"region": [800, 0, 1400, 50]},
    "persistent_bar_above_header": {"region": [0, 0, 1400, 40]},
    "hero_carousel": {"region": [0, 50, 1400, 600]},
    "secondary_editorial_strip_below_hero": None,  # Dynamic
    "brand_sponsor_highlighted_in_hero": {"region": [0, 0, 1400, 600]},
}


def capture_liverpool(page):
    """Capture Liverpool features."""
    club_id = "liverpool"
    true_features = get_true_features(club_id)
    print(f"  TRUE features: {len(true_features)}")

    # First get page sections
    sections = safe_eval(page, """() => {
        var s = {};
        document.querySelectorAll('h2, h3, h4').forEach(function(el) {
            if (el.closest('nav, header')) return;
            var txt = (el.innerText || '').trim().substring(0,50);
            if (txt.length > 2) s[txt] = Math.round(el.getBoundingClientRect().top + window.scrollY);
        });
        return s;
    }""") or {}
    print(f"  Sections: {json.dumps(sections, indent=2)[:500]}")

    captured = 0
    for feature in true_features:
        out_path = IMG_DIR / f"{club_id}_{feature}.png"
        info = LIVERPOOL_SECTIONS.get(feature)

        if info and "region" in info:
            r = info["region"]
            if safe_screenshot(page, out_path, {"x": r[0], "y": r[1], "width": r[2]-r[0], "height": r[3]-r[1]}):
                print(f"    [region] {feature}")
                captured += 1
            continue

        # Dynamic JS-based detection
        js_patterns = {
            "next_match_block": "next match|upcoming|fixture|matchday",
            "next_match_feature_rich": None,  # same as above
            "results_block": "result|score",
            "dedicated_news_section": "news|latest|stories",
            "news_rich_structure": None,
            "homepage_video_block": "watch|video|highlight",
            "video_thumbnails_inline": None,
            "transfer_news": "transfer|signing",
            "interactive_fan_poll": "poll|vote|goal of",
            "tickets_block": "ticket",
            "store_block": "shop|store|kit|merch",
            "store_individual_products": None,
            "trophies_honours": "trophy|honour|title",
            "heritage_past_content": "heritage|history|on this day|legend",
            "womens_team_featured": "women|wsl|lfc women",
            "academy_youth_block": "academy|youth|u18|u21",
            "charity_csr_block": "foundation|charity|community|lfc foundation",
            "app_store_badges": None,
            "social_links_in_footer": None,
        }

        pattern = js_patterns.get(feature)
        if pattern is None and feature in js_patterns:
            # same_as logic
            for ref_feat, ref_pattern in js_patterns.items():
                if ref_pattern and feature.replace("_rich_structure", "_section") == ref_feat.replace("_rich_structure", "_section"):
                    ref_path = IMG_DIR / f"{club_id}_{ref_feat}.png"
                    if ref_path.exists():
                        shutil.copy2(ref_path, out_path)
                        print(f"    [copy] {feature}")
                        captured += 1
                        break
            continue

        if pattern:
            # Search headings for this pattern
            js = f"""() => {{
                var headings = document.querySelectorAll('h2, h3, h4, a, span');
                var re = /{pattern}/i;
                for (var h of headings) {{
                    if (h.closest('nav, header, [role="navigation"]')) continue;
                    var t = (h.textContent || '').toLowerCase();
                    if (re.test(t)) {{
                        var absY = h.getBoundingClientRect().top + window.scrollY;
                        if (absY > 200) {{
                            var section = h.closest('section, div[class]') || h;
                            var r = section.getBoundingClientRect();
                            return {{x: Math.round(r.x), y: Math.round(r.top + window.scrollY), w: Math.round(Math.min(r.width, 1400)), h: Math.round(Math.min(r.height, 800))}};
                        }}
                    }}
                }}
                return null;
            }}"""
            el = safe_eval(page, js)
            if el and el["w"] > 5 and el["h"] > 5:
                pad = 15
                if safe_screenshot(page, out_path, {
                    "x": max(0, el["x"]-pad), "y": max(0, el["y"]-pad),
                    "width": el["w"]+2*pad, "height": el["h"]+2*pad
                }):
                    print(f"    [js] {feature} ({el['w']}x{el['h']} @ y:{el['y']})")
                    captured += 1
                    continue

        # Special: app_store_badges
        if feature == "app_store_badges":
            el = safe_eval(page, """() => {
                var els = document.querySelectorAll('a[href*="apps.apple"], a[href*="play.google"]');
                if (els.length > 0) {
                    var c = els[0].closest('div') || els[0].parentElement;
                    var r = c.getBoundingClientRect();
                    return {x: Math.round(r.x), y: Math.round(r.top+window.scrollY), w: Math.round(r.width), h: Math.round(r.height)};
                }
                return null;
            }""")
            if el:
                if safe_screenshot(page, out_path, {"x": max(0, el["x"]-10), "y": max(0, el["y"]-10), "width": max(el["w"]+20, 300), "height": el["h"]+20}):
                    print(f"    [js] app_store_badges")
                    captured += 1
                    continue

        # Special: social_links_in_footer
        if feature == "social_links_in_footer":
            el = safe_eval(page, """() => {
                var footer = document.querySelector('footer') || document.body;
                var socials = footer.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"]');
                if (socials.length >= 2) {
                    var c = socials[0].closest('div, ul, nav') || socials[0].parentElement;
                    var r = c.getBoundingClientRect();
                    return {x: Math.round(r.x), y: Math.round(r.top+window.scrollY), w: Math.round(r.width), h: Math.round(r.height)};
                }
                return null;
            }""")
            if el:
                if safe_screenshot(page, out_path, {"x": max(0, el["x"]-10), "y": max(0, el["y"]-10), "width": max(el["w"]+20, 300), "height": el["h"]+20}):
                    print(f"    [js] social_links_in_footer")
                    captured += 1
                    continue

        if feature not in LIVERPOOL_SECTIONS:
            print(f"    [SKIP] {feature}")

    return captured


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        # === PSG ===
        print(f"\n{'='*60}")
        print("CLUB: psg (https://www.psg.fr/en)")
        print(f"{'='*60}")

        page.goto("https://www.psg.fr/en", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # Didomi consent
        for _ in range(3):
            safe_eval(page, """() => {
                try { document.querySelector('button.didomi-dismiss-button, #didomi-notice-agree-button').click(); } catch(e) {}
                try { document.querySelectorAll('[class*="consent"], [class*="cookie"], [role="dialog"]').forEach(e => { try { e.remove(); } catch(ex) {} }); } catch(e) {}
            }""")
            time.sleep(2)

        # Scroll to lazy-load
        h = safe_eval(page, "document.body.scrollHeight") or 2000
        for i in range(1, 9):
            safe_eval(page, f"window.scrollTo(0, {h * i // 8})")
            time.sleep(0.6)
        safe_eval(page, "window.scrollTo(0, 0)")
        time.sleep(2)

        final_h = safe_eval(page, "document.body.scrollHeight") or 0
        print(f"  Page height: {final_h}px")

        if final_h > 3000:
            # Update section positions from live page
            sections = safe_eval(page, """() => {
                var s = {};
                document.querySelectorAll('h2, h3, h4').forEach(function(el) {
                    if (el.closest('nav, header')) return;
                    var txt = (el.innerText || '').trim().substring(0,50);
                    if (txt.length > 2) s[txt] = Math.round(el.getBoundingClientRect().top + window.scrollY);
                });
                return s;
            }""") or {}
            print(f"  Sections: {json.dumps(sections)[:300]}")

            # Update PSG_SECTIONS with live positions
            for key, pos in sections.items():
                kl = key.lower()
                if 'fixture' in kl:
                    PSG_SECTIONS["next_match_block"] = {"y": pos, "h": 350}
                elif 'news' == kl or 'news' in kl.split():
                    PSG_SECTIONS["dedicated_news_section"] = {"y": pos, "h": 500}
                elif 'interview' in kl or 'post game' in kl:
                    PSG_SECTIONS["press_conference_block"] = {"y": pos, "h": 400}
                    PSG_SECTIONS["homepage_video_block"] = {"y": pos, "h": 400}
                elif 'psg tv' in kl:
                    PSG_SECTIONS["homepage_video_block"] = {"y": pos, "h": 400}
                elif 'podcast' in kl:
                    PSG_SECTIONS["podcast_audio"] = {"y": pos, "h": 300}
                elif 'women' in kl:
                    PSG_SECTIONS["womens_team_featured"] = {"y": pos, "h": 250}
                elif 'stadium' in kl or 'tour' in kl:
                    PSG_SECTIONS["stadium_tours_block"] = {"y": pos, "h": 300}
                elif 'communit' in kl:
                    PSG_SECTIONS["charity_csr_block"] = {"y": pos, "h": 300}

            psg_count = capture_psg(page)
            print(f"  ✅ PSG: {psg_count} captured")
        else:
            print(f"  ❌ PSG page too short ({final_h}px)")

        # === Liverpool ===
        print(f"\n{'='*60}")
        print("CLUB: liverpool (https://www.liverpoolfc.com)")
        print(f"{'='*60}")

        page.goto("https://www.liverpoolfc.com", wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # Cookie handling
        for _ in range(5):
            safe_eval(page, """() => {
                try {
                    var btns = document.querySelectorAll('button, a, [role="button"]');
                    for (var b of btns) {
                        try {
                            var txt = (b.textContent || '').toLowerCase().trim();
                            if (txt.includes('accept') || txt.includes('agree') || txt.includes('ok') || txt.includes('got it')) {
                                b.click(); return true;
                            }
                        } catch(ex) {}
                    }
                } catch(e) {}
                try { document.querySelectorAll('[class*="consent"], [class*="cookie"], [role="dialog"]').forEach(e => { try { e.remove(); } catch(ex) {} }); } catch(e) {}
                try { document.body.style.overflow = 'auto'; document.documentElement.style.overflow = 'auto'; } catch(e) {}
                return false;
            }""")
            time.sleep(2)

        h = safe_eval(page, "document.body.scrollHeight") or 2000
        for i in range(1, 9):
            safe_eval(page, f"window.scrollTo(0, {h * i // 8})")
            time.sleep(0.6)
        safe_eval(page, "window.scrollTo(0, 0)")
        time.sleep(2)

        final_h = safe_eval(page, "document.body.scrollHeight") or 0
        print(f"  Page height: {final_h}px")

        if final_h > 2000:
            lfc_count = capture_liverpool(page)
            print(f"  ✅ Liverpool: {lfc_count} captured")
        else:
            print(f"  ❌ Liverpool page too short ({final_h}px) — capturing what we can")
            lfc_count = capture_liverpool(page)
            print(f"  Liverpool: {lfc_count} captured")

        context.close()
        browser.close()

    print(f"\nDone!")


if __name__ == "__main__":
    main()
