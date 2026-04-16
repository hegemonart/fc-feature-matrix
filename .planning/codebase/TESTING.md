# Testing

## Setup

**No test framework is installed or configured.**

The `package.json` has no test dependencies and no `test` script:
- No Jest, Vitest, Playwright, Cypress, or Testing Library packages
- No `jest.config.*`, `vitest.config.*`, or `playwright.config.*` files
- No `.spec.*` or `.test.*` files anywhere in the codebase
- Running `npm test` would fail (script not defined)

The only quality tooling present is ESLint (via `eslint-config-next`) and TypeScript strict mode.

## Test Types

**Unit tests:** None  
**Integration tests:** None  
**End-to-end tests:** None  
**Snapshot tests:** None  

No tests of any kind exist in this project.

## Coverage

**Coverage: 0%**

No code has automated test coverage. The entire codebase — data layer, scoring utilities, and UI components — is untested.

Files with no coverage:
- `lib/data.ts` — all type definitions, constants, and the `computeBands()` logic
- `lib/scoring.ts` — `getProductScores()` and `getRankedProducts()` scoring functions
- `app/page.tsx` — main interactive feature matrix page (Client Component with ~780 lines)
- `app/club/[id]/page.tsx` — club breakdown Server Component with derived scoring logic
- `app/layout.tsx` — root layout

## Patterns

No test patterns exist to document. There is no mocking approach, no test utilities, no fixtures, and no CI configuration referencing test runs.

## Gaps

The entire codebase is untested. The highest-value areas to add tests would be:

**Pure utility functions (easiest wins):**
- `lib/scoring.ts`: `getProductScores` computes coverage %, raw score, and weighted score from presence data — fully deterministic, no side effects, trivial to unit test
- `lib/scoring.ts`: `getRankedProducts` sorts all products by coverage — easy to assert on ordering and tie-breaking
- `lib/data.ts`: The `computeBands()` function (inlined at module load) assigns `adoption`, `adoptionPct`, and `band` to each feature based on presence counts — logic worth verifying

**Data integrity (static assertions):**
- Every `Feature.presence` record should contain an entry for every product ID in `PRODUCTS`
- All `CategoryId` references in features should match a valid entry in `CATEGORIES`
- `weight` values should be 1–5 with no out-of-range values
- `adoptionPct` should equal `(full + 0.5 * partial) / totalProducts * 100` rounded correctly

**UI component behavior:**
- Filter logic in `FeatureMatrixPage` (type/sport filters correctly hide products)
- Search filtering (case-insensitive match against `f.name` and `f.desc`)
- `selectedFeature`/`selectedProduct` mutual exclusion on panel selection
- `notFound()` invocation for unknown product IDs in `ClubDetailPage`
