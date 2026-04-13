/**
 * Live site crawl for screenshot-blind features.
 * Visits each homepage, scrolls full page, waits for delayed widgets,
 * then checks for features that can't be seen in a static screenshot.
 */
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const SITES = [
  { id: 'real_madrid',     url: 'https://www.realmadrid.com/en' },
  { id: 'fc_barcelona',    url: 'https://www.fcbarcelona.com/en/' },
  { id: 'bayern_munich',   url: 'https://fcbayern.com/en' },
  { id: 'psg',             url: 'https://en.psg.fr/' },
  { id: 'liverpool',       url: 'https://www.liverpoolfc.com/' },
  { id: 'man_city',        url: 'https://www.mancity.com/' },
  { id: 'arsenal',         url: 'https://www.arsenal.com/' },
  { id: 'man_united',      url: 'https://www.manutd.com/' },
  { id: 'tottenham',       url: 'https://www.tottenhamhotspur.com/' },
  { id: 'chelsea',         url: 'https://www.chelseafc.com/en' },
  { id: 'inter_milan',     url: 'https://www.inter.it/en' },
  { id: 'bvb_dortmund',    url: 'https://www.bvb.de/en/' },
  { id: 'atletico_madrid', url: 'https://en.atleticodemadrid.com/' },
  { id: 'aston_villa',     url: 'https://www.avfc.co.uk/' },
  { id: 'ac_milan',        url: 'https://www.acmilan.com/en' },
  { id: 'juventus',        url: 'https://www.juventus.com/en/' },
  { id: 'newcastle',       url: 'https://www.nufc.co.uk/' },
  { id: 'vfb_stuttgart',   url: 'https://www.vfb.de/en/' },
  { id: 'sl_benfica',      url: 'https://www.slbenfica.pt/en-us/' },
  { id: 'west_ham',        url: 'https://www.whufc.com/' },
  { id: 'uefa',            url: 'https://www.uefa.com/en/' },
  { id: 'f1',              url: 'https://www.formula1.com/' },
  { id: 'motogp',          url: 'https://www.motogp.com/' },
  { id: 'nba',             url: 'https://www.nba.com/' },
  { id: 'mls',             url: 'https://www.mlssoccer.com/' },
  { id: 'mlb',             url: 'https://www.mlb.com/' },
  { id: 'brentford',       url: 'https://www.brentfordfc.com/' },
  { id: 'atp_tour',        url: 'https://www.atptour.com/' },
  { id: 'club_brugge',     url: 'https://www.clubbrugge.be/en' },
  { id: 'eintracht',       url: 'https://www.eintracht.de/en/' },
  { id: 'itf_tennis',      url: 'https://www.itftennis.com/' },
  { id: 'rb_leipzig',      url: 'https://www.rbleipzig.com/en/' },
  { id: 'valencia_cf',     url: 'https://www.valenciacf.com/en' },
];

// Selectors for chat widgets
const CHAT_SELECTORS = [
  'iframe[src*="intercom"]', 'iframe[src*="drift"]', 'iframe[src*="hubspot"]',
  'iframe[src*="zendesk"]', 'iframe[src*="freshdesk"]', 'iframe[src*="tidio"]',
  'iframe[src*="crisp"]', 'iframe[src*="tawk"]', 'iframe[src*="livechat"]',
  'iframe[src*="chatbot"]', 'iframe[src*="kommunicate"]',
  '[class*="chatbot"]', '[class*="chat-widget"]', '[class*="chat-bubble"]',
  '[id*="chatbot"]', '[id*="chat-widget"]', '[id*="chat-bubble"]',
  '#intercom-container', '#drift-widget', '.intercom-lightweight-app',
  '[data-testid*="chat"]', '[aria-label*="chat"]', '[aria-label*="Chat"]',
  '.tidio-chat', '#tidio-chat', '#tawk-tooltip',
];

// Selectors for accessibility widgets
const A11Y_SELECTORS = [
  'iframe[src*="userway"]', 'iframe[src*="accessibe"]', 'iframe[src*="equalweb"]',
  '[class*="userway"]', '[class*="accessib"]', '[class*="a11y-widget"]',
  '[id*="userway"]', '[id*="accessib"]', '[id*="equalweb"]',
  '[aria-label*="accessibility"]', '[aria-label*="Accessibility"]',
  '.acsb-trigger', '#accessibilityWidget', '.ac-badge',
  'div[data-acsb-widget]', '.UserWay', '#userwayAccessibilityIcon',
];

// Selectors for language switcher
const LANG_HEADER_SELECTORS = [
  'header [class*="lang"]', 'header [class*="locale"]',
  'header select[name*="lang"]', 'header [data-lang]',
  'nav [class*="lang"]', 'nav [class*="locale"]',
  'header .globe', 'header [class*="globe"]',
  'header [aria-label*="language"]', 'header [aria-label*="Language"]',
  'header [class*="country"]',
];

const LANG_FOOTER_SELECTORS = [
  'footer [class*="lang"]', 'footer [class*="locale"]',
  'footer select[name*="lang"]', 'footer [data-lang]',
  'footer [aria-label*="language"]', 'footer [aria-label*="Language"]',
  'footer [class*="country"]',
];

// Selectors for push notification
const PUSH_SELECTORS = [
  '[class*="notification"]', '[class*="push-opt"]',
  '[id*="onesignal"]', '.onesignal-bell-launcher',
  '[class*="webpush"]', '#cleverpush-bell',
];

async function checkSite(page, site) {
  const result = {
    id: site.id,
    url: site.url,
    status: 'ok',
    findings: {},
    cookie_banner: false,
    errors: [],
  };

  try {
    // Navigate with longer timeout
    await page.goto(site.url, { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Check for cookie banner immediately
    const cookieTexts = await page.evaluate(() => {
      const body = document.body?.innerText?.toLowerCase() || '';
      return body.includes('accept cookies') || body.includes('cookie') && body.includes('consent')
        || !!document.querySelector('[class*="cookie"]') || !!document.querySelector('[id*="cookie"]')
        || !!document.querySelector('[class*="consent"]') || !!document.querySelector('[id*="consent"]');
    });
    result.cookie_banner = cookieTexts;

    // Try to dismiss cookie banner
    try {
      const cookieBtn = await page.$('[class*="cookie"] button, [id*="cookie"] button, [class*="consent"] button, button:has-text("Accept"), button:has-text("accept"), button:has-text("Agree"), button:has-text("OK"), [class*="onetrust"] button#onetrust-accept-btn-handler');
      if (cookieBtn) await cookieBtn.click({ timeout: 3000 }).catch(() => {});
    } catch {}

    // Wait for page to fully load
    await page.waitForTimeout(3000);

    // Scroll full page progressively
    await page.evaluate(async () => {
      const scrollStep = window.innerHeight;
      const maxScroll = document.body.scrollHeight;
      for (let y = 0; y < maxScroll; y += scrollStep) {
        window.scrollTo(0, y);
        await new Promise(r => setTimeout(r, 300));
      }
      window.scrollTo(0, 0); // Back to top
    });

    // Wait for delayed widgets (chat, a11y)
    await page.waitForTimeout(5000);

    // Check AI chat widget
    const chatFound = await checkSelectors(page, CHAT_SELECTORS);
    result.findings.ai_chat_assistant = chatFound;

    // Check accessibility widget
    const a11yFound = await checkSelectors(page, A11Y_SELECTORS);
    result.findings.w3c_a11y_features = a11yFound;

    // Check language switcher in header
    const langHeaderFound = await checkSelectors(page, LANG_HEADER_SELECTORS);
    result.findings.language_switcher_in_header = langHeaderFound;

    // Check language selector in footer
    const langFooterFound = await checkSelectors(page, LANG_FOOTER_SELECTORS);
    result.findings.language_selector_in_footer = langFooterFound;

    // Check push notification opt-in
    const pushFound = await checkSelectors(page, PUSH_SELECTORS);
    result.findings.push_notification_opt_in = pushFound;

    // Check for login/account by inspecting header more thoroughly
    const loginFound = await page.evaluate(() => {
      const header = document.querySelector('header') || document.querySelector('nav');
      if (!header) return false;
      const text = header.innerText?.toLowerCase() || '';
      const hasLoginText = text.includes('sign in') || text.includes('log in') || text.includes('login')
        || text.includes('my account') || text.includes('register') || text.includes('iniciar')
        || text.includes('anmelden') || text.includes('connexion');
      const hasIcon = !!header.querySelector('[class*="user"], [class*="account"], [class*="login"], [class*="profile"], [aria-label*="account"], [aria-label*="Account"], [aria-label*="login"], [aria-label*="Login"], [aria-label*="sign"], [aria-label*="Sign"]');
      return hasLoginText || hasIcon;
    });
    result.findings.login_account = loginFound;

    // Check footer for social links
    const socialFooter = await page.evaluate(() => {
      const footer = document.querySelector('footer');
      if (!footer) return false;
      const links = footer.querySelectorAll('a[href*="facebook"], a[href*="twitter"], a[href*="instagram"], a[href*="youtube"], a[href*="tiktok"], a[href*="linkedin"], a[href*="x.com"]');
      return links.length >= 2;
    });
    result.findings.social_links_in_footer = socialFooter;

    // Check for search in header
    const searchFound = await page.evaluate(() => {
      const header = document.querySelector('header') || document.querySelector('nav');
      if (!header) return false;
      return !!header.querySelector('input[type="search"], [class*="search"], [aria-label*="search"], [aria-label*="Search"], button[class*="search"], a[class*="search"], svg[class*="search"]');
    });
    result.findings.search_input_in_header = searchFound;

  } catch (err) {
    result.status = 'error';
    result.errors.push(err.message?.substring(0, 200));
  }

  return result;
}

async function checkSelectors(page, selectors) {
  for (const sel of selectors) {
    try {
      const el = await page.$(sel);
      if (el) {
        const visible = await el.isVisible().catch(() => false);
        if (visible) return { found: true, selector: sel };
      }
    } catch {}
  }
  return { found: false };
}

async function main() {
  const browser = await chromium.launch({
    headless: true,
    args: ['--disable-notifications', '--disable-popup-blocking'],
  });

  const allResults = [];
  const BATCH_SIZE = 4;

  for (let i = 0; i < SITES.length; i += BATCH_SIZE) {
    const batch = SITES.slice(i, i + BATCH_SIZE);
    console.log(`Processing batch ${Math.floor(i/BATCH_SIZE)+1}/${Math.ceil(SITES.length/BATCH_SIZE)}: ${batch.map(s => s.id).join(', ')}`);

    const results = await Promise.all(batch.map(async (site) => {
      const context = await browser.newContext({
        viewport: { width: 1440, height: 900 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      });
      const page = await context.newPage();

      try {
        const result = await checkSite(page, site);
        return result;
      } finally {
        await context.close();
      }
    }));

    allResults.push(...results);
  }

  await browser.close();

  // Write results
  const outPath = path.join(__dirname, 'analysis', 'results', '_live_crawl.json');
  fs.writeFileSync(outPath, JSON.stringify(allResults, null, 2) + '\n');
  console.log(`\nDone! Results written to ${outPath}`);

  // Summary
  for (const r of allResults) {
    const flags = [];
    for (const [key, val] of Object.entries(r.findings)) {
      if (val?.found || val === true) flags.push(key);
    }
    if (flags.length > 0 || r.status === 'error') {
      console.log(`${r.id}: ${r.status === 'error' ? 'ERROR' : flags.join(', ')}`);
    }
  }
}

main().catch(console.error);
