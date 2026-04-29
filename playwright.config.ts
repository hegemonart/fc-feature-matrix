import { defineConfig } from '@playwright/test';

// D-26 — visual-regression harness for the homepage matrix and downstream pages.
// Spec scaffolds live under tests/visual/. Plan 04 captures the first baseline
// PNG once the homepage refactor (HeaderBar / TopNav / matrix shell) ships.
export default defineConfig({
  testDir: './tests/visual',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  use: {
    // Plan 02-21: respect PLAYWRIGHT_BASE_URL when set so contributors
    // running multiple Next workspaces on different ports can still
    // run the visual suite without port collisions. Defaults to :3000.
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000',
    colorScheme: 'dark',
    trace: 'retain-on-failure',
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02,
    },
  },
});
