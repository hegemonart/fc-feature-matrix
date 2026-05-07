#!/usr/bin/env python3
"""Find the BE A MEMBER promo card on Wrexham, and the secondary editorial
strip + UNITING YOUR BUSINESS card on Barnsley."""

import time
from playwright.sync_api import sync_playwright


def kill_onetrust(page):
    page.evaluate("""
        const accept = document.getElementById('onetrust-accept-btn-handler');
        if (accept) accept.click();
        document.querySelectorAll('[class*="onetrust"], #onetrust-banner-sdk, #onetrust-consent-sdk, .onetrust-pc-dark-filter').forEach(e => e.remove());
    """)
    time.sleep(2)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # --- WREXHAM: find BE A MEMBER ---
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.wrexhamafc.co.uk/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6); kill_onetrust(page); time.sleep(1)
        page.evaluate("window.scrollTo(0, 1500)")
        time.sleep(2)

        print("=== WREXHAM: search for 'BE A MEMBER' / membership signal ===")
        info = page.evaluate(r"""
            (() => {
                const out = [];
                // Images with alt mentioning member/membership/wrexham story
                document.querySelectorAll('img').forEach(img => {
                    const alt = (img.alt || '').toLowerCase();
                    const src = (img.src || '').toLowerCase();
                    if (/member|wrexham story|join|belong/.test(alt) ||
                        /member|join|belong/.test(src)) {
                        const r = img.getBoundingClientRect();
                        out.push({type: 'img', alt: img.alt.substring(0, 80),
                                  src: img.src.substring(0, 100),
                                  top: Math.round(r.top + scrollY),
                                  width: Math.round(r.width), height: Math.round(r.height)});
                    }
                });
                // Links containing /membership in href
                document.querySelectorAll('a').forEach(a => {
                    const href = (a.href || '').toLowerCase();
                    if (/membership|member-info|join-us|belong/.test(href)) {
                        const r = a.getBoundingClientRect();
                        out.push({type: 'a', href: a.href.substring(0, 100),
                                  top: Math.round(r.top + scrollY),
                                  width: Math.round(r.width), height: Math.round(r.height),
                                  text: (a.textContent || '').trim().substring(0, 60)});
                    }
                });
                return out.slice(0, 20);
            })()
        """)
        for it in info:
            print(it)

        # Capture full-page screenshot to confirm visually
        png = page.screenshot(full_page=True)
        from pathlib import Path
        Path("/tmp/wrexham_full_for_member.png").write_bytes(png)
        print(f"  full-page saved to /tmp/wrexham_full_for_member.png")
        page.close()

        # --- BARNSLEY: find UNITING YOUR BUSINESS + secondary editorial strip ---
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.barnsleyfc.co.uk/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6); kill_onetrust(page); time.sleep(1)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(1)

        print("\n=== BARNSLEY: search for UNITING YOUR BUSINESS card ===")
        b2b = page.evaluate(r"""
            (() => {
                const out = [];
                document.querySelectorAll('a, div, section').forEach(el => {
                    const txt = (el.textContent || '').trim();
                    if (/uniting|with barnsley football|find out more/i.test(txt) && txt.length < 400) {
                        const r = el.getBoundingClientRect();
                        if (r.height > 80 && r.height < 700 && r.width > 200) {
                            out.push({tag: el.tagName,
                                      cls: (el.className || '').toString().substring(0, 80),
                                      top: Math.round(r.top + scrollY),
                                      width: Math.round(r.width), height: Math.round(r.height),
                                      text: txt.substring(0, 100)});
                        }
                    }
                });
                return out.slice(0, 10);
            })()
        """)
        for it in b2b:
            print(it)

        print("\n=== BARNSLEY: search for secondary editorial strip (3 cards under hero) ===")
        strip = page.evaluate(r"""
            (() => {
                const out = [];
                // Look for sections in the 600-1500px Y range that contain a row of 3 cards
                document.querySelectorAll('section, div').forEach(el => {
                    const r = el.getBoundingClientRect();
                    const top = r.top + scrollY;
                    if (top > 500 && top < 1500 && r.width > 1000 && r.height > 100 && r.height < 500) {
                        const links = el.querySelectorAll('a').length;
                        if (links >= 2 && links < 12) {
                            out.push({tag: el.tagName,
                                      cls: (el.className || '').toString().substring(0, 60),
                                      top: Math.round(top), height: Math.round(r.height),
                                      links: links});
                        }
                    }
                });
                return out.slice(0, 8);
            })()
        """)
        for it in strip:
            print(it)
        page.close()
        browser.close()


if __name__ == "__main__":
    main()
