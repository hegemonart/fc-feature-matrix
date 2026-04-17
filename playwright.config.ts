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
    baseURL: 'http://localhost:3000',
    colorScheme: 'dark',
    trace: 'retain-on-failure',
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.02,
    },
  },
});
