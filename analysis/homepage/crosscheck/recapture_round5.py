#!/usr/bin/env python3
"""Round 5: Targeted recapture with precise selectors based on visual review."""

import json
import time
import numpy as np
from pathlib import Path
from PIL import Image
from io import BytesIO
from playwright.sync_api import sync_playwright

IMG_DIR = Path("/Users/sergeykrasotin/Claude/26-04-sport-prototype/fc-feature-matrix/analysis/homepage/crosscheck/img")
RESULTS_FILE = Path("/Users/sergeykrasotin/Claude/26-04-sport-prototype/fc-feature-matrix/analysis/homepage/crosscheck/recapture_round5_results.json")

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
    print(f"    [OK] {feature}: {img.size[0]}x{img.size[1]}")
    results.setdefault("captured", {}).setdefault(club, []).append(feature)
    return True


def dismiss_cookies(page):
    try:
        page.evaluate("""
            const btns = document.querySelectorAll('button, a, [role="button"]');
            for (const b of btns) {
                const txt = (b.textContent || '').toLowerCase().trim();
                if (txt.includes('accept all') || txt.includes('reject all') || txt.includes('agree')
                    || txt.includes('accept') || txt.includes('aceptar') || txt.includes('aceitar')
                    || txt.includes('akzeptieren') || txt.includes('allow all') || txt.includes('accetto')
                    || txt.includes('i agree') || txt.includes('confirm')) {
                    b.click(); break;
                }
            }
        """)
        time.sleep(1)
        page.evaluate("""
            document.querySelectorAll('[class*="cookie"], [class*="consent"], [class*="banner"], [role="dialog"], [class*="modal"], [class*="popup"], [class*="overlay"]').forEach(e => {
                if (e.getBoundingClientRect().height > 100) e.remove();
            });
        """)
    except:
        pass
    time.sleep(0.5)


def scroll_lazy(page):
    try:
        h = page.evaluate("document.body.scrollHeight")
        for i in range(min(h // 600, 15)):
            page.evaluate(f"window.scrollTo(0, {(i+1)*600})")
            time.sleep(0.4)
        time.sleep(2)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)
    except:
        pass


def capture_from_fullpage(page, club, feature, js_code):
    """Take full-page screenshot, use JS to find element bounds, crop with PIL."""
    try:
        box = page.evaluate(js_code)
        if not box:
            print(f"    [MISS] {feature}: element not found")
            results.setdefault("failed", {}).setdefault(club, []).append(feature)
            return False

        # Take full-page screenshot
        full_png = page.screenshot(full_page=True)
        full_img = Image.open(BytesIO(full_png))
        fw, fh = full_img.size

        x = max(0, int(box["x"]))
        y = max(0, int(box["y"]))
        w = int(box["width"])
        h = int(box["height"])

        # Add padding
        pad = 10
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(fw, x + w + pad)
        y2 = min(fh, y + h + pad)

        if x2 - x1 < 20 or y2 - y1 < 10:
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


# ============================================================
# REAL MADRID — social_links_in_footer
# Footer has: Facebook, Instagram, X, YouTube, Twitch, Snapchat, TikTok icons
# ============================================================
def do_real_madrid(browser):
    print("\n" + "=" * 60)
    print("  real_madrid (https://www.realmadrid.com/en)")
    print("=" * 60)
    page = browser.new_page()
    try:
        page.goto("https://www.realmadrid.com/en", timeout=30000, wait_until="domcontentloaded")
        time.sleep(4)
        dismiss_cookies(page)
        scroll_lazy(page)

        # Social links are in the footer, after sponsor logos
        # They're SVG icons for facebook, instagram, x, youtube, etc.
        capture_from_fullpage(page, "real_madrid", "social_links_in_footer", """
            (() => {
                // Find social links by their href patterns
                const footer = document.querySelector('footer') || document.body;
                const socialLinks = footer.querySelectorAll('a[href*="facebook"], a[href*="instagram"], a[href*="twitter"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"]');
                if (socialLinks.length < 2) return null;

                // Get bounding box of the container holding these links
                let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
                for (const link of socialLinks) {
                    const r = link.getBoundingClientRect();
                    const absY = r.top + window.scrollY;
                    const absX = r.left + window.scrollX;
                    if (absX < minX) minX = absX;
                    if (absY < minY) minY = absY;
                    if (absX + r.width > maxX) maxX = absX + r.width;
                    if (absY + r.height > maxY) maxY = absY + r.height;
                }
                return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
            })()
        """)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


# ============================================================
# SL BENFICA — tickets_shortcut_in_header, shop_shortcut_in_header
# Header secondary nav: "Bilhetes" (tickets) and "Loja" (shop)
# ============================================================
def do_sl_benfica(browser):
    print("\n" + "=" * 60)
    print("  sl_benfica (https://www.slbenfica.pt)")
    print("=" * 60)
    page = browser.new_page()
    try:
        page.goto("https://www.slbenfica.pt", timeout=30000, wait_until="domcontentloaded")
        time.sleep(4)
        dismiss_cookies(page)
        time.sleep(1)

        # "Bilhetes" link in header nav
        capture_from_fullpage(page, "sl_benfica", "tickets_shortcut_in_header", """
            (() => {
                const links = document.querySelectorAll('a, button, span');
                for (const el of links) {
                    const txt = (el.textContent || '').trim();
                    if (txt === 'Bilhetes' || txt === 'bilhetes') {
                        const r = el.getBoundingClientRect();
                        if (r.top < 200 && r.width > 10) {
                            return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: r.height };
                        }
                    }
                }
                return null;
            })()
        """)

        # "Loja" link in header nav
        capture_from_fullpage(page, "sl_benfica", "shop_shortcut_in_header", """
            (() => {
                const links = document.querySelectorAll('a, button, span');
                for (const el of links) {
                    const txt = (el.textContent || '').trim();
                    if (txt === 'Loja' || txt === 'loja') {
                        const r = el.getBoundingClientRect();
                        if (r.top < 200 && r.width > 10) {
                            return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: r.height };
                        }
                    }
                }
                return null;
            })()
        """)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


# ============================================================
# TOTTENHAM — results_block
# "Highlights | Sunderland 1-0 Spurs" with scores visible
# ============================================================
def do_tottenham(browser):
    print("\n" + "=" * 60)
    print("  tottenham (https://www.tottenhamhotspur.com)")
    print("=" * 60)
    page = browser.new_page()
    try:
        page.goto("https://www.tottenhamhotspur.com", timeout=30000, wait_until="domcontentloaded")
        time.sleep(4)
        dismiss_cookies(page)
        scroll_lazy(page)

        # Find match results area — look for text with score patterns like "X-Y" or "X - Y"
        capture_from_fullpage(page, "tottenham", "results_block", """
            (() => {
                // Look for elements containing score patterns
                const walker = document.createTreeWalker(
                    document.querySelector('main') || document.body,
                    NodeFilter.SHOW_ELEMENT
                );
                let node;
                while (node = walker.nextNode()) {
                    const txt = (node.innerText || '').trim();
                    // Match score patterns: "1-0", "2 - 1", "3-2" near team names
                    if (/\\d\\s*[-–]\\s*\\d/.test(txt) && txt.length < 500) {
                        const r = node.getBoundingClientRect();
                        if (r.top + window.scrollY > 300 && r.height > 80 && r.height < 600 && r.width > 200) {
                            return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: r.height };
                        }
                    }
                }

                // Fallback: look for class names with match/fixture/result/score
                const selectors = '[class*="result"], [class*="score"], [class*="fixture"], [class*="match-card"], [class*="highlights"]';
                const els = document.querySelectorAll(selectors);
                for (const el of els) {
                    const r = el.getBoundingClientRect();
                    if (r.top + window.scrollY > 300 && r.height > 80 && r.width > 200) {
                        return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: r.height };
                    }
                }
                return null;
            })()
        """)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


# ============================================================
# UEFA — login_account
# "Log in" button with person icon, far right of nav bar
# ============================================================
def do_uefa(browser):
    print("\n" + "=" * 60)
    print("  uefa (https://www.uefa.com)")
    print("=" * 60)
    page = browser.new_page()
    try:
        page.goto("https://www.uefa.com", timeout=30000, wait_until="domcontentloaded")
        time.sleep(4)
        dismiss_cookies(page)
        time.sleep(1)

        # "Log in" button in header — visible text "Log in" with person icon
        capture_from_fullpage(page, "uefa", "login_account", """
            (() => {
                // Search for "Log in" text in header area
                const els = document.querySelectorAll('a, button, span, div');
                for (const el of els) {
                    const txt = (el.textContent || '').trim().toLowerCase();
                    if ((txt === 'log in' || txt === 'login' || txt === 'sign in') && el.getBoundingClientRect().top < 150) {
                        const r = el.getBoundingClientRect();
                        if (r.width > 5 && r.height > 5) {
                            return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: Math.max(r.width, 80), height: Math.max(r.height, 30) };
                        }
                    }
                }
                // Fallback: look for person/user icons in header
                const icons = document.querySelectorAll('header svg, header [class*="user"], header [class*="account"], header [class*="login"], header [aria-label*="log"], header [aria-label*="account"]');
                for (const el of icons) {
                    const r = el.getBoundingClientRect();
                    if (r.top < 150 && r.width > 5) {
                        return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: Math.max(r.width, 80), height: Math.max(r.height, 30) };
                    }
                }
                return null;
            })()
        """)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


# ============================================================
# MOTOGP — social_links_in_footer
# Footer has Facebook, Instagram, Threads, X, TikTok, YouTube, LinkedIn, etc.
# ============================================================
def do_motogp(browser):
    print("\n" + "=" * 60)
    print("  motogp (https://www.motogp.com)")
    print("=" * 60)
    page = browser.new_page()
    try:
        page.goto("https://www.motogp.com", timeout=30000, wait_until="domcontentloaded")
        time.sleep(5)
        dismiss_cookies(page)
        time.sleep(1)

        # Scroll to bottom carefully (MotoGP crashes on aggressive scrolling)
        try:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)
        except:
            # If crashed, re-navigate and try direct scroll
            try:
                page.goto("https://www.motogp.com", timeout=30000, wait_until="domcontentloaded")
                time.sleep(5)
                dismiss_cookies(page)
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(3)
            except:
                pass

        # Social links in footer
        capture_from_fullpage(page, "motogp", "social_links_in_footer", """
            (() => {
                const footer = document.querySelector('footer') || document.body;
                const socialLinks = footer.querySelectorAll('a[href*="facebook"], a[href*="instagram"], a[href*="twitter"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"], a[href*="linkedin"], a[href*="threads"]');
                if (socialLinks.length < 2) {
                    // Try broader search
                    const allLinks = document.querySelectorAll('a[href*="facebook"], a[href*="instagram"], a[href*="twitter"], a[href*="youtube"], a[href*="tiktok"], a[href*="x.com"]');
                    if (allLinks.length < 2) return null;
                    // Use the ones furthest down the page (footer ones)
                    let best = [];
                    for (const a of allLinks) {
                        const r = a.getBoundingClientRect();
                        best.push({ el: a, y: r.top + window.scrollY });
                    }
                    best.sort((a, b) => b.y - a.y);
                    const footerLinks = best.slice(0, Math.min(8, best.length));
                    let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
                    for (const item of footerLinks) {
                        const r = item.el.getBoundingClientRect();
                        const absY = r.top + window.scrollY;
                        const absX = r.left + window.scrollX;
                        if (absX < minX) minX = absX;
                        if (absY < minY) minY = absY;
                        if (absX + r.width > maxX) maxX = absX + r.width;
                        if (absY + r.height > maxY) maxY = absY + r.height;
                    }
                    return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
                }

                let minX = Infinity, minY = Infinity, maxX = 0, maxY = 0;
                for (const link of socialLinks) {
                    const r = link.getBoundingClientRect();
                    const absY = r.top + window.scrollY;
                    const absX = r.left + window.scrollX;
                    if (absX < minX) minX = absX;
                    if (absY < minY) minY = absY;
                    if (absX + r.width > maxX) maxX = absX + r.width;
                    if (absY + r.height > maxY) maxY = absY + r.height;
                }
                return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
            })()
        """)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


# ============================================================
# CLUB BRUGGE — store_block (re-check: need to verify if it exists)
# ============================================================
def do_club_brugge(browser):
    print("\n" + "=" * 60)
    print("  club_brugge (https://www.clubbrugge.be)")
    print("=" * 60)
    page = browser.new_page()
    try:
        page.goto("https://www.clubbrugge.be", timeout=30000, wait_until="domcontentloaded")
        time.sleep(4)
        dismiss_cookies(page)
        scroll_lazy(page)

        # Check if store block exists — look for shop/store/merchandise section
        capture_from_fullpage(page, "club_brugge", "store_block", """
            (() => {
                const main = document.querySelector('main') || document.body;
                // Look for store/shop sections by heading text
                const headings = main.querySelectorAll('h1, h2, h3, h4, [class*="title"]');
                for (const h of headings) {
                    const txt = (h.textContent || '').toLowerCase();
                    if (txt.includes('shop') || txt.includes('store') || txt.includes('merchandise')
                        || txt.includes('fanshop') || txt.includes('winkel') || txt.includes('boutique')) {
                        // Found a store heading — get its parent section
                        let section = h.closest('section') || h.parentElement;
                        const r = section.getBoundingClientRect();
                        if (r.height > 100 && r.width > 200) {
                            return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: Math.min(r.height, 800) };
                        }
                    }
                }
                // Look for product cards with prices
                const priceEls = main.querySelectorAll('[class*="product"], [class*="price"], [class*="store"], [class*="shop"]');
                for (const el of priceEls) {
                    const r = el.getBoundingClientRect();
                    if (r.top + window.scrollY > 500 && r.height > 100 && r.width > 200) {
                        return { x: r.left + window.scrollX, y: r.top + window.scrollY, width: r.width, height: Math.min(r.height, 800) };
                    }
                }
                return null;
            })()
        """)
    except Exception as e:
        print(f"  CRASH: {e}")
    finally:
        page.close()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        for handler in [do_real_madrid, do_sl_benfica, do_tottenham, do_uefa, do_motogp, do_club_brugge]:
            page = context.new_page()
            try:
                handler_name = handler.__name__.replace("do_", "")
                # Each handler creates its own page, so close this unused one
                page.close()
                handler(context)
            except Exception as e:
                print(f"  Unhandled error: {e}")
                try:
                    page.close()
                except:
                    pass

        browser.close()

    # Print summary
    total_ok = sum(len(v) for v in results.get("captured", {}).values())
    total_fail = sum(len(v) for v in results.get("failed", {}).values())

    print("\n" + "=" * 60)
    print(f"  ROUND 5 SUMMARY: {total_ok} captured, {total_fail} failed")
    print("=" * 60)
    for club, feats in results.get("captured", {}).items():
        for f in feats:
            print(f"  [OK]   {club}/{f}")
    for club, feats in results.get("failed", {}).items():
        for f in feats:
            print(f"  [FAIL] {club}/{f}")

    RESULTS_FILE.write_text(json.dumps(results, indent=2) + "\n")
    print(f"\n  Results saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
