import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const SCREENSHOT_DIR = './screenshots';
mkdirSync(SCREENSHOT_DIR, { recursive: true });

const sites = [
  { name: 'real-madrid', url: 'https://www.realmadrid.com' },
  { name: 'fc-barcelona', url: 'https://www.fcbarcelona.com' },
  { name: 'bayern-munich', url: 'https://fcbayern.com' },
  { name: 'psg', url: 'https://www.psg.fr' },
  { name: 'liverpool', url: 'https://www.liverpoolfc.com' },
  { name: 'man-city', url: 'https://www.mancity.com' },
  { name: 'arsenal', url: 'https://www.arsenal.com' },
  { name: 'man-united', url: 'https://www.manutd.com' },
  { name: 'tottenham', url: 'https://www.tottenhamhotspur.com' },
  { name: 'chelsea', url: 'https://www.chelseafc.com' },
  { name: 'inter-milan', url: 'https://www.inter.it' },
  { name: 'bvb-dortmund', url: 'https://www.bvb.de' },
  { name: 'atletico-madrid', url: 'https://www.atleticodemadrid.com' },
  { name: 'aston-villa', url: 'https://www.avfc.co.uk' },
  { name: 'ac-milan', url: 'https://www.acmilan.com' },
  { name: 'juventus', url: 'https://www.juventus.com' },
  { name: 'newcastle', url: 'https://www.nufc.co.uk' },
  { name: 'vfb-stuttgart', url: 'https://www.vfb.de' },
  { name: 'sl-benfica', url: 'https://www.slbenfica.pt' },
  { name: 'west-ham', url: 'https://www.whufc.com' },
  { name: 'uefa', url: 'https://www.uefa.com' },
  { name: 'f1', url: 'https://www.formula1.com' },
  { name: 'motogp', url: 'https://www.motogp.com' },
  { name: 'nba', url: 'https://www.nba.com' },
  { name: 'mls', url: 'https://www.mlssoccer.com' },
  { name: 'mlb', url: 'https://www.mlb.com' },
];

// Common cookie rejection selectors
const COOKIE_REJECT_SELECTORS = [
  // Generic reject/decline buttons
  'button[id*="reject"]',
  'button[id*="decline"]',
  'button[id*="deny"]',
  'button[class*="reject"]',
  'button[class*="decline"]',
  'button[class*="deny"]',
  '[data-testid*="reject"]',
  '[data-testid*="decline"]',
  // OneTrust (very common)
  '#onetrust-reject-all-handler',
  '.ot-pc-refuse-all-handler',
  '#onetrust-pc-btn-handler',
  // Cookiebot
  '#CybotCookiebotDialogBodyButtonDecline',
  '#CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll',
  // Didomi
  '#didomi-notice-disagree-button',
  '.didomi-dismiss-button',
  // Common text-based
  'button:has-text("Reject All")',
  'button:has-text("Reject all")',
  'button:has-text("reject all")',
  'button:has-text("Decline All")',
  'button:has-text("Decline all")',
  'button:has-text("Deny")',
  'button:has-text("Refuse")',
  'button:has-text("Refuse All")',
  'button:has-text("Refuser")',
  'button:has-text("Refuser tout")',
  'button:has-text("Tout refuser")',
  'button:has-text("Rechazar")',
  'button:has-text("Rechazar todo")',
  'button:has-text("Rechazar todas")',
  'button:has-text("Ablehnen")',
  'button:has-text("Alle ablehnen")',
  'button:has-text("Rifiuta")',
  'button:has-text("Rifiuta tutto")',
  'button:has-text("Rifiuta tutti")',
  'button:has-text("Recusar")',
  'button:has-text("Recusar tudo")',
  'button:has-text("Only necessary")',
  'button:has-text("Necessary only")',
  'button:has-text("Essential only")',
  'button:has-text("Solo necesarias")',
  'button:has-text("Nur notwendige")',
  'button:has-text("Nur erforderliche")',
  'button:has-text("Solo necessari")',
  'a:has-text("Reject All")',
  'a:has-text("Reject all")',
  'a:has-text("Decline")',
  'a:has-text("Refuse")',
  // Quantcast / CMP
  '.qc-cmp2-summary-buttons button:first-child',
  'button.css-47sehv', // common Quantcast
  // Generic cookie banner close/dismiss
  '[aria-label="Close cookie banner"]',
  '[aria-label="Reject cookies"]',
  '[aria-label="Decline cookies"]',
];

async function rejectCookies(page) {
  // Wait a moment for cookie banners to appear
  await page.waitForTimeout(2000);

  for (const selector of COOKIE_REJECT_SELECTORS) {
    try {
      const el = await page.$(selector);
      if (el && await el.isVisible()) {
        await el.click();
        console.log(`  ✓ Rejected cookies via: ${selector}`);
        await page.waitForTimeout(1000);
        return true;
      }
    } catch (e) {
      // Selector not found or not clickable, continue
    }
  }

  // Try to find any visible button with reject-like text via JS
  try {
    const rejected = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button, a, [role="button"]');
      const rejectWords = ['reject', 'decline', 'deny', 'refuse', 'refuser', 'rechazar', 'ablehnen', 'rifiuta', 'recusar', 'necessary only', 'essential only', 'nur notwendig', 'nur erforderlich', 'solo necesari'];
      for (const btn of buttons) {
        const text = btn.textContent?.toLowerCase().trim() || '';
        if (rejectWords.some(w => text.includes(w)) && btn.offsetParent !== null) {
          btn.click();
          return text;
        }
      }
      return null;
    });
    if (rejected) {
      console.log(`  ✓ Rejected cookies via JS: "${rejected}"`);
      await page.waitForTimeout(1000);
      return true;
    }
  } catch (e) {}

  console.log('  ⚠ No cookie reject button found');
  return false;
}

async function captureSite(browser, site, index) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    locale: 'en-GB',
  });

  const page = await context.newPage();
  const filename = join(SCREENSHOT_DIR, `${String(index + 1).padStart(2, '0')}-${site.name}.png`);

  try {
    console.log(`[${index + 1}/${sites.length}] Capturing ${site.name} (${site.url})`);

    await page.goto(site.url, {
      waitUntil: 'domcontentloaded',
      timeout: 30000
    });

    // Wait for page to settle
    await page.waitForTimeout(3000);

    // Try to reject cookies
    await rejectCookies(page);

    // Wait after cookie rejection for any overlays to disappear
    await page.waitForTimeout(1500);

    // Scroll down to trigger lazy loading, then back up
    await page.evaluate(async () => {
      const scrollStep = 500;
      const delay = ms => new Promise(r => setTimeout(r, ms));
      for (let y = 0; y < document.body.scrollHeight; y += scrollStep) {
        window.scrollTo(0, y);
        await delay(200);
      }
      // Scroll back to top
      window.scrollTo(0, 0);
      await delay(500);
    });

    await page.waitForTimeout(2000);

    // Take full page screenshot
    await page.screenshot({
      path: filename,
      fullPage: true,
      timeout: 30000
    });

    console.log(`  ✓ Saved: ${filename}`);
    return { site: site.name, file: filename, status: 'ok' };

  } catch (err) {
    console.error(`  ✗ Error: ${err.message}`);

    // Try a viewport-only screenshot as fallback
    try {
      await page.screenshot({ path: filename, fullPage: false });
      console.log(`  ⚠ Saved viewport-only fallback: ${filename}`);
      return { site: site.name, file: filename, status: 'viewport-only' };
    } catch (e2) {
      return { site: site.name, file: null, status: 'failed', error: err.message };
    }
  } finally {
    await context.close();
  }
}

async function main() {
  console.log(`Starting capture of ${sites.length} websites...\n`);

  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-blink-features=AutomationControlled']
  });

  const results = [];

  // Process in batches of 3 to avoid overwhelming
  const BATCH_SIZE = 3;
  for (let i = 0; i < sites.length; i += BATCH_SIZE) {
    const batch = sites.slice(i, i + BATCH_SIZE);
    const batchResults = await Promise.all(
      batch.map((site, idx) => captureSite(browser, site, i + idx))
    );
    results.push(...batchResults);
  }

  await browser.close();

  console.log('\n=== RESULTS ===');
  const ok = results.filter(r => r.status === 'ok').length;
  const viewport = results.filter(r => r.status === 'viewport-only').length;
  const failed = results.filter(r => r.status === 'failed').length;
  console.log(`OK: ${ok} | Viewport-only: ${viewport} | Failed: ${failed}`);

  if (failed > 0) {
    console.log('\nFailed sites:');
    results.filter(r => r.status === 'failed').forEach(r => {
      console.log(`  - ${r.site}: ${r.error}`);
    });
  }

  writeFileSync(join(SCREENSHOT_DIR, '_results.json'), JSON.stringify(results, null, 2));
}

main().catch(console.error);
