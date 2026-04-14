#!/usr/bin/env python3
"""Recapture arsenal_press_conference_block at the Trending Video section."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).resolve().parent.parent / "crosscheck" / "img"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    ctx = browser.new_context(
        viewport={"width": 1400, "height": 900},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    )
    page = ctx.new_page()
    page.goto("https://www.arsenal.com", wait_until="domcontentloaded", timeout=30000)
    time.sleep(5)

    # Dismiss cookies/popups
    page.evaluate("""(() => {
        document.querySelectorAll('button, a, [role="button"]').forEach(b => {
            const txt = (b.textContent || '').toLowerCase().trim();
            if (txt.includes('accept') || txt.includes('agree') || txt.includes('allow')) {
                try { b.click(); } catch(e) {}
            }
        });
        document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="promo"], [role="dialog"]').forEach(e => { try { e.remove(); } catch(ex) {} });
        document.querySelectorAll('div, section').forEach(e => {
            try {
                const s = window.getComputedStyle(e);
                const r = e.getBoundingClientRect();
                if ((s.position === 'fixed' || s.position === 'absolute') && r.width > 300 && r.height > 200 && parseInt(s.zIndex) > 50) e.remove();
            } catch(ex) {}
        });
        if (document.body) document.body.style.overflow = 'auto';
    })()""")
    time.sleep(2)

    # Scroll to lazy-load
    for i in range(10):
        page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/10})")
        time.sleep(0.5)
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1)

    # Dismiss again
    page.evaluate("""(() => {
        document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="overlay"], [class*="promo"], [role="dialog"]').forEach(e => { try { e.remove(); } catch(ex) {} });
        document.querySelectorAll('div, section').forEach(e => {
            try {
                const s = window.getComputedStyle(e);
                const r = e.getBoundingClientRect();
                if ((s.position === 'fixed' || s.position === 'absolute') && r.width > 300 && r.height > 200 && parseInt(s.zIndex) > 50) e.remove();
            } catch(ex) {}
        });
    })()""")
    time.sleep(1)

    # Find trending video section with press conferences
    info = page.evaluate("""(() => {
        const els = document.querySelectorAll('h2, section');
        for (const el of els) {
            const text = (el.innerText || '').toLowerCase();
            const rect = el.getBoundingClientRect();
            const absY = rect.top + window.scrollY;
            if (text.includes('trending video') && absY > 200) {
                return {y: Math.round(absY), h: Math.round(rect.height), text: text.substring(0, 120)};
            }
        }
        return null;
    })()""")
    print(f"Trending Video: {info}")

    if info:
        page.screenshot(
            path=str(IMG_DIR / "arsenal_press_conference_block.png"),
            full_page=True, timeout=60000,
            clip={"x": 0, "y": max(0, info['y'] - 20), "width": 1400, "height": min(info['h'] + 40, 500)}
        )
        size = (IMG_DIR / "arsenal_press_conference_block.png").stat().st_size
        print(f"Saved: {size:,} bytes")
    else:
        print("Trending Video section not found!")

    browser.close()
