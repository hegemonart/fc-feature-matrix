#!/usr/bin/env python3
"""
Re-capture broken/incorrect screenshots with manual positions.
Uses full_page=True screenshots and known element positions from the live cross-check.
"""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).resolve().parent.parent / "crosscheck" / "img"

# Manual fixes: (club_id, feature_key, url, scroll_to_y, clip)
# clip = {x, y, width, height} in absolute page coords
FIXES = [
    # Chelsea: store_block — need to show products, not just heading
    ("chelsea", "store_block", "https://www.chelseafc.com", {
        "scroll_y": 2300,
        "clip": {"x": 0, "y": 2300, "width": 1400, "height": 600},
    }),
    # Chelsea: store_individual_products — same section with products
    ("chelsea", "store_individual_products", "https://www.chelseafc.com", {
        "scroll_y": 2300,
        "clip": {"x": 0, "y": 2300, "width": 1400, "height": 600},
    }),
    # Chelsea: womens_team_featured — need to show actual women's content, not just toggle
    ("chelsea", "womens_team_featured", "https://www.chelseafc.com", {
        "scroll_y": 0,
        # The Women's toggle is at y:293 in standings; let's capture the relevant area
        "js_find": """() => {
            // Find "Women's" text and its context
            const links = document.querySelectorAll('a');
            for (const a of links) {
                const t = (a.textContent || '').trim();
                if (t === "Women's" || t === "WOMEN'S TEAM") {
                    const rect = a.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (absY < 300) {
                        // It's the nav link, check for the standings women's section
                        continue;
                    }
                }
            }
            // Check for women's team article/card
            const articles = document.querySelectorAll('article, a, div');
            for (const el of articles) {
                const t = (el.textContent || '').trim().toLowerCase();
                if ((t.includes('women') || t.includes("wsl")) && t.length < 200) {
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (absY > 500 && rect.height > 40) {
                        return {x: Math.max(0, rect.x - 10), y: absY - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 200, "width": 1400, "height": 200},  # fallback
    }),
    # Chelsea: next_match_block — the matches section
    ("chelsea", "next_match_block", "https://www.chelseafc.com", {
        "js_find": """() => {
            const headings = document.querySelectorAll('h2, h3, h4');
            for (const h of headings) {
                const t = h.textContent.trim().toLowerCase();
                if (t.includes('fixture') || t.includes('match') || t.includes('schedule') || t.includes('game')) {
                    const section = h.closest('section') || h.parentElement;
                    const rect = section.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    return {x: 0, y: absY - 10, w: 1400, h: Math.min(rect.height + 20, 700)};
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 3500, "width": 1400, "height": 600},  # fallback
    }),
    # Chelsea: next_match_feature_rich — same as next_match_block
    ("chelsea", "next_match_feature_rich", "https://www.chelseafc.com", {
        "same_as": "chelsea_next_match_block",
    }),
    # FC Barcelona: fan_club_signup — Penyes/fan club section
    ("fc_barcelona", "fan_club_signup", "https://www.fcbarcelona.com/en", {
        "js_find": """() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim().toLowerCase();
                if (t.includes('penyes') || t.includes('fan club') || t.includes('culer') || t.includes('member')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 300) {
                        const el = walker.currentNode.parentElement.closest('section, div[class], a');
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            const ey = rect.top + window.scrollY;
                            return {x: Math.max(0, rect.x - 10), y: ey - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                        }
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 900, "width": 1400, "height": 400},  # fallback
    }),
    # FC Barcelona: museum_block — Museu/Museum section
    ("fc_barcelona", "museum_block", "https://www.fcbarcelona.com/en", {
        "js_find": """() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim().toLowerCase();
                if (t.includes('museum') || t.includes('museu') || t.includes('museo')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, a, div[class]');
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            const ey = rect.top + window.scrollY;
                            return {x: Math.max(0, rect.x - 10), y: ey - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                        }
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 700, "width": 1400, "height": 400},  # fallback
    }),
    # FC Barcelona: stadium_content_block
    ("fc_barcelona", "stadium_content_block", "https://www.fcbarcelona.com/en", {
        "js_find": """() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim().toLowerCase();
                if (t.includes('spotify camp nou') || t.includes('camp nou') || t.includes('stadium') || t.includes('estadi')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, a, div[class]');
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            const ey = rect.top + window.scrollY;
                            return {x: Math.max(0, rect.x - 10), y: ey - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                        }
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 750, "width": 1400, "height": 400},  # fallback
    }),
    # FC Barcelona: tickets_shortcut_in_header
    ("fc_barcelona", "tickets_shortcut_in_header", "https://www.fcbarcelona.com/en", {
        "scroll_y": 0,
        "clip": {"x": 0, "y": 0, "width": 1400, "height": 100},
    }),
    # FC Barcelona: womens_team_featured
    ("fc_barcelona", "womens_team_featured", "https://www.fcbarcelona.com/en", {
        "js_find": """() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim().toLowerCase();
                if ((t.includes('femen') || t.includes('women') || t.includes('wch')) && t.length < 100) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, a, article, div[class]');
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            const ey = rect.top + window.scrollY;
                            if (rect.height > 20 && rect.height < 800) return {x: Math.max(0, rect.x - 10), y: ey - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                        }
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 1100, "width": 1400, "height": 400},  # fallback
    }),
    # Arsenal: dedicated_news_section — need to find actual news content, not hero
    ("arsenal", "dedicated_news_section", "https://www.arsenal.com", {
        "js_find": """() => {
            const articles = document.querySelectorAll('article, [class*="article"], [class*="Article"]');
            if (articles.length > 2) {
                // Find a cluster of articles below the hero
                for (const a of articles) {
                    const absY = a.getBoundingClientRect().top + window.scrollY;
                    if (absY > 500) {
                        const parent = a.closest('section') || a.parentElement;
                        const rect = parent.getBoundingClientRect();
                        const py = rect.top + window.scrollY;
                        return {x: 0, y: py - 10, w: 1400, h: Math.min(rect.height + 20, 700)};
                    }
                }
            }
            // Try heading-based
            const headings = document.querySelectorAll('h2, h3');
            for (const h of headings) {
                const t = h.textContent.trim().toLowerCase();
                if (t.includes('latest') || t.includes('news') || t.includes('stories')) {
                    const section = h.closest('section') || h.parentElement;
                    const rect = section.getBoundingClientRect();
                    const ey = rect.top + window.scrollY;
                    return {x: 0, y: ey - 10, w: 1400, h: Math.min(rect.height + 20, 700)};
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 1400, "width": 1400, "height": 600},  # fallback
    }),
    # Arsenal: news_rich_structure — same as news section
    ("arsenal", "news_rich_structure", "https://www.arsenal.com", {
        "same_as": "arsenal_dedicated_news_section",
    }),
    # Arsenal: quiz_trivia — need actual quiz content
    ("arsenal", "quiz_trivia", "https://www.arsenal.com", {
        "js_find": """() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim().toLowerCase();
                if (t.includes('quiz') || t.includes('trivia') || t.includes('predict') || t.includes('test your knowledge')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 300) {
                        const el = walker.currentNode.parentElement.closest('section, a, article, div[class]');
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            const ey = rect.top + window.scrollY;
                            if (rect.height > 30) return {x: Math.max(0, rect.x - 10), y: ey - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                        }
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 3000, "width": 1400, "height": 500},  # fallback
    }),
    # Arsenal: womens_team_featured
    ("arsenal", "womens_team_featured", "https://www.arsenal.com", {
        "js_find": """() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim().toLowerCase();
                if ((t.includes('women') || t.includes('wsl') || t.includes('arsenal women')) && t.length < 100) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, a, article, div[class]');
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            const ey = rect.top + window.scrollY;
                            if (rect.height > 30 && rect.height < 800) return {x: Math.max(0, rect.x - 10), y: ey - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                        }
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 2000, "width": 1400, "height": 500},  # fallback
    }),
    # Arsenal: charity_csr_block
    ("arsenal", "charity_csr_block", "https://www.arsenal.com", {
        "js_find": """() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = walker.currentNode.textContent.trim().toLowerCase();
                if (t.includes('foundation') || t.includes('community') || t.includes('charity')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, a, article, div[class]');
                        if (el) {
                            const rect = el.getBoundingClientRect();
                            const ey = rect.top + window.scrollY;
                            if (rect.height > 30 && rect.height < 800) return {x: Math.max(0, rect.x - 10), y: ey - 10, w: Math.min(rect.width + 20, 1400), h: Math.min(rect.height + 20, 500)};
                        }
                    }
                }
            }
            return null;
        }""",
        "clip": {"x": 0, "y": 4000, "width": 1400, "height": 500},  # fallback
    }),
    # Arsenal: footer_sponsor_wall
    ("arsenal", "footer_sponsor_wall", "https://www.arsenal.com", {
        "js_find": """() => {
            const imgs = document.querySelectorAll('img');
            const bottom = [];
            for (const i of imgs) {
                const absY = i.getBoundingClientRect().top + window.scrollY;
                const h = document.body.scrollHeight;
                if (absY > h * 0.6 && i.naturalWidth > 20 && i.naturalHeight > 10) {
                    bottom.push(i);
                }
            }
            if (bottom.length >= 3) {
                const parent = bottom[0].closest('section, div[class], ul');
                if (parent) {
                    const rect = parent.getBoundingClientRect();
                    const ey = rect.top + window.scrollY;
                    return {x: 0, y: ey - 10, w: 1400, h: Math.min(rect.height + 20, 500)};
                }
            }
            return null;
        }""",
        "scroll_y": 99999,  # scroll to bottom
        "clip": {"x": 0, "y": 6000, "width": 1400, "height": 400},  # fallback
    }),
    # Arsenal: social_links_in_footer
    ("arsenal", "social_links_in_footer", "https://www.arsenal.com", {
        "js_find": """() => {
            const socials = document.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"]');
            const footerSocials = Array.from(socials).filter(a => {
                const absY = a.getBoundingClientRect().top + window.scrollY;
                return absY > document.body.scrollHeight * 0.7;
            });
            if (footerSocials.length >= 2) {
                const parent = footerSocials[0].closest('div[class], ul, nav');
                if (parent) {
                    const rect = parent.getBoundingClientRect();
                    const ey = rect.top + window.scrollY;
                    return {x: Math.max(0, rect.x - 20), y: ey - 10, w: Math.min(rect.width + 40, 1400), h: Math.min(rect.height + 20, 200)};
                }
            }
            return null;
        }""",
        "scroll_y": 99999,
        "clip": {"x": 0, "y": 7000, "width": 1400, "height": 200},  # fallback
    }),
    # FC Barcelona: app_store_badges
    ("fc_barcelona", "app_store_badges", "https://www.fcbarcelona.com/en", {
        "js_find": """() => {
            const els = document.querySelectorAll('a[href*="apps.apple"], a[href*="play.google"], img[alt*="App Store"], img[alt*="Google Play"], img[alt*="app"], [class*="download"], [class*="Download"]');
            for (const el of els) {
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (rect.height > 10 && absY > 200) {
                    const parent = el.closest('div[class], section');
                    if (parent) {
                        const prect = parent.getBoundingClientRect();
                        const py = prect.top + window.scrollY;
                        return {x: Math.max(0, prect.x - 10), y: py - 10, w: Math.min(prect.width + 20, 1400), h: Math.min(prect.height + 20, 400)};
                    }
                    return {x: Math.max(0, rect.x - 20), y: absY - 10, w: Math.min(rect.width + 40, 600), h: rect.height + 20};
                }
            }
            return null;
        }""",
        "scroll_y": 99999,
        "clip": {"x": 0, "y": 6000, "width": 1400, "height": 400},  # fallback
    }),
]


def capture_fix(page, club_id, feature_key, config):
    """Capture a specific screenshot fix."""
    out_path = IMG_DIR / f"{club_id}_{feature_key}.png"

    # Handle same_as reference
    if "same_as" in config:
        ref_path = IMG_DIR / f"{config['same_as']}.png"
        if ref_path.exists():
            import shutil
            shutil.copy2(ref_path, out_path)
            print(f"  [copy] {club_id}_{feature_key} (same as {config['same_as']})")
            return True

    # Scroll to position
    scroll_y = config.get("scroll_y", 0)
    if scroll_y == 99999:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    else:
        page.evaluate(f"window.scrollTo(0, {scroll_y})")
    time.sleep(1.5)

    # Try JS-based element finding
    js_find = config.get("js_find")
    if js_find:
        try:
            result = page.evaluate(js_find)
            if result:
                clip = {
                    "x": max(0, result["x"]),
                    "y": max(0, result["y"]),
                    "width": min(result["w"], 1400),
                    "height": min(result["h"], 800),
                }
                page.screenshot(path=str(out_path), clip=clip, full_page=True)
                print(f"  [js] {club_id}_{feature_key} ({int(clip['width'])}x{int(clip['height'])} @ y:{int(clip['y'])})")
                return True
        except Exception as e:
            print(f"  [js-err] {club_id}_{feature_key}: {e}")

    # Fallback to fixed clip
    clip = config.get("clip")
    if clip:
        try:
            page.screenshot(path=str(out_path), clip=clip, full_page=True)
            print(f"  [fallback] {club_id}_{feature_key}")
            return True
        except Exception as e:
            print(f"  [error] {club_id}_{feature_key}: {e}")
            return False

    print(f"  [SKIP] {club_id}_{feature_key}")
    return False


def main():
    # Group fixes by URL
    url_groups = {}
    for club_id, feature_key, url, config in FIXES:
        if url not in url_groups:
            url_groups[url] = []
        url_groups[url].append((club_id, feature_key, config))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = context.new_page()

        for url, fixes in url_groups.items():
            print(f"\n--- {url} ---")
            page.goto(url, wait_until="networkidle", timeout=30000)
            time.sleep(3)

            # Dismiss cookies
            try:
                page.evaluate("""() => {
                    const btns = document.querySelectorAll('button, a, [role="button"]');
                    const priorities = ['accept all', 'accept', 'agree', 'consent', 'got it',
                        'reject all', 'decline', 'deny all', 'acepto', 'aceptar'];
                    for (const p of priorities) {
                        for (const b of btns) {
                            if ((b.textContent || '').toLowerCase().trim().includes(p)) { b.click(); return; }
                        }
                    }
                    if (window.__cmp) window.__cmp('setConsent', 0);
                }""")
                time.sleep(1)
            except:
                pass

            # Scroll to trigger lazy loading
            page_height = page.evaluate("document.body.scrollHeight")
            for i in range(1, 6):
                page.evaluate(f"window.scrollTo(0, {page_height * i // 5})")
                time.sleep(0.8)
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(2)

            for club_id, feature_key, config in fixes:
                capture_fix(page, club_id, feature_key, config)

        context.close()
        browser.close()

    print("\nDone!")


if __name__ == "__main__":
    main()
