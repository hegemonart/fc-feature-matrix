/**
 * One-off helper to render the Lighthouse a11y HTML report and screenshot
 * the score panel as homepage-a11y.png. Run manually after generating
 * the HTML report. Not part of the regular test suite.
 *
 * Usage: node tests/visual/lighthouse/capture-score-png.mjs
 */
import { chromium } from '@playwright/test';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const reportPath = path.join(__dirname, 'homepage-a11y.html');
const fileUrl = 'file:///' + reportPath.replace(/\\/g, '/');
const outPng = path.join(__dirname, 'homepage-a11y.png');

const browser = await chromium.launch();
const context = await browser.newContext({ viewport: { width: 1200, height: 800 } });
const page = await context.newPage();
await page.goto(fileUrl);
await page.waitForLoadState('networkidle');

// Lighthouse score gauge selector
const gauge = page.locator('.lh-gauge__svg-wrapper, .lh-category-headercol').first();
try {
  await gauge.waitFor({ timeout: 5000 });
  const box = await gauge.boundingBox();
  if (box) {
    // Capture a comfortable area around the gauge
    await page.screenshot({
      path: outPng,
      clip: {
        x: Math.max(0, box.x - 20),
        y: Math.max(0, box.y - 20),
        width: Math.min(800, box.width + 200),
        height: Math.min(400, box.height + 100),
      },
    });
  } else {
    await page.screenshot({ path: outPng, fullPage: false });
  }
} catch {
  await page.screenshot({ path: outPng, fullPage: false });
}

console.log('Saved', outPng);
await browser.close();
