#!/usr/bin/env python3
"""
Re-capture all deleted screenshots from the image review.
Uses Playwright to navigate, dismiss cookies, scroll for lazy-loading,
and capture element-level screenshots.
"""

import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent  # analysis/homepage/
RESULTS = BASE / "results"
IMG_DIR = BASE / "crosscheck" / "img"
IMG_DIR.mkdir(exist_ok=True)

# ── All deleted images organized by club ──
DELETED = {
    "ac_milan": {
        "url": "https://www.acmilan.com/en",
        "features": ["store_block", "store_individual_products", "video_thumbnails_inline"],
    },
    "arsenal": {
        "url": "https://www.arsenal.com",
        "features": ["academy_youth_block"],
    },
    "aston_villa": {
        "url": "https://www.avfc.co.uk",
        "features": ["brand_sponsor_highlighted_in_hero", "hero_carousel", "dedicated_news_section", "news_rich_structure", "sponsor_lockup_in_header"],
    },
    "atletico_madrid": {
        "url": "https://www.atleticodemadrid.com",
        "features": ["dedicated_news_section", "news_rich_structure", "secondary_editorial_strip_below_hero", "shop_shortcut_in_header"],
        # search_input_in_header already flipped to FALSE
    },
    "atp_tour": {
        "url": "https://www.atptour.com",
        "features": ["app_store_badges"],
    },
    "bayern_munich": {
        "url": "https://fcbayern.com/en",
        "features": ["dedicated_news_section", "news_rich_structure", "interactive_fan_poll", "paid_membership", "secondary_editorial_strip_below_hero", "sponsor_lockup_in_header", "trophies_honours", "video_thumbnails_inline"],
    },
    "brentford": {
        "url": "https://www.brentfordfc.com",
        "features": ["app_store_badges", "search_input_in_header", "shop_shortcut_in_header", "tickets_shortcut_in_header", "store_block"],
    },
    "club_brugge": {
        "url": "https://www.clubbrugge.be",
        "features": ["footer_sponsor_wall", "results_block", "shop_shortcut_in_header", "store_block", "tickets_shortcut_in_header"],
    },
    "f1": {
        "url": "https://www.formula1.com",
        "features": ["footer_sponsor_wall", "login_account"],
    },
    "fc_barcelona": {
        "url": "https://www.fcbarcelona.com/en",
        "features": ["app_store_badges", "fan_club_signup", "heritage_past_content"],
    },
    "inter_milan": {
        "url": "https://www.inter.it/en",
        "features": ["login_account"],
    },
    "itf_tennis": {
        "url": "https://www.itftennis.com",
        "features": ["app_store_badges", "language_switcher_in_header", "login_account", "search_input_in_header", "shop_shortcut_in_header", "social_links_in_footer"],
    },
    "juventus": {
        "url": "https://www.juventus.com/en",
        "features": ["academy_youth_block", "dedicated_news_section", "news_rich_structure", "next_match_block", "next_match_feature_rich", "shop_shortcut_in_header", "social_links_in_footer", "tickets_shortcut_in_header", "womens_team_featured"],
    },
    "man_city": {
        "url": "https://www.mancity.com",
        "features": ["academy_youth_block", "results_block", "womens_team_featured"],
    },
    "man_united": {
        "url": "https://www.manutd.com",
        "features": ["homepage_video_block", "shop_shortcut_in_header", "video_thumbnails_inline"],
    },
    "mls": {
        "url": "https://www.mlssoccer.com",
        "features": ["app_store_badges", "footer_sponsor_wall"],
    },
    "mlb": {
        "url": "https://www.mlb.com",
        "features": ["in_content_sponsor"],
    },
    "motogp": {
        "url": "https://www.motogp.com",
        "features": ["app_store_badges", "login_account", "predictor_fantasy", "social_links_in_footer"],
    },
    "nba": {
        "url": "https://www.nba.com",
        "features": ["search_input_in_header", "shop_shortcut_in_header", "tickets_shortcut_in_header"],
    },
    "newcastle": {
        "url": "https://www.newcastleunited.com",
        "features": ["dedicated_news_section", "footer_sponsor_wall", "news_rich_structure", "secondary_editorial_strip_below_hero", "video_thumbnails_inline"],
    },
    "rb_leipzig": {
        "url": "https://www.rbleipzig.com/en",
        "features": ["app_store_badges", "fan_club_signup"],
    },
    "real_madrid": {
        "url": "https://www.realmadrid.com/en",
        "features": ["dedicated_news_section", "footer_sponsor_wall", "language_switcher_in_header", "login_account", "news_rich_structure", "paid_membership", "results_block", "search_input_in_header", "social_links_in_footer", "sponsor_lockup_in_header"],
    },
    "sl_benfica": {
        "url": "https://www.slbenfica.pt",
        "features": ["dedicated_news_section", "news_rich_structure", "persistent_bar_above_header", "results_block", "secondary_editorial_strip_below_hero", "shop_shortcut_in_header", "store_block", "store_individual_products", "tickets_block", "tickets_shortcut_in_header", "video_thumbnails_inline"],
    },
    "tottenham": {
        "url": "https://www.tottenhamhotspur.com",
        "features": ["dedicated_news_section", "news_rich_structure", "results_block", "social_links_in_footer"],
    },
    "uefa": {
        "url": "https://www.uefa.com",
        "features": ["dedicated_news_section", "in_content_sponsor", "language_switcher_in_header", "login_account", "news_rich_structure", "standings_block"],
    },
    "valencia_cf": {
        "url": "https://www.valenciacf.com",
        "features": ["club_tv_app_promo", "language_switcher_in_header", "paid_membership", "results_block", "store_block"],
    },
    "west_ham": {
        "url": "https://www.whufc.com",
        "features": ["club_tv_app_promo", "hero_carousel", "newsletter_signup", "results_block", "secondary_editorial_strip_below_hero", "transfer_news", "video_thumbnails_inline"],
    },
}

# ── Cookie dismissal strategies by site ──
COOKIE_STRATEGIES = {
    "bayern_munich": "usercentrics",
    "bvb_dortmund": "consentmanager",
    "vfb_stuttgart": "consentmanager",
    "eintracht": "consentmanager",
    "rb_leipzig": "consentmanager",
    "fc_barcelona": "didomi",
    "psg": "didomi",
}

def dismiss_cookies_generic(page):
    """Try multiple cookie dismissal strategies."""
    # Strategy 1: Click common accept/reject buttons
    page.evaluate("""
        const btns = document.querySelectorAll('button, a, [role="button"]');
        for (const b of btns) {
            const txt = (b.textContent || '').toLowerCase().trim();
            if (txt.includes('accept all') || txt.includes('reject all') || txt.includes('agree')
                || txt.includes('confirm') || txt.includes('necessary only')
                || txt.includes('decline') || txt.includes('deny all')
                || txt.includes('accept') || txt.includes('aceitar') || txt.includes('aceptar')
                || txt.includes('akzeptieren') || txt.includes('alle akzeptieren')
                || txt.includes('allow all') || txt.includes('i agree')) {
                b.click(); break;
            }
        }
    """)
    time.sleep(1)

    # Strategy 2: Remove overlays
    page.evaluate("""
        document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="cookie"], [class*="consent"], [class*="banner"], [role="dialog"], [class*="backdrop"]').forEach(e => {
            if (e.getBoundingClientRect().height > 100) e.remove();
        });
        // Remove fixed/absolute overlays with high z-index
        document.querySelectorAll('div, section').forEach(e => {
            const s = window.getComputedStyle(e);
            const r = e.getBoundingClientRect();
            if ((s.position === 'fixed' || s.position === 'absolute') && r.width > 300 && r.height > 200 && parseInt(s.zIndex) > 100) {
                // Don't remove the header
                if (r.top > 50 || r.height > 400) e.remove();
            }
        });
    """)
    time.sleep(0.5)


def dismiss_cookies_consentmanager(page):
    """For Bundesliga sites using consentmanager."""
    try:
        page.evaluate("window.__cmp && window.__cmp('setConsent', 0)")
        time.sleep(1)
    except:
        pass
    dismiss_cookies_generic(page)


def dismiss_cookies_usercentrics(page):
    """For Bayern Munich using Usercentrics."""
    try:
        page.evaluate("""
            if (window.UC_UI) {
                UC_UI.acceptAllConsents();
                UC_UI.closeCMP();
            }
        """)
        time.sleep(1)
        page.evaluate("""
            const uc = document.getElementById('usercentrics-root');
            if (uc) uc.remove();
        """)
    except:
        pass
    dismiss_cookies_generic(page)


def dismiss_cookies_didomi(page):
    """For FCB, PSG using Didomi."""
    try:
        page.evaluate("""
            const btn = document.getElementById('didomi-notice-agree-button');
            if (btn) btn.click();
        """)
        time.sleep(1)
    except:
        pass
    dismiss_cookies_generic(page)


def dismiss_popups(page):
    """Remove promotional popups and overlays."""
    page.evaluate("""
        // Click close buttons
        var btns = document.querySelectorAll('[class*="close"], [aria-label="Close"], [aria-label="close"], .modal-close, [class*="dismiss"]');
        btns.forEach(b => { try { b.click(); } catch(e) {} });

        // Remove modals, popups, overlays
        document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="lightbox"], [class*="promo"], [class*="interstitial"], [class*="takeover"], [role="dialog"], [class*="backdrop"], [class*="mask"]').forEach(e => {
            if (e.getBoundingClientRect().height > 100) e.remove();
        });
    """)
    time.sleep(0.5)


def dismiss_cookies(page, club_id):
    """Dispatch to the correct cookie strategy for this club."""
    strategy = COOKIE_STRATEGIES.get(club_id, "generic")
    if strategy == "usercentrics":
        dismiss_cookies_usercentrics(page)
    elif strategy == "consentmanager":
        dismiss_cookies_consentmanager(page)
    elif strategy == "didomi":
        dismiss_cookies_didomi(page)
    else:
        dismiss_cookies_generic(page)


def scroll_page(page):
    """Scroll to trigger lazy-loading content."""
    try:
        height = page.evaluate("document.body.scrollHeight")
        steps = min(height // 500, 20)  # Cap at 20 steps
        for i in range(steps):
            try:
                page.evaluate(f"window.scrollTo(0, {(i + 1) * 500})")
                time.sleep(0.3)
            except:
                break
        time.sleep(2)
        try:
            page.evaluate("window.scrollTo(0, 0)")
        except:
            pass
        time.sleep(1)
    except Exception as e:
        print(f"  ⚠️  Scroll error: {e}")
        time.sleep(1)


def get_element_bounds(page, feature):
    """Find the element for a feature and return its bounding box."""
    locators = get_feature_locator(feature)
    if not locators:
        return None

    for js_code in locators:
        try:
            bounds = page.evaluate(f"""
                (() => {{
                    const el = (() => {{ {js_code} }})();
                    if (!el) return null;
                    el.scrollIntoView({{ behavior: 'instant', block: 'center' }});
                    // Wait for scroll
                    return new Promise(resolve => {{
                        setTimeout(() => {{
                            const r = el.getBoundingClientRect();
                            resolve({{
                                x: Math.max(0, Math.round(r.x - 20)),
                                y: Math.max(0, Math.round(r.y - 20)),
                                width: Math.min(1400, Math.round(r.width + 40)),
                                height: Math.min(900, Math.round(r.height + 40))
                            }});
                        }}, 500);
                    }});
                }})()
            """)
            if bounds and bounds["width"] > 20 and bounds["height"] > 10:
                return bounds
        except Exception as e:
            continue

    return None


def get_feature_locator(feature):
    """Return list of JS locator scripts for a feature."""
    locators = {
        # ── Header features ──
        "language_switcher_in_header": [
            """
            const els = document.querySelectorAll('[class*="lang"], [class*="Lang"], [data-lang], [class*="locale"], [class*="Locale"]');
            if (els.length) { const e = els[0]; if (e.getBoundingClientRect().top < 120) return e; }
            const all = document.querySelectorAll('a, button, select, span');
            for (const el of all) {
                const t = (el.textContent || '').trim();
                if (/^(EN|ES|CA|DE|FR|IT|PT|Deutsch|English|Español|Français)$/i.test(t)) {
                    if (el.getBoundingClientRect().top < 120) return el;
                }
            }
            return null;
            """,
        ],
        "login_account": [
            """
            const els = document.querySelectorAll('[class*="login"], [class*="Login"], [class*="account"], [class*="Account"], [class*="profile"], [class*="signin"], [class*="SignIn"], [href*="login"], [href*="account"], [href*="signin"]');
            for (const el of els) { if (el.getBoundingClientRect().top < 120) return el; }
            const all = document.querySelectorAll('a, button');
            for (const el of all) {
                const t = (el.textContent || '').trim().toLowerCase();
                if ((t.includes('log in') || t.includes('login') || t.includes('sign in') || t.includes('register') || t.includes('acceder') || t === 'login') && el.getBoundingClientRect().top < 120) return el;
            }
            return null;
            """,
        ],
        "search_input_in_header": [
            """
            const el = document.querySelector('[class*="search"], [class*="Search"], [type="search"], [aria-label*="earch"], input[placeholder*="earch"], svg[class*="search"]');
            if (el && el.getBoundingClientRect().top < 120) return el;
            const all = document.querySelectorAll('a, button');
            for (const el of all) {
                const t = (el.textContent || '').trim().toLowerCase();
                if (t === 'search' && el.getBoundingClientRect().top < 120) return el;
            }
            return null;
            """,
        ],
        "shop_shortcut_in_header": [
            """
            const all = document.querySelectorAll('a, button');
            for (const el of all) {
                const t = (el.textContent || '').trim().toLowerCase();
                if ((t === 'shop' || t === 'store' || t === 'stores' || t === 'tienda' || t === 'fanshop' || t === 'tienda online' || t === 'boutique') && el.getBoundingClientRect().top < 120) return el;
            }
            return null;
            """,
        ],
        "tickets_shortcut_in_header": [
            """
            const all = document.querySelectorAll('a, button');
            for (const el of all) {
                const t = (el.textContent || '').trim().toLowerCase();
                if ((t.includes('ticket') || t.includes('entrada') || t === 'tickets' || t === 'entradas') && el.getBoundingClientRect().top < 120) return el;
            }
            return null;
            """,
        ],
        "sponsor_lockup_in_header": [
            """
            const imgs = document.querySelectorAll('header img, nav img, [class*="header"] img, [class*="Header"] img, [class*="topbar"] img, [class*="top-bar"] img');
            const sponsors = Array.from(imgs).filter(i => {
                const r = i.getBoundingClientRect();
                return r.top < 80 && i.naturalWidth > 20 && r.width > 15;
            });
            if (sponsors.length >= 1) {
                const parent = sponsors[0].closest('div, span, ul');
                if (parent) return parent;
                return sponsors[0];
            }
            return null;
            """,
        ],
        "persistent_bar_above_header": [
            """
            // Look for a thin bar at the very top of the page
            const firstChild = document.querySelector('body > div, body > header, body > nav');
            if (firstChild) {
                const r = firstChild.getBoundingClientRect();
                if (r.height < 60 && r.top < 5) return firstChild;
            }
            return null;
            """,
        ],

        # ── Hero ──
        "hero_carousel": [
            """
            const hero = document.querySelector('[class*="hero"], [class*="Hero"], [class*="banner"], [class*="Banner"], [class*="slider"], [class*="Slider"], [class*="swiper"], [class*="carousel"]');
            if (hero && hero.getBoundingClientRect().height > 100) return hero;
            return null;
            """,
        ],
        "secondary_editorial_strip_below_hero": [
            """
            const sections = document.querySelectorAll('section, div[class]');
            for (const s of sections) {
                const r = s.getBoundingClientRect();
                const absY = r.top + window.scrollY;
                if (absY > 400 && absY < 1200 && r.height > 40 && r.height < 400) {
                    const cards = s.querySelectorAll('a, article, [class*="card"]');
                    if (cards.length >= 2) return s;
                }
            }
            return null;
            """,
        ],
        "brand_sponsor_highlighted_in_hero": [
            """
            const hero = document.querySelector('[class*="hero"], [class*="Hero"], [class*="banner"], [class*="Banner"]');
            if (hero) return hero;
            return null;
            """,
        ],

        # ── Match ──
        "next_match_block": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, span, div');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('next match') || t.includes('fixture') || t.includes('matches') || t.includes('matchday') || t.includes('upcoming') || t.includes('próximo') || t.includes('prochain')) && h.getBoundingClientRect().top + window.scrollY > 100) {
                    const section = h.closest('section, div[class*="match"], div[class*="fixture"]');
                    if (section && section.getBoundingClientRect().height > 50) return section;
                }
            }
            const matchEls = document.querySelectorAll('[class*="fixture"], [class*="match"], [class*="Match"], [class*="Fixture"]');
            for (const el of matchEls) {
                const r = el.getBoundingClientRect();
                if (r.height > 80 && r.width > 200 && (r.top + window.scrollY) > 100) return el;
            }
            return null;
            """,
        ],
        "next_match_feature_rich": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, span, div');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('next match') || t.includes('fixture') || t.includes('matches') || t.includes('matchday') || t.includes('upcoming')) && h.getBoundingClientRect().top + window.scrollY > 100) {
                    const section = h.closest('section, div[class*="match"], div[class*="fixture"]');
                    if (section && section.getBoundingClientRect().height > 50) return section;
                }
            }
            return null;
            """,
        ],
        "results_block": [
            """
            const all = document.querySelectorAll('span, div, td, p');
            for (const el of all) {
                if (el.children.length === 0) {
                    const t = (el.textContent || '').trim();
                    if (/^\\d\\s*[-–:]\\s*\\d$/.test(t)) {
                        let section = el.closest('section, [class*="result"], [class*="Result"], [class*="match"], [class*="score"]');
                        if (section && section.getBoundingClientRect().height > 40) return section;
                    }
                }
            }
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('result') || t.includes('last match') || t.includes('latest score')) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],
        "standings_block": [
            """
            const tables = document.querySelectorAll('table');
            for (const t of tables) {
                const text = t.textContent || '';
                if (/PTS|points|pos|standing/i.test(text) && t.getBoundingClientRect().height > 50) return t.closest('section, div[class]') || t;
            }
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                const t = (h.textContent || '').toLowerCase();
                if (t.includes('standing') || t.includes('classifica') || t.includes('league table') || t.includes('coefficient')) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],

        # ── Content ──
        "dedicated_news_section": [
            """
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('news') || t.includes('latest') || t.includes('noticias') || t.includes('actualidad') || t.includes('stories') || t.includes('nachrichten') || t.includes('aktuell')) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 100) return section;
                }
            }
            return null;
            """,
        ],
        "news_rich_structure": [
            """
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('news') || t.includes('latest') || t.includes('noticias') || t.includes('stories')) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 100) return section;
                }
            }
            return null;
            """,
        ],
        "homepage_video_block": [
            """
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('video') || t.includes('highlight') || t.includes('watch') || t.includes('tv')) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 100) return section;
                }
            }
            return null;
            """,
        ],
        "video_thumbnails_inline": [
            """
            const videos = document.querySelectorAll('[class*="video"], [class*="Video"], video, [class*="play"]');
            for (const v of videos) {
                const r = v.getBoundingClientRect();
                if (r.height > 30 && (r.top + window.scrollY) > 200) {
                    const section = v.closest('section, div[class]');
                    if (section) return section;
                    return v;
                }
            }
            return null;
            """,
        ],
        "club_tv_app_promo": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, a, span');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('tv') || t.includes('watch') || t.includes('stream') || t.includes('play') || t.includes('vcf media')) {
                    const absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const section = h.closest('section, div[class]');
                        if (section && section.getBoundingClientRect().height > 50) return section;
                    }
                }
            }
            return null;
            """,
        ],
        "in_content_sponsor": [
            """
            const imgs = document.querySelectorAll('main img, [class*="content"] img, article img');
            for (const img of imgs) {
                const src = (img.src || '').toLowerCase();
                const alt = (img.alt || '').toLowerCase();
                const absY = img.getBoundingClientRect().top + window.scrollY;
                if (absY > 200 && (src.includes('sponsor') || src.includes('partner') || alt.includes('sponsor') || alt.includes('partner'))) {
                    return img.closest('div') || img;
                }
            }
            // Look for "presented by" or "powered by" text
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if ((t.includes('presented by') || t.includes('powered by') || t.includes('sponsored by')) && walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY > 200) {
                    return walker.currentNode.parentElement.closest('div[class]') || walker.currentNode.parentElement;
                }
            }
            return null;
            """,
        ],

        # ── Commerce ──
        "store_block": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('store') || t.includes('shop') || t.includes('tienda') || t.includes('fanshop') || t.includes('boutique') || t.includes('kollektion') || t.includes('merch')) && (h.getBoundingClientRect().top + window.scrollY) > 300) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 80) return section;
                }
            }
            return null;
            """,
        ],
        "store_individual_products": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('store') || t.includes('shop') || t.includes('tienda') || t.includes('fanshop') || t.includes('kollektion')) && (h.getBoundingClientRect().top + window.scrollY) > 300) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 80) return section;
                }
            }
            return null;
            """,
        ],
        "tickets_block": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('ticket') || t.includes('entrada') || t.includes('bilhete') || t.includes('secure your seat')) && (h.getBoundingClientRect().top + window.scrollY) > 300) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 50) return section;
                }
            }
            return null;
            """,
        ],

        # ── Footer ──
        "footer_sponsor_wall": [
            """
            const footer = document.querySelector('footer, [class*="footer"], [class*="Footer"]');
            if (footer) {
                const imgs = footer.querySelectorAll('img');
                if (imgs.length >= 3) {
                    const parent = imgs[0].closest('div[class], section, ul');
                    if (parent) return parent;
                    return footer;
                }
            }
            // Look for partner/sponsor section
            const headings = document.querySelectorAll('h2, h3, h4, span, p');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('partner') || t.includes('sponsor') || t.includes('patrocinador')) && (h.getBoundingClientRect().top + window.scrollY) > 2000) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],
        "social_links_in_footer": [
            """
            const footer = document.querySelector('footer, [class*="footer"], [class*="Footer"]');
            if (footer) {
                const social = footer.querySelector('[class*="social"], [class*="Social"], [class*="follow"]');
                if (social) return social;
                // Look for social icon links
                const links = footer.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"]');
                if (links.length >= 2) {
                    const parent = links[0].closest('div, ul, nav');
                    if (parent) return parent;
                }
            }
            return null;
            """,
        ],
        "app_store_badges": [
            """
            const imgs = document.querySelectorAll('img');
            for (const img of imgs) {
                const src = (img.src || '').toLowerCase();
                const alt = (img.alt || '').toLowerCase();
                if (src.includes('app-store') || src.includes('appstore') || src.includes('google-play') || src.includes('play-store') || src.includes('apple') || alt.includes('app store') || alt.includes('google play') || alt.includes('download')) {
                    const parent = img.closest('div, section, a');
                    if (parent) return parent;
                    return img;
                }
            }
            // Look for download text
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if ((t.includes('download') && t.includes('app')) || t.includes('app store') || t.includes('google play')) {
                    const el = walker.currentNode.parentElement.closest('section, div[class]');
                    if (el) return el;
                }
            }
            return null;
            """,
        ],

        # ── Community ──
        "fan_club_signup": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, a, span, div');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('fan') || t.includes('membership') || t.includes('member') || t.includes('join') || t.includes('sign up') || t.includes('register') || t.includes('madridista') || t.includes('culer') || t.includes('bulls bande')) && (h.getBoundingClientRect().top + window.scrollY) > 300) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 50) return section;
                }
            }
            return null;
            """,
        ],
        "paid_membership": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, a, span');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('premium') || t.includes('subscription') || t.includes('subscribe') || t.includes('membership') || t.includes('platinum') || t.includes('socio') || t.includes('hazte socio')) && (h.getBoundingClientRect().top + window.scrollY) > 200) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 50) return section;
                }
            }
            return null;
            """,
        ],
        "newsletter_signup": [
            """
            const inputs = document.querySelectorAll('input[type="email"], input[placeholder*="email"], input[placeholder*="Email"]');
            for (const inp of inputs) {
                const section = inp.closest('section, div[class], form');
                if (section) return section;
            }
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('newsletter') || t.includes('subscribe') || t.includes('sign up')) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],

        # ── Heritage/Players ──
        "heritage_past_content": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('heritage') || t.includes('history') || t.includes('legend') || t.includes('on this day') || t.includes('classic') || t.includes('historia')) && (h.getBoundingClientRect().top + window.scrollY) > 200) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],
        "trophies_honours": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('trophy') || t.includes('trophies') || t.includes('honours') || t.includes('palmares') || t.includes('track record')) && (h.getBoundingClientRect().top + window.scrollY) > 200) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],
        "academy_youth_block": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, a, span');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('academy') || t.includes('youth') || t.includes('u18') || t.includes('u21') || t.includes('u23') || t.includes('nachwuchs') || t.includes('academia') || t.includes('cantera')) && (h.getBoundingClientRect().top + window.scrollY) > 300) {
                    const section = h.closest('section, div[class], article');
                    if (section && section.getBoundingClientRect().height > 30) return section;
                }
            }
            return null;
            """,
        ],
        "womens_team_featured": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, a, span, div');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('women') || t.includes('femen') || t.includes('frauen') || t.includes('féminin')) && (h.getBoundingClientRect().top + window.scrollY) > 200) {
                    const section = h.closest('section, article, div[class]');
                    if (section && section.getBoundingClientRect().height > 30) return section;
                }
            }
            return null;
            """,
        ],

        # ── Niche features ──
        "interactive_fan_poll": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('poll') || t.includes('vote') || t.includes('quiz') || t.includes('fan') || t.includes('predict')) && (h.getBoundingClientRect().top + window.scrollY) > 200) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],
        "predictor_fantasy": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, a');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('fantasy') || t.includes('predictor') || t.includes('predict') || t.includes('pick') || t.includes('game')) && (h.getBoundingClientRect().top + window.scrollY) > 200) {
                    const section = h.closest('section, div[class]');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],
        "transfer_news": [
            """
            const headings = document.querySelectorAll('h1, h2, h3, h4, a, span');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if ((t.includes('transfer') || t.includes('signing') || t.includes('rumour') || t.includes('fichaje')) && (h.getBoundingClientRect().top + window.scrollY) > 200) {
                    const section = h.closest('section, div[class], article');
                    if (section) return section;
                }
            }
            return null;
            """,
        ],
    }

    return locators.get(feature, [])


def capture_feature(page, club_id, feature, viewport_width=1400, viewport_height=900):
    """Capture a screenshot for a specific feature on the current page."""
    bounds = get_element_bounds(page, feature)
    if not bounds:
        print(f"    ⚠️  {feature}: element not found")
        return False

    # Ensure element is scrolled into view and take screenshot
    time.sleep(0.5)

    filename = f"{club_id}_{feature}.png"
    filepath = IMG_DIR / filename

    try:
        # Clip the screenshot to the element bounds
        page.screenshot(
            path=str(filepath),
            clip={
                "x": bounds["x"],
                "y": bounds["y"],
                "width": min(bounds["width"], viewport_width - bounds["x"]),
                "height": min(bounds["height"], viewport_height - bounds["y"]),
            }
        )
        print(f"    ✅ {feature}: captured ({bounds['width']}x{bounds['height']})")
        return True
    except Exception as e:
        print(f"    ❌ {feature}: capture failed — {e}")
        return False


def process_club(page, club_id, club_data):
    """Process all missing features for a single club."""
    url = club_data["url"]
    features = club_data["features"]

    print(f"\n{'='*60}")
    print(f"📸 {club_id} ({url}) — {len(features)} features to capture")
    print(f"{'='*60}")

    # Navigate
    try:
        page.goto(url, timeout=30000, wait_until="domcontentloaded")
    except Exception as e:
        print(f"  ❌ Failed to load {url}: {e}")
        return [], features

    time.sleep(4)

    # Dismiss cookies and popups
    dismiss_cookies(page, club_id)
    time.sleep(1)
    dismiss_popups(page)
    time.sleep(1)

    # Check page height
    height = page.evaluate("document.body.scrollHeight")
    print(f"  Page height: {height}px")
    if height < 2000:
        print(f"  ⚠️  Page seems short, retrying cookie dismissal...")
        dismiss_cookies(page, club_id)
        time.sleep(2)
        dismiss_popups(page)
        time.sleep(2)
        height = page.evaluate("document.body.scrollHeight")
        print(f"  Page height after retry: {height}px")

    # Scroll for lazy-loading
    try:
        scroll_page(page)
    except:
        pass
    time.sleep(1)

    # Second cookie/popup dismiss (some appear after scroll)
    try:
        dismiss_popups(page)
    except:
        pass

    captured = []
    failed = []

    for feature in features:
        success = capture_feature(page, club_id, feature)
        if success:
            captured.append(feature)
        else:
            failed.append(feature)

    print(f"\n  Summary: {len(captured)} captured, {len(failed)} failed")
    return captured, failed


def main():
    print("=" * 60)
    print("🔄 Re-capture deleted screenshots")
    print(f"   Clubs: {len(DELETED)}")
    total = sum(len(d['features']) for d in DELETED.values())
    print(f"   Total features: {total}")
    print("=" * 60)

    all_captured = {}
    all_failed = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for club_id, club_data in DELETED.items():
            # Skip clubs where all features already have images
            features = club_data["features"]
            missing = [f for f in features if not (IMG_DIR / f"{club_id}_{f}.png").exists()]
            if not missing:
                print(f"\n⏭️  {club_id}: all {len(features)} features already captured, skipping")
                all_captured[club_id] = features
                all_failed[club_id] = []
                continue
            club_data_filtered = {**club_data, "features": missing}
            try:
                captured, failed = process_club(page, club_id, club_data_filtered)
            except Exception as e:
                print(f"  ❌ Club {club_id} crashed: {e}")
                captured = []
                failed = missing
                # Try to recover the page
                try:
                    page.goto("about:blank", timeout=5000)
                    time.sleep(1)
                except:
                    pass
            all_captured[club_id] = captured
            all_failed[club_id] = failed

        browser.close()

    # Print final summary
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)

    total_captured = sum(len(v) for v in all_captured.values())
    total_failed = sum(len(v) for v in all_failed.values())

    print(f"\n✅ Captured: {total_captured}")
    print(f"❌ Failed: {total_failed}")

    if total_failed > 0:
        print("\nFailed features (need JSON flip to FALSE or manual capture):")
        for club_id, features in all_failed.items():
            if features:
                print(f"  {club_id}: {', '.join(features)}")

    # Write failed list to a JSON for next steps
    failed_path = Path(__file__).resolve().parent / "recapture_failed.json"
    with open(failed_path, "w") as f:
        json.dump(all_failed, f, indent=2)
    print(f"\nFailed list written to: {failed_path}")


if __name__ == "__main__":
    main()
