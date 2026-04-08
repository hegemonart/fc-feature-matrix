import { chromium } from 'playwright';
import { mkdirSync } from 'fs';
import { join } from 'path';

const SCREENSHOT_DIR = './screenshots';

const sites = [
  { name: 'bayern-munich', url: 'https://fcbayern.com', file: '03-bayern-munich.png' },
  { name: 'arsenal', url: 'https://www.arsenal.com', file: '07-arsenal.png' },
  { name: 'nba', url: 'https://www.nba.com', file: '24-nba.png' },
  { name: 'mlb', url: 'https://www.mlb.com', file: '26-mlb.png' },
];

async function captureSite(browser, site) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    locale: 'en-US',
    extraHTTPHeaders: {
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
      'Accept-Language': 'en-US,en;q=0.9',
      'Accept-Encoding': 'gzip, deflate, br',
      'Connection': 'keep-alive',
      'Upgrade-Insecure-Requests': '1',
      'Sec-Fetch-Dest': 'document',
      'Sec-Fetch-Mode': 'navigate',
      'Sec-Fetch-Site': 'none',
      'Sec-Fetch-User': '?1',
    }
  });

  // Add stealth scripts
  await context.addInitScript(() => {
    Object.defineProperty(navigator, 'webdriver', { get: () => false });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
    window.chrome = { runtime: {} };
  });

  const page = await context.newPage();
  const filename = join(SCREENSHOT_DIR, site.file);

  try {
    console.log(`Recapturing ${site.name} (${site.url})`);

    await page.goto(site.url, {
      waitUntil: 'networkidle',
      timeout: 45000
    });

    await page.waitForTimeout(5000);

    // Try reject cookies
    const rejectSelectors = [
      '#onetrust-reject-all-handler',
      '#CybotCookiebotDialogBodyButtonDecline',
      'button[id*="reject"]',
      'button:has-text("Reject All")',
      'button:has-text("Reject all")',
      'button:has-text("Decline")',
      'button:has-text("Alle ablehnen")',
      'a:has-text("Reject All")',
    ];

    for (const sel of rejectSelectors) {
      try {
        const el = await page.$(sel);
        if (el && await el.isVisible()) {
          await el.click();
          console.log(`  ✓ Rejected cookies via: ${sel}`);
          await page.waitForTimeout(1500);
          break;
        }
      } catch (e) {}
    }

    await page.waitForTimeout(2000);

    // Lazy load scroll
    await page.evaluate(async () => {
      const delay = ms => new Promise(r => setTimeout(r, ms));
      for (let y = 0; y < Math.min(document.body.scrollHeight, 15000); y += 500) {
        window.scrollTo(0, y);
        await delay(300);
      }
      window.scrollTo(0, 0);
      await delay(500);
    });

    await page.waitForTimeout(2000);

    await page.screenshot({ path: filename, fullPage: true, timeout: 30000 });
    console.log(`  ✓ Saved: ${filename}`);
  } catch (err) {
    console.error(`  ✗ Error: ${err.message}`);
    try {
      await page.screenshot({ path: filename, fullPage: false });
      console.log(`  ⚠ Viewport fallback saved`);
    } catch (e2) {
      console.error(`  ✗ Total failure`);
    }
  } finally {
    await context.close();
  }
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-blink-features=AutomationControlled', '--no-sandbox']
  });

  for (const site of sites) {
    await captureSite(browser, site);
  }

  await browser.close();
}

main().catch(console.error);
