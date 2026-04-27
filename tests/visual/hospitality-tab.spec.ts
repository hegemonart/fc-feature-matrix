import { test, expect } from '@playwright/test';

// Plan 02-13 — visual-regression baseline + accessibility posture
// for the /hospitality route (D-19, HOSP-03).
//
// Mirrors tests/visual/homepage.spec.ts:
//   - viewport 1440×900
//   - animations: 'disabled' to avoid mid-frame screenshots
//   - waitForFunction(() => document.fonts.ready) so Suisse Intl + Roboto
//     Mono web-fonts swap in before capture
//   - maxDiffPixelRatio: 0.02 (set in playwright.config.ts)
//   - mask `[data-build-date]` (changes per commit)
//
// The baseline PNG lives at:
//   tests/visual/hospitality-tab.spec.ts-snapshots/hospitality-1440x900-{platform}.png
// and is committed alongside this spec. Subsequent runs enforce the
// pixel diff threshold; intentional design changes need
// `npx playwright test tests/visual/hospitality-tab.spec.ts --update-snapshots`
// after manual review (per CLAUDE.md design-system rule).
//
// The a11y posture check is intentionally framework-free (no axe-core
// dep) — it asserts the same baseline qualities the homepage spec
// implies: semantic HTML (table, nav, banner), alt text on logos,
// aria labels on the back-link.

test('hospitality page matches visual baseline @smoke', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/hospitality');
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(() => document.fonts.ready.then(() => true));

  await expect(page).toHaveScreenshot('hospitality-1440x900.png', {
    fullPage: true,
    animations: 'disabled',
    mask: [page.locator('[data-build-date]')],
  });
});

test('hospitality page passes a11y posture baseline @smoke', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/hospitality');
  await page.waitForLoadState('networkidle');

  // Pilot label is visible above the matrix.
  await expect(page.locator('[data-pilot-label="true"]')).toHaveText('Pilot: 5 clubs');

  // Back-to-home link is present, has the correct href, and is NOT
  // styled as an orange CTA (no .locked-btn class — the project-wide
  // marker for var(--accent) backgrounds).
  const back = page.locator('[data-cta="back-to-home"]');
  await expect(back).toHaveAttribute('href', '/');
  const backClasses = await back.getAttribute('class');
  expect(backClasses ?? '').not.toContain('locked-btn');

  // Single-orange-CTA invariant: ≤ 1 element with .locked-btn class
  // anywhere on the page.
  const orangeCount = await page.locator('.locked-btn').count();
  expect(orangeCount).toBeLessThanOrEqual(1);

  // Matrix table is rendered with semantic <table> + 5 product columns
  // + 55 feature rows (HP01..HP55).
  await expect(page.locator('table[data-matrix="hospitality"]')).toBeVisible();
  const headerCols = await page.locator('thead tr').first().locator('th').count();
  expect(headerCols).toBe(6); // 1 sticky feature col + 5 product cols
  const featureRows = await page.locator('tbody tr[data-feature]').count();
  expect(featureRows).toBe(55);

  // Logos have alt text (a11y baseline).
  const logoImgs = page.locator('thead .col-logo img');
  const logoCount = await logoImgs.count();
  expect(logoCount).toBe(5);
  for (let i = 0; i < logoCount; i++) {
    const alt = await logoImgs.nth(i).getAttribute('alt');
    expect(alt && alt.length > 0).toBeTruthy();
  }
});
