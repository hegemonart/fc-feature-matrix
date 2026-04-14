#!/usr/bin/env python3
"""
Fix round 2: Re-capture broken/incorrect screenshots.
Step 1: Dump section positions from each page.
Step 2: Capture specific regions with known coordinates.
"""

import time
import json
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).resolve().parent.parent / "crosscheck" / "img"


def setup_page(page, url):
    """Navigate, dismiss cookies, scroll for lazy-load, return scroll height."""
    page.goto(url, wait_until="domcontentloaded")
    time.sleep(4)

    # Dismiss cookies
    try:
        page.evaluate("""
            const btns = document.querySelectorAll('button, a, [role="button"]');
            for (const b of btns) {
                const txt = (b.textContent || '').toLowerCase().trim();
                if (txt.includes('accept') || txt.includes('agree') || txt.includes('consent') || txt.includes('allow')) {
                    b.click(); break;
                }
            }
        """)
        time.sleep(1)
    except:
        pass

    # Scroll to trigger lazy loading
    for i in range(8):
        page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/8})")
        time.sleep(1)
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    return page.evaluate("document.body.scrollHeight")


def dump_sections(page):
    """Get all section headings with absolute Y positions."""
    return page.evaluate("""() => {
        const results = [];
        const visited = new Set();

        // Get ALL text blocks with positions
        const els = document.querySelectorAll('h1, h2, h3, h4, h5, [class*="title"], [class*="heading"], [class*="section-title"]');
        for (const el of els) {
            const t = el.textContent.trim().substring(0, 120);
            if (!t || visited.has(t)) continue;
            visited.add(t);
            const rect = el.getBoundingClientRect();
            const absY = Math.round(rect.top + window.scrollY);
            results.push({text: t, y: absY, h: Math.round(rect.height), tag: el.tagName});
        }

        // Also get links with specific keywords
        const links = document.querySelectorAll('a');
        for (const a of links) {
            const t = a.textContent.trim().substring(0, 80).toLowerCase();
            const rect = a.getBoundingClientRect();
            const absY = Math.round(rect.top + window.scrollY);
            if (absY > 200 && (t.includes('foundation') || t.includes('community') || t.includes('heritage') || t.includes('classic') || t.includes('press conference'))) {
                results.push({text: a.textContent.trim().substring(0, 120), y: absY, h: Math.round(rect.height), tag: 'A-keyword'});
            }
        }

        // Footer position
        const footer = document.querySelector('footer');
        if (footer) {
            const rect = footer.getBoundingClientRect();
            results.push({text: '--- FOOTER ---', y: Math.round(rect.top + window.scrollY), h: Math.round(rect.height), tag: 'FOOTER'});
        }

        // Social links in footer
        if (footer) {
            const socials = footer.querySelectorAll('a[href*="twitter"], a[href*="facebook"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"]');
            if (socials.length) {
                const parent = socials[0].closest('div, ul, nav') || socials[0].parentElement;
                const rect = parent.getBoundingClientRect();
                results.push({text: '--- SOCIAL LINKS ---', y: Math.round(rect.top + window.scrollY), h: Math.round(rect.height), tag: 'SOCIAL', x: Math.round(rect.x), w: Math.round(rect.width)});
            }
        }

        // App store badges
        const appLinks = document.querySelectorAll('a[href*="apps.apple"], a[href*="play.google"]');
        if (appLinks.length) {
            const parent = appLinks[0].closest('section, div') || appLinks[0].parentElement;
            const rect = parent.getBoundingClientRect();
            results.push({text: '--- APP BADGES ---', y: Math.round(rect.top + window.scrollY), h: Math.round(rect.height), tag: 'APP'});
        }

        // Partner/sponsor sections
        const allEls = document.querySelectorAll('*');
        for (const el of allEls) {
            if (el.children.length < 3) continue;
            const t = el.textContent.trim().toLowerCase().substring(0, 100);
            if ((t.includes('partner') || t.includes('sponsor')) && el.querySelectorAll('img').length >= 3) {
                const rect = el.getBoundingClientRect();
                const absY = Math.round(rect.top + window.scrollY);
                if (absY > 1000 && rect.height > 50 && rect.height < 600) {
                    results.push({text: '--- SPONSOR WALL ---', y: absY, h: Math.round(rect.height), tag: 'SPONSORS'});
                    break;
                }
            }
        }

        return results.sort((a, b) => a.y - b.y);
    }""")


def capture_clip(page, path, x, y, w, h):
    """Capture a clipped region of the full page."""
    page.screenshot(path=str(path), full_page=True,
                   clip={"x": x, "y": max(0, y), "width": w, "height": h})


def capture_fixes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        # ══════════════════════════════════════════════
        # FC BARCELONA
        # ══════════════════════════════════════════════
        print("\n=== FC BARCELONA ===")
        sh = setup_page(page, "https://www.fcbarcelona.com/en")
        print(f"  Page height: {sh}px")

        sections = dump_sections(page)
        print("  Page sections:")
        for s in sections:
            print(f"    y={s['y']:>5}  h={s['h']:>4}  [{s['tag']:>10}]  {s['text'][:80]}")

        # Now capture based on dumped sections
        # Store block — find "store" heading
        store_y = None
        for s in sections:
            if 'store' in s['text'].lower() or 'shop' in s['text'].lower() or 'tienda' in s['text'].lower():
                if s['y'] > 200:
                    store_y = s['y']
                    break
        if store_y:
            print(f"  store_block: found at y={store_y}")
            capture_clip(page, IMG_DIR / "fc_barcelona_store_block.png", 0, store_y - 20, 1400, 600)
            shutil.copy(IMG_DIR / "fc_barcelona_store_block.png", IMG_DIR / "fc_barcelona_store_individual_products.png")
        else:
            print("  store_block: NOT FOUND, using 55% fallback")
            capture_clip(page, IMG_DIR / "fc_barcelona_store_block.png", 0, int(sh * 0.55), 1400, 600)
            shutil.copy(IMG_DIR / "fc_barcelona_store_block.png", IMG_DIR / "fc_barcelona_store_individual_products.png")

        # Player roster / cards
        player_y = None
        for s in sections:
            t = s['text'].lower()
            if ('player' in t or 'squad' in t or 'roster' in t or 'plantilla' in t or 'first team' in t) and s['y'] > 200:
                player_y = s['y']
                break
        if player_y:
            print(f"  player_roster: found at y={player_y}")
            capture_clip(page, IMG_DIR / "fc_barcelona_player_roster_preview.png", 0, player_y - 20, 1400, 600)
            shutil.copy(IMG_DIR / "fc_barcelona_player_roster_preview.png", IMG_DIR / "fc_barcelona_individual_player_cards.png")
        else:
            print("  player_roster: NOT FOUND, using 50% fallback")
            capture_clip(page, IMG_DIR / "fc_barcelona_player_roster_preview.png", 0, int(sh * 0.5), 1400, 600)
            shutil.copy(IMG_DIR / "fc_barcelona_player_roster_preview.png", IMG_DIR / "fc_barcelona_individual_player_cards.png")

        # Social native content
        social_y = None
        for s in sections:
            t = s['text'].lower()
            if ('social' in t or 'instagram' in t or '#' in t) and s['y'] > 200 and s['tag'] != 'SOCIAL':
                social_y = s['y']
                break
        if social_y:
            print(f"  social_native_content: found at y={social_y}")
            capture_clip(page, IMG_DIR / "fc_barcelona_social_native_content.png", 0, social_y - 20, 1400, 500)
        else:
            print("  social_native_content: NOT FOUND, using 60% fallback")
            capture_clip(page, IMG_DIR / "fc_barcelona_social_native_content.png", 0, int(sh * 0.60), 1400, 500)

        # Footer sponsor wall
        sponsor_entry = None
        for s in sections:
            if s['tag'] == 'SPONSORS':
                sponsor_entry = s
                break
        if not sponsor_entry:
            # Look for "partner" in heading text
            for s in sections:
                if 'partner' in s['text'].lower() and s['y'] > sh * 0.6:
                    sponsor_entry = s
                    break
        if sponsor_entry:
            print(f"  footer_sponsor_wall: found at y={sponsor_entry['y']}")
            capture_clip(page, IMG_DIR / "fc_barcelona_footer_sponsor_wall.png", 0, sponsor_entry['y'] - 20, 1400, min(sponsor_entry['h'] + 40, 500))
        else:
            # Fallback: just above the social links or at bottom
            footer_entry = None
            for s in sections:
                if s['tag'] == 'FOOTER':
                    footer_entry = s
                    break
            if footer_entry:
                print(f"  footer_sponsor_wall: using footer area at y={footer_entry['y']}")
                capture_clip(page, IMG_DIR / "fc_barcelona_footer_sponsor_wall.png", 0, footer_entry['y'], 1400, 300)
            else:
                capture_clip(page, IMG_DIR / "fc_barcelona_footer_sponsor_wall.png", 0, sh - 500, 1400, 300)

        # Paid membership / Culers section
        membership_y = None
        for s in sections:
            t = s['text'].lower()
            if ('culer' in t or 'member' in t or 'join' in t or 'socis' in t or 'become' in t) and s['y'] > 200:
                membership_y = s['y']
                break
        if membership_y:
            print(f"  paid_membership: found at y={membership_y}")
            capture_clip(page, IMG_DIR / "fc_barcelona_paid_membership.png", 0, membership_y - 20, 1400, 500)
        else:
            print("  paid_membership: NOT FOUND, using 45% fallback")
            capture_clip(page, IMG_DIR / "fc_barcelona_paid_membership.png", 0, int(sh * 0.45), 1400, 500)

        # App store badges
        app_entry = None
        for s in sections:
            if s['tag'] == 'APP':
                app_entry = s
                break
        if app_entry:
            print(f"  app_store_badges: found at y={app_entry['y']}")
            capture_clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, app_entry['y'] - 20, 1400, min(app_entry['h'] + 40, 400))
        else:
            print("  app_store_badges: NOT FOUND, using bottom fallback")
            capture_clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, sh - 600, 1400, 300)

        # ══════════════════════════════════════════════
        # ARSENAL
        # ══════════════════════════════════════════════
        print("\n=== ARSENAL ===")
        sh = setup_page(page, "https://www.arsenal.com")
        print(f"  Page height: {sh}px")

        sections = dump_sections(page)
        print("  Page sections:")
        for s in sections:
            print(f"    y={s['y']:>5}  h={s['h']:>4}  [{s['tag']:>10}]  {s['text'][:80]}")

        # Search input in header
        print("  Capturing: search_input_in_header")
        search_pos = page.evaluate("""() => {
            // Look specifically for search-related elements in the header
            const header = document.querySelector('header') || document.querySelector('nav');
            if (!header) return null;
            const searchEls = header.querySelectorAll('[class*="search"], [aria-label*="earch"], a[href*="search"], button[title*="earch"]');
            for (const el of searchEls) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 5 && rect.height > 5) {
                    return {x: Math.max(0, rect.x - 40), y: Math.max(0, rect.top + window.scrollY - 10), w: Math.min(rect.width + 80, 300), h: rect.height + 20};
                }
            }
            return null;
        }""")
        if search_pos:
            capture_clip(page, IMG_DIR / "arsenal_search_input_in_header.png",
                        search_pos['x'], search_pos['y'], search_pos['w'], search_pos['h'])
            print(f"    -> Captured at x:{search_pos['x']}, y:{search_pos['y']}")
        else:
            # Fallback: entire header area
            capture_clip(page, IMG_DIR / "arsenal_search_input_in_header.png", 0, 0, 1400, 80)
            print("    -> Used header fallback")

        # Charity/CSR block
        charity_y = None
        for s in sections:
            t = s['text'].lower()
            if ('foundation' in t or 'community' in t or 'charity' in t or 'social responsibility' in t) and s['y'] > 300:
                charity_y = s['y']
                break
        if charity_y:
            print(f"  charity_csr_block: found at y={charity_y}")
            capture_clip(page, IMG_DIR / "arsenal_charity_csr_block.png", 0, charity_y - 20, 1400, 500)
        else:
            print("  charity_csr_block: NOT FOUND via headings, searching in links...")
            # Look in keyword links
            for s in sections:
                if s['tag'] == 'A-keyword' and ('foundation' in s['text'].lower() or 'community' in s['text'].lower()):
                    charity_y = s['y']
                    break
            if charity_y:
                print(f"  charity_csr_block: found keyword link at y={charity_y}")
                capture_clip(page, IMG_DIR / "arsenal_charity_csr_block.png", 0, max(0, charity_y - 100), 1400, 500)
            else:
                print("  charity_csr_block: FALLBACK at 75%")
                capture_clip(page, IMG_DIR / "arsenal_charity_csr_block.png", 0, int(sh * 0.75), 1400, 500)

        # Social links in footer
        social_entry = None
        for s in sections:
            if s['tag'] == 'SOCIAL':
                social_entry = s
                break
        if social_entry:
            print(f"  social_links_in_footer: found at y={social_entry['y']}")
            x = social_entry.get('x', 0)
            w = social_entry.get('w', 1400)
            capture_clip(page, IMG_DIR / "arsenal_social_links_in_footer.png",
                        max(0, x - 20), social_entry['y'] - 20, min(w + 40, 1400), social_entry['h'] + 40)
        else:
            print("  social_links_in_footer: FALLBACK at bottom")
            capture_clip(page, IMG_DIR / "arsenal_social_links_in_footer.png", 0, sh - 200, 1400, 200)

        # Heritage/past content
        heritage_y = None
        for s in sections:
            t = s['text'].lower()
            if ('heritage' in t or 'classic' in t or 'retro' in t or 'history' in t or 'on this day' in t or 'throwback' in t or 'flashback' in t) and s['y'] > 300:
                heritage_y = s['y']
                break
        if heritage_y:
            print(f"  heritage_past_content: found at y={heritage_y}")
            capture_clip(page, IMG_DIR / "arsenal_heritage_past_content.png", 0, heritage_y - 20, 1400, 500)
        else:
            print("  heritage_past_content: NOT FOUND, using 65% fallback")
            capture_clip(page, IMG_DIR / "arsenal_heritage_past_content.png", 0, int(sh * 0.65), 1400, 500)

        # Press conference block
        press_y = None
        for s in sections:
            if 'press conference' in s['text'].lower() and s['y'] > 300:
                press_y = s['y']
                break
        if press_y:
            print(f"  press_conference_block: found at y={press_y}")
            capture_clip(page, IMG_DIR / "arsenal_press_conference_block.png", 0, max(0, press_y - 100), 1400, 400)
        else:
            print("  press_conference_block: NOT FOUND, using trending video area fallback")
            # Find "trending" heading
            for s in sections:
                if 'trending' in s['text'].lower():
                    press_y = s['y']
                    break
            if press_y:
                capture_clip(page, IMG_DIR / "arsenal_press_conference_block.png", 0, press_y - 20, 1400, 400)
            else:
                capture_clip(page, IMG_DIR / "arsenal_press_conference_block.png", 0, 1000, 1400, 400)

        browser.close()
        print("\n=== ALL FIXES COMPLETE ===")


if __name__ == "__main__":
    capture_fixes()
