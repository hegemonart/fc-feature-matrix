/* ================================================================
   tests/setup-rtl.ts

   Global Vitest setup for React Testing Library.
   Runs cleanup() after every test so that successive renders in
   the same describe block don't pile DOM nodes onto the same
   document body. Without this, queries like getByTestId fail with
   "Found multiple elements" once a single test file has more than
   one render() call against the same testid.

   Wired in vitest.config.ts via test.setupFiles.
   ================================================================ */

import { afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

afterEach(() => {
  cleanup();
});
