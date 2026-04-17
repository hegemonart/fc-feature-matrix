import { test, expect } from '@playwright/test';

// D-26 (extended) — visual-regression baseline for /admin/analytics.
//
// Skipped pending an admin auth fixture. The /admin/* routes are
// gated by getSessionFromCookie() in app/admin/layout.tsx, which
// requires (a) a real DATABASE_URL with a seeded admin user and
// (b) a Playwright storageState fixture posting to /api/auth/login
// to obtain the fc_session cookie. The current worktree has no
// DATABASE_URL configured (.env.example only), so attempting to
// authenticate produces "Environment validation failed: DATABASE_URL
// Required" 500s.
//
// The admin re-theme (D-23) is verified by:
//   - npx next build (compiles all admin routes against new tokens)
//   - tests/components/Modal.test.tsx (modal CTA invariant)
//   - manual sign-off against the running dev server when DATABASE_URL
//     is wired (see CONTEXT.md D-26 manual gate).
//
// TODO(infra-redesign-v2.1): wire admin auth fixture + capture baseline.
//   Steps:
//     1. Add tests/visual/global-setup.ts that POSTs to /api/auth/login
//        with admin creds from process.env (TEST_ADMIN_EMAIL/PASSWORD).
//     2. Save the response Set-Cookie header to playwright/.auth/admin.json.
//     3. Reference it from playwright.config.ts via projects[].use.storageState.
//     4. Drop the test.skip below and run --update-snapshots.

test.skip('admin /analytics matches visual baseline @smoke', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('/admin/analytics');
  await page.waitForLoadState('networkidle');
  await page.waitForFunction(() => document.fonts.ready.then(() => true));

  await expect(page).toHaveScreenshot('admin-analytics-1440x900.png', {
    fullPage: true,
    animations: 'disabled',
  });
});
