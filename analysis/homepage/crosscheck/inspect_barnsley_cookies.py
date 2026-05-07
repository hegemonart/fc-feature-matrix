#!/usr/bin/env python3
"""Inspect Barnsley homepage to identify the actual cookie banner selectors."""

import time
from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.barnsleyfc.co.uk/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6)

        # Dump every visible fixed/sticky element above 100px tall in the top
        # 600 pixels — likely the cookie banner / consent overlay.
        info = page.evaluate("""
            (() => {
                const out = [];
                document.querySelectorAll('*').forEach(el => {
                    const cs = getComputedStyle(el);
                    const r = el.getBoundingClientRect();
                    if ((cs.position === 'fixed' || cs.position === 'sticky' || cs.position === 'absolute')
                        && r.top < 600 && r.height > 60 && r.width > 200
                        && cs.display !== 'none' && cs.visibility !== 'hidden') {
                        out.push({
                            tag: el.tagName,
                            id: el.id,
                            cls: el.className.toString ? el.className.toString().substring(0, 120) : '',
                            top: Math.round(r.top),
                            height: Math.round(r.height),
                            width: Math.round(r.width),
                            zIndex: cs.zIndex,
                            text: (el.innerText || '').substring(0, 200).replace(/\\n/g, ' | ')
                        });
                    }
                });
                return out.slice(0, 30);
            })()
        """)
        for it in info:
            print(it)

        # Also check window-level cookie APIs that might exist.
        apis = page.evaluate("""
            ({
                hasOneTrust: typeof window.OneTrust !== 'undefined',
                hasOptanon: typeof window.Optanon !== 'undefined',
                hasUC_UI: typeof window.UC_UI !== 'undefined',
                hasCmp: typeof window.__cmp !== 'undefined',
                hasDidomi: typeof window.Didomi !== 'undefined',
                hasCookiebot: typeof window.Cookiebot !== 'undefined',
                cookieyesPresent: !!document.querySelector('[class*="cky"]'),
            })
        """)
        print("\nAPIs:", apis)

        # Dump button text for all buttons inside top 600px
        btns = page.evaluate("""
            (() => {
                const out = [];
                document.querySelectorAll('button, a[role="button"], [role="button"]').forEach(el => {
                    const r = el.getBoundingClientRect();
                    if (r.top < 800 && r.width > 30 && (el.innerText || '').trim()) {
                        out.push({
                            tag: el.tagName,
                            id: el.id || '',
                            cls: (el.className || '').toString().substring(0, 100),
                            top: Math.round(r.top),
                            text: (el.innerText || '').trim().substring(0, 80)
                        });
                    }
                });
                return out.slice(0, 40);
            })()
        """)
        print("\nButtons in viewport:")
        for b in btns:
            print(b)

        browser.close()


if __name__ == "__main__":
    main()
