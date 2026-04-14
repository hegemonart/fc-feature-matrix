#!/usr/bin/env python3
"""
Capture element-level screenshots for TRUE features on club homepages.
Uses Playwright to navigate, scroll, and screenshot specific page regions.
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

# Club URLs
CLUB_URLS = {
    "chelsea": "https://www.chelseafc.com",
    "fc_barcelona": "https://www.fcbarcelona.com/en",
    "arsenal": "https://www.arsenal.com",
}

# Feature detection strategies — JS selectors or heuristics to find each feature's DOM element
# Returns { selector, fallback_region } for each feature
FEATURE_LOCATORS = {
    # ── Header & Navigation ──
    "persistent_bar_above_header": {
        "desc": "Utility bar above main navigation",
        "strategy": "region",
        "region": [0, 0, 1400, 50],
    },
    "language_switcher_in_header": {
        "desc": "Language selector dropdown in header",
        "strategy": "js",
        "js": """
            const els = document.querySelectorAll('[class*="lang"], [class*="Lang"], [data-lang], [class*="locale"]');
            if (els.length) return els[0];
            // Look for language text patterns
            const all = document.querySelectorAll('a, button, select');
            for (const el of all) {
                const t = (el.textContent || '').trim().toLowerCase();
                if (/^(en|es|ca|de|fr|it|pt)$/i.test(t) || /english|espanol|catala/i.test(t)) {
                    const y = el.getBoundingClientRect().top;
                    if (y < 100) return el;
                }
            }
            return null;
        """,
        "fallback_region": [0, 0, 1400, 50],
    },
    "login_account": {
        "desc": "Login/account/profile link in header",
        "strategy": "js",
        "js": """
            const els = document.querySelectorAll('[class*="profile"], [class*="Profile"], [class*="login"], [class*="Login"], [class*="account"], [class*="Account"], [href*="login"], [href*="account"], [href*="profile"]');
            for (const el of els) {
                if (el.getBoundingClientRect().top < 100) return el;
            }
            return null;
        """,
        "fallback_region": [700, 0, 1400, 50],
    },
    "search_input_in_header": {
        "desc": "Search icon/input in header",
        "strategy": "js",
        "js": """
            const el = document.querySelector('[class*="search"], [class*="Search"], [type="search"], [aria-label*="search"], [aria-label*="Search"], svg[class*="search"]');
            if (el && el.getBoundingClientRect().top < 120) return el;
            return null;
        """,
        "fallback_region": [900, 40, 1200, 120],
    },
    "shop_shortcut_in_header": {
        "desc": "Shop/Store link in main navigation",
        "strategy": "js",
        "js": """
            const all = document.querySelectorAll('a, button');
            for (const el of all) {
                const t = (el.textContent || '').trim().toLowerCase();
                if ((t === 'shop' || t === 'store' || t === 'tienda' || t === 'botiga') && el.getBoundingClientRect().top < 120) return el;
            }
            return null;
        """,
        "fallback_region": [800, 40, 1100, 120],
    },
    "tickets_shortcut_in_header": {
        "desc": "Tickets link in main navigation",
        "strategy": "js",
        "js": """
            const all = document.querySelectorAll('a, button');
            for (const el of all) {
                const t = (el.textContent || '').trim().toLowerCase();
                if ((t.includes('ticket') || t.includes('entrada')) && el.getBoundingClientRect().top < 120) return el;
            }
            return null;
        """,
        "fallback_region": [600, 40, 1000, 120],
    },
    "sponsor_lockup_in_header": {
        "desc": "Sponsor logos in header area",
        "strategy": "js",
        "js": """
            const imgs = document.querySelectorAll('header img, nav img, [class*="header"] img, [class*="Header"] img');
            const sponsors = Array.from(imgs).filter(i => i.getBoundingClientRect().top < 80 && i.naturalWidth > 20);
            if (sponsors.length) return sponsors[0].closest('div') || sponsors[0];
            return null;
        """,
        "fallback_region": [800, 0, 1400, 50],
    },

    # ── Hero ──
    "hero_carousel": {
        "desc": "Hero carousel/slider at top of page",
        "strategy": "region",
        "region": [0, 50, 1400, 600],
    },
    "secondary_editorial_strip_below_hero": {
        "desc": "Editorial card row below hero",
        "strategy": "js",
        "js": """
            // Look for a row of 2-5 card-like elements below the hero
            const cards = document.querySelectorAll('[class*="card"], [class*="Card"], [class*="editorial"], [class*="Editorial"], [class*="strip"], [class*="Strip"]');
            for (const el of cards) {
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > 500 && absY < 1200 && rect.height > 40 && rect.height < 300) return el;
            }
            return null;
        """,
        "fallback_region": [0, 550, 1400, 800],
    },
    "brand_sponsor_highlighted_in_hero": {
        "desc": "Sponsor logo prominently in hero area",
        "strategy": "js",
        "js": """
            const heroImgs = document.querySelectorAll('img');
            for (const img of heroImgs) {
                const rect = img.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > 50 && absY < 600) {
                    const src = (img.src || '').toLowerCase();
                    const alt = (img.alt || '').toLowerCase();
                    if (src.includes('sponsor') || src.includes('partner') || alt.includes('sponsor') || alt.includes('partner')) return img;
                }
            }
            return null;
        """,
        "fallback_region": [0, 50, 1400, 600],
    },

    # ── Match & Fixtures ──
    "next_match_block": {
        "desc": "Next/upcoming match widget",
        "strategy": "js",
        "js": """
            // Strategy 1: text-based
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('next match') || t.includes('upcoming') || t.includes('next fixture')
                    || t.includes('proximo partido') || t.includes('proper partit')
                    || t.includes('fixtures') || t.includes('matches') || t.includes('matchday')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 100 && absY < 2000) {
                        const el = walker.currentNode.parentElement.closest('section, div[class], article');
                        if (el && el.getBoundingClientRect().height > 50) return el;
                    }
                }
            }
            // Strategy 2: class-based
            const matchEls = document.querySelectorAll('[class*="fixture"], [class*="Fixture"], [class*="match"], [class*="Match"], [class*="next-game"], [class*="upcoming"]');
            for (const el of matchEls) {
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > 100 && absY < 2000 && rect.height > 50) return el;
            }
            return null;
        """,
    },
    "next_match_feature_rich": {
        "desc": "Rich next-match block with extras (countdown, broadcaster, ticket CTA)",
        "strategy": "same_as",
        "same_as": "next_match_block",
    },
    "results_block": {
        "desc": "Recent results with scores",
        "strategy": "js",
        "js": """
            // Strategy 1: look for score patterns
            const all = document.querySelectorAll('span, div, td, p');
            for (const el of all) {
                if (el.children.length === 0) {
                    const t = (el.textContent || '').trim();
                    if (/^\\d\\s*[-–:]\\s*\\d$/.test(t)) {
                        let section = el.closest('section, [class*="result"], [class*="Result"], [class*="match"], [class*="Match"], [class*="fixture"], [class*="score"]');
                        if (section && section.getBoundingClientRect().height > 40) return section;
                        let parent = el;
                        for (let i = 0; i < 6; i++) { parent = parent.parentElement; if (!parent) break; }
                        if (parent && parent.getBoundingClientRect().height > 40) return parent;
                    }
                }
            }
            // Strategy 2: class-based
            const resultEls = document.querySelectorAll('[class*="result"], [class*="Result"], [class*="score"], [class*="Score"]');
            for (const el of resultEls) {
                const rect = el.getBoundingClientRect();
                if (rect.height > 50 && rect.width > 200) return el;
            }
            // Strategy 3: heading-based
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('result') || t.includes('latest score') || t.includes('recent match')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 100) {
                        const el = walker.currentNode.parentElement.closest('section, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "standings_block": {
        "desc": "League table/standings widget",
        "strategy": "js",
        "js": """
            // Look for standings/table content
            const tables = document.querySelectorAll('table');
            for (const t of tables) {
                const text = t.textContent || '';
                if (/PTS|points|pos/i.test(text) && t.getBoundingClientRect().height > 50) return t.closest('section, div[class]') || t;
            }
            // Look for "standings" heading
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('standing') || t.includes('league table') || t.includes('clasificacion') || t.includes('classificacio')) {
                    const el = walker.currentNode.parentElement.closest('section, div[class]');
                    if (el) return el;
                }
            }
            return null;
        """,
    },

    # ── Content ──
    "dedicated_news_section": {
        "desc": "News section on homepage",
        "strategy": "js",
        "js": """
            // Strategy 1: heading-based
            const headings = document.querySelectorAll('h2, h3');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('news') || t.includes('latest') || t.includes('noticias')
                    || t.includes('actualidad') || t.includes('breaking') || t.includes('stories')
                    || t.includes('article') || t.includes('editorial')) {
                    const section = h.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 100) return section;
                }
            }
            // Strategy 2: article cards
            const articles = document.querySelectorAll('article, [class*="article"], [class*="Article"], [class*="news"], [class*="News"], [class*="story"], [class*="Story"]');
            if (articles.length > 2) {
                const parent = articles[0].closest('section') || articles[0].parentElement;
                if (parent && parent.getBoundingClientRect().height > 100) return parent;
            }
            // Strategy 3: any large content section with multiple cards
            const sections = document.querySelectorAll('section');
            for (const s of sections) {
                const cards = s.querySelectorAll('a[href*="article"], a[href*="news"], a[href*="story"]');
                if (cards.length >= 3) return s;
            }
            return null;
        """,
    },
    "news_rich_structure": {
        "desc": "News with categories, timestamps, or multi-card layout",
        "strategy": "same_as",
        "same_as": "dedicated_news_section",
    },
    "homepage_video_block": {
        "desc": "Video content block on homepage",
        "strategy": "js",
        "js": """
            const els = document.querySelectorAll('[class*="video"], [class*="Video"], [class*="watch"], [class*="Watch"], video, iframe[src*="youtube"]');
            for (const el of els) {
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > 100 && rect.height > 50) {
                    const section = el.closest('section, div[class]');
                    return section || el;
                }
            }
            // Text-based: "Watch", "Video"
            const headings = document.querySelectorAll('h2, h3');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('watch') || t.includes('video') || t.includes('highlights')) {
                    return h.closest('section, div[class]') || h;
                }
            }
            return null;
        """,
    },
    "video_thumbnails_inline": {
        "desc": "Video thumbnails visible inline on homepage",
        "strategy": "same_as",
        "same_as": "homepage_video_block",
    },
    "social_native_content": {
        "desc": "Social media content embedded on homepage",
        "strategy": "js",
        "js": """
            const els = document.querySelectorAll('[class*="social"], [class*="Social"], [class*="instagram"], [class*="twitter"], [class*="tiktok"], iframe[src*="instagram"], iframe[src*="twitter"]');
            for (const el of els) {
                const rect = el.getBoundingClientRect();
                if (rect.height > 30) {
                    const section = el.closest('section, div[class]');
                    return section || el;
                }
            }
            return null;
        """,
    },
    "press_conference_block": {
        "desc": "Press conference content on homepage",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('press conference') || t.includes('rueda de prensa') || t.includes('roda de premsa') || t.includes('pressekonferenz')) {
                    const el = walker.currentNode.parentElement.closest('section, article, div[class]');
                    if (el) return el;
                }
            }
            return null;
        """,
    },

    # ── Tickets & Hospitality ──
    "tickets_block": {
        "desc": "Tickets promotion block on homepage",
        "strategy": "js",
        "js": """
            const headings = document.querySelectorAll('h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('ticket') || t.includes('entrada')) {
                    const absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) { // Not just header
                        return h.closest('section, div[class]') || h;
                    }
                }
            }
            return null;
        """,
    },

    # ── Commerce ──
    "store_block": {
        "desc": "Store/shop section on homepage",
        "strategy": "js",
        "js": """
            // Strategy 1: heading-based
            const headings = document.querySelectorAll('h2, h3, h4');
            for (const h of headings) {
                const t = (h.textContent || '').trim().toLowerCase();
                if (t.includes('shop') || t.includes('store') || t.includes('tienda') || t.includes('botiga')
                    || t.includes('kit') || t.includes('merch') || t.includes('gear') || t.includes('jersey')
                    || t.includes('camiseta') || t.includes('samarreta')) {
                    const absY = h.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        return h.closest('section, div[class]') || h;
                    }
                }
            }
            // Strategy 2: class-based
            const els = document.querySelectorAll('[class*="shop"], [class*="Shop"], [class*="store"], [class*="Store"], [class*="product"], [class*="Product"], [class*="merch"], [class*="Merch"]');
            for (const el of els) {
                const rect = el.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                if (absY > 300 && rect.height > 100 && rect.width > 300) return el;
            }
            // Strategy 3: product images/links
            const prodLinks = document.querySelectorAll('a[href*="/shop"], a[href*="/store"], a[href*="shop."]');
            for (const a of prodLinks) {
                const absY = a.getBoundingClientRect().top + window.scrollY;
                if (absY > 300) {
                    const section = a.closest('section, div[class]');
                    if (section && section.getBoundingClientRect().height > 100) return section;
                }
            }
            return null;
        """,
    },
    "store_individual_products": {
        "desc": "Individual product cards in store section",
        "strategy": "same_as",
        "same_as": "store_block",
    },

    # ── Community & Membership ──
    "newsletter_signup": {
        "desc": "Newsletter signup form/CTA",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('newsletter') || t.includes('subscribe') || t.includes('suscribete')) {
                    const el = walker.currentNode.parentElement.closest('section, div[class], form');
                    if (el) return el;
                }
            }
            return null;
        """,
    },
    "fan_club_signup": {
        "desc": "Fan club signup/registration",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('fan club') || t.includes('penyes') || t.includes('join') || t.includes('sign up') || t.includes('member')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 300) {
                        const el = walker.currentNode.parentElement.closest('section, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "paid_membership": {
        "desc": "Paid membership promotion",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('membership') || t.includes('culer') || t.includes('socio') || t.includes('member')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 300) {
                        const el = walker.currentNode.parentElement.closest('section, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "draws_contests": {
        "desc": "Draws, contests, or giveaways",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('draw') || t.includes('contest') || t.includes('giveaway') || t.includes('win') || t.includes('sorteo') || t.includes('concurso')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 300) {
                        const el = walker.currentNode.parentElement.closest('section, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },

    # ── Heritage ──
    "heritage_past_content": {
        "desc": "Heritage or historical content block",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('heritage') || t.includes('history') || t.includes('on this day') || t.includes('throwback') || t.includes('classic') || t.includes('historia')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, article, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "stadium_content_block": {
        "desc": "Stadium content on homepage",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('stadium') || t.includes('camp nou') || t.includes('spotify camp') || t.includes('stamford') || t.includes('emirates') || t.includes('estadio')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, article, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "museum_block": {
        "desc": "Museum promotion block",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('museum') || t.includes('museo') || t.includes('museu') || t.includes('tour') || t.includes('experience')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, article, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },

    # ── Players & Teams ──
    "player_roster_preview": {
        "desc": "Player roster/squad preview",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('squad') || t.includes('roster') || t.includes('players') || t.includes('plantilla') || t.includes('plantell')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "individual_player_cards": {
        "desc": "Individual player cards with photos",
        "strategy": "same_as",
        "same_as": "player_roster_preview",
    },
    "womens_team_featured": {
        "desc": "Women's team content on homepage",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes("women") || t.includes("femeni") || t.includes("femenino") || t.includes("wsl")) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 100) {
                        const el = walker.currentNode.parentElement.closest('section, article, div[class], a');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "academy_youth_block": {
        "desc": "Academy/youth team block",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('academy') || t.includes('youth') || t.includes('u18') || t.includes('u21') || t.includes('cantera') || t.includes('masia')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, article, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "charity_csr_block": {
        "desc": "Charity/CSR/Foundation block",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('foundation') || t.includes('charity') || t.includes('community') || t.includes('fundacio') || t.includes('fundacion')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    if (absY > 200) {
                        const el = walker.currentNode.parentElement.closest('section, article, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "quiz_trivia": {
        "desc": "Quiz or trivia feature",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('quiz') || t.includes('trivia') || t.includes('predict')) {
                    const el = walker.currentNode.parentElement.closest('section, article, div[class]');
                    if (el) return el;
                }
            }
            return null;
        """,
    },

    # ── Partners / Footer ──
    "footer_sponsor_wall": {
        "desc": "Sponsor logo wall in footer area",
        "strategy": "js",
        "js": """
            const footerArea = document.querySelector('footer') || document.body;
            const imgs = footerArea.querySelectorAll('img');
            const sponsorImgs = Array.from(imgs).filter(i => {
                const y = i.getBoundingClientRect().top + window.scrollY;
                const alt = (i.alt || '').toLowerCase();
                const src = (i.src || '').toLowerCase();
                return y > document.body.scrollHeight * 0.7 && (alt.includes('sponsor') || alt.includes('partner') || src.includes('sponsor') || src.includes('partner'));
            });
            if (sponsorImgs.length >= 3) {
                return sponsorImgs[0].closest('div[class], section') || sponsorImgs[0].parentElement;
            }
            // Fallback: look for multiple small images clustered near bottom
            const bottomImgs = Array.from(imgs).filter(i => {
                const rect = i.getBoundingClientRect();
                const absY = rect.top + window.scrollY;
                return absY > document.body.scrollHeight * 0.7 && rect.width < 200 && rect.height < 100;
            });
            if (bottomImgs.length >= 3) {
                return bottomImgs[0].closest('div[class], section') || bottomImgs[0].parentElement;
            }
            return null;
        """,
    },
    "in_content_sponsor": {
        "desc": "Sponsor placement within homepage content",
        "strategy": "js",
        "js": """
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const t = (walker.currentNode.textContent || '').trim().toLowerCase();
                if (t.includes('presented by') || t.includes('sponsored by') || t.includes('powered by') || t.includes('partner')) {
                    const absY = walker.currentNode.parentElement.getBoundingClientRect().top + window.scrollY;
                    const pageH = document.body.scrollHeight;
                    if (absY > 200 && absY < pageH * 0.8) {
                        const el = walker.currentNode.parentElement.closest('section, div[class]');
                        if (el) return el;
                    }
                }
            }
            return null;
        """,
    },
    "app_store_badges": {
        "desc": "App store download badges",
        "strategy": "js",
        "js": """
            const els = document.querySelectorAll('a[href*="apps.apple"], a[href*="play.google"], a[href*="itunes"], img[alt*="App Store"], img[alt*="Google Play"], [class*="app-badge"], [class*="download"]');
            for (const el of els) {
                const rect = el.getBoundingClientRect();
                if (rect.height > 10) {
                    return el.closest('div[class], section') || el;
                }
            }
            return null;
        """,
    },
    "social_links_in_footer": {
        "desc": "Social media links in footer",
        "strategy": "js",
        "js": """
            const footer = document.querySelector('footer') || document.body;
            const socials = footer.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"]');
            if (socials.length >= 2) {
                return socials[0].closest('div[class], ul, nav') || socials[0].parentElement;
            }
            return null;
        """,
    },
}


def get_true_features(club_id):
    """Get list of feature keys that are TRUE for a given club."""
    path = RESULTS / f"{club_id}.json"
    with open(path) as f:
        data = json.load(f)
    return [k for k, v in data["features"].items() if v is True]


def capture_element_screenshot(page, feature_key, club_id, locator_info):
    """Capture a screenshot of a specific feature element on the page."""
    out_path = IMG_DIR / f"{club_id}_{feature_key}.png"

    strategy = locator_info.get("strategy", "js")

    if strategy == "region":
        # Fixed region crop
        region = locator_info["region"]
        page.screenshot(
            path=str(out_path),
            clip={"x": region[0], "y": region[1], "width": region[2] - region[0], "height": region[3] - region[1]},
        )
        print(f"  [region] {club_id}_{feature_key}.png")
        return True

    if strategy == "same_as":
        # Use the same element as another feature
        ref_key = locator_info["same_as"]
        ref_path = IMG_DIR / f"{club_id}_{ref_key}.png"
        if ref_path.exists():
            import shutil
            shutil.copy2(ref_path, out_path)
            print(f"  [copy] {club_id}_{feature_key}.png (same as {ref_key})")
            return True
        # Fallback: try to locate using the referenced feature's locator
        ref_locator = FEATURE_LOCATORS.get(ref_key, {})
        return capture_element_screenshot(page, feature_key, club_id, ref_locator)

    # JS-based element location
    js_code = locator_info.get("js", "null")
    try:
        el = page.evaluate(f"""() => {{
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
        }}""")

        if el and el["width"] > 5 and el["height"] > 5:
            # Cap dimensions
            clip_h = min(el["height"], 800)
            clip_w = min(el["width"], 1400)
            if clip_w < 200:
                clip_w = 600  # Widen narrow elements
                el["x"] = max(0, el["x"] - 200)

            # Add some padding
            pad = 10
            clip = {
                "x": max(0, el["x"] - pad),
                "y": max(0, el["y"] - pad),
                "width": clip_w + 2 * pad,
                "height": clip_h + 2 * pad,
            }
            page.screenshot(path=str(out_path), clip=clip, full_page=True)
            print(f"  [js] {club_id}_{feature_key}.png ({int(clip['width'])}x{int(clip['height'])} @ y:{int(el['y'])})")
            return True

    except Exception as e:
        print(f"  [error] {club_id}_{feature_key}: {e}")

    # Fallback region if JS failed
    fallback = locator_info.get("fallback_region")
    if fallback:
        page.screenshot(
            path=str(out_path),
            clip={"x": fallback[0], "y": fallback[1], "width": fallback[2] - fallback[0], "height": fallback[3] - fallback[1]},
        )
        print(f"  [fallback] {club_id}_{feature_key}.png")
        return True

    print(f"  [SKIP] {club_id}_{feature_key} — element not found, no fallback")
    return False


def process_club(browser, club_id, url):
    """Process all TRUE features for a club."""
    print(f"\n{'='*60}")
    print(f"Processing: {club_id} ({url})")
    print(f"{'='*60}")

    true_features = get_true_features(club_id)
    print(f"TRUE features: {len(true_features)}")

    context = browser.new_context(
        viewport={"width": 1400, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    )
    page = context.new_page()

    # Navigate
    page.goto(url, wait_until="networkidle", timeout=30000)
    time.sleep(3)

    # Dismiss cookies — try multiple strategies
    for attempt in range(3):
        try:
            dismissed = page.evaluate("""() => {
                const btns = document.querySelectorAll('button, a, [role="button"], span[role="button"]');
                const priorities = ['accept all', 'accept', 'agree', 'consent', 'got it', 'ok',
                    'reject all', 'decline', 'necessary only', 'refuse', 'deny all',
                    'acepto', 'acceptar', 'aceptar', 'akzeptieren'];
                for (const p of priorities) {
                    for (const b of btns) {
                        const txt = (b.textContent || '').toLowerCase().trim();
                        if (txt.includes(p)) { b.click(); return true; }
                    }
                }
                // Try consentmanager API
                if (window.__cmp) { window.__cmp('setConsent', 0); return true; }
                return false;
            }""")
            if dismissed:
                time.sleep(1)
                break
        except Exception:
            pass
        time.sleep(1)

    # Scroll incrementally to trigger lazy loading
    page_height = page.evaluate("document.body.scrollHeight")
    steps = 5
    for i in range(1, steps + 1):
        page.evaluate(f"window.scrollTo(0, {page_height * i // steps})")
        time.sleep(0.8)
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(2)

    captured = 0
    skipped = 0

    for feature in true_features:
        locator = FEATURE_LOCATORS.get(feature)
        if not locator:
            print(f"  [NO LOCATOR] {feature} — no detection strategy defined")
            skipped += 1
            continue

        success = capture_element_screenshot(page, feature, club_id, locator)
        if success:
            captured += 1
        else:
            skipped += 1

    print(f"\nDone: {captured} captured, {skipped} skipped out of {len(true_features)} TRUE features")

    context.close()
    return captured, skipped


def main():
    clubs = ["chelsea", "fc_barcelona", "arsenal"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        total_captured = 0
        total_skipped = 0

        for club_id in clubs:
            url = CLUB_URLS[club_id]
            captured, skipped = process_club(browser, club_id, url)
            total_captured += captured
            total_skipped += skipped

        browser.close()

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_captured} screenshots captured, {total_skipped} skipped")
    print(f"Output: {IMG_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
