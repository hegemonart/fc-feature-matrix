#!/usr/bin/env python3
"""
Batch 1: Capture element-level screenshots for 7 clubs.
Real Madrid, Liverpool, Bayern Munich, PSG, Man City, Man United, Tottenham.

v2: Fixed mega-menu exclusion, improved cookie handling, page height validation.
"""

import sys
import os
import json
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent  # analysis/homepage/
RESULTS = BASE / "results"
IMG_DIR = BASE / "crosscheck" / "img"
IMG_DIR.mkdir(exist_ok=True)

BATCH1_URLS = {
    "real_madrid": "https://www.realmadrid.com/en",
    "liverpool": "https://www.liverpoolfc.com",
    "bayern_munich": "https://fcbayern.com/en",
    "psg": "https://www.psg.fr/en",
    "man_city": "https://www.mancity.com",
    "man_united": "https://www.manutd.com",
    "tottenham": "https://www.tottenhamhotspur.com",
}

# Minimum Y position for body content (excludes header/hero/mega-menu)
MIN_BODY_Y = 500

# Features that ARE in the header (use low y threshold)
HEADER_FEATURES = {
    "language_switcher_in_header", "login_account", "search_input_in_header",
    "shop_shortcut_in_header", "tickets_shortcut_in_header", "sponsor_lockup_in_header",
    "persistent_bar_above_header",
}

# Features in the hero area
HERO_FEATURES = {
    "hero_carousel", "secondary_editorial_strip_below_hero", "brand_sponsor_highlighted_in_hero",
}


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
        # Validate clip dimensions
        if clip["width"] <= 0 or clip["height"] <= 0:
            return False
        if clip["x"] < 0:
            clip["x"] = 0
        if clip["y"] < 0:
            clip["y"] = 0
        page.screenshot(path=str(path), clip=clip, full_page=full_page, timeout=60000)
        return True
    except Exception as e:
        print(f"    [screenshot error] {str(e)[:100]}")
        return False


def dismiss_cookies(page, club_id):
    """Dismiss cookies with site-specific strategies."""

    # Site-specific handlers first
    if club_id == "psg":
        safe_eval(page, """() => {
            try { var btn = document.querySelector('button.didomi-dismiss-button, #didomi-notice-agree-button'); if (btn) btn.click(); } catch(e) {}
        }""")
        time.sleep(2)

    if club_id in ("bayern_munich", "vfb_stuttgart", "bvb_dortmund", "eintracht", "rb_leipzig"):
        safe_eval(page, """() => { try { window.__cmp('setConsent', 0); } catch(e) {} }""")
        time.sleep(2)

    # Generic cookie dismissal — multiple passes
    for attempt in range(5):
        safe_eval(page, """() => {
            try {
                var btns = document.querySelectorAll('button, a, [role="button"], span[role="button"]');
                var priorities = ['accept all', 'accept all cookies', 'allow all', 'agree to all',
                    'accept', 'agree', 'consent', 'got it', 'ok', 'i understand',
                    'reject all', 'decline all', 'necessary only', 'refuse', 'deny all',
                    'acepto', 'acceptar', 'aceptar', 'akzeptieren', 'alle akzeptieren',
                    'tout accepter', 'accepter'];
                for (var p of priorities) {
                    for (var b of btns) {
                        try {
                            var txt = (b.textContent || '').toLowerCase().trim();
                            if (txt === p || txt.includes(p)) { b.click(); return true; }
                        } catch(ex) {}
                    }
                }
            } catch(e) {}
            return false;
        }""")
        time.sleep(1)

        # Check if page expanded
        height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
        if height > 3000:
            break

    # Force-remove overlay elements
    safe_eval(page, """() => {
        try {
            document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="consent"], [class*="cookie"], [class*="gdpr"], [role="dialog"], [class*="backdrop"], [class*="mask"], [id*="onetrust"], [id*="didomi"]').forEach(function(e) {
                try { e.remove(); } catch(ex) {}
            });
        } catch(e) {}
        try {
            document.querySelectorAll('div, section').forEach(function(e) {
                try {
                    var s = window.getComputedStyle(e);
                    var r = e.getBoundingClientRect();
                    if ((s.position === 'fixed' || s.position === 'sticky') && r.width > 300 && r.height > 200 && parseInt(s.zIndex) > 50) e.remove();
                } catch(ex) {}
            });
        } catch(e) {}
        // Reset body overflow
        try { document.body.style.overflow = 'auto'; document.documentElement.style.overflow = 'auto'; } catch(e) {}
    }""")
    time.sleep(1)


def scroll_lazy_load(page):
    """Scroll to trigger lazy loading, return final page height."""
    height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000

    # Incremental scroll
    steps = 8
    for i in range(1, steps + 1):
        safe_eval(page, f"window.scrollTo(0, {height * i // steps})")
        time.sleep(0.6)

    # Check if page grew
    new_height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000
    if new_height > height + 500:
        for i in range(1, 5):
            safe_eval(page, f"window.scrollTo(0, {new_height * i // 4})")
            time.sleep(0.5)

    safe_eval(page, "window.scrollTo(0, 0)")
    time.sleep(2)
    return safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0


def setup_page(page, url, club_id):
    """Navigate, dismiss cookies, scroll. Returns page height."""
    print(f"  Navigating to {url}...")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation warning: {str(e)[:80]}")

    # Extra wait for JS rendering
    time.sleep(5)

    dismiss_cookies(page, club_id)

    height = scroll_lazy_load(page)
    print(f"  Page height: {height}px")

    # If page is too short, retry cookie dismissal and reload
    if height < 3000:
        print(f"  ⚠️ Short page ({height}px) — retrying cookie dismissal...")
        dismiss_cookies(page, club_id)
        time.sleep(3)

        height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
        if height < 3000:
            print(f"  ⚠️ Still short ({height}px) — reloading page...")
            try:
                page.reload(wait_until="domcontentloaded", timeout=30000)
            except Exception:
                pass
            time.sleep(5)
            dismiss_cookies(page, club_id)
            time.sleep(2)
            height = scroll_lazy_load(page)
            print(f"  Page height after reload: {height}px")

    return height


# ─── Feature Locator JS templates ───
# Each returns a JS function body that finds the element.
# Body features use MIN_BODY_Y to exclude mega-menu items.
# The {min_y} placeholder gets replaced at runtime.

LOCATORS = {
    # ── Header features (use y < 120) ──
    "language_switcher_in_header": {
        "js": """
            var els = document.querySelectorAll('[class*="lang"], [class*="Lang"], [data-lang], [class*="locale"], [class*="country"]');
            for (var el of els) { if (el.getBoundingClientRect().top < 120 && el.getBoundingClientRect().height > 0) return el; }
            var all = document.querySelectorAll('a, button, select');
            for (var el of all) {
                var t = (el.textContent || '').trim();
                if (/^(EN|ES|CA|DE|FR|IT|PT|English|Español)$/i.test(t) && el.getBoundingClientRect().top < 120) return el;
            }
            return null;
        """,
        "fallback": [0, 0, 1400, 50],
    },
    "login_account": {
        "js": """
            var els = document.querySelectorAll('[class*="profile"], [class*="login"], [class*="Login"], [class*="account"], [class*="Account"], [href*="login"], [href*="account"], [href*="sign-in"], [aria-label*="Sign"], [aria-label*="Log"]');
            for (var el of els) { if (el.getBoundingClientRect().top < 120 && el.getBoundingClientRect().height > 0) return el; }
            return null;
        """,
        "fallback": [1100, 0, 1400, 50],
    },
    "search_input_in_header": {
        "js": """
            var el = document.querySelector('[class*="search"], [class*="Search"], [type="search"], [aria-label*="search"], [aria-label*="Search"], [aria-label*="buscar"]');
            if (el && el.getBoundingClientRect().top < 120) return el;
            return null;
        """,
        "fallback": [1000, 0, 1400, 50],
    },
    "shop_shortcut_in_header": {
        "js": """
            var all = document.querySelectorAll('a, button');
            for (var el of all) {
                var t = (el.textContent || '').trim().toLowerCase();
                var r = el.getBoundingClientRect();
                if (r.top < 120 && r.height > 0 && (t === 'shop' || t === 'store' || t === 'tienda' || t === 'boutique' || t === 'fanshop')) return el;
            }
            return null;
        """,
        "fallback": [500, 0, 1100, 50],
    },
    "tickets_shortcut_in_header": {
        "js": """
            var all = document.querySelectorAll('a, button');
            for (var el of all) {
                var t = (el.textContent || '').trim().toLowerCase();
                var r = el.getBoundingClientRect();
                if (r.top < 120 && r.height > 0 && (t.includes('ticket') || t.includes('entrada') || t === 'entradas')) return el;
            }
            return null;
        """,
        "fallback": [400, 0, 1000, 50],
    },
    "sponsor_lockup_in_header": {
        "js": """
            var imgs = document.querySelectorAll('header img, [class*="header"] img, [class*="Header"] img');
            var sponsors = [];
            for (var i of imgs) {
                var r = i.getBoundingClientRect();
                if (r.top < 80 && r.top > -10 && r.width > 20 && r.height > 10) sponsors.push(i);
            }
            if (sponsors.length > 0) {
                var container = sponsors[0].closest('div') || sponsors[0].parentElement;
                return container;
            }
            return null;
        """,
        "fallback": [1000, 0, 1400, 50],
    },
    "persistent_bar_above_header": {
        "region": [0, 0, 1400, 50],
    },

    # ── Hero features (y < 900) ──
    "hero_carousel": {
        "region": [0, 50, 1400, 600],
    },
    "secondary_editorial_strip_below_hero": {
        "js": """
            var cards = document.querySelectorAll('[class*="card"], [class*="Card"], [class*="editorial"], [class*="strip"]');
            for (var el of cards) {
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > 500 && absY < 1200 && el.getBoundingClientRect().height > 40 && el.getBoundingClientRect().height < 400) return el;
            }
            return null;
        """,
        "fallback": [0, 500, 1400, 900],
    },
    "brand_sponsor_highlighted_in_hero": {
        "region": [0, 0, 1400, 600],
    },

    # ── Body content features (use min_y to exclude mega-menu) ──
    "next_match_block": {
        "js": """
            // Class-based first
            var matchEls = document.querySelectorAll('[class*="fixture"], [class*="Fixture"], [class*="next-match"], [class*="upcoming"], [class*="NextMatch"]');
            for (var el of matchEls) {
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 50) return el;
            }
            // Heading-based (excluding nav)
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('next match') || t.includes('upcoming') || t.includes('fixture') || t.includes('próximos')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "next_match_feature_rich": { "same_as": "next_match_block" },
    "results_block": {
        "js": """
            // Look for score patterns in body (not nav)
            var all = document.querySelectorAll('main span, main div, main td, main p, [class*="result"], [class*="score"]');
            for (var el of all) {
                if (el.closest('nav, header, footer, [role="navigation"]')) continue;
                var t = (el.textContent || '').trim();
                if (/^\\d\\s*[-–:]\\s*\\d$/.test(t)) {
                    var section = el.closest('section, [class*="result"], [class*="match"]');
                    var absY = (section || el).getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y} && (section || el).getBoundingClientRect().height > 40) return section || el;
                }
            }
            // Heading-based
            var headings = document.querySelectorAll('h2, h3');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('result') || t.includes('score') || t.includes('resultado')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "dedicated_news_section": {
        "js": """
            var headings = document.querySelectorAll('h2, h3');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('news') || t.includes('latest') || t.includes('noticias') || t.includes('stories') || t.includes('articles')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) {
                        var section = h.closest('section, div[class]');
                        if (section && section.getBoundingClientRect().height > 100) return section;
                    }
                }
            }
            return null;
        """,
    },
    "news_rich_structure": { "same_as": "dedicated_news_section" },
    "homepage_video_block": {
        "js": """
            var headings = document.querySelectorAll('h2, h3');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('watch') || t.includes('video') || t.includes('highlights') || t.includes('vídeo')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            var vids = document.querySelectorAll('[class*="video"], [class*="Video"], video');
            for (var el of vids) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 100) return el.closest('section, div[class]') || el;
            }
            return null;
        """,
    },
    "video_thumbnails_inline": { "same_as": "homepage_video_block" },
    "episodic_docu_series": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4, a, span');
            for (var el of headings) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if ((t.includes('episode') || t.includes('ep.')) && (t.includes('inside') || t.includes('behind') || t.includes('matchday') || t.includes('series'))) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "press_conference_block": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a, span, p');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('press conference') || t.includes('rueda de prensa') || t.includes('pressekonferenz') || t.includes('conférence')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, article, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "social_native_content": {
        "js": """
            var els = document.querySelectorAll('[class*="social"], [class*="instagram"], [class*="tiktok"], [class*="stories"], iframe[src*="instagram"]');
            for (var el of els) {
                if (el.closest('nav, header, footer, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 30) return el.closest('section, div[class]') || el;
            }
            return null;
        """,
    },
    "transfer_news": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('transfer') || t.includes('signing') || t.includes('fichaje')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, article, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "interactive_fan_poll": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a, div');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('poll') || t.includes('vote') || t.includes('goal of the month') || t.includes('player of the month')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, article, div[class]') || el;
                }
            }
            return null;
        """,
    },

    # ── Tickets & Hospitality ──
    "tickets_block": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('ticket') || t.includes('entrada')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "hospitality_block": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('hospitality') || t.includes('vip') || t.includes('premium experience')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "stadium_tours_block": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('stadium tour') || t.includes('tour del estadio') || t.includes('bernabéu tour') || t.includes('stadium experience')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },

    # ── Commerce ──
    "store_block": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('shop') || t.includes('store') || t.includes('tienda') || t.includes('kit') || t.includes('merch') || t.includes('boutique')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            var els = document.querySelectorAll('[class*="shop"], [class*="store"], [class*="product"], [class*="merch"]');
            for (var el of els) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 100 && el.getBoundingClientRect().width > 300) return el;
            }
            return null;
        """,
    },
    "store_individual_products": { "same_as": "store_block" },

    # ── Community & Membership ──
    "newsletter_signup": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, form, div');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('newsletter') || t.includes('subscribe') || t.includes('suscríbete')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, form, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "fan_club_signup": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('member') || t.includes('join') || t.includes('sign up') || t.includes('madridista') || t.includes('community') || t.includes('comunidad')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "paid_membership": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4, a');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('premium') || t.includes('subscribe') || t.includes('membership plan') || t.includes('become a member') || t.includes('join now')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },

    # ── Heritage ──
    "trophies_honours": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('trophy') || t.includes('honour') || t.includes('palmarés') || t.includes('palmares') || t.includes('leyenda') || t.includes('titles')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "heritage_past_content": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('heritage') || t.includes('history') || t.includes('on this day') || t.includes('throwback') || t.includes('historia') || t.includes('legends') || t.includes('specials') || t.includes('especiales')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "stadium_content_block": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('stadium') || t.includes('bernabéu') || t.includes('anfield') || t.includes('etihad') || t.includes('parc des princes') || t.includes('estadio') || t.includes('old trafford')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "museum_block": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('museum') || t.includes('museo') || t.includes('museu')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },

    # ── Players & Teams ──
    "player_roster_preview": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('squad') || t.includes('roster') || t.includes('players') || t.includes('plantilla') || t.includes('jugadores')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "individual_player_cards": { "same_as": "player_roster_preview" },
    "womens_team_featured": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a, span');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes("women") || t.includes("femeni") || t.includes("femenino") || t.includes("wsl") || t.includes("féminin")) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) return el.closest('section, article, div[class], a') || el;
                }
            }
            return null;
        """,
    },
    "academy_youth_block": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a, span');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('academy') || t.includes('youth') || t.includes('u18') || t.includes('u21') || t.includes('cantera') || t.includes('masia')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, article, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "charity_csr_block": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('foundation') || t.includes('charity') || t.includes('community') || t.includes('fundación') || t.includes('fundació')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "quiz_trivia": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a, div');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('quiz') || t.includes('trivia') || t.includes('predict')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, article, div[class]') || el;
                }
            }
            return null;
        """,
    },

    # ── Partners / Footer ──
    "footer_sponsor_wall": {
        "js": """
            var footer = document.querySelector('footer') || document.body;
            var imgs = footer.querySelectorAll('img');
            var bottomImgs = [];
            for (var i of imgs) {
                var r = i.getBoundingClientRect();
                var absY = r.top + window.scrollY;
                if (absY > document.body.scrollHeight * 0.7 && r.width < 200 && r.height < 100 && r.width > 10) bottomImgs.push(i);
            }
            if (bottomImgs.length >= 3) return bottomImgs[0].closest('div[class], section') || bottomImgs[0].parentElement;
            return null;
        """,
    },
    "in_content_sponsor": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, span, div');
            for (var el of all) {
                if (el.closest('nav, header, footer, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('presented by') || t.includes('sponsored by') || t.includes('powered by')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y} && absY < document.body.scrollHeight * 0.8) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "app_store_badges": {
        "js": """
            var els = document.querySelectorAll('a[href*="apps.apple"], a[href*="play.google"], a[href*="itunes"], img[alt*="App Store"], img[alt*="Google Play"]');
            for (var el of els) {
                if (el.getBoundingClientRect().height > 10) return el.closest('div[class], section') || el;
            }
            return null;
        """,
    },
    "club_tv_app_promo": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4, a, div');
            for (var el of headings) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('rm play') || t.includes('rmtv') || t.includes('lfctv') || t.includes('city+') || t.includes('mutv') || t.includes('spursplay') || t.includes('psgtv') || t.includes('barça one') || t.includes('fc bayern.tv')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "social_links_in_footer": {
        "js": """
            var footer = document.querySelector('footer') || document.body;
            var socials = footer.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"]');
            if (socials.length >= 2) return socials[0].closest('div[class], ul, nav') || socials[0].parentElement;
            return null;
        """,
    },
}


def capture_feature(page, feature_key, club_id):
    """Capture a screenshot for one feature."""
    locator = LOCATORS.get(feature_key)
    if not locator:
        print(f"    [NO LOCATOR] {feature_key}")
        return False

    out_path = IMG_DIR / f"{club_id}_{feature_key}.png"

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
        # Try locating using referenced feature's locator
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


def process_club(browser, club_id, url):
    """Process all TRUE features for a club."""
    print(f"\n{'='*60}")
    print(f"CLUB: {club_id} ({url})")
    print(f"{'='*60}")

    true_features = get_true_features(club_id)
    print(f"  TRUE features: {len(true_features)}")

    context = browser.new_context(
        viewport={"width": 1400, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    page = context.new_page()

    try:
        height = setup_page(page, url, club_id)

        captured = 0
        skipped = 0
        for feature in true_features:
            if capture_feature(page, feature, club_id):
                captured += 1
            else:
                skipped += 1

        print(f"\n  ✅ {captured} captured, {skipped} skipped / {len(true_features)} TRUE")
    except Exception as e:
        print(f"  ❌ FATAL: {e}")
        captured, skipped = 0, len(true_features)
    finally:
        context.close()

    return captured, skipped


def main():
    clubs = list(BATCH1_URLS.keys())

    if len(sys.argv) > 1:
        clubs = [c for c in sys.argv[1:] if c in BATCH1_URLS]
        if not clubs:
            print(f"Unknown club(s). Available: {list(BATCH1_URLS.keys())}")
            sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        total_c, total_s = 0, 0
        for club_id in clubs:
            c, s = process_club(browser, club_id, BATCH1_URLS[club_id])
            total_c += c
            total_s += s

        browser.close()

    print(f"\n{'='*60}")
    print(f"BATCH 1 TOTAL: {total_c} captured, {total_s} skipped")
    print(f"Output: {IMG_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
