import { test, expect } from '@playwright/test';

// D-26 — visual-regression scaffold for the homepage matrix.
// Skipped intentionally: the baseline PNG is captured in plan 04 once the
// homepage refactor (HeaderBar / TopNav / matrix shell) is in place. Until
// then the homepage still renders the legacy markup, so a baseline now would
// be invalidated by plans 02–04. Unskip after plan 04 lands.
test.skip(true, 'baseline captured in plan 04 once homepage refactor lands');

test('homepage matches visual baseline', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await expect(page).toHaveScreenshot('homepage.png', {
    fullPage: true,
  });
});
