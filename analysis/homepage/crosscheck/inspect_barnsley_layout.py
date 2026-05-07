#!/usr/bin/env python3
"""Walk the Barnsley homepage DOM at known Y ranges to identify the
secondary editorial strip and the UNITING YOUR BUSINESS card."""

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
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.barnsleyfc.co.uk/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6); kill_onetrust(page); time.sleep(1)
        # Scroll all the way through and back
        h = page.evaluate("document.body.scrollHeight")
        for i in range(h // 600):
            page.evaluate(f"window.scrollTo(0, {(i+1)*600})")
            time.sleep(0.3)
        page.evaluate("window.scrollTo(0, 0)")
        time.sleep(2)
        kill_onetrust(page)

        print("=== Barnsley DOM tree at Y=600..1500 (below hero) ===")
        info = page.evaluate(r"""
            (() => {
                const out = [];
                document.querySelectorAll('section, div').forEach(el => {
                    const r = el.getBoundingClientRect();
                    const top = r.top + scrollY;
                    if (top > 600 && top < 1500 && r.width > 800 && r.height > 80 && r.height < 600) {
                        const cls = (el.className || '').toString();
                        const txt = (el.innerText || '').trim().substring(0, 120).replace(/\n/g, ' | ');
                        out.push({tag: el.tagName, top: Math.round(top),
                                  width: Math.round(r.width), height: Math.round(r.height),
                                  cls: cls.substring(0, 80), txt: txt});
                    }
                });
                return out.slice(0, 25);
            })()
        """)
        for it in info:
            print(it)

        print("\n=== Search for UNITING / 'Find Out More' B2B card ===")
        b2b = page.evaluate(r"""
            (() => {
                const out = [];
                // Look for any element containing UNITING text
                document.querySelectorAll('*').forEach(el => {
                    const txt = (el.innerText || '').trim();
                    if (/uniting your business/i.test(txt) && txt.length < 400) {
                        const r = el.getBoundingClientRect();
                        out.push({tag: el.tagName,
                                  cls: (el.className || '').toString().substring(0, 80),
                                  top: Math.round(r.top + scrollY),
                                  width: Math.round(r.width), height: Math.round(r.height),
                                  txt: txt.substring(0, 80)});
                    }
                });
                return out.slice(0, 15);
            })()
        """)
        for it in b2b:
            print(it)

        # Also try to find the row immediately below hero
        print("\n=== Row immediately below hero (Y just after hero) ===")
        after_hero = page.evaluate(r"""
            (() => {
                // Find the hero section first
                let heroBottom = 0;
                const heroes = document.querySelectorAll('section, div');
                for (const h of heroes) {
                    const r = h.getBoundingClientRect();
                    const top = r.top + scrollY;
                    if (top < 100 && r.height > 400 && r.width > 1000) {
                        const bottom = top + r.height;
                        if (bottom > heroBottom) heroBottom = bottom;
                    }
                }
                return {heroBottom: Math.round(heroBottom)};
            })()
        """)
        print(after_hero)
        browser.close()


if __name__ == "__main__":
    main()
