#!/usr/bin/env python3
"""
Capture element-level cutouts for the 4 new clubs added on 2026-04-28:
Sunderland, Nottingham Forest, Leeds United, Fulham.

Strategy: full-page screenshot + JS-driven bbox + PIL crop.
Output: analysis/homepage/crosscheck/img/{club}_{feature}.png
"""

import time
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / "img"
SCREENSHOTS_DIR = ROOT.parent / "screenshots"

CLUBS = [
    {
        "id": "sunderland",
        "url": "https://www.safc.com/",
        "fullpage_filename": "34-sunderland.png",
    },
    {
        "id": "nottm_forest",
        "url": "https://www.nottinghamforest.co.uk/",
        "fullpage_filename": "35-nottm-forest.png",
    },
    {
        "id": "leeds",
        "url": "https://www.leedsunited.com/",
        "fullpage_filename": "36-leeds.png",
    },
    {
        "id": "fulham",
        "url": "https://www.fulhamfc.com/",
        "fullpage_filename": "37-fulham.png",
    },
]

# Generic JS selector recipes keyed by feature.
# Each returns {x,y,width,height} in absolute page coords or null.
RECIPES = {
    "login_account": r"""
        (() => {
            const root = document.querySelector('header') || document.body;
            const candidates = root.querySelectorAll('a, button, [role="button"]');
            for (const el of candidates) {
                const txt = (el.textContent || '').trim().toLowerCase();
                const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                if (/^(log\s*in|sign\s*in|login|account|my\s*account)$/.test(txt) ||
                    /(login|sign in|account|profile)/.test(aria)) {
                    const r = el.getBoundingClientRect();
                    if (r.top < 200 && r.width > 5 && r.height > 5) {
                        return { x: r.left + scrollX, y: r.top + scrollY,
                                 width: Math.max(r.width, 60), height: Math.max(r.height, 24) };
                    }
                }
            }
            const icons = root.querySelectorAll('[class*="login" i], [class*="account" i], [class*="user" i]');
            for (const el of icons) {
                const r = el.getBoundingClientRect();
                if (r.top < 150 && r.width > 5 && r.height > 5)
                    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
            }
            return null;
        })()
    """,
    "search_input_in_header": r"""
        (() => {
            const root = document.querySelector('header') || document.body;
            const els = root.querySelectorAll('input[type="search"], [class*="search" i] svg, [aria-label*="search" i], button[class*="search" i]');
            for (const el of els) {
                const r = el.getBoundingClientRect();
                if (r.top < 200 && r.width > 5)
                    return { x: r.left + scrollX, y: r.top + scrollY, width: Math.max(r.width, 40), height: Math.max(r.height, 24) };
            }
            return null;
        })()
    """,
    "shop_shortcut_in_header": r"""
        (() => {
            const root = document.querySelector('header') || document.body;
            const els = root.querySelectorAll('a, button');
            for (const el of els) {
                const txt = (el.textContent || '').trim().toLowerCase();
                if (/^(shop|store|stores)$/.test(txt)) {
                    const r = el.getBoundingClientRect();
                    if (r.top < 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "tickets_shortcut_in_header": r"""
        (() => {
            const root = document.querySelector('header') || document.body;
            const els = root.querySelectorAll('a, button');
            for (const el of els) {
                const txt = (el.textContent || '').trim().toLowerCase();
                if (/^tickets?$/.test(txt)) {
                    const r = el.getBoundingClientRect();
                    if (r.top < 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "sponsor_lockup_in_header": r"""
        (() => {
            const header = document.querySelector('header');
            if (!header) return null;
            const r = header.getBoundingClientRect();
            return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
        })()
    """,
    "persistent_bar_above_header": r"""
        (() => {
            const header = document.querySelector('header');
            if (!header) return null;
            const r = header.getBoundingClientRect();
            // Capture topmost slice of the page above first content
            return { x: 0, y: 0, width: innerWidth, height: Math.min(60, r.top + r.height) };
        })()
    """,
    "hero_carousel": r"""
        (() => {
            const main = document.querySelector('main') || document.body;
            const candidates = main.querySelectorAll('[class*="hero" i], [class*="carousel" i], [class*="slider" i], [class*="swiper" i]');
            for (const el of candidates) {
                const r = el.getBoundingClientRect();
                if (r.width > 600 && r.height > 250 && r.top + scrollY < 1500) {
                    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "secondary_editorial_strip_below_hero": r"""
        (() => {
            const main = document.querySelector('main') || document.body;
            const heroes = main.querySelectorAll('[class*="hero" i], [class*="banner" i]');
            let heroBottom = 0;
            for (const h of heroes) {
                const r = h.getBoundingClientRect();
                const b = r.top + scrollY + r.height;
                if (b > heroBottom && b < 2000) heroBottom = b;
            }
            if (!heroBottom) heroBottom = 600;
            // Find a row near heroBottom
            const all = main.querySelectorAll('section, div, ul');
            for (const el of all) {
                const r = el.getBoundingClientRect();
                const top = r.top + scrollY;
                if (top > heroBottom - 50 && top < heroBottom + 350 && r.width > 600 && r.height > 80 && r.height < 400) {
                    const cards = el.querySelectorAll('article, [class*="card" i], a[href]');
                    if (cards.length >= 2) return { x: r.left + scrollX, y: top, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "brand_sponsor_highlighted_in_hero": r"""
        (() => {
            // Capture the top 900px fold as a proxy
            return { x: 0, y: 0, width: innerWidth, height: 900 };
        })()
    """,
    "next_match_block": r"""
        (() => {
            const els = document.querySelectorAll('[class*="match" i], [class*="fixture" i], [class*="next-game" i], [class*="upcoming" i]');
            for (const el of els) {
                const r = el.getBoundingClientRect();
                const top = r.top + scrollY;
                if (top > 100 && top < 3500 && r.height > 80 && r.width > 250) {
                    return { x: r.left + scrollX, y: top, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "next_match_feature_rich": r"""
        (() => {
            const els = document.querySelectorAll('[class*="match" i], [class*="fixture" i]');
            for (const el of els) {
                const r = el.getBoundingClientRect();
                const top = r.top + scrollY;
                if (top > 100 && top < 3500 && r.height > 120 && r.width > 350) {
                    return { x: r.left + scrollX, y: top, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "results_block": r"""
        (() => {
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_ELEMENT);
            let node;
            while (node = walker.nextNode()) {
                const txt = (node.innerText || '').trim();
                if (/\b\d\s*[-–]\s*\d\b/.test(txt) && txt.length < 400) {
                    const r = node.getBoundingClientRect();
                    const top = r.top + scrollY;
                    if (top > 200 && r.height > 80 && r.height < 500 && r.width > 200) {
                        return { x: r.left + scrollX, y: top, width: r.width, height: r.height };
                    }
                }
            }
            return null;
        })()
    """,
    "standings_block": r"""
        (() => {
            const tables = document.querySelectorAll('table, [class*="standings" i], [class*="league-table" i], [class*="table" i]');
            for (const el of tables) {
                const r = el.getBoundingClientRect();
                const top = r.top + scrollY;
                if (top > 300 && r.height > 100 && r.height < 600 && r.width > 200 && r.width < 700) {
                    return { x: r.left + scrollX, y: top, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "dedicated_news_section": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/news|headlines|latest/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    const top = r.top + scrollY;
                    if (r.height > 200) return { x: r.left + scrollX, y: top, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "news_rich_structure": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/news|headlines|latest/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const cards = sec.querySelectorAll('article, [class*="card" i], a[href]');
                    if (cards.length < 3) continue;
                    const r = sec.getBoundingClientRect();
                    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "homepage_video_block": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/video|watch|tv$/i.test((h.textContent || '').trim())) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "tickets_block": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3, [class*="title" i]');
            for (const h of headings) {
                if (/ticket(s|ing)|season ticket|waiting list/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement?.parentElement || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 100 && r.width > 250) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "hospitality_block": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3, [class*="title" i]');
            for (const h of headings) {
                if (/hospitality|premium|matchday experience/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement?.parentElement || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 100 && r.width > 250) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "store_block": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/shop|store|kit|kits|merchandise/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 200 && r.width > 400) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "store_individual_products": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/shop|store|kit|merchandise/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const buys = sec.querySelectorAll('a, button');
                    let buyCount = 0;
                    for (const b of buys) if (/buy|shop now/i.test((b.textContent || '').trim())) buyCount++;
                    if (buyCount < 2) continue;
                    const r = sec.getBoundingClientRect();
                    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "newsletter_signup": r"""
        (() => {
            const inputs = document.querySelectorAll('input[type="email"], input[name*="email" i]');
            for (const inp of inputs) {
                const wrap = inp.closest('section, form, div');
                if (!wrap) continue;
                const r = wrap.getBoundingClientRect();
                if (r.height > 60 && r.width > 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 400) };
            }
            return null;
        })()
    """,
    "fan_club_signup": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/membership|myforest|fan club|join us|free account/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 150 && r.width > 250) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "paid_membership": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/subscribe|premium|plans|memberships/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 150 && r.width > 250) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "press_conference_block": r"""
        (() => {
            const all = document.querySelectorAll('article, [class*="card" i], a[href]');
            for (const el of all) {
                const txt = (el.textContent || '').trim();
                if (/press conference|interview|reflects|speaks|reaction/i.test(txt) && txt.length < 200) {
                    const r = el.getBoundingClientRect();
                    if (r.height > 100 && r.width > 200 && r.height < 600) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "video_thumbnails_inline": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/news|latest/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const playIcons = sec.querySelectorAll('[class*="play" i], [class*="video" i] svg, [aria-label*="play" i]');
                    if (playIcons.length === 0) continue;
                    const r = sec.getBoundingClientRect();
                    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 800) };
                }
            }
            return null;
        })()
    """,
    "episodic_docu_series": r"""
        (() => {
            const all = document.querySelectorAll('section, [class*="episode" i], [class*="series" i]');
            for (const el of all) {
                const txt = (el.textContent || '').toLowerCase();
                if (/episode|series|chapter|extended|matchday/.test(txt)) {
                    const r = el.getBoundingClientRect();
                    if (r.height > 200 && r.width > 400) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "player_roster_preview": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/squads?|first team|teams|players/i.test((h.textContent || '').trim())) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 200 && r.width > 400) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "individual_player_cards": r"""
        (() => {
            const all = document.querySelectorAll('[class*="player" i], [class*="profile" i]');
            for (const el of all) {
                const r = el.getBoundingClientRect();
                if (r.height > 250 && r.width > 250 && r.height < 700) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: r.height };
            }
            return null;
        })()
    """,
    "womens_team_featured": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3, [role="tab"]');
            for (const h of headings) {
                if (/women|ffcw|safc women/i.test((h.textContent || '').trim())) {
                    const sec = h.closest('section') || h.parentElement?.parentElement || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 100 && r.width > 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "womens_team_tickets": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/women/i.test((h.textContent || '').trim())) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const ticketCta = sec.querySelector('a, button');
                    if (!ticketCta) continue;
                    const txt = (sec.textContent || '').toLowerCase();
                    if (!/ticket|book|buy/.test(txt)) continue;
                    const r = sec.getBoundingClientRect();
                    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "academy_youth_block": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3, [role="tab"]');
            for (const h of headings) {
                if (/academy|u\d\d|youth/i.test((h.textContent || '').trim())) {
                    const sec = h.closest('section') || h.parentElement?.parentElement || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 100 && r.width > 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "charity_csr_block": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3');
            for (const h of headings) {
                if (/community|foundation|charity|csr/i.test((h.textContent || '').trim())) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const r = sec.getBoundingClientRect();
                    if (r.height > 100) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "footer_sponsor_wall": r"""
        (() => {
            const footer = document.querySelector('footer');
            if (!footer) return null;
            const partners = footer.querySelectorAll('[class*="partner" i], [class*="sponsor" i], img');
            if (partners.length < 3) {
                const r = footer.getBoundingClientRect();
                return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 500) };
            }
            let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0, count = 0;
            for (const p of partners) {
                const r = p.getBoundingClientRect();
                if (r.width < 30 || r.height < 20) continue;
                count++;
                minX = Math.min(minX, r.left + scrollX);
                minY = Math.min(minY, r.top + scrollY);
                maxX = Math.max(maxX, r.left + scrollX + r.width);
                maxY = Math.max(maxY, r.top + scrollY + r.height);
            }
            if (count < 3) return null;
            return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
        })()
    """,
    "in_content_sponsor": r"""
        (() => {
            // Look for sponsor markers in body content (between header & footer)
            const main = document.querySelector('main') || document.body;
            const els = main.querySelectorAll('[class*="sponsor" i], [class*="partner" i], img[alt*="sponsor" i]');
            for (const el of els) {
                const r = el.getBoundingClientRect();
                const top = r.top + scrollY;
                if (top > 600 && top < 4000 && r.height > 50 && r.width > 100) {
                    return { x: r.left + scrollX, y: top, width: r.width, height: r.height };
                }
            }
            return null;
        })()
    """,
    "app_store_badges": r"""
        (() => {
            const imgs = document.querySelectorAll('img');
            for (const img of imgs) {
                const alt = (img.alt || '').toLowerCase();
                const src = (img.src || '').toLowerCase();
                if (/app[\s_-]?store|google[\s_-]?play|app store|play store/.test(alt) ||
                    /appstore|google.*play|googleplay/.test(src)) {
                    const r = img.getBoundingClientRect();
                    return { x: r.left + scrollX, y: r.top + scrollY, width: Math.max(r.width, 100), height: Math.max(r.height, 30) };
                }
            }
            return null;
        })()
    """,
    "club_tv_app_promo": r"""
        (() => {
            const headings = document.querySelectorAll('h1, h2, h3, [class*="title" i]');
            for (const h of headings) {
                if (/tv|stream|subscribe/i.test(h.textContent || '')) {
                    const sec = h.closest('section') || h.parentElement;
                    if (!sec) continue;
                    const cta = sec.querySelector('a, button');
                    if (!cta) continue;
                    const txt = (cta.textContent || '').toLowerCase();
                    if (!/subscribe|sign up|watch|join|download/.test(txt)) continue;
                    const r = sec.getBoundingClientRect();
                    return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "heritage_past_content": r"""
        (() => {
            const all = document.querySelectorAll('section, [class*="legacy" i], [class*="heritage" i], [class*="legend" i], [class*="history" i]');
            for (const el of all) {
                const txt = (el.textContent || '').toLowerCase();
                if (/legacy|heritage|legend|history|all-time|trophies/.test(txt)) {
                    const r = el.getBoundingClientRect();
                    if (r.height > 100 && r.width > 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "stadium_content_block": r"""
        (() => {
            const all = document.querySelectorAll('section, [class*="stadium" i]');
            for (const el of all) {
                const txt = (el.textContent || '').toLowerCase();
                if (/stadium|stand|legacy stones|stadium of light/.test(txt)) {
                    const r = el.getBoundingClientRect();
                    if (r.height > 100 && r.width > 200) return { x: r.left + scrollX, y: r.top + scrollY, width: r.width, height: Math.min(r.height, 700) };
                }
            }
            return null;
        })()
    """,
    "social_links_in_footer": r"""
        (() => {
            const footer = document.querySelector('footer') || document.body;
            const socials = footer.querySelectorAll(
                'a[href*="facebook"], a[href*="instagram"], a[href*="twitter"], a[href*="x.com"], a[href*="youtube"], a[href*="tiktok"], a[href*="linkedin"]'
            );
            if (socials.length < 2) return null;
            let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
            for (const s of socials) {
                const r = s.getBoundingClientRect();
                minX = Math.min(minX, r.left + scrollX);
                minY = Math.min(minY, r.top + scrollY);
                maxX = Math.max(maxX, r.left + scrollX + r.width);
                maxY = Math.max(maxY, r.top + scrollY + r.height);
            }
            return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
        })()
    """,
}

# Per-club override list of features to actually try (TRUE in JSON)
CLUB_FEATURES = {
    "sunderland": [
        "login_account", "search_input_in_header", "shop_shortcut_in_header", "tickets_shortcut_in_header",
        "sponsor_lockup_in_header", "persistent_bar_above_header", "hero_carousel",
        "secondary_editorial_strip_below_hero", "brand_sponsor_highlighted_in_hero",
        "next_match_block", "next_match_feature_rich", "standings_block",
        "dedicated_news_section", "news_rich_structure", "homepage_video_block",
        "press_conference_block", "store_block", "store_individual_products",
        "newsletter_signup", "womens_team_featured", "footer_sponsor_wall", "social_links_in_footer",
    ],
    "nottm_forest": [
        "login_account", "search_input_in_header", "shop_shortcut_in_header", "tickets_shortcut_in_header",
        "persistent_bar_above_header", "hero_carousel", "secondary_editorial_strip_below_hero",
        "next_match_block", "next_match_feature_rich", "standings_block",
        "dedicated_news_section", "news_rich_structure", "homepage_video_block", "episodic_docu_series",
        "hospitality_block", "store_block", "store_individual_products",
        "fan_club_signup", "paid_membership", "player_roster_preview",
        "womens_team_featured", "womens_team_tickets", "academy_youth_block",
        "footer_sponsor_wall", "app_store_badges", "club_tv_app_promo", "social_links_in_footer",
    ],
    "leeds": [
        "login_account", "search_input_in_header", "shop_shortcut_in_header", "tickets_shortcut_in_header",
        "sponsor_lockup_in_header", "persistent_bar_above_header", "secondary_editorial_strip_below_hero",
        "next_match_block", "next_match_feature_rich", "results_block", "standings_block",
        "dedicated_news_section", "news_rich_structure", "homepage_video_block",
        "tickets_block", "newsletter_signup", "heritage_past_content", "stadium_content_block",
        "womens_team_featured", "academy_youth_block", "charity_csr_block",
        "footer_sponsor_wall", "app_store_badges", "social_links_in_footer",
    ],
    "fulham": [
        "login_account", "search_input_in_header", "shop_shortcut_in_header", "tickets_shortcut_in_header",
        "persistent_bar_above_header", "secondary_editorial_strip_below_hero",
        "brand_sponsor_highlighted_in_hero",
        "dedicated_news_section", "news_rich_structure", "homepage_video_block", "video_thumbnails_inline",
        "tickets_block", "hospitality_block", "store_block", "store_individual_products",
        "player_roster_preview", "individual_player_cards", "womens_team_featured",
        "footer_sponsor_wall", "in_content_sponsor", "club_tv_app_promo", "social_links_in_footer",
    ],
}

results = {"captured": {}, "failed": {}}


def is_blank(png_bytes):
    img = Image.open(BytesIO(png_bytes))
    arr = np.array(img)
    return arr.std() < 5


def save_img(club, feature, png_bytes):
    if is_blank(png_bytes):
        print(f"    [BLANK] {feature}")
        results["failed"].setdefault(club, []).append(feature)
        return False
    path = IMG_DIR / f"{club}_{feature}.png"
    path.write_bytes(png_bytes)
    img = Image.open(BytesIO(png_bytes))
    print(f"    [OK] {feature}: {img.size[0]}x{img.size[1]}")
    results["captured"].setdefault(club, []).append(feature)
    return True


def dismiss_cookies(page):
    try:
        page.evaluate("""
            const btns = document.querySelectorAll('button, a, [role="button"]');
            for (const b of btns) {
                const txt = (b.textContent || '').toLowerCase().trim();
                if (txt.includes('accept all') || txt === 'accept' || txt.includes('agree')
                    || txt.includes('allow all') || txt === 'i agree' || txt.includes('confirm')
                    || txt.includes('reject all') || txt === 'reject') {
                    b.click(); break;
                }
            }
        """)
        time.sleep(1)
        page.evaluate("""
            document.querySelectorAll('[class*="cookie" i], [class*="consent" i], [class*="banner" i], [role="dialog"], [class*="modal" i], [class*="popup" i], [class*="overlay" i], [id*="cookie" i]').forEach(e => {
                if (e.getBoundingClientRect().height > 100 || e.style.position === 'fixed') e.remove();
            });
        """)
    except Exception:
        pass
    time.sleep(0.5)


def scroll_lazy(page):
    try:
        h = page.evaluate("document.body.scrollHeight")
        for i in range(min(h // 600, 25)):
            page.evaluate(f"window.scrollTo(0, {(i+1)*600})")
            time.sleep(0.35)
        time.sleep(1.5)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(0.8)
    except Exception:
        pass


def capture_full_page(page, club, fullpage_filename):
    """Capture and save the full-page screenshot to analysis/homepage/screenshots/."""
    try:
        png = page.screenshot(full_page=True)
        out = SCREENSHOTS_DIR / fullpage_filename
        out.write_bytes(png)
        img = Image.open(BytesIO(png))
        print(f"  fullpage saved: {out.name} ({img.size[0]}x{img.size[1]})")
        return png
    except Exception as e:
        print(f"  fullpage FAILED: {e}")
        return None


def capture_feature(page, full_png, club, feature):
    js = RECIPES.get(feature)
    if not js:
        print(f"    [SKIP] {feature}: no recipe")
        return False
    try:
        box = page.evaluate(js)
    except Exception as e:
        print(f"    [JS-ERR] {feature}: {e}")
        results["failed"].setdefault(club, []).append(feature)
        return False
    if not box:
        print(f"    [MISS] {feature}: not found")
        results["failed"].setdefault(club, []).append(feature)
        return False

    full_img = Image.open(BytesIO(full_png))
    fw, fh = full_img.size
    x = max(0, int(box["x"]))
    y = max(0, int(box["y"]))
    w = int(box["width"])
    h = int(box["height"])
    pad = 8
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(fw, x + w + pad)
    y2 = min(fh, y + h + pad)

    if x2 - x1 < 30 or y2 - y1 < 20:
        print(f"    [TINY] {feature}: {x2-x1}x{y2-y1}")
        results["failed"].setdefault(club, []).append(feature)
        return False

    cropped = full_img.crop((x1, y1, x2, y2))
    buf = BytesIO()
    cropped.save(buf, format="PNG")
    return save_img(club, feature, buf.getvalue())


def process_club(browser, club_def):
    cid = club_def["id"]
    url = club_def["url"]
    fullpage_filename = club_def["fullpage_filename"]

    print("\n" + "=" * 60)
    print(f"  {cid} ({url})")
    print("=" * 60)

    page = browser.new_page(viewport={"width": 1440, "height": 900})
    try:
        page.goto(url, timeout=45000, wait_until="domcontentloaded")
        time.sleep(4)
        dismiss_cookies(page)
        scroll_lazy(page)

        full_png = capture_full_page(page, cid, fullpage_filename)
        if not full_png:
            return

        for feature in CLUB_FEATURES.get(cid, []):
            capture_feature(page, full_png, cid, feature)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            for club in CLUBS:
                process_club(browser, club)
        finally:
            browser.close()

    summary = {
        "captured_total": sum(len(v) for v in results["captured"].values()),
        "failed_total": sum(len(v) for v in results["failed"].values()),
        "captured": results["captured"],
        "failed": results["failed"],
    }
    print("\n" + "=" * 60)
    print(f"  CAPTURED: {summary['captured_total']}")
    print(f"  FAILED  : {summary['failed_total']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
