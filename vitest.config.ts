import { defineConfig } from 'vitest/config';
import path from 'node:path';

export default defineConfig({
  resolve: {
    alias: {
      '@': path.resolve(__dirname, '.'),
    },
  },
  test: {
    include: ['**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', '.next', 'concept', 'references', 'tests/visual/**'],
    // jsdom is needed for tests/components/* (React Testing Library renders DOM nodes).
    // Other suites are environment-agnostic, so jsdom is a safe global default.
    environment: 'jsdom',
  },
});
