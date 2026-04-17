import { test, expect } from '@playwright/test';

// D-26 (extended) — visual-regression baseline for the re-themed
// /club/[id] page. Token-swap from plan 05 task 05-01 should leave
// the page rendering with the new --bg-page / --bg-cell / --border /
// --accent palette, mono-caption stat labels, and a single white-
// outlined "Back to matrix" CTA (no second orange button per surface).
//
// Pattern mirrors tests/visual/homepage.spec.ts:
//   - viewport 1440×900
//   - animations: 'disabled'
//   - waitForFunction(() => document.fonts.ready)
//   - maxDiffPixelRatio: 0.02 (set in playwright.config.ts)
//
// /club/real_madrid is chosen as the canonical fixture because it has
// dense tier coverage, exercising MeterRow, status badges, and the
// stats grid in one shot.

test('club page (real_madrid) matches visual baseline @smoke', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/club/real_madrid');
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(() => document.fonts.ready.then(() => true));

  await expect(page).toHaveScreenshot('club-real_madrid-1440x900.png', {
    fullPage: true,
    animations: 'disabled',
  });
});
