#!/usr/bin/env python3
"""May 4 Nottm Forest recapture: 12 features.

NEW (9):
- login_account, shop_shortcut_in_header, sponsor_lockup_in_header
- results_block, video_thumbnails_inline, press_conference_block
- womens_team_tickets, footer_sponsor_wall, app_store_badges

RECAPTURE (3 — design changed since previous capture):
- search_input_in_header, next_match_block, next_match_feature_rich
"""

import time
import numpy as np
from pathlib import Path
from PIL import Image
from io import BytesIO
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).parent / "img"
URL = "https://www.nottinghamforest.co.uk/"

results = {"captured": {}, "failed": {}}


def is_blank(png_bytes):
    img = Image.open(BytesIO(png_bytes))
    arr = np.array(img)
    return arr.std() < 5


def save_img(feature, png_bytes):
    if is_blank(png_bytes):
        print(f"  [BLANK] {feature}")
        results["failed"].setdefault("nottm_forest", []).append(feature)
        return False
    path = IMG_DIR / f"nottm_forest_{feature}.png"
    path.write_bytes(png_bytes)
    img = Image.open(BytesIO(png_bytes))
    print(f"  [OK] {feature}: {img.size[0]}x{img.size[1]}")
    results["captured"].setdefault("nottm_forest", []).append(feature)
    return True


def dismiss_cookies(page):
    try:
        page.evaluate("""
            const btns = document.querySelectorAll('button, a, [role="button"]');
            for (const b of btns) {
                const txt = (b.textContent || '').toLowerCase().trim();
                if (txt.includes('accept all') || txt.includes('agree') || txt === 'accept'
                    || txt.includes('allow all') || txt.includes('confirm')) {
                    b.click(); break;
                }
            }
        """)
        time.sleep(1)
        # OneTrust-specific
        page.evaluate("""
            const ot = document.querySelector('#onetrust-accept-btn-handler');
            if (ot) ot.click();
        """)
        time.sleep(1)
        # Remove leftover banners/overlays
        page.evaluate("""
            document.querySelectorAll('[class*="cookie"], [class*="consent"], [id*="onetrust"], [role="dialog"], [class*="modal"], [class*="popup"]').forEach(e => {
                const r = e.getBoundingClientRect();
                if (r.height > 100 || r.width > 300) e.remove();
            });
        """)
    except Exception:
        pass
    time.sleep(0.5)


def scroll_lazy(page):
    h = page.evaluate("document.body.scrollHeight")
    for i in range(min(h // 600, 25)):
        page.evaluate(f"window.scrollTo(0, {(i+1)*600})")
        time.sleep(0.4)
    time.sleep(2)
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)


def capture_from_fullpage(page, full_img, feature, js_code, pad=10):
    try:
        box = page.evaluate(js_code)
        if not box:
            print(f"  [MISS] {feature}: element not found")
            results["failed"].setdefault("nottm_forest", []).append(feature)
            return False
        fw, fh = full_img.size
        x, y, w, h = int(box["x"]), int(box["y"]), int(box["width"]), int(box["height"])
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(fw, x + w + pad)
        y2 = min(fh, y + h + pad)
        if x2 - x1 < 50 or y2 - y1 < 25:
            print(f"  [TINY] {feature}: {x2-x1}x{y2-y1}")
            results["failed"].setdefault("nottm_forest", []).append(feature)
            return False
        cropped = full_img.crop((x1, y1, x2, y2))
        buf = BytesIO()
        cropped.save(buf, format="PNG")
        return save_img(feature, buf.getvalue())
    except Exception as e:
        print(f"  [ERR] {feature}: {e}")
        results["failed"].setdefault("nottm_forest", []).append(feature)
        return False


# ============================================================
# JS selectors per feature
# ============================================================

JS_LOGIN_ACCOUNT = """
(() => {
    // Forest: visible "LOG IN" button at y=0 (size 60x44 or 100x44).
    // Skip duplicates with y < 0 (sticky/hidden variants).
    const all = document.querySelectorAll('button, a, [role="button"]');
    let best = null, bestArea = 0;
    for (const el of all) {
        const txt = (el.innerText || '').trim();
        const aria = (el.getAttribute('aria-label') || '').toLowerCase();
        const href = (el.getAttribute('href') || '').toLowerCase();
        const isMatch = /^(log in|login|sign in)$/i.test(txt) || aria.includes('log in') || aria.includes('login') || aria.includes('sign in');
        if (!isMatch) continue;
        const r = el.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (absY < 0 || absY > 200) continue;
        if (r.width < 30 || r.height < 25) continue;
        // Prefer button > div for tightest bounds
        const tagBonus = el.tagName === 'BUTTON' ? 100 : 0;
        const area = r.width * r.height + tagBonus;
        if (area > bestArea) {
            bestArea = area;
            best = { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
        }
    }
    return best;
})()
"""

JS_SHOP_SHORTCUT = """
(() => {
    const candidates = document.querySelectorAll('header a, header button, nav a, nav button');
    for (const el of candidates) {
        const txt = (el.innerText || '').trim();
        if (txt === 'Shop' || txt === 'Store' || txt === 'SHOP' || txt === 'STORE') {
            const r = el.getBoundingClientRect();
            const absY = r.top + window.scrollY;
            if (absY > 200) continue;
            if (r.width < 10 || r.height < 10) continue;
            return { x: r.left + window.scrollX, y: absY, width: Math.max(r.width, 50), height: Math.max(r.height, 30) };
        }
    }
    return null;
})()
"""

JS_SEARCH = """
(() => {
    // Forest: rounded search button at y=63, size 42x42, aria='search'
    const all = document.querySelectorAll('div, button, a, input, [role="button"]');
    for (const el of all) {
        const aria = (el.getAttribute('aria-label') || '').toLowerCase();
        const cls = (el.className || '').toString().toLowerCase();
        const type = (el.getAttribute('type') || '').toLowerCase();
        if (aria !== 'search' && !cls.includes('search') && type !== 'search') continue;
        const r = el.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (absY < 0 || absY > 200) continue;
        if (r.width < 20 || r.height < 20) continue;
        return { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
    }
    return null;
})()
"""

JS_SPONSOR_LOCKUP = """
(() => {
    // Sponsor logos in header (e.g. Boohoo Man, official partner)
    // Look for IMG elements in the header that aren't club crests
    const headerEls = document.querySelectorAll('header img, header svg, [class*="header"] img, [class*="topbar"] img, [class*="top-bar"] img');
    const candidates = [];
    for (const el of headerEls) {
        const r = el.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (absY > 200) continue;
        if (r.width < 30 || r.height < 15) continue;
        const src = (el.getAttribute('src') || '').toLowerCase();
        const alt = (el.getAttribute('alt') || '').toLowerCase();
        // Skip the club crest itself
        if (alt.includes('forest') || alt.includes('nottingham') || src.includes('crest') || src.includes('badge') || src.includes('logo-club') || alt === 'club logo') continue;
        candidates.push({ x: r.left + window.scrollX, y: absY, w: r.width, h: r.height });
    }
    if (candidates.length === 0) return null;
    // Bounding box of all sponsor candidates
    let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
    for (const c of candidates) {
        if (c.x < minX) minX = c.x;
        if (c.y < minY) minY = c.y;
        if (c.x + c.w > maxX) maxX = c.x + c.w;
        if (c.y + c.h > maxY) maxY = c.y + c.h;
    }
    if (maxX - minX < 40 || maxY - minY < 15) return null;
    return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
})()
"""

JS_NEXT_MATCH = """
(() => {
    // Next-match block — look for fixture cards with date/time/opponent in body
    const all = document.querySelectorAll('section, div, article');
    let best = null, bestScore = 0;
    for (const el of all) {
        const txt = (el.innerText || '').toUpperCase();
        if (!/(NEXT MATCH|NEXT FIXTURE|UPCOMING|FIXTURE|VS\\.?|V\\.?\\s)/i.test(txt)) continue;
        const hasDate = /\\b(MON|TUE|WED|THU|FRI|SAT|SUN|JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\\b/i.test(txt);
        const hasTime = /\\d{1,2}:\\d{2}/.test(txt);
        if (!(hasDate || hasTime)) continue;
        const r = el.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (absY < 200 || absY > 4500) continue;
        if (r.height < 150 || r.height > 900) continue;
        if (r.width < 400) continue;
        // Prefer compact match-card-like structures
        const score = (txt.includes('NEXT MATCH') ? 100 : 0) + (hasTime ? 30 : 0) + (hasDate ? 20 : 0) - r.height / 30;
        if (score > bestScore) {
            bestScore = score;
            best = { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
        }
    }
    return best;
})()
"""

JS_RESULTS_BLOCK = """
(() => {
    // Results block — contains score patterns like "1-0", "2 - 1"
    const all = document.querySelectorAll('section, div, article');
    let best = null, bestScore = 0;
    for (const el of all) {
        const txt = el.innerText || '';
        const upper = txt.toUpperCase();
        // Need score pattern + RESULT/HIGHLIGHTS/FT label
        const scoreCount = (txt.match(/\\b\\d\\s*[-–]\\s*\\d\\b/g) || []).length;
        if (scoreCount < 1) continue;
        const hasResultLabel = /(RESULT|HIGHLIGHT|FT|FULL[- ]?TIME|FULL TIME|MATCH REPORT)/i.test(upper);
        if (!hasResultLabel && scoreCount < 2) continue;
        const r = el.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (absY < 300 || absY > 5000) continue;
        if (r.height < 120 || r.height > 800) continue;
        if (r.width < 400) continue;
        const score = scoreCount * 20 + (hasResultLabel ? 50 : 0) - r.height / 30;
        if (score > bestScore) {
            bestScore = score;
            best = { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
        }
    }
    return best;
})()
"""

JS_VIDEO_THUMBNAILS = """
(() => {
    // Forest: video carousel splide__list at y~3971, 1248x340, with 12+ video thumbnails
    const lists = document.querySelectorAll('ul.splide__list, [class*="splide__list"]');
    let best = null, bestScore = 0;
    for (const ul of lists) {
        const imgs = ul.querySelectorAll('img').length;
        if (imgs < 5) continue;
        const txt = (ul.innerText || '').toUpperCase();
        const videoMarkers = (txt.match(/\\b(HIGHLIGHTS|MATCHDAY PASS|FULL MATCH|PRESS CONFERENCE|REACTS|DISCUSSES|PREVIEWS|EPISODE|VIDEO|WATCH|HIGHLIGHT)\\b/g) || []).length;
        if (videoMarkers < 3) continue;
        const r = ul.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (absY < 200 || absY > 7500) continue;
        if (r.height < 150 || r.height > 700) continue;
        if (r.width < 600) continue;
        const score = videoMarkers * 10 + imgs * 2 - r.height / 50;
        if (score > bestScore) {
            bestScore = score;
            best = { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
        }
    }
    return best;
})()
"""

JS_PRESS_CONFERENCE = """
(() => {
    // Forest: PRESS CONFERENCE H3 inside a video card (splide slide). Find a card with valid coords.
    // Loop all matches — some may be in cloned/off-screen splide slides with negative x.
    const hs = document.querySelectorAll('h3');
    for (const h of hs) {
        const t = (h.innerText || '').trim();
        if (!/PRESS CONFERENCE/i.test(t)) continue;
        let p = h.parentElement;
        for (let i = 0; i < 8 && p; i++) {
            const cls = (p.className || '').toString();
            const isCard = /splide__slide|content-card|content-card-contents/.test(cls);
            if (isCard) {
                const r = p.getBoundingClientRect();
                const absX = r.left + window.scrollX;
                const absY = r.top + window.scrollY;
                // Must have positive coords (on-screen) and reasonable size
                if (absX >= 0 && absX < 1400 && r.width >= 150 && r.width <= 600
                    && r.height >= 200 && r.height <= 600) {
                    return { x: absX, y: absY, width: r.width, height: r.height };
                }
            }
            p = p.parentElement;
        }
    }
    return null;
})()
"""

JS_WOMENS_TICKETS = """
(() => {
    // Forest: FOREST WOMEN section at y=5979, contains "Previous Result" + "No Upcoming Fixtures"
    // — no explicit tickets but it's the women's match/fixture widget. Capture this section.
    const hs = document.querySelectorAll('h1');
    for (const h of hs) {
        if (!/FOREST WOMEN\\b/i.test(h.innerText || '')) continue;
        let p = h.parentElement;
        for (let i = 0; i < 6 && p; i++) {
            const r = p.getBoundingClientRect();
            const absY = r.top + window.scrollY;
            const cls = (p.className || '').toString();
            if ((p.tagName === 'SECTION' || /sectionElement/.test(cls))
                && r.height >= 250 && r.height <= 800 && r.width >= 800) {
                return { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
            }
            p = p.parentElement;
        }
    }
    return null;
})()
"""

JS_FOOTER_SPONSOR_WALL = """
(() => {
    // Footer sponsor wall — partner logos row
    const footer = document.querySelector('footer') || document.body;
    const imgs = footer.querySelectorAll('img');
    const sponsorImgs = [];
    for (const img of imgs) {
        const r = img.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (absY < 1500) continue; // footer area
        if (r.width < 50 || r.height < 20) continue;
        if (r.width > 400 || r.height > 200) continue;
        const alt = (img.getAttribute('alt') || '').toLowerCase();
        const src = (img.getAttribute('src') || '').toLowerCase();
        // Skip social icons, app store badges
        if (/facebook|instagram|twitter|youtube|tiktok|x[-_]logo|app[-_]store|google[-_]play|apple/.test(alt + ' ' + src)) continue;
        // Skip club crest
        if (alt.includes('forest') || alt.includes('nottingham') || alt === 'logo') continue;
        sponsorImgs.push({ x: r.left + window.scrollX, y: absY, w: r.width, h: r.height });
    }
    if (sponsorImgs.length < 3) return null;
    // Cluster by y-band (within 400px)
    sponsorImgs.sort((a, b) => a.y - b.y);
    let bestCluster = null, bestSize = 0;
    for (const seed of sponsorImgs) {
        const cluster = sponsorImgs.filter(s => Math.abs(s.y - seed.y) < 400);
        if (cluster.length > bestSize) {
            bestSize = cluster.length;
            bestCluster = cluster;
        }
    }
    if (!bestCluster || bestCluster.length < 3) return null;
    let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
    for (const s of bestCluster) {
        if (s.x < minX) minX = s.x;
        if (s.y < minY) minY = s.y;
        if (s.x + s.w > maxX) maxX = s.x + s.w;
        if (s.y + s.h > maxY) maxY = s.y + s.h;
    }
    return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
})()
"""

JS_APP_STORE_BADGES = """
(() => {
    // Forest: "Download our app" promo banner at y=7521, 622x350.
    // Find the largest <a href="/download-our-app"> element (the body banner, not the header link).
    const all = document.querySelectorAll('a[href*="download-our-app"], a[href*="download-app"], a[href*="app.store"], a[href*="apps.apple"], a[href*="play.google"]');
    let best = null, bestArea = 0;
    for (const el of all) {
        const r = el.getBoundingClientRect();
        const absY = r.top + window.scrollY;
        if (r.width < 200 || r.height < 100) continue; // skip header link
        if (absY < 300) continue; // skip header
        if (r.width * r.height > bestArea) {
            bestArea = r.width * r.height;
            best = { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
        }
    }
    return best;
})()
"""


def capture_via_viewport(page, feature, js_box, pad=10):
    """Scroll element into viewport, then take a clipped viewport screenshot.
    Use for elements that lazy-load or live in horizontally-scrollable carousels.
    """
    try:
        # First locate (in document coords)
        box = page.evaluate(js_box)
        if not box:
            print(f"  [MISS] {feature}: not found")
            results["failed"].setdefault("nottm_forest", []).append(feature)
            return False
        target_y = max(0, int(box["y"]) - 100)
        page.evaluate(f"window.scrollTo(0, {target_y})")
        time.sleep(2)
        # Re-measure in viewport coords (no scrollX/scrollY offset)
        viewport_js = js_box.replace("+ window.scrollX", "").replace("+ window.scrollY", "")
        new_box = page.evaluate(viewport_js)
        if not new_box:
            print(f"  [MISS] {feature}: not found after scroll")
            results["failed"].setdefault("nottm_forest", []).append(feature)
            return False
        x = max(0, int(new_box["x"]) - pad)
        y = max(0, int(new_box["y"]) - pad)
        w = int(new_box["width"]) + pad * 2
        h = int(new_box["height"]) + pad * 2
        if w < 50 or h < 25:
            print(f"  [TINY] {feature}: {w}x{h}")
            results["failed"].setdefault("nottm_forest", []).append(feature)
            return False
        png = page.screenshot(clip={"x": x, "y": y, "width": w, "height": h})
        return save_img(feature, png)
    except Exception as e:
        print(f"  [ERR] {feature}: {e}")
        results["failed"].setdefault("nottm_forest", []).append(feature)
        return False


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page.goto(URL, timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)
        dismiss_cookies(page)
        time.sleep(1)
        scroll_lazy(page)

        h = page.evaluate("document.body.scrollHeight")
        print(f"page height: {h}px")

        # Phase 1: full-page screenshot for the 10 stable features
        full_png = page.screenshot(full_page=True)
        full_img = Image.open(BytesIO(full_png))

        capture_from_fullpage(page, full_img, "login_account", JS_LOGIN_ACCOUNT, pad=8)
        capture_from_fullpage(page, full_img, "shop_shortcut_in_header", JS_SHOP_SHORTCUT, pad=8)
        capture_from_fullpage(page, full_img, "search_input_in_header", JS_SEARCH, pad=8)
        capture_from_fullpage(page, full_img, "sponsor_lockup_in_header", JS_SPONSOR_LOCKUP, pad=10)
        capture_from_fullpage(page, full_img, "next_match_block", JS_NEXT_MATCH, pad=15)
        capture_from_fullpage(page, full_img, "next_match_feature_rich", JS_NEXT_MATCH, pad=15)
        capture_from_fullpage(page, full_img, "results_block", JS_RESULTS_BLOCK, pad=15)
        capture_from_fullpage(page, full_img, "video_thumbnails_inline", JS_VIDEO_THUMBNAILS, pad=15)
        capture_from_fullpage(page, full_img, "womens_team_tickets", JS_WOMENS_TICKETS, pad=15)
        capture_from_fullpage(page, full_img, "footer_sponsor_wall", JS_FOOTER_SPONSOR_WALL, pad=20)

        # Phase 2: per-element captures for lazy-loading/carousel-internal features

        # APP STORE BADGES: scroll banner into view, wait for image lazy-load, then viewport-clip
        try:
            page.evaluate("""
                const a = document.querySelectorAll('a[href*="download-our-app"]');
                for (const el of a) {
                    const r = el.getBoundingClientRect();
                    if (r.width >= 200 && r.height >= 100) {
                        el.scrollIntoView({block: 'center'});
                        // Force-load any images inside (in case of native lazy-loading)
                        el.querySelectorAll('img').forEach(img => {
                            const ds = img.getAttribute('data-src');
                            if (ds && !img.src) img.src = ds;
                            img.loading = 'eager';
                        });
                        break;
                    }
                }
            """)
            time.sleep(3)
            new_box = page.evaluate("""
                (() => {
                    const all = document.querySelectorAll('a[href*="download-our-app"]');
                    let best = null, bestArea = 0;
                    for (const el of all) {
                        const r = el.getBoundingClientRect();
                        if (r.width < 200 || r.height < 100) continue;
                        if (r.width * r.height > bestArea) {
                            bestArea = r.width * r.height;
                            best = { x: r.left, y: r.top, w: r.width, h: r.height };
                        }
                    }
                    return best;
                })()
            """)
            if new_box:
                pad = 12
                x = max(0, int(new_box["x"]) - pad)
                y = max(0, int(new_box["y"]) - pad)
                w = int(new_box["w"]) + pad * 2
                h = int(new_box["h"]) + pad * 2
                png = page.screenshot(clip={"x": x, "y": y, "width": w, "height": h})
                save_img("app_store_badges", png)
            else:
                print("  [MISS] app_store_badges: not found")
                results["failed"].setdefault("nottm_forest", []).append("app_store_badges")
        except Exception as e:
            print(f"  [ERR] app_store_badges: {e}")
            results["failed"].setdefault("nottm_forest", []).append("app_store_badges")

        # PRESS CONFERENCE: shift the splide__list transform to bring the press-conference slide
        # into the viewport. Forest's arrow buttons aren't reliably clickable; direct transform works.
        try:
            # Position the carousel containing PRESS CONFERENCE in viewport
            page.evaluate("""
                const splides = document.querySelectorAll('.splide');
                for (const sp of splides) {
                    if (!/PRESS CONFERENCE/i.test(sp.innerText || '')) continue;
                    sp.scrollIntoView({block: 'center'});
                    break;
                }
            """)
            time.sleep(1)
            # Try a series of transform offsets until press conference lands in viewport
            slide_w = 316  # card 300 + gap 16
            captured = False
            for offset_slides in range(5, 12):
                tx = -offset_slides * slide_w
                page.evaluate(f"""
                    const splides = document.querySelectorAll('.splide');
                    for (const sp of splides) {{
                        if (!/PRESS CONFERENCE/i.test(sp.innerText || '')) continue;
                        const list = sp.querySelector('.splide__list');
                        if (list) {{
                            list.style.transition = 'none';
                            list.style.transform = 'translateX({tx}px)';
                        }}
                        break;
                    }}
                """)
                time.sleep(0.5)
                in_view = page.evaluate("""
                    (() => {
                        const hs = document.querySelectorAll('h3');
                        for (const h of hs) {
                            if (!/PRESS CONFERENCE/i.test(h.innerText || '')) continue;
                            let p = h.parentElement;
                            for (let i = 0; i < 8 && p; i++) {
                                const cls = (p.className || '').toString();
                                if (/splide__slide|content-card/.test(cls)) {
                                    const r = p.getBoundingClientRect();
                                    if (r.left >= 0 && r.left + r.width <= 1400
                                        && r.width >= 150 && r.width <= 600
                                        && r.top + r.height <= 900 && r.bottom >= 0) {
                                        return { x: r.left, y: r.top, w: r.width, h: r.height };
                                    }
                                }
                                p = p.parentElement;
                            }
                        }
                        return null;
                    })()
                """)
                if in_view:
                    pad = 12
                    x = max(0, int(in_view["x"]) - pad)
                    y = max(0, int(in_view["y"]) - pad)
                    w = int(in_view["w"]) + pad * 2
                    h = int(in_view["h"]) + pad * 2
                    png = page.screenshot(clip={"x": x, "y": y, "width": w, "height": h})
                    if save_img("press_conference_block", png):
                        captured = True
                    break
            if not captured:
                print("  [MISS] press_conference_block: still off-viewport after transform shifts")
                results["failed"].setdefault("nottm_forest", []).append("press_conference_block")
        except Exception as e:
            print(f"  [ERR] press_conference_block: {e}")
            results["failed"].setdefault("nottm_forest", []).append("press_conference_block")

        browser.close()

    print("\n=== Summary ===")
    print(f"Captured: {sum(len(v) for v in results['captured'].values())}")
    for f in results.get("captured", {}).get("nottm_forest", []):
        print(f"  [OK] {f}")
    print(f"Failed: {sum(len(v) for v in results['failed'].values())}")
    for f in results.get("failed", {}).get("nottm_forest", []):
        print(f"  [FAIL] {f}")


if __name__ == "__main__":
    main()
