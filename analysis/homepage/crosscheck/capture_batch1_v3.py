#!/usr/bin/env python3
"""
Batch 1 v3: Re-capture with improved locators and cookie handling.
Fixes: Bayern cookie wall, broader news/results/footer locators.
Only re-captures clubs with issues: Real Madrid, Bayern, Man City, Man United, Tottenham.
PSG already complete. Liverpool postponed (Hillsborough memorial).
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

CLUBS = {
    "real_madrid": "https://www.realmadrid.com/en",
    "bayern_munich": "https://fcbayern.com/en",
    "man_city": "https://www.mancity.com",
    "man_united": "https://www.manutd.com",
    "tottenham": "https://www.tottenhamhotspur.com",
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
        if clip["width"] <= 0 or clip["height"] <= 0:
            return False
        clip["x"] = max(0, clip["x"])
        clip["y"] = max(0, clip["y"])
        page.screenshot(path=str(path), clip=clip, full_page=full_page, timeout=60000)
        return True
    except Exception as e:
        print(f"    [screenshot error] {str(e)[:100]}")
        return False


def dismiss_cookies(page, club_id):
    """Enhanced cookie dismissal with site-specific handlers."""

    # Bayern Munich: Usercentrics
    if club_id == "bayern_munich":
        safe_eval(page, """() => {
            try { if (typeof UC_UI !== 'undefined') { UC_UI.acceptAllConsents(); UC_UI.closeCMP(); } } catch(e) {}
            try {
                var ucRoot = document.querySelector('#usercentrics-root');
                if (ucRoot && ucRoot.shadowRoot) {
                    var btns = ucRoot.shadowRoot.querySelectorAll('button');
                    for (var b of btns) {
                        var txt = (b.textContent || '').toLowerCase().trim();
                        if (txt.includes('accept all') || txt.includes('alle akzeptieren')) { b.click(); break; }
                    }
                }
            } catch(e) {}
            try { var ucRoot = document.querySelector('#usercentrics-root'); if (ucRoot) ucRoot.remove(); } catch(e) {}
            document.body.style.overflow = 'auto';
            document.documentElement.style.overflow = 'auto';
        }""")
        time.sleep(2)

    # Bundesliga (non-Bayern): consentmanager
    if club_id in ("vfb_stuttgart", "bvb_dortmund", "eintracht", "rb_leipzig"):
        safe_eval(page, '() => { try { window.__cmp("setConsent", 0); } catch(e) {} }')
        time.sleep(2)
        safe_eval(page, """() => {
            var btns = document.querySelectorAll('button, a, [role="button"]');
            for (var b of btns) {
                var txt = (b.textContent || '').toLowerCase().trim();
                if (txt.includes('accept all') || txt.includes('alle akzeptieren') || txt === 'accept') {
                    b.click(); return true;
                }
            }
            return false;
        }""")
        time.sleep(2)

    # Generic cookie dismissal — multiple passes
    for attempt in range(6):
        safe_eval(page, """() => {
            var btns = document.querySelectorAll('button, a, [role="button"], span[role="button"]');
            var priorities = ['accept all', 'accept all cookies', 'allow all', 'agree to all',
                'accept', 'agree', 'consent', 'got it', 'ok', 'i understand',
                'reject all', 'decline all', 'necessary only', 'refuse', 'deny all',
                'save settings', 'confirm',
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
            return false;
        }""")
        time.sleep(1.5)

        height = safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0
        if height > 3000:
            break

    # Force-remove overlay elements
    safe_eval(page, """() => {
        try {
            document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="consent"], [class*="cookie"], [class*="gdpr"], [role="dialog"], [class*="backdrop"], [class*="mask"], [id*="onetrust"], [id*="didomi"], [class*="cmpbox"], [id*="cmpbox"], [class*="consentmanager"]').forEach(function(e) {
                try { e.remove(); } catch(ex) {}
            });
        } catch(e) {}
        try {
            document.querySelectorAll('div, section, iframe').forEach(function(e) {
                try {
                    var s = window.getComputedStyle(e);
                    var r = e.getBoundingClientRect();
                    if ((s.position === 'fixed' || s.position === 'sticky') && r.width > 300 && r.height > 200 && parseInt(s.zIndex) > 50) e.remove();
                } catch(ex) {}
            });
        } catch(e) {}
        try { document.body.style.overflow = 'auto'; document.documentElement.style.overflow = 'auto'; } catch(e) {}
    }""")
    time.sleep(1)


def scroll_lazy_load(page):
    height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000
    steps = 10
    for i in range(1, steps + 1):
        safe_eval(page, f"window.scrollTo(0, {height * i // steps})")
        time.sleep(0.5)
    new_height = safe_eval(page, "document.body ? document.body.scrollHeight : 2000") or 2000
    if new_height > height + 500:
        for i in range(1, 6):
            safe_eval(page, f"window.scrollTo(0, {new_height * i // 5})")
            time.sleep(0.4)
    safe_eval(page, "window.scrollTo(0, 0)")
    time.sleep(2)
    return safe_eval(page, "document.body ? document.body.scrollHeight : 0") or 0


# ─── IMPROVED LOCATORS ───
# Key improvements:
# 1. Broader text matching for news sections (many sites use different headings)
# 2. Class-based detection as primary, heading-based as fallback
# 3. Better footer detection (not just heading-based)
# 4. Broader results_block detection

LOCATORS = {
    # ── Header (y < 120) ──
    "language_switcher_in_header": {
        "js": """
            var els = document.querySelectorAll('[class*="lang"], [class*="Lang"], [data-lang], [class*="locale"]');
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
            var el = document.querySelector('[class*="search"], [class*="Search"], [type="search"], [aria-label*="search"], [aria-label*="Search"]');
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
                if (r.top < 120 && r.height > 0 && (t === 'shop' || t === 'store' || t === 'tienda' || t === 'boutique' || t === 'fanshop' || t === 'online store')) return el;
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
                if (r.top < 120 && r.height > 0 && (t.includes('ticket') || t.includes('entrada') || t === 'entradas' || t.includes('tickets & hospitality'))) return el;
            }
            return null;
        """,
        "fallback": [400, 0, 1000, 50],
    },
    "sponsor_lockup_in_header": {
        "js": """
            var imgs = document.querySelectorAll('header img, [class*="header"] img, [class*="Header"] img, [class*="topbar"] img');
            var sponsors = [];
            for (var i of imgs) {
                var r = i.getBoundingClientRect();
                if (r.top < 80 && r.top > -10 && r.width > 20 && r.height > 10) sponsors.push(i);
            }
            if (sponsors.length > 0) return sponsors[0].closest('div') || sponsors[0].parentElement;
            return null;
        """,
        "fallback": [1000, 0, 1400, 50],
    },
    "persistent_bar_above_header": { "region": [0, 0, 1400, 50] },

    # ── Hero (y < 900) ──
    "hero_carousel": { "region": [0, 50, 1400, 600] },
    "secondary_editorial_strip_below_hero": {
        "js": """
            var cards = document.querySelectorAll('[class*="card"], [class*="Card"], [class*="editorial"], [class*="strip"], [class*="grid"]');
            for (var el of cards) {
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > 400 && absY < 1200 && el.getBoundingClientRect().height > 40 && el.getBoundingClientRect().height < 500) return el;
            }
            return null;
        """,
        "fallback": [0, 500, 1400, 900],
    },
    "brand_sponsor_highlighted_in_hero": { "region": [0, 0, 1400, 600] },

    # ── IMPROVED: News section (broader detection) ──
    "dedicated_news_section": {
        "js": """
            // Strategy 1: heading-based
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('news') || t.includes('latest') || t.includes('noticias') || t.includes('stories') || t.includes('articles') || t.includes('nachrichten') || t.includes('aktuell') || t.includes('today on') || t.includes('aktuelle')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) {
                        var section = h.closest('section, div[class]');
                        if (section && section.getBoundingClientRect().height > 100) return section;
                        return h;
                    }
                }
            }
            // Strategy 2: class-based (many sites use 'news' in class names)
            var newsEls = document.querySelectorAll('[class*="news-grid"], [class*="newsGrid"], [class*="news-list"], [class*="newsList"], [class*="article-grid"], [class*="articleGrid"], [class*="latest-news"], [class*="latestNews"], [data-component*="news"], [class*="editorial-grid"]');
            for (var el of newsEls) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 100) return el;
            }
            // Strategy 3: Find a section with multiple article cards
            var sections = document.querySelectorAll('main section, [role="main"] section');
            for (var s of sections) {
                var articles = s.querySelectorAll('article, [class*="card"], [class*="Card"]');
                var absY = s.getBoundingClientRect().top + window.scrollY;
                if (articles.length >= 3 && absY > {min_y} && s.getBoundingClientRect().height > 200) return s;
            }
            return null;
        """,
    },
    "news_rich_structure": { "same_as": "dedicated_news_section" },

    # ── IMPROVED: Match blocks (broader detection) ──
    "next_match_block": {
        "js": """
            // Class-based
            var matchEls = document.querySelectorAll('[class*="fixture"], [class*="Fixture"], [class*="next-match"], [class*="nextMatch"], [class*="NextMatch"], [class*="upcoming"], [class*="matchday"], [class*="next-fixture"], [class*="nextFixture"]');
            for (var el of matchEls) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 50) return el;
            }
            // Heading-based
            var headings = document.querySelectorAll('h2, h3, h4, [class*="heading"]');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('next match') || t.includes('next fixture') || t.includes('upcoming') || t.includes('fixture') || t.includes('próximo')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "next_match_feature_rich": { "same_as": "next_match_block" },

    # ── IMPROVED: Results block ──
    "results_block": {
        "js": """
            // Class-based first
            var resultEls = document.querySelectorAll('[class*="result"], [class*="Result"], [class*="score"], [class*="Score"], [class*="last-match"], [class*="lastMatch"], [class*="recent-result"]');
            for (var el of resultEls) {
                if (el.closest('nav, header, footer, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 40 && el.getBoundingClientRect().width > 200) return el.closest('section, div[class]') || el;
            }
            // Score pattern search in main content
            var main = document.querySelector('main, [role="main"]') || document.body;
            var all = main.querySelectorAll('span, div, td, p');
            for (var el of all) {
                if (el.closest('nav, header, footer, [role="navigation"]')) continue;
                var t = (el.textContent || '').trim();
                if (/^\\d\\s*[-–:]\\s*\\d$/.test(t)) {
                    var section = el.closest('section, [class*="result"], [class*="match"], [class*="score"]');
                    var target = section || el;
                    var absY = target.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y} && target.getBoundingClientRect().height > 30) return target;
                }
            }
            // Heading-based
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('result') || t.includes('score') || t.includes('last result') || t.includes('ergebnis') || t.includes('resultado')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },

    # ── Video ──
    "homepage_video_block": {
        "js": """
            var headings = document.querySelectorAll('h2, h3');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('watch') || t.includes('video') || t.includes('highlights') || t.includes('vídeo') || t.includes('tv')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            var vids = document.querySelectorAll('[class*="video"], [class*="Video"], video, [class*="player"]');
            for (var el of vids) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 100 && el.getBoundingClientRect().width > 400) return el.closest('section, div[class]') || el;
            }
            return null;
        """,
    },
    "video_thumbnails_inline": { "same_as": "homepage_video_block" },
    "episodic_docu_series": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a, span');
            for (var el of all) {
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
                if (t.includes('press conference') || t.includes('pressekonferenz') || t.includes('conférence') || t.includes('rueda de prensa')) {
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
                if (t.includes('poll') || t.includes('vote') || t.includes('goal of the') || t.includes('player of the')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, article, div[class]') || el;
                }
            }
            return null;
        """,
    },

    # ── Tickets & Commerce ──
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
    "store_block": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('shop') || t.includes('store') || t.includes('tienda') || t.includes('kit') || t.includes('merch') || t.includes('boutique') || t.includes('fanshop')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            var els = document.querySelectorAll('[class*="shop"], [class*="store"], [class*="product"], [class*="merch"], [class*="Store"], [class*="Shop"]');
            for (var el of els) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var absY = el.getBoundingClientRect().top + window.scrollY;
                if (absY > {min_y} && el.getBoundingClientRect().height > 100 && el.getBoundingClientRect().width > 300) return el;
            }
            return null;
        """,
    },
    "store_individual_products": { "same_as": "store_block" },
    "stadium_tours_block": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('stadium tour') || t.includes('tour') || t.includes('bernabéu tour') || t.includes('stadium experience')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },

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
                if (t.includes('member') || t.includes('join') || t.includes('sign up') || t.includes('madridista') || t.includes('community') || t.includes('fan club')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "paid_membership": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, a, div');
            for (var el of all) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('premium') || t.includes('subscribe') || t.includes('membership plan') || t.includes('become a member') || t.includes('join now') || t.includes('fc bayern membership')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
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
                if (t.includes('trophy') || t.includes('honour') || t.includes('palmarés') || t.includes('titles') || t.includes('palmares') || t.includes('treble')) {
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
                if (t.includes('heritage') || t.includes('history') || t.includes('on this day') || t.includes('throwback') || t.includes('legends') || t.includes('specials') || t.includes('klassiker') || t.includes('retro') || t.includes('classic')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "anniversary_milestone": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4');
            for (var h of headings) {
                if (h.closest('nav, header, [role="navigation"]')) continue;
                var t = (h.textContent || '').toLowerCase();
                if (t.includes('anniversary') || t.includes('jubiläum') || t.includes('milestone') || t.includes('birthday') || t.includes('años') || t.includes('years')) {
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
                if (t.includes('stadium') || t.includes('bernabéu') || t.includes('anfield') || t.includes('etihad') || t.includes('old trafford') || t.includes('allianz arena') || t.includes('estadio') || t.includes('tottenham hotspur stadium')) {
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
                if (t.includes('squad') || t.includes('roster') || t.includes('players') || t.includes('plantilla') || t.includes('mannschaft') || t.includes('kader')) {
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
                if (t.includes("women") || t.includes("femeni") || t.includes("femenino") || t.includes("wsl") || t.includes("frauen")) {
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
                if (t.includes('academy') || t.includes('youth') || t.includes('u18') || t.includes('u21') || t.includes('cantera') || t.includes('nachwuchs')) {
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
                if (t.includes('foundation') || t.includes('charity') || t.includes('community') || t.includes('fundación') || t.includes('stiftung') || t.includes('cityzens')) {
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
    "ai_chat_assistant": {
        "js": """
            var all = document.querySelectorAll('[class*="chat"], [class*="Chat"], [class*="assistant"], [class*="ai-"], [class*="bot"], [id*="chat"]');
            for (var el of all) {
                if (el.getBoundingClientRect().height > 10) return el;
            }
            return null;
        """,
    },

    # ── IMPROVED: Footer features ──
    "footer_sponsor_wall": {
        "js": """
            // Look for sponsor logos in bottom 30% of page
            var pageH = document.body.scrollHeight;
            var threshold = pageH * 0.65;
            // Find sections with multiple images (likely sponsor wall)
            var sections = document.querySelectorAll('footer, footer div, section, div[class]');
            for (var s of sections) {
                var absY = s.getBoundingClientRect().top + window.scrollY;
                if (absY < threshold) continue;
                var imgs = s.querySelectorAll('img');
                var validImgs = 0;
                for (var i of imgs) {
                    var r = i.getBoundingClientRect();
                    if (r.width > 10 && r.width < 250 && r.height > 10 && r.height < 120) validImgs++;
                }
                if (validImgs >= 3 && s.getBoundingClientRect().height < 400) return s;
            }
            // Fallback: heading-based
            var headings = document.querySelectorAll('h2, h3, h4, h5, h6, span, p');
            for (var h of headings) {
                var t = (h.textContent || '').toLowerCase().trim();
                if (t.includes('partner') || t.includes('sponsor') || t.includes('patrocinador')) {
                    var absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > threshold) return h.closest('section, div[class], footer div') || h;
                }
            }
            return null;
        """,
    },
    "in_content_sponsor": {
        "js": """
            var all = document.querySelectorAll('h2, h3, h4, span, div, a');
            for (var el of all) {
                if (el.closest('nav, header, footer, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('presented by') || t.includes('sponsored by') || t.includes('powered by') || t.includes('brought to you by')) {
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
                if (el.closest('nav, [class*="menu"], [class*="sidebar"], [class*="drawer"]')) continue;
                var r = el.getBoundingClientRect();
                var absY = r.top + window.scrollY;
                if (r.height > 10 && absY > {min_y}) return el.closest('div[class], section') || el;
            }
            return null;
        """,
    },
    "club_tv_app_promo": {
        "js": """
            var headings = document.querySelectorAll('h2, h3, h4, a, div, span');
            for (var el of headings) {
                if (el.closest('nav, header, [role="navigation"]')) continue;
                var t = (el.textContent || '').toLowerCase();
                if (t.includes('rm play') || t.includes('rmtv') || t.includes('lfctv') || t.includes('city+') || t.includes('mutv') || t.includes('spursplay') || t.includes('fc bayern.tv') || t.includes('barca one') || t.includes('psgtv')) {
                    var absY = el.getBoundingClientRect().top + window.scrollY;
                    if (absY > {min_y}) return el.closest('section, div[class]') || el;
                }
            }
            return null;
        """,
    },
    "social_links_in_footer": {
        "js": """
            // Look for social links in footer or bottom area
            var footer = document.querySelector('footer');
            if (!footer) {
                // Try finding footer-like area
                var divs = document.querySelectorAll('div[class]');
                for (var d of divs) {
                    var absY = d.getBoundingClientRect().top + window.scrollY;
                    if (absY > document.body.scrollHeight * 0.8) { footer = d; break; }
                }
            }
            if (!footer) footer = document.body;
            var socials = footer.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"], a[href*="linkedin"]');
            if (socials.length >= 2) return socials[0].closest('div[class], ul, nav, footer div') || socials[0].parentElement;
            return null;
        """,
    },
}


def capture_feature(page, feature_key, club_id):
    locator = LOCATORS.get(feature_key)
    if not locator:
        print(f"    [NO LOCATOR] {feature_key}")
        return False

    out_path = IMG_DIR / f"{club_id}_{feature_key}.png"

    # Region-based
    if "region" in locator:
        r = locator["region"]
        if safe_screenshot(page, out_path, {"x": r[0], "y": r[1], "width": r[2]-r[0], "height": r[3]-r[1]}):
            print(f"    [region] {feature_key}")
            return True
        return False

    # Same-as
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

    # JS-based
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

    fb = locator.get("fallback")
    if fb:
        if safe_screenshot(page, out_path, {"x": fb[0], "y": fb[1], "width": fb[2]-fb[0], "height": fb[3]-fb[1]}):
            print(f"    [fallback] {feature_key}")
            return True

    print(f"    [SKIP] {feature_key}")
    return False


def process_club(page, club_id, url):
    print(f"\n{'='*60}")
    print(f"CLUB: {club_id} ({url})")
    print(f"{'='*60}")

    true_features = get_true_features(club_id)
    print(f"  TRUE features: {len(true_features)}")

    # Navigate
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
    except Exception as e:
        print(f"  Navigation warning: {str(e)[:80]}")
    time.sleep(6)

    dismiss_cookies(page, club_id)
    height = scroll_lazy_load(page)
    print(f"  Page height: {height}px")

    if height < 3000:
        print(f"  ⚠️ Short page — retrying...")
        dismiss_cookies(page, club_id)
        time.sleep(3)
        try:
            page.reload(wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
        time.sleep(5)
        dismiss_cookies(page, club_id)
        height = scroll_lazy_load(page)
        print(f"  After retry: {height}px")

    captured = 0
    skipped = []
    for feature in true_features:
        if capture_feature(page, feature, club_id):
            captured += 1
        else:
            skipped.append(feature)

    print(f"\n  Result: {captured}/{len(true_features)}")
    if skipped:
        print(f"  Skipped: {', '.join(skipped)}")
    return captured, len(true_features), skipped


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        context.add_init_script('Object.defineProperty(navigator, "webdriver", { get: () => undefined })')

        page = context.new_page()
        results = {}

        for club_id, url in CLUBS.items():
            captured, total, skipped = process_club(page, club_id, url)
            results[club_id] = {"captured": captured, "total": total, "skipped": skipped}

        context.close()
        browser.close()

    print(f"\n{'='*60}")
    print("SUMMARY")
    for club_id, r in results.items():
        print(f"  {club_id}: {r['captured']}/{r['total']}")
        if r['skipped']:
            print(f"    Skipped: {', '.join(r['skipped'])}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
