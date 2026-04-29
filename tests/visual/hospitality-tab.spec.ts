import { test, expect } from '@playwright/test';

// Plan 02-13 → Plan 02-21 — visual-regression baseline + accessibility
// posture for the /hospitality route.
//
// Plan 02-21 unified the hospitality view with the homepage matrix
// shell: same HeaderBar, TopNav, sidebar (CategoryFilter + TypeFilter),
// matrix grid, detail panel, hover tooltips. The earlier minimal
// <HospitalityIsland> standalone view was removed. The visual baseline
// PNG was regenerated alongside the refactor and is committed at
//   tests/visual/hospitality-tab.spec.ts-snapshots/hospitality-1440x900-{platform}.png
// Subsequent runs enforce maxDiffPixelRatio: 0.02 (playwright.config.ts).
//
// Pitfalls handled (mirrors tests/visual/homepage.spec.ts):
//   - viewport 1440×900
//   - animations: 'disabled'
//   - waitForFunction(() => document.fonts.ready) so Inter Tight + Roboto
//     Mono web-fonts swap in before capture
//   - mask `[data-build-date]` (changes per commit)

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

  // Plan 02-21 — the unified matrix shell renders the SAME HeaderBar
  // + TopNav + sidebar + table chrome as the homepage.

  // 1. HeaderBar with build date is present.
  const buildDate = page.locator('[data-build-date]');
  await expect(buildDate).toBeVisible();

  // 2. TopNav: the "hospitality" tab is the active pill (Plan 02-21).
  const activeTab = page.locator('[data-tab-active="true"]');
  await expect(activeTab).toHaveCount(1);
  await expect(activeTab).toHaveAttribute('data-tab-id', 'hospitality');

  // 3. Sidebar shows the 8 hospitality categories (CategoryFilter).
  const catRows = page.locator('.sidebar [data-category-id]');
  await expect(catRows).toHaveCount(8);

  // 4. Matrix table renders with 1 sticky feature col + 5 product cols
  //    + 55 feature rows (HP01..HP55).
  const headerCols = page.locator('thead tr').first().locator('th');
  await expect(headerCols).toHaveCount(6);
  const featureRows = page.locator('tbody tr[data-feature-row]');
  await expect(featureRows).toHaveCount(55);

  // 5. Logos have alt text (a11y baseline).
  const logoImgs = page.locator('thead .col-logo img');
  await expect(logoImgs).toHaveCount(5);
  const logoCount = await logoImgs.count();
  for (let i = 0; i < logoCount; i++) {
    const alt = await logoImgs.nth(i).getAttribute('alt');
    expect(alt && alt.length > 0).toBeTruthy();
  }

  // 6. Single-orange-CTA invariant: ≤ 1 visible .locked-btn (modals
  //    are hidden until triggered, so visible count is 0 in default
  //    state — strictly preserved by the unified shell).
  const visibleOranges = page.locator(
    '.locked-overlay.visible .locked-btn, .preview-blur-overlay .locked-btn',
  );
  const orangeCount = await visibleOranges.count();
  expect(orangeCount).toBeLessThanOrEqual(1);
});
