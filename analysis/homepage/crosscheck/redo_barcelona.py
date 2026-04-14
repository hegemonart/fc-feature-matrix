#!/usr/bin/env python3
"""Redo BAD + WEAK Barcelona screenshots. Barcelona uses Didomi consent."""

import time
from pathlib import Path
from playwright.sync_api import sync_playwright

IMG_DIR = Path(__file__).resolve().parent.parent / "crosscheck" / "img"


def safe_eval(page, expr):
    try:
        return page.evaluate(expr)
    except Exception as e:
        print(f"    eval error: {str(e)[:80]}")
        return None


def clip(page, path, x, y, w, h):
    try:
        page.screenshot(path=str(path), full_page=True, timeout=60000,
                        clip={"x": max(0, x), "y": max(0, y),
                              "width": max(w, 100), "height": min(max(h, 100), 2000)})
        size = Path(path).stat().st_size
        print(f"    -> {Path(path).name} ({size:,} bytes)")
    except Exception as e:
        print(f"    ❌ FAILED {Path(path).name}: {str(e)[:80]}")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        ctx = browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        )
        page = ctx.new_page()

        print("="*60)
        print("FC BARCELONA — fcbarcelona.com/en")
        print("="*60)

        page.goto("https://www.fcbarcelona.com/en", wait_until="domcontentloaded", timeout=30000)
        time.sleep(5)

        sh = page.evaluate("document.body.scrollHeight")
        print(f"  Initial page height: {sh}px")

        # Dismiss Didomi consent — click "Agree"
        print("  Clicking 'Agree' on Didomi consent...")
        try:
            page.click("button.didomi-dismiss-button", timeout=5000)
            time.sleep(2)
        except Exception:
            print("    Didomi button not found, trying alternatives...")
            safe_eval(page, """(() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    const txt = (b.textContent || '').toLowerCase().trim();
                    if (txt === 'agree' || txt.includes('accept')) {
                        b.click();
                        break;
                    }
                }
            })()""")
            time.sleep(2)

        # Scroll to trigger lazy-loading
        for i in range(10):
            safe_eval(page, f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/10})")
            time.sleep(0.8)
        safe_eval(page, "window.scrollTo(0, 0)")
        time.sleep(2)

        sh = page.evaluate("document.body.scrollHeight")
        print(f"  Final page height: {sh}px")

        # Dump page structure
        sections = safe_eval(page, """(() => {
            const results = [];
            const els = document.querySelectorAll('h1, h2, h3, h4, section');
            for (const el of els) {
                try {
                    if (el.closest('nav, header')) continue;
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (rect.height < 5 || absY < 0) continue;
                    const text = (el.innerText || '').substring(0, 120).replace(/\\n/g, ' | ').trim();
                    if (!text) continue;
                    results.push({tag: el.tagName, y: Math.round(absY), h: Math.round(rect.height), text: text});
                } catch(e) {}
            }
            results.sort((a, b) => a.y - b.y);
            return results.slice(0, 40);
        })()""") or []

        print(f"\n  Page sections ({len(sections)}):")
        for s in sections[:30]:
            print(f"    y={s['y']:5d} h={s['h']:5d} [{s['tag']:4s}] {s['text'][:80]}")

        # ═══════════════════════════════════════
        # BAD screenshots
        # ═══════════════════════════════════════

        # 1. hero_carousel — carousel controls at y=862 ("Previous slides" / "Next slides")
        print("\n  [BAD] hero_carousel")
        hero_info = safe_eval(page, """(() => {
            // Find hero carousel container
            const hero = document.querySelector('[class*="hero"], [class*="match-hero"], [class*="carousel"]');
            if (hero) {
                const rect = hero.getBoundingClientRect();
                return {y: Math.round(rect.top + window.scrollY), h: Math.round(rect.height)};
            }
            return null;
        })()""")
        # Get carousel nav buttons
        carousel_btns = safe_eval(page, """(() => {
            const btns = document.querySelectorAll('[class*="carousel__nav"], [class*="promo-carousel"], [class*="swiper-button"]');
            const results = [];
            for (const b of btns) {
                try {
                    const rect = b.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (rect.height > 0) results.push({y: Math.round(absY), h: Math.round(rect.height), x: Math.round(rect.x), cls: (b.className || '').toString().substring(0, 60)});
                } catch(e) {}
            }
            return results;
        })()""") or []
        print(f"    Hero: {hero_info}, Carousel buttons: {len(carousel_btns)}")
        if carousel_btns:
            for b in carousel_btns:
                print(f"      y={b['y']} cls={b['cls']}")

        # Capture the full hero area including carousel controls
        if hero_info:
            # Include carousel nav area which might be below hero
            max_y = hero_info['y'] + hero_info['h']
            if carousel_btns:
                max_y = max(max_y, max(b['y'] + b['h'] for b in carousel_btns) + 20)
            clip(page, IMG_DIR / "fc_barcelona_hero_carousel.png", 0, hero_info['y'], 1400, max_y - hero_info['y'])
        else:
            clip(page, IMG_DIR / "fc_barcelona_hero_carousel.png", 0, 0, 1400, 950)

        # 2. brand_sponsor_highlighted_in_hero — partner logos at y=773
        print("\n  [BAD] brand_sponsor_highlighted_in_hero")
        partners = safe_eval(page, """(() => {
            const links = document.querySelectorAll('[class*="marketing-partners"], [class*="partner"], [class*="sponsor"]');
            const results = [];
            for (const el of links) {
                try {
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (rect.height > 10 && absY < 1000 && absY > 100) {
                        results.push({y: Math.round(absY), h: Math.round(rect.height), w: Math.round(rect.width), cls: (el.className || '').toString().substring(0, 60)});
                    }
                } catch(e) {}
            }
            return results;
        })()""") or []
        if partners:
            min_y = min(p['y'] for p in partners)
            print(f"    Found {len(partners)} partner elements starting at y={min_y}")
            clip(page, IMG_DIR / "fc_barcelona_brand_sponsor_highlighted_in_hero.png", 0, max(0, min_y - 50), 1400, 200)
        else:
            # Fallback — capture area around y=773 where we saw partner logos
            clip(page, IMG_DIR / "fc_barcelona_brand_sponsor_highlighted_in_hero.png", 0, 700, 1400, 200)

        # 3. news_rich_structure + dedicated_news_section
        print("\n  [BAD] news_rich_structure + dedicated_news_section")
        news_y = None
        for s in sections:
            txt = s['text'].lower()
            if any(t in txt for t in ['stories', 'news', 'latest', 'articles']):
                if s['y'] > 200:
                    news_y = s['y']
                    print(f"    Found news section: '{s['text'][:60]}' at y={s['y']}")
                    break
        if news_y:
            clip(page, IMG_DIR / "fc_barcelona_news_rich_structure.png", 0, max(0, news_y - 30), 1400, 700)
            clip(page, IMG_DIR / "fc_barcelona_dedicated_news_section.png", 0, max(0, news_y - 60), 1400, 600)
        else:
            # Search DOM
            news_info = safe_eval(page, """(() => {
                const main = document.querySelector('main') || document.body;
                const headings = main.querySelectorAll('h2, h3');
                for (const h of headings) {
                    const text = (h.innerText || '').toLowerCase();
                    if (text.includes('stories') || text.includes('news') || text.includes('latest')) {
                        const rect = h.getBoundingClientRect();
                        const absY = rect.top + window.scrollY;
                        if (absY > 200) return {y: Math.round(absY), text: text.substring(0, 60)};
                    }
                }
                return null;
            })()""")
            if news_info:
                clip(page, IMG_DIR / "fc_barcelona_news_rich_structure.png", 0, max(0, news_info['y'] - 30), 1400, 700)
                clip(page, IMG_DIR / "fc_barcelona_dedicated_news_section.png", 0, max(0, news_info['y'] - 60), 1400, 600)

        # 4. video_thumbnails_inline
        print("\n  [BAD] video_thumbnails_inline")
        vid_info = safe_eval(page, """(() => {
            const cards = document.querySelectorAll('[class*="video"], [class*="play"]');
            const results = [];
            for (const el of cards) {
                try {
                    if (el.closest('nav, header, footer')) continue;
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (rect.height > 10 && absY > 200 && rect.width > 50) {
                        results.push({y: Math.round(absY), h: Math.round(rect.height)});
                    }
                } catch(e) {}
            }
            if (!results.length) return null;
            const minY = Math.min(...results.map(r => r.y));
            return {y: minY, count: results.length};
        })()""")
        if vid_info:
            clip(page, IMG_DIR / "fc_barcelona_video_thumbnails_inline.png", 0, max(0, vid_info['y'] - 50), 1400, 500)
        else:
            for s in sections:
                if 'video' in s['text'].lower() or 'highlights' in s['text'].lower():
                    clip(page, IMG_DIR / "fc_barcelona_video_thumbnails_inline.png", 0, max(0, s['y'] - 30), 1400, 500)
                    break

        # 5. draws_contests — "Only For Culers" section with benefits
        print("\n  [BAD] draws_contests")
        culers_y = None
        for s in sections:
            txt = s['text'].lower()
            if 'culers' in txt or 'draws' in txt or 'benefits' in txt or 'contests' in txt:
                culers_y = s['y']
                print(f"    Found: '{s['text'][:60]}' at y={s['y']}")
                break
        if culers_y:
            clip(page, IMG_DIR / "fc_barcelona_draws_contests.png", 0, max(0, culers_y - 30), 1400, 500)
        else:
            # Search more broadly
            culers_info = safe_eval(page, """(() => {
                const els = document.querySelectorAll('*');
                for (const el of els) {
                    try {
                        if (el.closest('nav, header, footer')) continue;
                        const text = (el.innerText || '').toLowerCase();
                        const rect = el.getBoundingClientRect();
                        const absY = rect.top + window.scrollY;
                        if (absY > 200 && rect.height > 50 && rect.height < 1000) {
                            if (text.includes('draws') || text.includes('contests') || text.includes('culers')) {
                                return {y: Math.round(absY), h: Math.round(rect.height), text: text.substring(0, 80)};
                            }
                        }
                    } catch(e) {}
                }
                return null;
            })()""")
            if culers_info:
                clip(page, IMG_DIR / "fc_barcelona_draws_contests.png", 0, max(0, culers_info['y'] - 30), 1400, 500)

        # 6. fan_club_signup
        print("\n  [BAD] fan_club_signup")
        fan_info = safe_eval(page, """(() => {
            const els = document.querySelectorAll('a, button, [class*="cta"], [class*="register"], [class*="signup"]');
            for (const el of els) {
                try {
                    if (el.closest('nav, header, footer')) continue;
                    const text = (el.innerText || '').toLowerCase();
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (absY > 200 && rect.height > 10) {
                        if (text.includes('join') || text.includes('sign up') || text.includes('become a member') || text.includes('register') || text.includes('view plans')) {
                            return {y: Math.round(absY), h: Math.round(rect.height), text: text.substring(0, 60)};
                        }
                    }
                } catch(e) {}
            }
            return null;
        })()""")
        if fan_info:
            print(f"    Found: '{fan_info['text'][:40]}' at y={fan_info['y']}")
            clip(page, IMG_DIR / "fc_barcelona_fan_club_signup.png", 0, max(0, fan_info['y'] - 100), 1400, 500)
        elif culers_y:
            clip(page, IMG_DIR / "fc_barcelona_fan_club_signup.png", 0, max(0, culers_y - 30), 1400, 500)

        # 7. app_store_badges
        print("\n  [BAD] app_store_badges")
        badges = safe_eval(page, """(() => {
            const badges = [];
            document.querySelectorAll('a').forEach(a => {
                try {
                    const href = (a.getAttribute('href') || '').toLowerCase();
                    if (href.includes('apps.apple') || href.includes('play.google') || href.includes('itunes.apple')) {
                        const rect = a.getBoundingClientRect();
                        const absY = rect.top + window.scrollY;
                        if (rect.height > 0 && rect.width > 0) badges.push({y: Math.round(absY), h: Math.round(rect.height)});
                    }
                } catch(e) {}
            });
            document.querySelectorAll('img').forEach(img => {
                try {
                    const src = (img.getAttribute('src') || '').toLowerCase();
                    const alt = (img.getAttribute('alt') || '').toLowerCase();
                    if (src.includes('app-store') || src.includes('google-play') || alt.includes('app store') || alt.includes('google play')) {
                        const rect = img.getBoundingClientRect();
                        if (rect.height > 0) badges.push({y: Math.round(rect.top + window.scrollY), h: Math.round(rect.height)});
                    }
                } catch(e) {}
            });
            const visible = badges.filter(b => b.h > 5);
            if (!visible.length) return null;
            return {y: Math.min(...visible.map(b => b.y)), h: Math.max(...visible.map(b => b.y + b.h)) - Math.min(...visible.map(b => b.y)), count: visible.length};
        })()""")
        if badges:
            print(f"    Found {badges['count']} badges at y={badges['y']}")
            clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, max(0, badges['y'] - 50), 1400, max(badges['h'] + 100, 300))
        else:
            # Look for "Barça Mobile" section
            mobile = safe_eval(page, """(() => {
                const els = document.querySelectorAll('*');
                for (const el of els) {
                    try {
                        const text = (el.innerText || '').toLowerCase();
                        const rect = el.getBoundingClientRect();
                        const absY = rect.top + window.scrollY;
                        if (absY > 200 && rect.height > 20 && rect.height < 500) {
                            if (text.includes('barça mobile') || text.includes('download app') || text.includes('mobile app')) {
                                return {y: Math.round(absY)};
                            }
                        }
                    } catch(e) {}
                }
                return null;
            })()""")
            if mobile:
                clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, max(0, mobile['y'] - 50), 1400, 400)
            else:
                print("    ⚠️ No app badges found")
                clip(page, IMG_DIR / "fc_barcelona_app_store_badges.png", 0, sh - 500, 1400, 300)

        # 8. stadium_content_block — MUST show stadium, NOT tickets
        print("\n  [BAD] stadium_content_block")
        stadium_y = None
        for s in sections:
            txt = s['text'].lower()
            if any(t in txt for t in ['camp nou', 'stadium', 'estadi', 'tour', 'immersive', 'espai barça']):
                if 'ticket' not in txt:  # Skip tickets section!
                    stadium_y = s['y']
                    print(f"    Found: '{s['text'][:60]}' at y={s['y']}")
                    break
        if stadium_y:
            clip(page, IMG_DIR / "fc_barcelona_stadium_content_block.png", 0, max(0, stadium_y - 30), 1400, 500)
        else:
            # DOM search
            stadium_info = safe_eval(page, """(() => {
                const els = document.querySelectorAll('*');
                for (const el of els) {
                    try {
                        if (el.closest('nav, header, footer')) continue;
                        const text = (el.innerText || '').toLowerCase();
                        const rect = el.getBoundingClientRect();
                        const absY = rect.top + window.scrollY;
                        if (absY > 200 && rect.height > 50 && rect.height < 800) {
                            if ((text.includes('camp nou') || text.includes('stadium') || text.includes('tour') || text.includes('espai')) && !text.includes('ticket')) {
                                return {y: Math.round(absY), text: text.substring(0, 80)};
                            }
                        }
                    } catch(e) {}
                }
                return null;
            })()""")
            if stadium_info:
                print(f"    DOM found: '{stadium_info['text'][:60]}' at y={stadium_info['y']}")
                clip(page, IMG_DIR / "fc_barcelona_stadium_content_block.png", 0, max(0, stadium_info['y'] - 30), 1400, 500)
            else:
                print("    ⚠️ No stadium content found — feature may be FALSE")

        # ═══════════════════════════════════════
        # WEAK screenshots
        # ═══════════════════════════════════════

        # homepage_video_block — large video player
        print("\n  [WEAK] homepage_video_block")
        vid = safe_eval(page, """(() => {
            const els = document.querySelectorAll('video, [class*="video-player"], iframe[src*="youtube"]');
            for (const el of els) {
                try {
                    if (el.closest('nav, header, footer')) continue;
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (absY > 100 && rect.height > 100 && rect.width >= 462) {
                        return {y: Math.round(absY), h: Math.round(rect.height), w: Math.round(rect.width)};
                    }
                } catch(e) {}
            }
            return null;
        })()""")
        if vid:
            clip(page, IMG_DIR / "fc_barcelona_homepage_video_block.png", 0, max(0, vid['y'] - 30), 1400, min(vid['h'] + 60, 700))
        else:
            for s in sections:
                if 'video' in s['text'].lower() or 'highlights' in s['text'].lower():
                    clip(page, IMG_DIR / "fc_barcelona_homepage_video_block.png", 0, max(0, s['y'] - 30), 1400, 500)
                    break

        # social_native_content
        print("\n  [WEAK] social_native_content")
        social = safe_eval(page, """(() => {
            const els = document.querySelectorAll('[class*="stories"], [class*="social"], [class*="instagram"]');
            for (const el of els) {
                try {
                    if (el.closest('nav, header, footer')) continue;
                    const rect = el.getBoundingClientRect();
                    const absY = rect.top + window.scrollY;
                    if (absY > 200 && rect.height > 50) return {y: Math.round(absY), h: Math.round(rect.height)};
                } catch(e) {}
            }
            return null;
        })()""")
        if social:
            clip(page, IMG_DIR / "fc_barcelona_social_native_content.png", 0, max(0, social['y'] - 30), 1400, 500)
        else:
            for s in sections:
                if 'stories' in s['text'].lower() or 'barça stories' in s['text'].lower():
                    clip(page, IMG_DIR / "fc_barcelona_social_native_content.png", 0, max(0, s['y'] - 30), 1400, 500)
                    break

        # paid_membership
        print("\n  [WEAK] paid_membership")
        for s in sections:
            txt = s['text'].lower()
            if 'culers' in txt or 'membership' in txt or 'subscribe' in txt or 'subscription' in txt:
                clip(page, IMG_DIR / "fc_barcelona_paid_membership.png", 0, max(0, s['y'] - 30), 1400, 500)
                break

        browser.close()
        print("\n" + "="*60)
        print("BARCELONA REDO COMPLETE")
        print("="*60)


if __name__ == "__main__":
    main()
