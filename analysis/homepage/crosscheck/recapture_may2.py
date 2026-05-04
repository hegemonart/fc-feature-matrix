#!/usr/bin/env python3
"""May 2 recapture: 7 missing crops after PSG/F1/BVB feature flips.

Captures:
- psg: footer_sponsor_wall, app_store_badges, social_links_in_footer
- f1: player_roster_preview, individual_player_cards, footer_sponsor_wall
- bvb_dortmund: store_block
"""

import time
import numpy as np
from pathlib import Path
from PIL import Image
from io import BytesIO
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).parent / "img"

results = {"captured": {}, "failed": {}}


def is_blank(png_bytes):
    img = Image.open(BytesIO(png_bytes))
    arr = np.array(img)
    return arr.std() < 5


def save_img(club, feature, png_bytes):
    if is_blank(png_bytes):
        print(f"    [BLANK] {feature}")
        results.setdefault("failed", {}).setdefault(club, []).append(feature)
        return False
    path = IMG_DIR / f"{club}_{feature}.png"
    path.write_bytes(png_bytes)
    img = Image.open(BytesIO(png_bytes))
    print(f"    [OK] {feature}: {img.size[0]}x{img.size[1]} -> {path.name}")
    results.setdefault("captured", {}).setdefault(club, []).append(feature)
    return True


def dismiss_cookies_generic(page):
    try:
        page.evaluate("""
            const btns = document.querySelectorAll('button, a, [role="button"]');
            for (const b of btns) {
                const txt = (b.textContent || '').toLowerCase().trim();
                if (txt.includes('accept all') || txt.includes('agree') || txt.includes('accept')
                    || txt.includes('aceptar') || txt.includes('akzeptieren') || txt.includes('confirm')) {
                    b.click(); break;
                }
            }
        """)
        time.sleep(1)
        page.evaluate("""
            document.querySelectorAll('[class*="cookie"], [class*="consent"], [role="dialog"], [class*="modal"], [class*="popup"], [class*="overlay"]').forEach(e => {
                const r = e.getBoundingClientRect();
                if (r.height > 100 || r.width > 300) e.remove();
            });
        """)
    except Exception:
        pass
    time.sleep(0.5)


def dismiss_cookies_psg(page):
    """PSG uses Didomi."""
    try:
        page.evaluate("""
            const b = document.querySelector('#didomi-notice-agree-button');
            if (b) b.click();
        """)
        time.sleep(1)
    except Exception:
        pass
    dismiss_cookies_generic(page)


def dismiss_cookies_consentmanager(page):
    """BVB Dortmund + other Bundesliga sites."""
    try:
        page.evaluate("window.__cmp && window.__cmp('setConsent', 0);")
        time.sleep(1)
    except Exception:
        pass
    dismiss_cookies_generic(page)


def scroll_lazy(page):
    try:
        h = page.evaluate("document.body.scrollHeight")
        for i in range(min(h // 600, 20)):
            page.evaluate(f"window.scrollTo(0, {(i+1)*600})")
            time.sleep(0.4)
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
    except Exception:
        pass


def capture_from_fullpage(page, club, feature, js_code, pad=10):
    try:
        box = page.evaluate(js_code)
        if not box:
            print(f"    [MISS] {feature}: element not found")
            results.setdefault("failed", {}).setdefault(club, []).append(feature)
            return False
        full_png = page.screenshot(full_page=True)
        full_img = Image.open(BytesIO(full_png))
        fw, fh = full_img.size
        x, y, w, h = int(box["x"]), int(box["y"]), int(box["width"]), int(box["height"])
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(fw, x + w + pad)
        y2 = min(fh, y + h + pad)
        if x2 - x1 < 50 or y2 - y1 < 30:
            print(f"    [TINY] {feature}: {x2-x1}x{y2-y1}")
            results.setdefault("failed", {}).setdefault(club, []).append(feature)
            return False
        cropped = full_img.crop((x1, y1, x2, y2))
        buf = BytesIO()
        cropped.save(buf, format="PNG")
        return save_img(club, feature, buf.getvalue())
    except Exception as e:
        print(f"    [ERR] {feature}: {e}")
        results.setdefault("failed", {}).setdefault(club, []).append(feature)
        return False


def capture_via_viewport_clip(page, club, feature, js_box, pad=10):
    """Capture by scrolling element into viewport and clipping a viewport screenshot.

    Use this for elements inside position:sticky containers — full-page screenshot doesn't
    render sticky correctly.
    """
    try:
        box = page.evaluate(js_box)
        if not box:
            print(f"    [MISS] {feature}: element not found")
            results.setdefault("failed", {}).setdefault(club, []).append(feature)
            return False
        # Scroll so the element is visible in the viewport (target ~100px from top)
        target_y = max(0, int(box["y"]) - 100)
        page.evaluate(f"window.scrollTo(0, {target_y})")
        time.sleep(1)
        # Re-measure in viewport coords
        new_box = page.evaluate(js_box.replace("+ window.scrollX", "").replace("+ window.scrollY", ""))
        if not new_box:
            print(f"    [MISS] {feature}: element not found after scroll")
            results.setdefault("failed", {}).setdefault(club, []).append(feature)
            return False
        x = max(0, int(new_box["x"]) - pad)
        y = max(0, int(new_box["y"]) - pad)
        w = int(new_box["width"]) + pad * 2
        h = int(new_box["height"]) + pad * 2
        if w < 50 or h < 30:
            print(f"    [TINY] {feature}: {w}x{h}")
            results.setdefault("failed", {}).setdefault(club, []).append(feature)
            return False
        png = page.screenshot(clip={"x": x, "y": y, "width": w, "height": h})
        return save_img(club, feature, png)
    except Exception as e:
        print(f"    [ERR] {feature}: {e}")
        results.setdefault("failed", {}).setdefault(club, []).append(feature)
        return False


def unstick_footer(page):
    """Break position:sticky on footer so element coordinates match visible rendering."""
    page.evaluate("""
        document.querySelectorAll('footer, [class*="footer"], [class*="sticky"]').forEach(el => {
            const cs = window.getComputedStyle(el);
            if (cs.position === 'sticky' || cs.position === 'fixed') {
                el.style.position = 'relative';
                el.style.transform = 'none';
                el.style.top = 'auto';
            }
        });
    """)
    time.sleep(0.5)


# ============================================================
# PSG — psg.fr/en
# ============================================================
def do_psg(browser):
    print("\n" + "=" * 60)
    print("  psg (https://www.psg.fr/en)")
    print("=" * 60)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    try:
        page.goto("https://www.psg.fr/en", timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)
        dismiss_cookies_psg(page)
        time.sleep(1)
        scroll_lazy(page)

        h = page.evaluate("document.body.scrollHeight")
        print(f"    page height: {h}px")

        # footer_sponsor_wall — Nike, Qatar Airways, Beyond, Visit Qatar, Ooredoo, etc.
        # Restrict to imgs whose src is in PSG's media CDN (rules out 3rd-party ads).
        # Then cluster by y-band and pick the densest cluster.
        capture_from_fullpage(page, "psg", "footer_sponsor_wall", """
            (() => {
                const sponsorRe = /nike|qatar_airways|qatar-airways|ooredoo|accor|whoop|bitpanda|aspetar|snipes|parions|bein-sports|bein_sports|qnb|visit-rwanda|visit_rwanda|beyond|visit-qatar/i;
                const imgs = document.querySelectorAll('img');
                const matches = [];
                for (const img of imgs) {
                    const src = (img.getAttribute('src') || '').toLowerCase();
                    const alt = (img.getAttribute('alt') || '').toLowerCase();
                    // Only PSG CDN logos — excludes third-party ads
                    const isPsgCdn = src.includes('media.psg.fr');
                    if (!isPsgCdn) continue;
                    if (!sponsorRe.test(src) && !sponsorRe.test(alt)) continue;
                    const r = img.getBoundingClientRect();
                    if (r.width < 30 || r.height < 15) continue;
                    matches.push({
                        x: r.left + window.scrollX,
                        y: r.top + window.scrollY,
                        w: r.width,
                        h: r.height
                    });
                }
                if (matches.length < 4) return null;
                // Cluster by y-band (within 500px)
                matches.sort((a, b) => a.y - b.y);
                let bestCluster = null, bestCount = 0;
                for (let i = 0; i < matches.length; i++) {
                    const baseY = matches[i].y;
                    const cluster = matches.filter(m => Math.abs(m.y - baseY) < 500);
                    if (cluster.length > bestCount) {
                        bestCount = cluster.length;
                        bestCluster = cluster;
                    }
                }
                if (!bestCluster || bestCluster.length < 4) return null;
                let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
                for (const s of bestCluster) {
                    if (s.x < minX) minX = s.x;
                    if (s.y < minY) minY = s.y;
                    if (s.x + s.w > maxX) maxX = s.x + s.w;
                    if (s.y + s.h > maxY) maxY = s.y + s.h;
                }
                return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
            })()
        """, pad=30)

        # app_store_badges — PSG's footer is position:sticky, so badges only render in the
        # visible footer when the user has scrolled to the bottom. Unstick first, then use
        # viewport-clip capture (full-page screenshot doesn't honour sticky behaviour).
        unstick_footer(page)
        # Re-trigger lazy-load of the badge images that were hidden until unsticking
        page.evaluate("""
            document.querySelectorAll('img[src*="download_on_the_app_store_badge"], img[src*="google-play-download-logo"]').forEach(img => {
                if (img.scrollIntoView) img.scrollIntoView();
            });
        """)
        time.sleep(1)

        capture_via_viewport_clip(page, "psg", "app_store_badges", """
            (() => {
                const apple = Array.from(document.querySelectorAll('img')).find(i => /download_on_the_app_store_badge/i.test(i.src || ''));
                const google = Array.from(document.querySelectorAll('img')).find(i => /google-play-download-logo/i.test(i.src || ''));
                if (!apple || !google) return null;
                let p = apple.parentElement;
                for (let i = 0; i < 8 && p; i++) {
                    if (p.contains(apple) && p.contains(google)) {
                        const r = p.getBoundingClientRect();
                        if (r.width > 100 && r.width < 600 && r.height > 50 && r.height < 400) {
                            return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: r.height };
                        }
                    }
                    p = p.parentElement;
                }
                return null;
            })()
        """, pad=12)

        # social_links_in_footer — PSG footer has a row of social icons (FB, IG, X, YT, Snap, TikTok, Threads, WhatsApp, Twitch, BeReal, Discord)
        # PSG may use SVG sprites or labelled buttons rather than direct social-domain hrefs. Search broadly.
        capture_from_fullpage(page, "psg", "social_links_in_footer", """
            (() => {
                const socialRe = /facebook|instagram|twitter|x\\.com|youtube|tiktok|snapchat|threads|whatsapp|discord|twitch|bereal/i;
                const all = document.querySelectorAll('a, button, [role="link"]');
                const items = [];
                for (const el of all) {
                    const href = (el.getAttribute('href') || '').toLowerCase();
                    const aria = (el.getAttribute('aria-label') || '').toLowerCase();
                    const title = (el.getAttribute('title') || '').toLowerCase();
                    const cls = (el.className || '').toString().toLowerCase();
                    if (!socialRe.test(href + ' ' + aria + ' ' + title + ' ' + cls)) continue;
                    const r = el.getBoundingClientRect();
                    const absY = r.top + window.scrollY;
                    if (r.width < 8 || r.height < 8) continue;
                    if (absY < 1500) continue; // skip header social, target footer
                    items.push({
                        x: r.left + window.scrollX,
                        y: absY,
                        w: r.width,
                        h: r.height
                    });
                }
                if (items.length < 3) return null;
                // Find the densest horizontal row
                items.sort((a, b) => a.y - b.y);
                let bestRow = null, bestRowSize = 0;
                for (let i = 0; i < items.length; i++) {
                    const rowY = items[i].y;
                    const row = items.filter(it => Math.abs(it.y - rowY) < 50);
                    if (row.length > bestRowSize) {
                        bestRowSize = row.length;
                        bestRow = row;
                    }
                }
                if (!bestRow || bestRow.length < 3) return null;
                let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
                for (const s of bestRow) {
                    if (s.x < minX) minX = s.x;
                    if (s.y < minY) minY = s.y;
                    if (s.x + s.w > maxX) maxX = s.x + s.w;
                    if (s.y + s.h > maxY) maxY = s.y + s.h;
                }
                return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
            })()
        """, pad=12)

    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


# ============================================================
# F1 — formula1.com
# ============================================================
def do_f1(browser):
    print("\n" + "=" * 60)
    print("  f1 (https://www.formula1.com)")
    print("=" * 60)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    try:
        page.goto("https://www.formula1.com/", timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)
        dismiss_cookies_generic(page)
        time.sleep(1)
        scroll_lazy(page)

        h = page.evaluate("document.body.scrollHeight")
        print(f"    page height: {h}px")

        # individual_player_cards — top-3 driver cards (Antonelli, Russell, Leclerc) with photos + points
        capture_from_fullpage(page, "f1", "individual_player_cards", """
            (() => {
                // Look for cards that include "PTS" or driver names with portrait imagery
                const all = document.querySelectorAll('section, div, ul');
                let best = null, bestScore = 0;
                for (const el of all) {
                    const txt = (el.innerText || '');
                    if (!txt.toUpperCase().includes('PTS')) continue;
                    // Need at least 3 PTS occurrences for top-3 cards
                    const ptsCount = (txt.toUpperCase().match(/\\bPTS\\b/g) || []).length;
                    if (ptsCount < 3) continue;
                    const imgs = el.querySelectorAll('img');
                    if (imgs.length < 3) continue;
                    const r = el.getBoundingClientRect();
                    const absY = r.top + window.scrollY;
                    if (r.height < 200 || r.width < 600) continue;
                    if (r.height > 800) continue;
                    const score = ptsCount * 50 - r.height / 10;
                    if (score > bestScore) {
                        bestScore = score;
                        best = { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
                    }
                }
                return best;
            })()
        """, pad=15)

        # player_roster_preview — drivers/teams tabs + standings table
        capture_from_fullpage(page, "f1", "player_roster_preview", """
            (() => {
                // Look for a section containing both DRIVERS heading/tab and a list of names
                const sections = document.querySelectorAll('section, div');
                let best = null, bestScore = 0;
                for (const el of sections) {
                    const txt = (el.innerText || '').toUpperCase();
                    if (!txt.includes('DRIVERS') && !txt.includes('STANDINGS')) continue;
                    const teamHits = (txt.match(/MERCEDES|FERRARI|MCLAREN|RED BULL|WILLIAMS|ASTON MARTIN|ALPINE/g) || []).length;
                    if (teamHits < 3) continue;
                    const r = el.getBoundingClientRect();
                    const absY = r.top + window.scrollY;
                    if (r.height < 300 || r.width < 600) continue;
                    if (r.height > 1500) continue;
                    if (absY < 200) continue; // skip header nav
                    const score = teamHits * 30 + (txt.includes('DRIVERS') ? 200 : 0) - r.height / 20;
                    if (score > bestScore) {
                        bestScore = score;
                        best = { x: r.left + window.scrollX, y: absY, width: r.width, height: r.height };
                    }
                }
                return best;
            })()
        """, pad=15)

        # footer_sponsor_wall — "OUR PARTNERS" section with LVMH, Pirelli, Aramco, AWS, etc.
        # Sponsor logos are imgs at y=5028-5169 with alt text matching brand names.
        capture_from_fullpage(page, "f1", "footer_sponsor_wall", """
            (() => {
                const sponsorRe = /lvmh|pirelli|aramco|heineken|aws|lenovo|dhl|qatar.airways|salesforce|tag.heuer|pepsi|crypto|santander|globant|allwyn|pwc|nestle|barilla|liqui|paramount|puma|tata|aggreko|mcdonald|mobile|amex|american.express|standard.chartered|marsh|moet|moët|hennessy|las.vegas|^msc$|msc.cruises|louis.vuitton/i;
                const imgs = document.querySelectorAll('img');
                const sponsorImgs = [];
                for (const img of imgs) {
                    const alt = (img.getAttribute('alt') || '').toLowerCase();
                    const src = (img.getAttribute('src') || '').toLowerCase();
                    if (!sponsorRe.test(alt) && !sponsorRe.test(src)) continue;
                    const r = img.getBoundingClientRect();
                    const absY = r.top + window.scrollY;
                    if (r.width < 30 || r.height < 15) continue;
                    if (absY < 1000) continue; // ignore header sponsor lockup
                    sponsorImgs.push({
                        x: r.left + window.scrollX,
                        y: absY,
                        w: r.width,
                        h: r.height
                    });
                }
                if (sponsorImgs.length < 6) return null;
                let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
                for (const s of sponsorImgs) {
                    if (s.x < minX) minX = s.x;
                    if (s.y < minY) minY = s.y;
                    if (s.x + s.w > maxX) maxX = s.x + s.w;
                    if (s.y + s.h > maxY) maxY = s.y + s.h;
                }
                return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
            })()
        """, pad=30)

    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


# ============================================================
# BVB Dortmund — bvb.de
# ============================================================
def do_bvb(browser):
    print("\n" + "=" * 60)
    print("  bvb_dortmund (https://www.bvb.de)")
    print("=" * 60)
    page = browser.new_page(viewport={"width": 1400, "height": 900})
    try:
        page.goto("https://www.bvb.de/", timeout=45000, wait_until="domcontentloaded")
        time.sleep(5)
        dismiss_cookies_consentmanager(page)
        time.sleep(2)
        scroll_lazy(page)

        h = page.evaluate("document.body.scrollHeight")
        print(f"    page height: {h}px")

        # store_block — BVB body has a "Fanshop voucher" promo card embedded in news (no traditional
        # store grid). Find the most prominent body element whose text directly references "Fanshop".
        capture_from_fullpage(page, "bvb_dortmund", "store_block", """
            (() => {
                const all = document.querySelectorAll('li, article, section, div, a');
                const candidates = [];
                for (const el of all) {
                    const txt = (el.innerText || el.textContent || '').trim();
                    if (!/fanshop/i.test(txt)) continue;
                    if (txt.length > 400) continue; // exclude broad parents
                    const r = el.getBoundingClientRect();
                    const absY = r.top + window.scrollY;
                    if (absY < 800) continue;     // skip header
                    if (absY > 5000) continue;    // skip footer
                    if (r.width < 200 || r.height < 150) continue;
                    if (r.width > 1500 || r.height > 900) continue;
                    const imgs = el.querySelectorAll('img');
                    if (imgs.length < 1) continue;
                    candidates.push({
                        x: r.left + window.scrollX,
                        y: absY,
                        w: r.width,
                        h: r.height,
                        len: txt.length
                    });
                }
                if (candidates.length === 0) return null;
                // Prefer tightest crop (smaller text = more focused element)
                candidates.sort((a, b) => a.len - b.len || (a.w * a.h) - (b.w * b.h));
                const c = candidates[0];
                return { x: c.x, y: c.y, width: c.w, height: c.h };
            })()
        """, pad=15)

    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            do_psg(browser)
            do_f1(browser)
            do_bvb(browser)
        finally:
            browser.close()

    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  Captured: {sum(len(v) for v in results['captured'].values())}")
    for club, feats in results.get("captured", {}).items():
        for f in feats:
            print(f"    [OK] {club}_{f}")
    print(f"  Failed: {sum(len(v) for v in results['failed'].values())}")
    for club, feats in results.get("failed", {}).items():
        for f in feats:
            print(f"    [FAIL] {club}_{f}")


if __name__ == "__main__":
    main()
