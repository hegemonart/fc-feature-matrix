import { chromium } from 'playwright';
import { join } from 'path';

const SCREENSHOT_DIR = './screenshots';

const sites = [
  { name: 'man-city', url: 'https://www.mancity.com', file: '06-man-city.png' },
  { name: 'man-united', url: 'https://www.manutd.com', file: '08-man-united.png' },
  { name: 'ac-milan', url: 'https://www.acmilan.com', file: '15-ac-milan.png' },
  { name: 'f1', url: 'https://www.formula1.com', file: '22-f1.png' },
];

async function dismissAllOverlays(page) {
  // Wait for overlays to appear
  await page.waitForTimeout(3000);

  // Attempt multiple rounds of dismissal
  for (let round = 0; round < 3; round++) {
    // OneTrust - full flow: open settings then reject
    try {
      const onetrust = await page.$('#onetrust-reject-all-handler');
      if (onetrust && await onetrust.isVisible()) {
        await onetrust.click();
        console.log(`  ✓ [Round ${round}] OneTrust reject-all`);
        await page.waitForTimeout(1000);
        continue;
      }
    } catch (e) {}

    // OneTrust settings button -> then reject in preferences
    try {
      const settings = await page.$('#onetrust-pc-btn-handler');
      if (settings && await settings.isVisible()) {
        await settings.click();
        await page.waitForTimeout(1500);
        // Now look for reject all in the preferences center
        const rejectInPrefs = await page.$('.ot-pc-refuse-all-handler');
        if (rejectInPrefs && await rejectInPrefs.isVisible()) {
          await rejectInPrefs.click();
          console.log(`  ✓ [Round ${round}] OneTrust prefs -> reject all`);
          await page.waitForTimeout(1000);
          continue;
        }
      }
    } catch (e) {}

    // Generic reject patterns
    const rejectSelectors = [
      '#onetrust-reject-all-handler',
      '.ot-pc-refuse-all-handler',
      '#CybotCookiebotDialogBodyButtonDecline',
      '#didomi-notice-disagree-button',
      'button[id*="reject"]',
      'button[id*="decline"]',
      'button[class*="reject"]',
      'button[class*="decline"]',
      '[data-testid*="reject"]',
      'button:has-text("Reject All")',
      'button:has-text("Reject all")',
      'button:has-text("Decline All")',
      'button:has-text("Decline all")',
      'button:has-text("Refuse All")',
      'button:has-text("Rifiuta tutto")',
      'button:has-text("Rifiuta tutti")',
      'button:has-text("Solo necessari")',
      'button:has-text("Only necessary")',
      'button:has-text("Necessary only")',
      'button:has-text("Essential only")',
      'a:has-text("Reject All")',
      'a:has-text("Reject all")',
      'a:has-text("Decline")',
    ];

    for (const sel of rejectSelectors) {
      try {
        const el = await page.$(sel);
        if (el && await el.isVisible()) {
          await el.click();
          console.log(`  ✓ [Round ${round}] Rejected via: ${sel}`);
          await page.waitForTimeout(1000);
          break;
        }
      } catch (e) {}
    }

    // Try closing any remaining modals/overlays via close buttons
    const closeSelectors = [
      '[aria-label="Close"]',
      '[aria-label="close"]',
      '.modal-close',
      '.close-btn',
      '.overlay-close',
      'button.close',
      '[data-dismiss="modal"]',
      '.cookie-banner button',
      '.cookie-notice button',
      '.consent-banner button',
      // Location selectors for Man City
      'button:has-text("Continue")',
      'button:has-text("OK")',
      'button:has-text("Got it")',
      // F1 specific
      '.evidon-banner-acceptbutton',
      '#truste-consent-required',
      'button:has-text("I Understand")',
    ];

    for (const sel of closeSelectors) {
      try {
        const el = await page.$(sel);
        if (el && await el.isVisible()) {
          await el.click();
          console.log(`  ✓ [Round ${round}] Closed overlay via: ${sel}`);
          await page.waitForTimeout(800);
        }
      } catch (e) {}
    }

    // JavaScript-based removal of common overlays
    await page.evaluate(() => {
      // Remove OneTrust
      document.querySelectorAll('#onetrust-consent-sdk, #onetrust-banner-sdk, .onetrust-pc-dark-filter').forEach(el => el.remove());
      // Remove Cookiebot
      document.querySelectorAll('#CybotCookiebotDialog, #CybotCookiebotDialogBodyUnderlay').forEach(el => el.remove());
      // Remove Didomi
      document.querySelectorAll('#didomi-host, .didomi-popup-container').forEach(el => el.remove());
      // Remove generic overlays
      document.querySelectorAll('.cookie-banner, .cookie-notice, .consent-banner, .cookie-overlay, .gdpr-banner').forEach(el => el.remove());
      // Remove any fixed/sticky overlays that block content
      document.querySelectorAll('[class*="cookie"], [class*="consent"], [id*="cookie"], [id*="consent"]').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.position === 'fixed' || style.position === 'sticky' || style.zIndex > 999) {
          el.remove();
        }
      });
      // Restore body scroll
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    });

    await page.waitForTimeout(500);
  }
}

async function captureSite(browser, site) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    locale: 'en-GB',
    extraHTTPHeaders: {
      'Accept-Language': 'en-GB,en;q=0.9',
    }
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
  });

  const page = await context.newPage();
  const filename = join(SCREENSHOT_DIR, site.file);

  try {
    console.log(`Recapturing ${site.name} (${site.url})`);

    await page.goto(site.url, {
      waitUntil: 'domcontentloaded',
      timeout: 40000
    });

    await dismissAllOverlays(page);

    // Scroll to trigger lazy load
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

    // Final cleanup of any remaining overlays
    await page.evaluate(() => {
      document.querySelectorAll('#onetrust-consent-sdk, #onetrust-banner-sdk, .onetrust-pc-dark-filter, #CybotCookiebotDialog, #CybotCookiebotDialogBodyUnderlay, #didomi-host, .didomi-popup-container').forEach(el => el.remove());
      document.querySelectorAll('[class*="cookie"], [class*="consent"], [id*="cookie"], [id*="consent"]').forEach(el => {
        const style = window.getComputedStyle(el);
        if (style.position === 'fixed' || style.position === 'sticky' || parseInt(style.zIndex) > 999) {
          el.remove();
        }
      });
      document.body.style.overflow = '';
      document.documentElement.style.overflow = '';
    });

    await page.waitForTimeout(1000);

    await page.screenshot({ path: filename, fullPage: true, timeout: 30000 });
    console.log(`  ✓ Saved: ${filename}`);
  } catch (err) {
    console.error(`  ✗ Error: ${err.message}`);
    try {
      await page.screenshot({ path: filename, fullPage: false });
      console.log(`  ⚠ Viewport fallback`);
    } catch (e2) {}
  } finally {
    await context.close();
  }
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-blink-features=AutomationControlled']
  });

  for (const site of sites) {
    await captureSite(browser, site);
  }

  await browser.close();
  console.log('Done!');
}

main().catch(console.error);
