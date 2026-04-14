#!/usr/bin/env python3
"""
Redo all BAD and WEAK screenshots identified by the comprehensive audit.
Each club is processed in its own function with full error handling.
"""

import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).resolve().parent.parent / "crosscheck" / "img"


def safe_eval(page, expr):
    try:
        return page.evaluate(expr)
    except Exception:
        return None


def dismiss_all(page):
    """Dismiss ALL popups, overlays, modals, and cookie banners."""
    safe_eval(page, """(() => {
        // Close buttons first
        document.querySelectorAll('[class*="close"], [aria-label="Close"], [aria-label="close"], .modal-close, [class*="dismiss"]')
            .forEach(b => { try { b.click(); } catch(e) {} });

        // Remove overlay elements
        document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="lightbox"], [class*="promo"], [class*="interstitial"], [class*="takeover"], [role="dialog"], [class*="backdrop"], [class*="mask"], [class*="cookie"], [class*="consent"], [class*="gdpr"], [id*="cookie"], [id*="consent"], [id*="gdpr"]')
            .forEach(e => { try { e.remove(); } catch(ex) {} });

        // Remove high z-index fixed/absolute elements covering the page
        document.querySelectorAll('div, section, aside').forEach(e => {
            try {
                const s = window.getComputedStyle(e);
                const r = e.getBoundingClientRect();
                if ((s.position === 'fixed' || s.position === 'absolute') &&
                    r.width > 300 && r.height > 300 && parseInt(s.zIndex) > 100) {
                    e.remove();
                }
            } catch(ex) {}
        });
    })()""")
    time.sleep(0.5)

    # Click accept/reject cookie buttons
    safe_eval(page, """(() => {
        const btns = document.querySelectorAll('button, a, [role="button"]');
        for (const b of btns) {
            const txt = (b.textContent || '').toLowerCase().trim();
            if (txt.includes('accept all') || txt.includes('reject all') || txt.includes('agree') ||
                txt.includes('accept') || txt.includes('allow all') || txt.includes('confirm choices') ||
                txt.includes('necessary only') || txt.includes('decline') || txt.includes('deny all')) {
                try { b.click(); } catch(e) {}
                break;
            }
        }
    })()""")
    time.sleep(0.5)

    # consentmanager API
    safe_eval(page, "window.__cmp && window.__cmp('setConsent', 0)")

    # Second pass removal
    safe_eval(page, """(() => {
        document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="cookie"], [class*="consent"], [role="dialog"], [class*="backdrop"]')
            .forEach(e => { try { e.remove(); } catch(ex) {} });
        document.querySelectorAll('div, section').forEach(e => {
            try {
                const s = window.getComputedStyle(e);
                const r = e.getBoundingClientRect();
                if ((s.position === 'fixed' || s.position === 'absolute') &&
                    r.width > 300 && r.height > 200 && parseInt(s.zIndex) > 50) {
                    e.remove();
                }
            } catch(ex) {}
        });
        if (document.body) document.body.style.overflow = 'auto';
        if (document.documentElement) document.documentElement.style.overflow = 'auto';
    })()""")
    time.sleep(0.3)


def setup_page(page, url):
    """Navigate, dismiss everything, scroll for lazy-load, return page height."""
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)
    try:
        page.wait_for_selector("body", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    dismiss_all(page)
    time.sleep(2)
    dismiss_all(page)
    time.sleep(2)

    # Check if page is still short (content blocked by cookie wall)
    sh = safe_eval(page, "document.body?.scrollHeight || document.documentElement.scrollHeight || 900") or 900
    if sh < 2000:
        print(f"    ⚠️ Page only {sh}px tall — trying harder to dismiss cookies/load content...")
        safe_eval(page, """(() => {
            document.querySelectorAll('button, a, [role="button"]').forEach(b => {
                const txt = (b.textContent || '').toLowerCase();
                const rect = b.getBoundingClientRect();
                if (rect.height > 20 && rect.width > 50 && rect.top > 0 && rect.top < 800) {
                    if (txt.includes('accept') || txt.includes('agree') || txt.includes('allow') ||
                        txt.includes('ok') || txt.includes('continue') || txt.includes('got it')) {
                        try { b.click(); } catch(e) {}
                    }
                }
            });
        })()""")
        time.sleep(3)
        dismiss_all(page)
        time.sleep(2)

        sh2 = safe_eval(page, "document.body?.scrollHeight || document.documentElement.scrollHeight || 900") or 900
        if sh2 < 2000:
            print(f"    ⚠️ Still only {sh2}px — reloading...")
            try:
                page.reload(wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)
                dismiss_all(page)
                time.sleep(2)
                dismiss_all(page)
                time.sleep(2)
            except Exception:
                pass

    # Scroll incrementally to trigger lazy-loading
    for i in range(10):
        safe_eval(page, f"window.scrollTo(0, (document.body?.scrollHeight || document.documentElement.scrollHeight) * {(i+1)/10})")
        time.sleep(0.8)

    safe_eval(page, "window.scrollTo(0, 0)")
    time.sleep(1)

    dismiss_all(page)
    time.sleep(0.5)

    sh = safe_eval(page, "document.body?.scrollHeight || document.documentElement.scrollHeight || 5000") or 5000
    print(f"  Page height: {sh}px")
    return sh


def clip(page, path, x, y, w, h):
    """Capture a clipped screenshot."""
    try:
        page.screenshot(path=str(path), full_page=True, timeout=60000,
                        clip={"x": max(0, x), "y": max(0, y),
                              "width": max(w, 100), "height": min(max(h, 100), 2000)})
        size = Path(path).stat().st_size
        print(f"    -> {Path(path).name} ({size:,} bytes)")
    except Exception as e:
        print(f"    ❌ FAILED {Path(path).name}: {str(e)[:80]}")


def dump_sections(page):
    """Get structured info about page sections."""
    result = safe_eval(page, """(() => {
        const results = [];
        const els = document.querySelectorAll('h1, h2, h3, h4, section, [class*="block"], [class*="widget"]');
        for (const el of els) {
            try {
                if (el.closest('nav, header, [class*="nav"], [class*="menu"]')) continue;
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (rect.height < 5 || absY < 0) continue;
                const text = (el.innerText || '').substring(0, 120).replace(/\\n/g, ' | ').trim();
                if (!text) continue;
                results.push({
                    tag: el.tagName,
                    y: Math.round(absY),
                    h: Math.round(rect.height),
                    text: text,
                    cls: (el.className || '').toString().substring(0, 80)
                });
            } catch(e) {}
        }
        results.sort((a, b) => a.y - b.y);
        return results.slice(0, 60);
    })()""")
    return result or []


def find_el(page, search_terms, min_y=100):
    """Find y-position of element containing search terms in main content."""
    return safe_eval(page, f"""(() => {{
        const root = document.querySelector('main') || document.querySelector('body') || document.documentElement;
        if (!root) return null;
        const allEls = root.querySelectorAll('*');
        const terms = {json.dumps(search_terms)};
        for (const el of allEls) {{
            try {{
                const text = (el.innerText || '').toLowerCase();
                const cls = (el.className || '').toString().toLowerCase();
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY < {min_y} || rect.height < 20 || rect.height > 5000) continue;
                if (el.closest('nav, header, footer, [class*="nav"], [class*="menu"]')) continue;
                for (const term of terms) {{
                    if (text.includes(term.toLowerCase()) || cls.includes(term.toLowerCase())) {{
                        return {{y: Math.round(absY), h: Math.round(rect.height), w: Math.round(rect.width), text: text.substring(0, 100)}};
                    }}
                }}
            }} catch(e) {{}}
        }}
        return null;
    }})()""")


def find_by_sections(sections, keywords):
    """Find a section by keyword match."""
    for s in sections:
        txt = s['text'].lower()
        if any(k in txt for k in keywords):
            return s
    return None


def find_carousel(page):
    """Find carousel controls."""
    return safe_eval(page, """(() => {
        const found = [];
        const sels = [
            '[class*="swiper-button"]', '[class*="carousel-arrow"]', '[class*="slider-arrow"]',
            '[class*="swiper-pagination"]', '[class*="carousel-dot"]', '[class*="slider-dot"]',
            '[class*="carousel-nav"]', '[class*="slider-nav"]', '[class*="carousel-control"]',
            '[class*="slick-arrow"]', '[class*="slick-dots"]', '[class*="owl-nav"]',
            'button[aria-label*="previous" i]', 'button[aria-label*="next" i]',
            'button[aria-label*="Previous"]', 'button[aria-label*="Next"]'
        ];
        for (const sel of sels) {
            try {
                const els = document.querySelectorAll(sel);
                for (const el of els) {
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (rect.height > 0 && rect.width > 0 && absY < 900) {
                        found.push({y: Math.round(absY), x: Math.round(rect.x), h: Math.round(rect.height), w: Math.round(rect.width), cls: (el.className || '').toString().substring(0, 60)});
                    }
                }
            } catch(e) {}
        }
        let heroRect = null;
        const heroSels = ['[class*="hero"]', '[class*="carousel"]', '[class*="swiper"]', '[class*="slider"]', '[class*="banner"]'];
        for (const sel of heroSels) {
            try {
                const el = document.querySelector(sel);
                if (el) {
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (rect.height > 200 && absY < 300) {
                        heroRect = {y: Math.round(absY), h: Math.round(rect.height), w: Math.round(rect.width)};
                        break;
                    }
                }
            } catch(e) {}
        }
        return {controls: found, hero: heroRect};
    })()""")


def find_video_block(page, min_y=100):
    """Find a large video block (>33% page width)."""
    return safe_eval(page, f"""(() => {{
        const allEls = document.querySelectorAll('video, [class*="video"], [class*="player"], iframe[src*="youtube"], iframe[src*="vimeo"]');
        for (const el of allEls) {{
            try {{
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY < {min_y} || rect.height < 100) continue;
                if (el.closest('nav, header, footer')) continue;
                if (rect.width >= 462) {{
                    return {{y: Math.round(absY), h: Math.round(rect.height), w: Math.round(rect.width), x: Math.round(rect.x)}};
                }}
            }} catch(e) {{}}
        }}
        const playBtns = document.querySelectorAll('[class*="play"], [aria-label*="play" i], [aria-label*="Play"]');
        for (const btn of playBtns) {{
            try {{
                const rect = btn.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY < {min_y}) continue;
                let parent = btn.parentElement;
                for (let i = 0; i < 5 && parent; i++) {{
                    const pr = parent.getBoundingClientRect();
                    if (pr.width >= 462 && pr.height >= 200) {{
                        return {{y: Math.round(pr.top + window.scrollY), h: Math.round(pr.height), w: Math.round(pr.width)}};
                    }}
                    parent = parent.parentElement;
                }}
            }} catch(e) {{}}
        }}
        return null;
    }})()""")


def find_app_badges(page):
    """Find App Store / Google Play badges."""
    return safe_eval(page, """(() => {
        const badges = [];
        document.querySelectorAll('a').forEach(a => {
            try {
                const href = (a.getAttribute('href') || '').toLowerCase();
                if (href.includes('apps.apple') || href.includes('play.google') || href.includes('itunes.apple') || href.includes('app-store') || href.includes('google-play')) {
                    const rect = a.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (rect.height > 0 && rect.width > 0) badges.push({y: Math.round(absY), h: Math.round(rect.height)});
                }
            } catch(e) {}
        });
        document.querySelectorAll('img').forEach(img => {
            try {
                const src = (img.getAttribute('src') || '').toLowerCase();
                const alt = (img.getAttribute('alt') || '').toLowerCase();
                if (src.includes('app-store') || src.includes('google-play') || src.includes('badge') ||
                    alt.includes('app store') || alt.includes('google play') || alt.includes('download on')) {
                    const rect = img.getBoundingClientRect();
                    if (rect.height > 0) badges.push({y: Math.round(rect.top + window.scrollY), h: Math.round(rect.height)});
                }
            } catch(e) {}
        });
        const visible = badges.filter(b => b.h > 5);
        if (!visible.length) return null;
        const minY = Math.min(...visible.map(b => b.y));
        const maxY = Math.max(...visible.map(b => b.y + b.h));
        return {y: minY, h: maxY - minY, count: visible.length};
    })()""")


# ═══════════════════════════════════════════════════
# CHELSEA
# ═══════════════════════════════════════════════════

def do_chelsea(page):
    print("\n" + "="*60)
    print("CHELSEA — chelseafc.com")
    print("="*60)
    sh = setup_page(page, "https://www.chelseafc.com/en")
    sections = dump_sections(page)
    for s in sections[:15]:
        print(f"    y={s['y']:5d} h={s['h']:5d} [{s['tag']:8s}] {s['text'][:80]}")

    # hero_carousel — must show carousel controls
    print("\n  [BAD] hero_carousel")
    cc = find_carousel(page)
    if cc and cc.get('hero'):
        hero = cc['hero']
        clip(page, IMG_DIR / "chelsea_hero_carousel.png", 0, hero['y'], 1400, min(hero['h'] + 50, 800))
        print(f"    Controls: {len(cc.get('controls', []))}")
    else:
        clip(page, IMG_DIR / "chelsea_hero_carousel.png", 0, 0, 1400, 700)

    # brand_sponsor_highlighted_in_hero
    print("\n  [BAD] brand_sponsor_highlighted_in_hero")
    sponsors = safe_eval(page, """(() => {
        const imgs = document.querySelectorAll('img');
        const sponsors = [];
        for (const img of imgs) {
            try {
                const rect = img.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > 800 || rect.height < 10) continue;
                const src = (img.getAttribute('src') || '').toLowerCase();
                const alt = (img.getAttribute('alt') || '').toLowerCase();
                if (src.includes('sponsor') || src.includes('partner') || src.includes('nike') ||
                    src.includes('three') || src.includes('infinity') || src.includes('trivago') ||
                    alt.includes('sponsor') || alt.includes('partner')) {
                    sponsors.push({y: Math.round(absY), h: Math.round(rect.height), alt: alt.substring(0, 40)});
                }
            } catch(e) {}
        }
        return sponsors;
    })()""") or []
    if sponsors:
        min_y = min(s['y'] for s in sponsors)
        clip(page, IMG_DIR / "chelsea_brand_sponsor_highlighted_in_hero.png", 0, max(0, min_y - 50), 1400, 500)
    else:
        clip(page, IMG_DIR / "chelsea_brand_sponsor_highlighted_in_hero.png", 0, 0, 1400, 600)

    # secondary_editorial_strip_below_hero
    print("\n  [BAD] secondary_editorial_strip_below_hero")
    hero_info = safe_eval(page, """(() => {
        const hero = document.querySelector('[class*="hero"], [class*="banner"], [class*="carousel"], [class*="swiper"]');
        if (hero) {
            const rect = hero.getBoundingClientRect();
            return {y: Math.round(rect.top + window.scrollY), h: Math.round(rect.height)};
        }
        return {y: 0, h: 600};
    })()""") or {'y': 0, 'h': 600}
    strip_y = hero_info['y'] + hero_info['h']
    clip(page, IMG_DIR / "chelsea_secondary_editorial_strip_below_hero.png", 0, max(0, strip_y - 20), 1400, 400)

    # news_rich_structure
    print("\n  [BAD] news_rich_structure")
    news = find_el(page, ['latest news', 'news', 'stories', 'articles'])
    if news:
        clip(page, IMG_DIR / "chelsea_news_rich_structure.png", 0, max(0, news['y'] - 30), 1400, 700)
    else:
        s = find_by_sections(sections, ['news', 'latest', 'stories'])
        if s:
            clip(page, IMG_DIR / "chelsea_news_rich_structure.png", 0, max(0, s['y'] - 30), 1400, 700)

    # homepage_video_block
    print("\n  [BAD] homepage_video_block")
    vid = find_video_block(page)
    if vid:
        clip(page, IMG_DIR / "chelsea_homepage_video_block.png", 0, max(0, vid['y'] - 30), 1400, min(vid['h'] + 60, 700))
    else:
        vid_s = find_el(page, ['video', 'watch', 'highlights', 'tv'])
        if vid_s:
            clip(page, IMG_DIR / "chelsea_homepage_video_block.png", 0, max(0, vid_s['y'] - 30), 1400, 500)
        else:
            clip(page, IMG_DIR / "chelsea_homepage_video_block.png", 0, 800, 1400, 500)

    # academy_youth_block
    print("\n  [BAD] academy_youth_block")
    academy = find_el(page, ['academy', 'youth', 'u21', 'u18', 'development'])
    if academy:
        clip(page, IMG_DIR / "chelsea_academy_youth_block.png", 0, max(0, academy['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['academy', 'youth', 'development'])
        if s:
            clip(page, IMG_DIR / "chelsea_academy_youth_block.png", 0, max(0, s['y'] - 30), 1400, 500)

    # app_store_badges
    print("\n  [BAD] app_store_badges")
    badges = find_app_badges(page)
    if badges:
        clip(page, IMG_DIR / "chelsea_app_store_badges.png", 0, max(0, badges['y'] - 50), 1400, max(badges['h'] + 100, 300))
    else:
        clip(page, IMG_DIR / "chelsea_app_store_badges.png", 0, sh - 500, 1400, 300)

    # WEAK: standings_block
    print("\n  [WEAK] standings_block")
    standings = find_el(page, ['standings', 'table', 'league table', 'current standings'])
    if standings:
        clip(page, IMG_DIR / "chelsea_standings_block.png", 0, max(0, standings['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['standings', 'table'])
        if s:
            clip(page, IMG_DIR / "chelsea_standings_block.png", 0, max(0, s['y'] - 30), 1400, 500)

    # WEAK: next_match_block + next_match_feature_rich
    print("\n  [WEAK] next_match_block + next_match_feature_rich")
    match = safe_eval(page, """(() => {
        const els = document.querySelectorAll('[class*="match"], [class*="fixture"], [class*="game-bar"], [class*="matchday"]');
        for (const el of els) {
            try {
                if (el.closest('nav, header, footer')) continue;
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (rect.height > 30 && absY > 50 && absY < 1500) {
                    return {y: Math.round(absY), h: Math.round(rect.height)};
                }
            } catch(e) {}
        }
        return null;
    })()""")
    if match:
        clip(page, IMG_DIR / "chelsea_next_match_block.png", 0, max(0, match['y'] - 30), 1400, 400)
        clip(page, IMG_DIR / "chelsea_next_match_feature_rich.png", 0, max(0, match['y'] - 30), 1400, 500)

    # WEAK: tickets_block
    print("\n  [WEAK] tickets_block")
    tickets = find_el(page, ['tickets', 'matchday tickets', 'buy tickets'])
    if tickets:
        clip(page, IMG_DIR / "chelsea_tickets_block.png", 0, max(0, tickets['y'] - 30), 1400, 500)


# ═══════════════════════════════════════════════════
# FC BARCELONA
# ═══════════════════════════════════════════════════

def do_barcelona(page):
    print("\n" + "="*60)
    print("FC BARCELONA — fcbarcelona.com/en")
    print("="*60)
    sh = setup_page(page, "https://www.fcbarcelona.com/en")
    sections = dump_sections(page)
    for s in sections[:20]:
        print(f"    y={s['y']:5d} h={s['h']:5d} [{s['tag']:8s}] {s['text'][:80]}")

    # hero_carousel
    print("\n  [BAD] hero_carousel")
    cc = find_carousel(page)
    if cc and cc.get('hero'):
        clip(page, IMG_DIR / "fc_barcelona_hero_carousel.png", 0, cc['hero']['y'], 1400, min(cc['hero']['h'] + 50, 800))
    else:
        clip(page, IMG_DIR / "fc_barcelona_hero_carousel.png", 0, 0, 1400, 700)

    # brand_sponsor_highlighted_in_hero
    print("\n  [BAD] brand_sponsor_highlighted_in_hero")
    sponsors = safe_eval(page, """(() => {
        const imgs = document.querySelectorAll('img');
        const sponsors = [];
        for (const img of imgs) {
            try {
                const rect = img.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > 800 || rect.height < 10) continue;
                const src = (img.getAttribute('src') || '').toLowerCase();
                const alt = (img.getAttribute('alt') || '').toLowerCase();
                if (src.includes('sponsor') || src.includes('partner') || src.includes('nike') ||
                    src.includes('spotify') || src.includes('allianz') || src.includes('rakuten') ||
                    alt.includes('sponsor') || alt.includes('partner') || alt.includes('nike') || alt.includes('spotify')) {
                    sponsors.push({y: Math.round(absY), h: Math.round(rect.height), alt: alt.substring(0, 40)});
                }
            } catch(e) {}
        }
        return sponsors;
    })()""") or []
    if sponsors:
        clip(page, IMG_DIR / "fc_barcelona_brand_sponsor_highlighted_in_hero.png", 0, max(0, min(s['y'] for s in sponsors) - 50), 1400, 500)
    else:
        clip(page, IMG_DIR / "fc_barcelona_brand_sponsor_highlighted_in_hero.png", 0, 0, 1400, 600)

    # news_rich_structure
    print("\n  [BAD] news_rich_structure")
    news = find_el(page, ['news', 'latest', 'stories', 'articles', 'barça stories'])
    if news:
        clip(page, IMG_DIR / "fc_barcelona_news_rich_structure.png", 0, max(0, news['y'] - 30), 1400, 700)
    else:
        s = find_by_sections(sections, ['news', 'stories', 'latest'])
        if s:
            clip(page, IMG_DIR / "fc_barcelona_news_rich_structure.png", 0, max(0, s['y'] - 30), 1400, 700)

    # dedicated_news_section
    print("\n  [BAD] dedicated_news_section")
    if news:
        clip(page, IMG_DIR / "fc_barcelona_dedicated_news_section.png", 0, max(0, news['y'] - 60), 1400, 600)

    # video_thumbnails_inline
    print("\n  [BAD] video_thumbnails_inline")
    vt = safe_eval(page, """(() => {
        const playEls = document.querySelectorAll('[class*="play"], [class*="video"], svg[class*="play"]');
        const results = [];
        for (const el of playEls) {
            try {
                if (el.closest('nav, header, footer')) continue;
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (rect.height > 5 && absY > 200) results.push({y: Math.round(absY)});
            } catch(e) {}
        }
        if (results.length) return {y: Math.min(...results.map(r => r.y)), count: results.length};
        return null;
    })()""")
    if vt:
        clip(page, IMG_DIR / "fc_barcelona_video_thumbnails_inline.png", 0, max(0, vt['y'] - 50), 1400, 500)
    else:
        s = find_by_sections(sections, ['video', 'highlights'])
        if s:
            clip(page, IMG_DIR / "fc_barcelona_video_thumbnails_inline.png", 0, max(0, s['y'] - 30), 1400, 500)

    # draws_contests
    print("\n  [BAD] draws_contests")
    draws = find_el(page, ['draws', 'contests', 'sweepstakes', 'giveaway', 'sorteo'])
    if not draws:
        draws = find_el(page, ['culers', 'benefits', 'discounts'])
    if draws:
        clip(page, IMG_DIR / "fc_barcelona_draws_contests.png", 0, max(0, draws['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['culers', 'benefits', 'draws', 'contests'])
        if s:
            clip(page, IMG_DIR / "fc_barcelona_draws_contests.png", 0, max(0, s['y'] - 30), 1400, 500)

    # fan_club_signup
    print("\n  [BAD] fan_club_signup")
    fan = find_el(page, ['join', 'sign up', 'register', 'culers', 'become a member'])
    if fan:
        clip(page, IMG_DIR / "fc_barcelona_fan_club_signup.png", 0, max(0, fan['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['culers', 'join', 'membership'])
        if s:
            clip(page, IMG_DIR / "fc_barcelona_fan_club_signup.png", 0, max(0, s['y'] - 30), 1400, 500)

    # app_store_badges
    print("\n  [BAD] app_store_badges")
    badges = find_app_badges(page)
    if badges:
        clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, max(0, badges['y'] - 50), 1400, max(badges['h'] + 100, 300))
    else:
        app = find_el(page, ['app', 'mobile', 'download'])
        if app:
            clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, max(0, app['y'] - 30), 1400, 400)
        else:
            clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, sh - 500, 1400, 300)

    # stadium_content_block — MUST show stadium content, NOT tickets
    print("\n  [BAD] stadium_content_block")
    stadium = find_el(page, ['camp nou', 'spotify camp nou', 'stadium tour', 'estadi', 'visit the stadium', 'immersive tour'])
    if stadium:
        print(f"    Found stadium content at y={stadium['y']}: {stadium['text'][:60]}")
        clip(page, IMG_DIR / "fc_barcelona_stadium_content_block.png", 0, max(0, stadium['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['camp nou', 'stadium', 'estadi', 'tour', 'immersive'])
        if s:
            clip(page, IMG_DIR / "fc_barcelona_stadium_content_block.png", 0, max(0, s['y'] - 30), 1400, 500)
        else:
            print("    ⚠️ No stadium section found")
            clip(page, IMG_DIR / "fc_barcelona_stadium_content_block.png", 0, sh - 1200, 1400, 500)

    # WEAK: homepage_video_block
    print("\n  [WEAK] homepage_video_block")
    vid = find_video_block(page)
    if vid:
        clip(page, IMG_DIR / "fc_barcelona_homepage_video_block.png", 0, max(0, vid['y'] - 30), 1400, min(vid['h'] + 60, 700))
    else:
        vs = find_el(page, ['video', 'watch', 'highlights', 'barça tv'])
        if vs:
            clip(page, IMG_DIR / "fc_barcelona_homepage_video_block.png", 0, max(0, vs['y'] - 30), 1400, 500)

    # WEAK: social_native_content
    print("\n  [WEAK] social_native_content")
    social = find_el(page, ['stories', 'social', 'instagram', 'tiktok'])
    if social:
        clip(page, IMG_DIR / "fc_barcelona_social_native_content.png", 0, max(0, social['y'] - 30), 1400, 500)

    # WEAK: paid_membership
    print("\n  [WEAK] paid_membership")
    mem = find_el(page, ['culers', 'membership', 'subscribe', 'premium', 'paid'])
    if mem:
        clip(page, IMG_DIR / "fc_barcelona_paid_membership.png", 0, max(0, mem['y'] - 30), 1400, 500)


# ═══════════════════════════════════════════════════
# ARSENAL
# ═══════════════════════════════════════════════════

def do_arsenal(page):
    print("\n" + "="*60)
    print("ARSENAL — arsenal.com")
    print("="*60)
    sh = setup_page(page, "https://www.arsenal.com")

    # Arsenal-specific: extra popup removal
    safe_eval(page, """(() => {
        document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="lightbox"], [class*="promo"], [role="dialog"]').forEach(e => { try { e.remove(); } catch(ex) {} });
        document.querySelectorAll('div, section').forEach(e => {
            try {
                const s = window.getComputedStyle(e);
                const r = e.getBoundingClientRect();
                if ((s.position === 'fixed' || s.position === 'absolute') && r.width > 300 && r.height > 200 && parseInt(s.zIndex) > 50) e.remove();
            } catch(ex) {}
        });
        if (document.body) document.body.style.overflow = 'auto';
        if (document.documentElement) document.documentElement.style.overflow = 'auto';
    })()""")
    time.sleep(1)

    sections = dump_sections(page)
    for s in sections[:20]:
        print(f"    y={s['y']:5d} h={s['h']:5d} [{s['tag']:8s}] {s['text'][:80]}")

    # hero_carousel
    print("\n  [BAD] hero_carousel")
    cc = find_carousel(page)
    if cc and cc.get('hero'):
        clip(page, IMG_DIR / "arsenal_hero_carousel.png", 0, cc['hero']['y'], 1400, min(cc['hero']['h'] + 50, 800))
        print(f"    Controls: {len(cc.get('controls', []))}")
    else:
        clip(page, IMG_DIR / "arsenal_hero_carousel.png", 0, 0, 1400, 700)

    # tickets_shortcut_in_header
    print("\n  [BAD] tickets_shortcut_in_header")
    ticket = safe_eval(page, """(() => {
        const header = document.querySelector('header') || document.querySelector('[class*="header"]');
        if (!header) return null;
        const links = header.querySelectorAll('a');
        for (const a of links) {
            const text = (a.innerText || '').trim().toLowerCase();
            if (text.includes('ticket')) {
                const rect = a.getBoundingClientRect();
                return {x: Math.round(rect.x), y: Math.round(rect.top + window.scrollY), w: Math.round(rect.width), h: Math.round(rect.height), text: text.substring(0, 30)};
            }
        }
        return null;
    })()""")
    if ticket:
        print(f"    Found '{ticket['text']}' at x={ticket['x']}")
        clip(page, IMG_DIR / "arsenal_tickets_shortcut_in_header.png",
             max(0, ticket['x'] - 100), max(0, ticket['y'] - 10),
             min(ticket['w'] + 200, 500), ticket['h'] + 30)
    else:
        clip(page, IMG_DIR / "arsenal_tickets_shortcut_in_header.png", 0, 0, 1400, 80)

    # homepage_video_block
    print("\n  [BAD] homepage_video_block")
    vid = find_video_block(page)
    if vid:
        clip(page, IMG_DIR / "arsenal_homepage_video_block.png", 0, max(0, vid['y'] - 30), 1400, min(vid['h'] + 60, 700))
    else:
        vs = find_el(page, ['video', 'trending video', 'watch', 'highlights'])
        if vs:
            clip(page, IMG_DIR / "arsenal_homepage_video_block.png", 0, max(0, vs['y'] - 30), 1400, 500)
        else:
            s = find_by_sections(sections, ['video'])
            if s:
                clip(page, IMG_DIR / "arsenal_homepage_video_block.png", 0, max(0, s['y'] - 30), 1400, 500)

    # next_match_block + next_match_feature_rich
    print("\n  [BAD] next_match_block + next_match_feature_rich")
    match = safe_eval(page, """(() => {
        const els = document.querySelectorAll('[class*="match"], [class*="fixture"], [class*="game-bar"], [class*="matchday"]');
        for (const el of els) {
            try {
                if (el.closest('nav, header, footer')) continue;
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (rect.height > 30 && absY > 50 && absY < 1500) {
                    return {y: Math.round(absY), h: Math.round(rect.height), text: (el.innerText || '').substring(0, 100)};
                }
            } catch(e) {}
        }
        return null;
    })()""")
    if not match:
        match = find_el(page, ['next match', 'upcoming', 'fixture'])
    if match:
        clip(page, IMG_DIR / "arsenal_next_match_block.png", 0, max(0, match['y'] - 30), 1400, 400)
        clip(page, IMG_DIR / "arsenal_next_match_feature_rich.png", 0, max(0, match['y'] - 30), 1400, 500)
    else:
        # Try sections for match-like content
        for s in sections:
            txt = s['text'].lower()
            if any(t in txt for t in ['v ', 'vs', 'premier league']) and s['y'] > 50 and s['y'] < 2000:
                clip(page, IMG_DIR / "arsenal_next_match_block.png", 0, max(0, s['y'] - 30), 1400, 400)
                clip(page, IMG_DIR / "arsenal_next_match_feature_rich.png", 0, max(0, s['y'] - 30), 1400, 500)
                break

    # charity_csr_block
    print("\n  [BAD] charity_csr_block")
    charity = find_el(page, ['foundation', 'community', 'charity', 'csr', 'arsenal in the community'])
    if charity:
        clip(page, IMG_DIR / "arsenal_charity_csr_block.png", 0, max(0, charity['y'] - 30), 1400, 500)
    else:
        # Look for community-related cards
        comm = safe_eval(page, """(() => {
            const cards = document.querySelectorAll('article, [class*="card"], [class*="story"]');
            for (const el of cards) {
                try {
                    if (el.closest('nav, header, footer')) continue;
                    const text = (el.innerText || '').toLowerCase();
                    if (text.includes('community') || text.includes('foundation') || text.includes('charity')) {
                        const rect = el.getBoundingClientRect();
                        const absY = rect.top + window.scrollY;
                        if (rect.height > 30 && absY > 200) return {y: Math.round(absY), h: Math.round(rect.height)};
                    }
                } catch(e) {}
            }
            return null;
        })()""")
        if comm:
            clip(page, IMG_DIR / "arsenal_charity_csr_block.png", 0, max(0, comm['y'] - 30), 1400, 500)
        else:
            print("    ⚠️ No charity/CSR block found — feature may be FALSE")

    # heritage_past_content
    print("\n  [BAD] heritage_past_content")
    heritage = find_el(page, ['heritage', 'history', 'classics', 'legends', 'on this day', 'archive'])
    if heritage:
        clip(page, IMG_DIR / "arsenal_heritage_past_content.png", 0, max(0, heritage['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['heritage', 'history', 'classic', 'legend', 'archive'])
        if s:
            clip(page, IMG_DIR / "arsenal_heritage_past_content.png", 0, max(0, s['y'] - 30), 1400, 500)
        else:
            print("    ⚠️ No heritage section found — feature may be FALSE")

    # press_conference_block
    print("\n  [BAD] press_conference_block")
    press = find_el(page, ['press conference', 'manager', 'arteta', 'pre-match'])
    if press:
        clip(page, IMG_DIR / "arsenal_press_conference_block.png", 0, max(0, press['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['press', 'conference', 'arteta'])
        if s:
            clip(page, IMG_DIR / "arsenal_press_conference_block.png", 0, max(0, s['y'] - 30), 1400, 500)
        else:
            print("    ⚠️ No press conference section found — feature may be FALSE")

    # WEAK: sponsor_lockup_in_header
    print("\n  [WEAK] sponsor_lockup_in_header")
    sponsors = safe_eval(page, """(() => {
        const header = document.querySelector('header') || document.querySelector('[class*="header"]');
        if (!header) return null;
        const imgs = header.querySelectorAll('img');
        const sponsors = [];
        for (const img of imgs) {
            try {
                const rect = img.getBoundingClientRect();
                if (rect.width < 20 || rect.height < 10) continue;
                if (rect.x < 200 && sponsors.length === 0) continue;
                const src = (img.getAttribute('src') || '').toLowerCase();
                const alt = (img.getAttribute('alt') || '').toLowerCase();
                if (src.includes('sponsor') || src.includes('partner') || src.includes('adidas') ||
                    src.includes('emirates') || src.includes('sobha') || src.includes('rwanda') ||
                    alt.includes('sponsor') || alt.includes('partner') || alt.includes('adidas') ||
                    alt.includes('emirates') || (rect.x > 200 && rect.width > 30 && rect.width < 200)) {
                    sponsors.push({x: Math.round(rect.x), y: Math.round(rect.top + window.scrollY), w: Math.round(rect.width), h: Math.round(rect.height)});
                }
            } catch(e) {}
        }
        return sponsors.length ? sponsors : null;
    })()""")
    if sponsors:
        min_x = min(s['x'] for s in sponsors)
        max_x = max(s['x'] + s['w'] for s in sponsors)
        min_y = min(s['y'] for s in sponsors)
        clip(page, IMG_DIR / "arsenal_sponsor_lockup_in_header.png",
             max(0, min_x - 20), max(0, min_y - 10),
             min(max_x - min_x + 40, 600), max(s['h'] for s in sponsors) + 20)
    else:
        clip(page, IMG_DIR / "arsenal_sponsor_lockup_in_header.png", 800, 0, 600, 70)

    # WEAK: store_block + store_individual_products
    print("\n  [WEAK] store_block + store_individual_products")
    store = find_el(page, ['shop now', 'store', 'merch', 'kit', 'gear', 'adidas'])
    if store:
        clip(page, IMG_DIR / "arsenal_store_block.png", 0, max(0, store['y'] - 30), 1400, 500)
        clip(page, IMG_DIR / "arsenal_store_individual_products.png", 0, max(0, store['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['shop', 'store', 'adidas', 'kit'])
        if s:
            clip(page, IMG_DIR / "arsenal_store_block.png", 0, max(0, s['y'] - 30), 1400, 500)
            clip(page, IMG_DIR / "arsenal_store_individual_products.png", 0, max(0, s['y'] - 30), 1400, 500)

    # WEAK: quiz_trivia
    print("\n  [WEAK] quiz_trivia")
    quiz = find_el(page, ['quiz', 'trivia', 'quizzes'])
    if quiz:
        clip(page, IMG_DIR / "arsenal_quiz_trivia.png", 0, max(0, quiz['y'] - 30), 1400, 500)
    else:
        s = find_by_sections(sections, ['quiz'])
        if s:
            clip(page, IMG_DIR / "arsenal_quiz_trivia.png", 0, max(0, s['y'] - 30), 1400, 500)

    # WEAK: social_links_in_footer
    print("\n  [WEAK] social_links_in_footer")
    social = safe_eval(page, f"""(() => {{
        const sh = {sh};
        const links = document.querySelectorAll('a');
        const socials = [];
        for (const a of links) {{
            try {{
                const href = (a.getAttribute('href') || '').toLowerCase();
                const rect = a.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (rect.height > 0 && absY > sh * 0.7) {{
                    if (href.includes('twitter') || href.includes('x.com') || href.includes('facebook') ||
                        href.includes('instagram') || href.includes('youtube') || href.includes('tiktok')) {{
                        socials.push({{y: Math.round(absY), h: Math.round(rect.height)}});
                    }}
                }}
            }} catch(e) {{}}
        }}
        if (socials.length < 2) return null;
        const minY = Math.min(...socials.map(s => s.y));
        const maxY = Math.max(...socials.map(s => s.y + s.h));
        return {{y: minY, h: maxY - minY + 20, count: socials.length}};
    }})()""")
    if social:
        clip(page, IMG_DIR / "arsenal_social_links_in_footer.png", 0, max(0, social['y'] - 20), 1400, max(social['h'] + 40, 120))
    else:
        clip(page, IMG_DIR / "arsenal_social_links_in_footer.png", 0, sh - 200, 1400, 200)


# ═══════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        try:
            do_chelsea(page)
        except Exception as e:
            print(f"\n❌ CHELSEA FAILED: {e}")

        try:
            do_barcelona(page)
        except Exception as e:
            print(f"\n❌ BARCELONA FAILED: {e}")

        try:
            do_arsenal(page)
        except Exception as e:
            print(f"\n❌ ARSENAL FAILED: {e}")

        browser.close()
        print("\n" + "="*60)
        print("ALL BAD + WEAK SCREENSHOTS REDONE")
        print("="*60)


if __name__ == "__main__":
    main()
