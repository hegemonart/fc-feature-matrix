#!/usr/bin/env python3
"""Inspect Wrexham footer to understand social link layout."""

import time
from playwright.sync_api import sync_playwright


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto("https://www.wrexhamafc.co.uk/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(6)
        # Dismiss cookie banner
        page.evaluate("""
            document.querySelectorAll('#onetrust-banner-sdk, .onetrust-pc-dark-filter, #onetrust-consent-sdk, [class*="onetrust"]').forEach(e => e.remove());
            const accept = document.getElementById('onetrust-accept-btn-handler');
            if (accept) accept.click();
        """)
        time.sleep(2)
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        # Find every social-link href + its position
        social_info = page.evaluate("""
            (() => {
                const out = [];
                const sel = 'a[href*="facebook"], a[href*="instagram"], a[href*="twitter"], a[href*="x.com"], a[href*="youtube"], a[href*="tiktok"], a[href*="linkedin"]';
                document.querySelectorAll(sel).forEach(el => {
                    const r = el.getBoundingClientRect();
                    out.push({
                        href: el.href.substring(0, 80),
                        top: Math.round(r.top + scrollY),
                        left: Math.round(r.left + scrollX),
                        width: Math.round(r.width),
                        height: Math.round(r.height),
                        text: (el.textContent || '').trim().substring(0, 30),
                        aria: el.getAttribute('aria-label') || ''
                    });
                });
                return out;
            })()
        """)
        print(f"Found {len(social_info)} social-href links:\n")
        for s in social_info:
            print(s)
        # Also check for STORE / LATEST PRODUCTS sections
        print("\n--- 'LATEST PRODUCTS' / store sections ---")
        store_info = page.evaluate("""
            (() => {
                const out = [];
                document.querySelectorAll('h1, h2, h3, h4').forEach(h => {
                    const t = (h.textContent || '').trim();
                    if (/products|store|shop|latest products|latest|shop now|featured/i.test(t)) {
                        const r = h.getBoundingClientRect();
                        out.push({tag: h.tagName, text: t.substring(0, 60),
                                  top: Math.round(r.top + scrollY)});
                    }
                });
                return out;
            })()
        """)
        for s in store_info:
            print(s)
        # Check paid_membership / "BE A MEMBER"
        print("\n--- 'BE A MEMBER' / membership cards ---")
        member_info = page.evaluate("""
            (() => {
                const out = [];
                document.querySelectorAll('*').forEach(el => {
                    const txt = (el.textContent || '').trim();
                    if (txt.length < 200 && /be a member|become a member|join now|membership/i.test(txt)) {
                        const r = el.getBoundingClientRect();
                        if (r.height > 50 && r.width > 100) {
                            out.push({tag: el.tagName, cls: (el.className || '').toString().substring(0, 80),
                                      top: Math.round(r.top + scrollY),
                                      width: Math.round(r.width), height: Math.round(r.height),
                                      text: txt.substring(0, 80)});
                        }
                    }
                });
                return out.slice(0, 10);
            })()
        """)
        for s in member_info:
            print(s)
        # Footer sponsor wall
        print("\n--- partner / sponsor sections ---")
        partner_info = page.evaluate("""
            (() => {
                const out = [];
                document.querySelectorAll('h1, h2, h3, h4, [class*="title" i]').forEach(h => {
                    const t = (h.textContent || '').trim();
                    if (/partner|sponsor/i.test(t) && t.length < 80) {
                        const r = h.getBoundingClientRect();
                        out.push({tag: h.tagName, text: t,
                                  top: Math.round(r.top + scrollY)});
                    }
                });
                return out.slice(0, 15);
            })()
        """)
        for s in partner_info:
            print(s)
        browser.close()


if __name__ == "__main__":
    main()
