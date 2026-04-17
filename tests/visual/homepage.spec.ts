import { test, expect } from '@playwright/test';

// D-26 — visual-regression baseline for the homepage matrix.
// Plan infra-redesign-v2-04 captured the baseline PNG once the homepage
// refactor (Server Component shell + <MatrixIsland> + atomic components +
// portaled <HoverTooltipCard>) was in place. The baseline lives at
// tests/visual/homepage.spec.ts-snapshots/homepage-1440x900-{platform}.png
// and is committed alongside this spec. Subsequent runs enforce
// `maxDiffPixelRatio: 0.02` (set in playwright.config.ts) — anything above
// that threshold fails the test and signals visual drift.
//
// Pitfalls handled (RESEARCH.md):
//   - `animations: 'disabled'` freezes the matrix transitions so the
//     screenshot doesn't capture mid-animation frames.
//   - `await page.waitForFunction(() => document.fonts.ready)` ensures the
//     Inter Tight + Roboto Mono web-fonts have swapped in before the
//     screenshot fires (otherwise the first run captures FOUT and the
//     baseline is wrong).
//   - The HeaderBar's date span carries `data-build-date` so we can mask
//     it; the build-date string changes per commit and would otherwise
//     fail the diff on every CI run.

test('homepage matches visual baseline @smoke', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(() => document.fonts.ready.then(() => true));

  await expect(page).toHaveScreenshot('homepage-1440x900.png', {
    fullPage: true,
    animations: 'disabled',
    mask: [page.locator('[data-build-date]')],
  });
});
