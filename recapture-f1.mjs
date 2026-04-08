import { chromium } from 'playwright';
import { join } from 'path';

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-blink-features=AutomationControlled']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    locale: 'en-GB',
  });

  const page = await context.newPage();

  console.log('Loading F1...');
  await page.goto('https://www.formula1.com', { waitUntil: 'domcontentloaded', timeout: 40000 });
  await page.waitForTimeout(5000);

  // Log what cookie elements exist
  const cookieElements = await page.evaluate(() => {
    const all = document.querySelectorAll('*');
    const found = [];
    for (const el of all) {
      const id = el.id || '';
      const cls = el.className || '';
      const tag = el.tagName;
      const idLower = id.toLowerCase();
      const clsLower = (typeof cls === 'string' ? cls : '').toLowerCase();
      if (idLower.includes('cookie') || idLower.includes('consent') || idLower.includes('privacy') || idLower.includes('truste') || idLower.includes('evidon') ||
          clsLower.includes('cookie') || clsLower.includes('consent') || clsLower.includes('privacy') || clsLower.includes('truste') || clsLower.includes('evidon')) {
        const style = window.getComputedStyle(el);
        found.push({
          tag, id: id.substring(0, 60), cls: (typeof cls === 'string' ? cls : '').substring(0, 80),
          visible: el.offsetParent !== null || style.display !== 'none',
          position: style.position, zIndex: style.zIndex
        });
      }
    }
    return found;
  });

  console.log('Cookie-related elements found:');
  cookieElements.filter(e => e.visible).forEach(e => {
    console.log(`  ${e.tag} #${e.id} .${e.cls} (pos:${e.position} z:${e.zIndex})`);
  });

  // Try clicking specific F1 reject buttons
  const selectors = [
    'button.trustarc-agree-btn',
    '#truste-consent-button',
    '#truste-consent-required',
    'button:has-text("Required Only")',
    'button:has-text("Reject")',
    'button:has-text("Decline")',
    'button:has-text("Only Required")',
    'button:has-text("Necessary")',
    '.trustarc-banner__button--reject',
  ];

  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      if (el && await el.isVisible()) {
        const text = await el.textContent();
        console.log(`  Found clickable: ${sel} -> "${text}"`);
        // Don't click accept, only reject
        if (text && !text.toLowerCase().includes('accept') && !text.toLowerCase().includes('agree')) {
          await el.click();
          console.log(`  ✓ Clicked: ${sel}`);
          await page.waitForTimeout(1500);
        }
      }
    } catch (e) {}
  }

  // Nuclear option: remove all overlays via JS
  await page.evaluate(() => {
    // Find and remove any element with high z-index that covers the page
    const removeOverlays = () => {
      document.querySelectorAll('*').forEach(el => {
        const style = window.getComputedStyle(el);
        const zIndex = parseInt(style.zIndex);
        if ((style.position === 'fixed' || style.position === 'absolute') && zIndex > 100) {
          const rect = el.getBoundingClientRect();
          // If it covers a significant portion of the viewport
          if (rect.width > 200 && rect.height > 100) {
            const id = el.id || '';
            const cls = el.className || '';
            const txt = (el.textContent || '').substring(0, 50);
            if (id.toLowerCase().includes('cookie') || id.toLowerCase().includes('consent') || id.toLowerCase().includes('truste') ||
                (typeof cls === 'string' && (cls.toLowerCase().includes('cookie') || cls.toLowerCase().includes('consent') || cls.toLowerCase().includes('truste') || cls.toLowerCase().includes('modal') || cls.toLowerCase().includes('overlay'))) ||
                txt.toLowerCase().includes('cookie') || txt.toLowerCase().includes('consent') || txt.toLowerCase().includes('privacy')) {
              el.remove();
              console.log('Removed:', id || cls || txt.substring(0, 30));
            }
          }
        }
      });
      // Also remove backdrop/overlay divs
      document.querySelectorAll('.truste_overlay, .truste_box_overlay, [class*="truste"], [id*="truste"], .consent-overlay, .cookie-overlay').forEach(el => el.remove());
      // Restore scrolling
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
      document.body.classList.remove('no-scroll', 'modal-open', 'overflow-hidden');
    };
    removeOverlays();
  });

  await page.waitForTimeout(1000);

  // Scroll for lazy loading
  await page.evaluate(async () => {
    const delay = ms => new Promise(r => setTimeout(r, ms));
    for (let y = 0; y < document.body.scrollHeight; y += 500) {
      window.scrollTo(0, y);
      await delay(200);
    }
    window.scrollTo(0, 0);
    await delay(500);
  });

  await page.waitForTimeout(2000);

  // Final removal pass
  await page.evaluate(() => {
    document.querySelectorAll('[class*="truste"], [id*="truste"], [class*="cookie"], [id*="cookie"], [class*="consent"], [id*="consent"]').forEach(el => {
      const style = window.getComputedStyle(el);
      if (style.position === 'fixed' || style.position === 'sticky' || parseInt(style.zIndex) > 100) {
        el.remove();
      }
    });
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
  });

  await page.waitForTimeout(500);

  await page.screenshot({ path: './screenshots/22-f1.png', fullPage: true, timeout: 30000 });
  console.log('✓ F1 screenshot saved');

  await browser.close();
}

main().catch(console.error);
