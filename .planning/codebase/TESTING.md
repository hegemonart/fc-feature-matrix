# Testing Patterns

**Analysis Date:** 2026-04-16

## Test Framework

**Runner:**
- Vitest v2.1.8
- Config: `vitest.config.ts`

**Assertion Library:**
- Vitest built-in `expect()` (assertion module)

**Run Commands:**
```bash
npm test                # Run all tests once
npm run test:watch     # Watch mode (re-run on changes)
```

**Vitest Configuration:**
- Path alias support: `@/` maps to project root
- Included files: `**/*.{test,spec}.{ts,tsx}`
- Excluded: `node_modules`, `.next`, `concept`, `references`

**CI Integration:**
Tests run as part of `.github/workflows/ci.yml`:
```yaml
- name: Test
  run: npm test
```

Pipeline order: Lint → Typecheck → Test → Build

## Test File Organization

**Existing Tests:**
- Single test file in codebase: `lib/scoring.test.ts`

**Location Pattern:**
- Co-located with source: Tests sit next to the module they test
- File naming: `[module].test.ts` suffix

**File Structure:**
Tests use standard Vitest/Jest describe-it pattern with `expect()` assertions.

## Test Structure

**Suite Organization:**
```typescript
import { describe, it, expect } from 'vitest';
import { getProductScores, getRankedProducts } from './scoring';
import { PRODUCTS } from './data';

describe('scoring', () => {
  it('returns coverage between 0 and 100 for every product', () => {
    for (const p of PRODUCTS) {
      const { coveragePct } = getProductScores(p.id);
      expect(coveragePct).toBeGreaterThanOrEqual(0);
      expect(coveragePct).toBeLessThanOrEqual(100);
    }
  });

  it('ranks products in descending order by coverage', () => {
    const ranked = getRankedProducts();
    expect(ranked.length).toBe(PRODUCTS.length);
    for (let i = 1; i < ranked.length; i++) {
      expect(ranked[i - 1].pct).toBeGreaterThanOrEqual(ranked[i].pct);
    }
  });
});
```

**Patterns Observed:**
- Setup: Import statements at top; no explicit setup/teardown fixtures
- Assertions: Use built-in Vitest matchers (`toBeGreaterThanOrEqual()`, `toBeLessThanOrEqual()`, `toBe()`)
- Loop-based testing: `for` loop over data arrays to check constraints across all items
- No mocking framework observed in existing tests

## Mocking

**Framework:** None observed in existing test file

**What to Mock (inferred from codebase structure):**
- External fetch calls (would use `fetch` mocks)
- File system operations (would mock `fs` module in Node.js code)
- Env vars (would set via test config if needed)

**What NOT to Mock:**
- Data module imports (`PRODUCTS`, `FEATURES`, `CATEGORIES`) — use real data for scoring tests
- Internal utility functions — test them directly
- Business logic — test the actual logic, not the behavior

## Fixtures and Factories

**Test Data:**
- No fixture files observed
- Tests import real data from `lib/data.ts` (e.g., `PRODUCTS`, `FEATURES`)
- Ad-hoc test data created in test bodies if needed

**Location:**
- Data would live co-located in `lib/` directory
- Fixtures would follow `.test.ts` or `.fixture.ts` naming if created

## Coverage

**Requirements:** None enforced
- No coverage configuration in `vitest.config.ts`
- No coverage reporting in CI pipeline

**View Coverage:**
Coverage command not set up. To enable:
```bash
npm test -- --coverage   # Would require @vitest/coverage-* package
```

## Test Types

**Unit Tests:**
- Scope: Individual functions (e.g., `getProductScores()`, `getRankedProducts()`)
- Approach: Import function, call with test data, assert on return value
- Example: `lib/scoring.test.ts` tests scoring functions with real product data

**Integration Tests:**
- Not present in codebase
- API routes (`app/api/**/route.ts`) have no integration tests

**E2E Tests:**
- Framework: Not used
- No Playwright, Cypress, or similar tool configured

## Coverage Gaps

**API Routes (untested):**
- `app/api/auth/login/route.ts` — Auth logic not tested
- `app/api/auth/logout/route.ts` — Session clearing not tested
- `app/api/auth/me/route.ts` — Auth verification not tested
- `app/api/analytics/route.ts` — Event logging not tested
- `app/api/analytics/view/route.ts` — View tracking not tested
- `app/api/email/route.ts` — Email sending not tested
- `app/api/crosscheck-img/route.ts` — Image serving not tested

**React Components (untested):**
- `app/page.tsx` — Main feature matrix page (1,046 lines, largest component)
- `app/club/[id]/page.tsx` — Club detail page
- `app/club/[id]/CategoryFilter.tsx` — Category filtering UI
- `app/club/[id]/PageTracker.tsx` — Page tracking component
- `app/club/[id]/ScrollRestore.tsx` — Scroll restoration

**Authentication (untested):**
- `lib/auth.ts` — Session creation/parsing, password hashing
- Cookie handling
- Token verification

**Analytics (untested):**
- `lib/analytics.ts` — Event logging
- `lib/track.ts` — Client-side event tracking

## Common Patterns

**Async Testing:**
- Not observed in existing tests
- API routes use async/await but have no tests
- Client-side async operations (fetch, setState) have no tests

**Error Testing:**
- Error paths in scoring logic (if any) not explicitly tested
- Edge cases: Not systematically tested

**Data-Driven Tests:**
- Used in `scoring.test.ts`: Loop over `PRODUCTS` array to test every product
- Pattern: `for (const p of PRODUCTS) { ... }`

## Test Maintenance

**Running Tests Locally:**
```bash
cd /Users/hgmn/conductor/repos/fc-feature-matrix/.claude/worktrees/gallant-bouman
npm test              # Run once
npm run test:watch   # Continuous watch mode
```

**Adding New Tests:**
1. Create `[feature].test.ts` in same directory as source
2. Import Vitest: `import { describe, it, expect } from 'vitest'`
3. Import code under test
4. Write describe/it blocks with expect assertions
5. Run `npm test` to verify

**Test File Location Decision:**
- Scoring logic: `lib/scoring.test.ts` ✓ (existing pattern)
- Component: `app/page.test.tsx` (if created)
- API route: `app/api/auth/login.test.ts` (if created)

---

*Testing analysis: 2026-04-16*
