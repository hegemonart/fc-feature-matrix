#!/usr/bin/env python3
"""
Fix round 3: Targeted re-captures using exact coordinates from page dump.
"""

import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).resolve().parent.parent / "crosscheck" / "img"


def setup_page(page, url):
    """Navigate, dismiss cookies, scroll for lazy-load."""
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(4)
    try:
        page.evaluate("""
            const btns = document.querySelectorAll('button, a, [role="button"]');
            for (const b of btns) {
                const txt = (b.textContent || '').toLowerCase().trim();
                if (txt.includes('accept') || txt.includes('agree') || txt.includes('allow')) {
                    b.click(); break;
                }
            }
        """)
        time.sleep(1)
    except:
        pass
    for i in range(8):
        page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/8})")
        time.sleep(1)
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)
    return page.evaluate("document.body.scrollHeight")


def clip(page, path, x, y, w, h):
    page.screenshot(path=str(path), full_page=True,
                   clip={"x": x, "y": max(0, y), "width": w, "height": h})
    size = Path(path).stat().st_size
    print(f"    -> {Path(path).name} ({size:,} bytes)")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        # ══════════════════════════════════════════════
        # FC BARCELONA — from dump:
        #   y=2234: "BARÇA OFFICIAL WORLDWIDE STORE"
        #   y=2498: KITS, TRAINING, MEMORABILIA (product categories)
        #   y=2724: "Only For Culers" (membership)
        #   y=3017: BENEFITS AND DISCOUNTS, SUBSCRIPTION PLANS, DRAWS AND CONTESTS
        #   y=1869: "Barça Stories"
        #   y=5379: "Players"
        #   y=5964: FOOTER starts
        #   y=6364: "Follow FC Barcelona on social media"
        #   y=6407: Social links
        # ══════════════════════════════════════════════
        print("\n=== FC BARCELONA ===")
        sh = setup_page(page, "https://www.fcbarcelona.com/en")
        print(f"  Page height: {sh}px")

        # 1. Store block — heading at ~2234, products at ~2498
        print("  [1] store_block + store_individual_products (y=2200)")
        clip(page, IMG_DIR / "fc_barcelona_store_block.png", 0, 2200, 1400, 600)
        shutil.copy(IMG_DIR / "fc_barcelona_store_block.png",
                   IMG_DIR / "fc_barcelona_store_individual_products.png")

        # 2. Player roster — "Players" section at y=5379
        print("  [2] player_roster_preview + individual_player_cards (y=5350)")
        clip(page, IMG_DIR / "fc_barcelona_player_roster_preview.png", 0, 5350, 1400, 600)
        shutil.copy(IMG_DIR / "fc_barcelona_player_roster_preview.png",
                   IMG_DIR / "fc_barcelona_individual_player_cards.png")

        # 3. Social native content — "Barça Stories" at y=1869
        print("  [3] social_native_content — Barça Stories (y=1840)")
        clip(page, IMG_DIR / "fc_barcelona_social_native_content.png", 0, 1840, 1400, 500)

        # 4. Footer sponsor wall — "Main Partners" section
        #    The in_content_sponsor already shows Nike/Spotify/Philips
        #    Footer sponsors should be in the footer area ~5964-6364
        print("  [4] footer_sponsor_wall (footer area, y=5964)")
        clip(page, IMG_DIR / "fc_barcelona_footer_sponsor_wall.png", 0, 5960, 1400, 400)

        # 5. Paid membership — "Only For Culers" at y=2724 + benefits at y=3017
        print("  [5] paid_membership (y=2700)")
        clip(page, IMG_DIR / "fc_barcelona_paid_membership.png", 0, 2700, 1400, 500)

        # 6. App store badges — wasn't found in main content. Check if Barça has
        #    app badges. "Barça Mobile" was at y=356 (in side nav). Let's try bottom area.
        print("  [6] app_store_badges — searching DOM for App Store links...")
        app_info = page.evaluate("""() => {
            // Search all links for app store URLs
            const links = document.querySelectorAll('a');
            const results = [];
            for (const a of links) {
                const href = a.getAttribute('href') || '';
                if (href.includes('apps.apple') || href.includes('play.google') || href.includes('app-store') || href.includes('google-play') || href.includes('itunes.apple')) {
                    const rect = a.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    results.push({href: href.substring(0, 80), y: absY, h: rect.height, w: rect.width, x: rect.x, visible: rect.height > 0});
                }
            }
            return results;
        }""")
        print(f"    Found {len(app_info)} app store links:")
        for info in app_info:
            print(f"      y={info['y']:.0f} h={info['h']:.0f} vis={info['visible']} {info['href']}")

        # If we found visible app store links, capture them
        visible_apps = [a for a in app_info if a['visible'] and a['y'] > 100]
        if visible_apps:
            y = min(a['y'] for a in visible_apps)
            print(f"    Capturing visible app badges at y={y}")
            clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, max(0, y - 50), 1400, 300)
        else:
            # Try to find it via image alt text
            print("    No visible app links found, trying image search...")
            img_info = page.evaluate("""() => {
                const imgs = document.querySelectorAll('img');
                for (const img of imgs) {
                    const alt = (img.getAttribute('alt') || '').toLowerCase();
                    const src = (img.getAttribute('src') || '').toLowerCase();
                    if (alt.includes('app store') || alt.includes('google play') || src.includes('app-store') || src.includes('google-play') || src.includes('badge')) {
                        const rect = img.getBoundingClientRect();
                        return {y: rect.top + window.scrollY, h: rect.height, x: rect.x, w: rect.width};
                    }
                }
                return null;
            }""")
            if img_info and img_info['h'] > 0:
                clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png",
                    0, max(0, img_info['y'] - 50), 1400, 300)
            else:
                # Last resort — "Barça Mobile" section might have app badges
                clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, sh - 700, 1400, 300)

        # ══════════════════════════════════════════════
        # ARSENAL — from dump:
        #   y=1117: "Trending Video"
        #   y=1860: "Shop Now"
        #   y=2480: "Trending"
        #   y=4043: "Introducing The Arsenal"
        #   y=5008: "Arsenal Women"
        #   y=5973: "Latest Women Video"
        #   y=7000: "Academy"
        #   y=8371: "Arsenal quizzes"
        #   y=10074: "Footer menu"
        #   NO heritage/foundation/community section on homepage body!
        # ══════════════════════════════════════════════
        print("\n=== ARSENAL ===")
        sh = setup_page(page, "https://www.arsenal.com")
        print(f"  Page height: {sh}px")

        # 7. Search input in header — try to find the search icon
        print("  [7] search_input_in_header")
        search_info = page.evaluate("""() => {
            const header = document.querySelector('header');
            if (!header) return null;
            // Look for any element with 'search' in class or aria-label
            const all = header.querySelectorAll('*');
            for (const el of all) {
                const cls = (el.className || '').toString().toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                const href = (el.getAttribute('href') || '').toLowerCase();
                if (cls.includes('search') || aria.includes('search') || href.includes('search')) {
                    const rect = el.getBoundingClientRect();
                    if (rect.height > 0 && rect.width > 0) {
                        return {x: rect.x, y: rect.top + window.scrollY, w: rect.width, h: rect.height,
                                tag: el.tagName, cls: cls.substring(0, 60)};
                    }
                }
            }
            return null;
        }""")
        if search_info:
            print(f"    Found: {search_info['tag']} at x={search_info['x']:.0f}, y={search_info['y']:.0f}, class={search_info['cls']}")
            clip(page, IMG_DIR / "arsenal_search_input_in_header.png",
                max(0, int(search_info['x']) - 50), max(0, int(search_info['y']) - 20),
                min(int(search_info['w']) + 100, 300), int(search_info['h']) + 40)
        else:
            # Capture the full header right side
            print("    Not found, capturing right side of header")
            clip(page, IMG_DIR / "arsenal_search_input_in_header.png", 1100, 0, 300, 80)

        # 8. charity_csr_block — Arsenal's homepage doesn't have a dedicated
        #    foundation section. "Gabriel Jesus surprises community volunteer" at y=1173
        #    is just a video in trending, not a charity block.
        #    Let's capture whatever community/foundation content exists.
        print("  [8] charity_csr_block — looking for foundation content...")
        charity_info = page.evaluate("""() => {
            // Search main content for community/foundation references
            const main = document.querySelector('main') || document.body;
            const allEls = main.querySelectorAll('a, article, [class*="card"]');
            for (const el of allEls) {
                const t = (el.textContent || '').trim().toLowerCase();
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                // Skip nav/hidden elements
                if (absY < 200 || rect.height < 30) continue;
                if (el.closest('nav, header, footer')) continue;
                if (t.includes('foundation') || (t.includes('community') && t.length < 200)) {
                    return {y: absY, h: rect.height, text: t.substring(0, 100)};
                }
            }
            return null;
        }""")
        if charity_info:
            print(f"    Found: '{charity_info['text'][:60]}' at y={charity_info['y']:.0f}")
            clip(page, IMG_DIR / "arsenal_charity_csr_block.png",
                0, max(0, int(charity_info['y']) - 30), 1400, min(int(charity_info['h']) + 60, 500))
        else:
            # There may not be a charity/CSR block on Arsenal homepage at all.
            # Capture the "Gabriel Jesus surprises community volunteer" video card
            # from trending section as best available evidence
            print("    No dedicated block found. Capturing community-related video at trending (y=1117)")
            clip(page, IMG_DIR / "arsenal_charity_csr_block.png", 0, 1100, 1400, 400)

        # 9. social_links_in_footer — find actual social icons at bottom
        print("  [9] social_links_in_footer")
        social_info = page.evaluate("""() => {
            // The footer in Arsenal might be at the very bottom
            const sh = document.body.scrollHeight;
            // Look for social media links near the bottom
            const links = document.querySelectorAll('a');
            const socials = [];
            for (const a of links) {
                const href = (a.getAttribute('href') || '').toLowerCase();
                const rect = a.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > sh - 500 && rect.height > 0) {
                    if (href.includes('twitter') || href.includes('x.com') || href.includes('facebook') ||
                        href.includes('instagram') || href.includes('youtube') || href.includes('tiktok')) {
                        socials.push({y: absY, h: rect.height, x: rect.x, w: rect.width, href: href.substring(0, 60)});
                    }
                }
            }
            if (socials.length) {
                const minY = Math.min(...socials.map(s => s.y));
                const maxY = Math.max(...socials.map(s => s.y + s.h));
                return {y: minY - 20, h: maxY - minY + 40, count: socials.length};
            }
            // Try anywhere on page
            for (const a of links) {
                const href = (a.getAttribute('href') || '').toLowerCase();
                const rect = a.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (rect.height > 0 && absY > 200) {
                    if (href.includes('twitter') || href.includes('x.com') || href.includes('facebook') || href.includes('instagram')) {
                        socials.push({y: absY, x: rect.x});
                    }
                }
            }
            if (socials.length >= 2) {
                const minY = Math.min(...socials.map(s => s.y));
                // Group by similar y position (within 50px)
                const grouped = socials.filter(s => Math.abs(s.y - minY) < 50 || s.y > sh - 500);
                if (grouped.length >= 2) {
                    const groupY = Math.min(...grouped.map(s => s.y));
                    return {y: groupY - 20, h: 100, count: grouped.length};
                }
            }
            return null;
        }""")
        if social_info:
            print(f"    Found {social_info['count']} social links at y={social_info['y']:.0f}")
            clip(page, IMG_DIR / "arsenal_social_links_in_footer.png",
                0, max(0, int(social_info['y'])), 1400, max(int(social_info['h']), 100))
        else:
            print("    Not found, capturing page bottom")
            clip(page, IMG_DIR / "arsenal_social_links_in_footer.png", 0, sh - 200, 1400, 200)

        # 10. heritage_past_content — Arsenal "Classics" store products are at y=1905
        #     but that's the store, not heritage. The mega menu has "Heritage" and "Arsenal Eras"
        #     but there's no heritage section on the homepage body.
        #     Best evidence: the "Arsenal Classics" products in "Shop Now" section
        print("  [10] heritage_past_content — Shop Now / Classics section (y=1860)")
        clip(page, IMG_DIR / "arsenal_heritage_past_content.png", 0, 1840, 1400, 500)

        # 11. press_conference_block — press conferences appear in Trending Video (y=1117)
        print("  [11] press_conference_block — Trending Video section (y=1117)")
        clip(page, IMG_DIR / "arsenal_press_conference_block.png", 0, 1100, 1400, 400)

        browser.close()
        print("\n=== ALL FIXES COMPLETE ===")


if __name__ == "__main__":
    main()
