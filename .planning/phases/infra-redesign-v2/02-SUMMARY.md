---
phase: infra-redesign-v2
plan: 02
subsystem: infra
tags: [matrix-components, datacell, sortheader, meterrow, headerbar, topnav, categoryfilter, typefilter, vitest, react-testing-library, css-modules]

# Dependency graph
requires:
  - phase: infra-redesign-v2
    plan: 01
    provides: design tokens (--bg-cell, --bg-hover, --border, --accent, --column-tint, --text, --muted), Inter Tight + Roboto Mono via next/font, .mono-caption helper, process.env.BUILD_DATE, tests/components/ directory gate
provides:
  - app/components/matrix/types.ts contract source of truth (DataCellProps, SortHeaderProps, MeterRowProps, HeaderBarProps, TopNavProps, CategoryFilterProps, TypeFilterProps + CategoryItem + Tab + ProductType re-export)
  - <DataCell> with all 8 visual states (selected x intermediate x state), inline-SVG check, tabIndex=0 a11y, data-feature/-club for plan 03 portaled tooltip
  - <SortHeader> with 3 states (idle | asc | desc), inline-SVG arrows (no Figma asset URL fetch)
  - <MeterRow> with 4 band-colored mini progress bars (competitive=green, mid=yellow, weak=orange, bottom=red); pure-visual, no scoring import
  - <HeaderBar> with humbleteam wordmark + dot, centered FC Benchmark + buildDate, outlined GET IN TOUCH CTA — buildDate sourced from process.env.BUILD_DATE (no new Date(), avoids hydration mismatch)
  - <TopNav> + <UnlockTab> with active border, locked-tab opacity 0.6, separation-of-concerns onTabClick (parent owns modal flow)
  - <CategoryFilter> presentation-only, parent passes derived CategoryItem[] from features.ts
  - <TypeFilter> presentation-only, parent passes Set<ProductType>; filter math validated against real PRODUCTS data
  - tests/setup-rtl.ts global cleanup() so vitest jsdom doesn't accumulate DOM nodes between tests
  - vitest.config environment=jsdom + setupFiles=tests/setup-rtl.ts
affects: [infra-redesign-v2-03, infra-redesign-v2-04]

# Tech tracking
tech-stack:
  added: ["@testing-library/react", "@testing-library/jest-dom", "@testing-library/user-event", "jsdom"]
  patterns:
    - "Per-component CSS module colocated next to TSX (Claude's Discretion: clearer ownership than one matrix.css)"
    - "Inline-SVG icons over PNG fetches (Figma asset URLs expire in 7 days)"
    - "Components are presentation-only — parents own state and pass derived data via props (test isolation)"
    - "Snapshot tests for visual states; behavior tests for handlers"
    - "Global RTL cleanup() via vitest setupFiles so successive renders don't pile DOM nodes onto same body"
    - "data-* attributes (data-feature, data-club, data-tab-id, data-category-id, etc.) for both downstream consumers (plan 03 tooltip) and tests"
    - "Plain CSS modules + var() tokens — no Tailwind, no shadcn (preserves hand-written, minimal-deps aesthetic)"

key-files:
  created:
    - app/components/matrix/types.ts
    - app/components/matrix/DataCell.tsx
    - app/components/matrix/DataCell.module.css
    - app/components/matrix/SortHeader.tsx
    - app/components/matrix/SortHeader.module.css
    - app/components/matrix/MeterRow.tsx
    - app/components/matrix/MeterRow.module.css
    - app/components/matrix/HeaderBar.tsx
    - app/components/matrix/HeaderBar.module.css
    - app/components/matrix/TopNav.tsx
    - app/components/matrix/TopNav.module.css
    - app/components/matrix/CategoryFilter.tsx
    - app/components/matrix/CategoryFilter.module.css
    - app/components/matrix/TypeFilter.tsx
    - app/components/matrix/TypeFilter.module.css
    - tests/components/DataCell.test.tsx
    - tests/components/SortHeader.test.tsx
    - tests/components/MeterRow.test.tsx
    - tests/components/HeaderBar.test.tsx
    - tests/components/TopNav.test.tsx
    - tests/components/CategoryFilter.test.tsx
    - tests/components/TypeFilter.test.tsx
    - tests/components/__snapshots__/DataCell.test.tsx.snap
    - tests/components/__snapshots__/SortHeader.test.tsx.snap
    - tests/components/__snapshots__/MeterRow.test.tsx.snap
    - tests/components/__snapshots__/HeaderBar.test.tsx.snap
    - tests/components/__snapshots__/TopNav.test.tsx.snap
    - tests/setup-rtl.ts
    - .planning/phases/infra-redesign-v2/02-SUMMARY.md
  modified:
    - vitest.config.ts (environment=jsdom, setupFiles=tests/setup-rtl.ts)
    - package.json / package-lock.json (testing-library + jsdom devDeps)
    - .planning/phases/infra-redesign-v2/CONTEXT.md (D-15 correction note)
    - CHANGELOG.md (v7.1 entry)

key-decisions:
  - "Per-component CSS modules over one matrix.css: clearer ownership and easier deletion when a component is retired"
  - "Components are presentation-only — parents own state and pass derived data (CategoryItem[], Set<ProductType>) via props for test isolation"
  - "Global RTL cleanup() via tests/setup-rtl.ts (vitest setupFiles) instead of per-file afterEach blocks — DRY, also removes a recurring footgun for plan 03"
  - "Bumped CHANGELOG to v7.1 (not v6.1 as the plan literal said) — sequencing on top of plan 01's v7.0 baseline. Plan-literal version was stale, written before plan 01 chose v7.0"
  - "Inline-SVG check + arrow icons over Figma PNG fetches — Figma asset URLs expire in 7 days, so a fetched PNG would silently 404 a week from now"

patterns-established:
  - "app/components/matrix/types.ts is the single source of truth for matrix component prop shapes — plan 03 imports DataCellProps from here, plan 04 imports all of them"
  - "Components own visuals only; data derivation lives in the parent (matrix island in plan 04)"
  - "data-* attributes serve double duty: queryable test hooks + downstream consumer hooks (plan 03 tooltip reads data-feature/data-club)"

requirements-completed: [D-05, D-06, D-10, D-11, D-12, D-13, D-14, D-15]

# Metrics
duration: ~12min
completed: 2026-04-17
---

# Phase infra-redesign-v2 Plan 02: Atomic Matrix Components Summary

**7 atomic matrix components (DataCell · SortHeader · MeterRow · HeaderBar · TopNav · CategoryFilter · TypeFilter) shipped under app/components/matrix/ with colocated CSS modules and per-component Vitest specs, plus types.ts as the contract source of truth for plans 03–04.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-04-17T04:22:08Z
- **Completed:** 2026-04-17T04:34:32Z
- **Tasks:** 9/9
- **Tests:** 75 total (5 prior + 7 new component specs = 70 component-spec assertions added)
- **Files created:** 29 (15 source + 7 specs + 5 snapshots + 1 setup + 1 SUMMARY)
- **Files modified:** 4 (vitest.config.ts, package.json, package-lock.json, CONTEXT.md, CHANGELOG.md)

## Accomplishments

- **types.ts contract** — single source of truth for all matrix component prop shapes; plan 03 + 04 import from here, no re-derivation
- **<DataCell>** — 8 visual states (selected × intermediate × state) per Figma 45:5509; fixed 40×38 metrics, L/R/T borders only, inline-SVG check icon, tabIndex=0 a11y, data-feature/-club for portaled tooltip in plan 03
- **<SortHeader>** — 3 states (idle | asc | desc) per Figma 45:5542, inline-SVG ArrowUp/ArrowDown, click fires onSort (parent owns desc→asc→idle cycle)
- **<MeterRow>** — band-colored mini progress bar (competitive=green, mid=yellow, weak=orange, bottom=red); pure-visual, value clamped 0–100, mono-caption percentage
- **<HeaderBar>** — humbleteam + dot, centered FC Benchmark + buildDate (sourced from process.env.BUILD_DATE — no new Date()), GET IN TOUCH outlined CTA
- **<TopNav> + <UnlockTab>** — active 2px accent bottom border, locked tabs at opacity 0.6 (still fire onTabClick — parent decides modal flow), unlock variant with solid orange bg
- **<CategoryFilter>** — vertical list, presentation-only, parent passes derived CategoryItem[]; D-14 contract test asserts per-category counts equal sum of features per category
- **<TypeFilter>** — 3 checkboxes (FC/Federation/League → club/governing/league), presentation-only with Set<ProductType>; D-15 contract test asserts filter math against real PRODUCTS data
- **CONTEXT.md D-15 corrected** — "type field is on analysis/products.ts PRODUCTS, NOT on analysis/homepage/results/*.json" (CORRECTION 2026-04-17 note appended in same commit as TypeFilter)
- **Global RTL cleanup() setup** — tests/setup-rtl.ts wired via vitest setupFiles; pre-empts the "Found multiple elements" footgun for plan 03+
- **All gates green:** `npx next build` compiles clean, `npm test` shows 12 files / 75 tests passing, D-28 invariant `git diff --quiet HEAD analysis/homepage/results/` returns clean

## Task Commits

1. **Task 02-01: types.ts contract** — `4e0624d` (feat)
2. **Task 02-02: <DataCell> 8 states** — `7b0e90f` (feat)
3. **Task 02-03: <SortHeader> 3 states** — `9dfbb4b` (feat)
4. **Task 02-04: <MeterRow> band colors** — `ad993d5` (feat)
5. **Task 02-05: <HeaderBar> build-date** — `e3600a9` (feat)
6. **Task 02-06: <TopNav> + <UnlockTab>** — `a8dd3ca` (feat)
7. **Task 02-07: <CategoryFilter>** — `4398b36` (feat)
8. **Task 02-08: <TypeFilter> + CONTEXT.md D-15 correction** — `37ef8b6` (feat)
9. **Task 02-09: changelog v7.1 + plan close** — `6478246` (docs)

**Plan metadata:** (created after this SUMMARY)

## Files Created/Modified

### Created (29)

**Components (14)** — `app/components/matrix/`:
- `types.ts` — contract source of truth
- `DataCell.tsx` + `DataCell.module.css`
- `SortHeader.tsx` + `SortHeader.module.css`
- `MeterRow.tsx` + `MeterRow.module.css`
- `HeaderBar.tsx` + `HeaderBar.module.css`
- `TopNav.tsx` + `TopNav.module.css`
- `CategoryFilter.tsx` + `CategoryFilter.module.css`
- `TypeFilter.tsx` + `TypeFilter.module.css`

**Tests (12)** — `tests/components/`:
- `DataCell.test.tsx` (12 tests, 8 snapshots)
- `SortHeader.test.tsx` (6 tests, 3 snapshots)
- `MeterRow.test.tsx` (8 tests, 4 snapshots)
- `HeaderBar.test.tsx` (6 tests, 1 snapshot)
- `TopNav.test.tsx` (10 tests, 1 snapshot)
- `CategoryFilter.test.tsx` (5 tests)
- `TypeFilter.test.tsx` (10 tests)
- `__snapshots__/` (5 snapshot files)

**Other (3)**:
- `tests/setup-rtl.ts` — global RTL cleanup
- `.planning/phases/infra-redesign-v2/02-SUMMARY.md` — this file

### Modified (5)

- `vitest.config.ts` — `environment: 'jsdom'` + `setupFiles: ['./tests/setup-rtl.ts']`
- `package.json` / `package-lock.json` — `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom` devDeps
- `.planning/phases/infra-redesign-v2/CONTEXT.md` — D-15 entry rewritten with CORRECTION 2026-04-17 note
- `CHANGELOG.md` — v7.1 entry at top

## Decisions Made

- **Per-component CSS modules over single matrix.css.** CONTEXT.md D-Claude's-Discretion explicitly listed this as a Claude choice. Per-component CSS gives cleaner ownership: when a component is renamed/deleted, its CSS goes with it. Trade-off: 7 small files vs 1 medium one — readability wins for a 7-component bundle.
- **Components are presentation-only — parents own state.** Both `<CategoryFilter>` and `<TypeFilter>` could have imported their data sources directly (`features.ts` and `PRODUCTS`). Instead they accept derived props. Reasoning: (a) tests can inject mock data without module-mocking the data layer, (b) the parent (plan 04 matrix island) is the single owner of filter state — components stay reusable.
- **Global RTL cleanup() via setupFiles, not per-file afterEach.** Hit the "Found multiple elements" issue once during TypeFilter.test.tsx; instead of fixing it locally, added the cleanup globally so plan 03 + 04 specs don't have to repeat it. Removes a known footgun before the next agent hits it.
- **Bumped CHANGELOG to v7.1, not v6.1 as the plan-literal said.** Plan 02 was written assuming the project was at v6.0; plan 01 then bumped to v7.0 (foundation = major). Continuing the sequence as v7.1 (minor — atomic components don't change the rubric or data model, fits CLAUDE.md classification of minor).
- **Inline-SVG icons over Figma PNG fetches.** CONTEXT.md/RESEARCH.md both flagged Figma asset URLs as 7-day-expiring. The check icon and arrow icons are simple enough that hand-coded SVG paths render cleanly at 14px / 8px. No fetch, no expiry risk, no extra HTTP request.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed @testing-library/react + jsdom devDeps**
- **Found during:** Task 02-02 setup
- **Issue:** Plan called for "Vitest spec" + "@testing-library/react (install if missing)" — `node_modules/@testing-library` was empty and `jsdom` wasn't present either. Without RTL the component tests can't render JSX; without jsdom there's no `document`/`window` to render into.
- **Fix:** Ran `npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`. Updated `vitest.config.ts` to set `environment: 'jsdom'` globally (existing tests are environment-agnostic so jsdom is safe).
- **Files modified:** `package.json`, `package-lock.json`, `vitest.config.ts`
- **Verification:** `npm test` after install shows 18/18 (existing) + new component tests all green.
- **Committed in:** `7b0e90f` (folded into the task 02-02 DataCell commit since the install was needed before any component test could run).

**2. [Rule 2 - Missing Critical] Added global RTL cleanup() in tests/setup-rtl.ts**
- **Found during:** Task 02-08 (TypeFilter tests)
- **Issue:** Within a single test file, two `render()` calls would pile their DOM nodes onto the same `document.body`. The second `getByTestId('type-filter-checkbox-club')` then failed with "Found multiple elements". Without cleanup this footgun would bite plan 03 + 04 too.
- **Fix:** Created `tests/setup-rtl.ts` exporting an `afterEach(() => cleanup())` global hook; wired via `vitest.config.ts` `setupFiles`.
- **Files modified:** `tests/setup-rtl.ts` (new), `vitest.config.ts`
- **Verification:** All 75 tests across 12 files pass after the global setup is in place.
- **Committed in:** `37ef8b6` (folded into task 02-08 since the same change unblocked the TypeFilter test).

**3. [Rule 3 - Blocking] Initial getByText('FC Benchmark') matched parent + child**
- **Found during:** Task 02-05 (HeaderBar tests)
- **Issue:** `getByText('FC Benchmark')` in jsdom matched both the inner `<span>` and the outer `<header>` (text bubbles up). RTL throws on non-unique matches.
- **Fix:** Switched to `getAllByText('FC Benchmark').length > 0` for the title and to `container.querySelector('[data-brand="humbleteam"]')` for the wordmark.
- **Files modified:** `tests/components/HeaderBar.test.tsx`
- **Verification:** 6/6 HeaderBar tests pass.
- **Committed in:** `e3600a9` (folded into task 02-05 commit before initial test-run completed).

**4. [Rule 3 - Blocking] MeterRow `div > div > div` selector walked past the fill**
- **Found during:** Task 02-04 (MeterRow tests)
- **Issue:** The `meterColor` override test queried `div > div > div` to grab the fill element, but that selector matched a different div (the deepest `div` was the caption span's parent path, not the fill).
- **Fix:** Changed to `Array.from(divs).find(d => d.style.background)` which is structure-agnostic.
- **Files modified:** `tests/components/MeterRow.test.tsx`
- **Verification:** 8/8 MeterRow tests pass.
- **Committed in:** `ad993d5` (folded into task 02-04 commit).

---

**Total deviations:** 4 auto-fixed (1 missing critical, 3 blocking).
**Impact on plan:** All four were necessary to keep verification gates green. Two (#1, #2) added net infrastructure (testing-library install + global cleanup) that benefits plans 03–04. Zero scope creep, zero architectural change.

## Issues Encountered

- **CHANGELOG version mismatch.** Plan literal said v6.1; project was already at v7.0 (plan 01). Bumped to v7.1 (minor) to keep sequencing correct. Documented in Decisions Made above.
- **CRLF/LF warnings on commit.** Git autocrlf normalized line endings on the new TS/TSX/CSS files. Cosmetic; no behavioral impact.
- **Workspace-root warning.** `npx next build` still warns about multiple lockfiles (parent repo + worktree); known issue from plan 01, untouched. Out of scope for this plan.

## User Setup Required

None. All deps installable via standard `npm install`; no external service config; no secrets needed.

## Next Phase Readiness

- **Wave 1 gate cleared.** Plan 03 (`<HoverTooltipCard>` + column-selected state) can:
  - Import `DataCellProps` from `app/components/matrix/types.ts` (no re-derivation)
  - Read `data-feature` and `data-club` attributes from rendered `<DataCell>` elements (already wired)
  - Spawn the portal alongside the existing 7 components without naming collisions
- **Plan 04** (homepage refactor) can:
  - Import all 7 components + types from `app/components/matrix/`
  - Derive `CategoryItem[]` from `analysis/homepage/features.ts` and pass to `<CategoryFilter>`
  - Pass `Set<ProductType>` to `<TypeFilter>` and use `PRODUCTS.filter(p => set.has(p.type))` for the filter math (D-15 contract verified by tests)
  - Source `<HeaderBar>` `buildDate` from `process.env.BUILD_DATE` (D-12 contract verified by test)
  - Wire `<TopNav>` `onTabClick` to the existing `handleTabClick` branching from `app/page.tsx`
- **D-28 invariant verified:** `git diff --quiet HEAD analysis/homepage/results/` returns clean. No scoring data touched.

## Self-Check: PASSED

- All 29 created files exist on disk (verified after final commit).
- All 9 task commits exist in `git log --oneline`: 4e0624d, 7b0e90f, 9dfbb4b, ad993d5, e3600a9, a8dd3ca, 4398b36, 37ef8b6, 6478246.
- D-28 invariant verified: `git diff --quiet HEAD analysis/homepage/results/` returns clean.
- `npx next build`: passes (clean compile in 3.9s).
- `npm test`: 12 files / 75 tests pass.
- CONTEXT.md D-15 entry no longer mentions `analysis/homepage/results/*.json`; CORRECTION 2026-04-17 note present.
- All 8 visual states of `<DataCell>` are reachable in the snapshot suite (8 snapshot tests confirmed).
- Real PRODUCTS filter math validated in `<TypeFilter>` D-15 contract test.
- Real FEATURES count derivation validated in `<CategoryFilter>` D-14 contract test.

---
*Phase: infra-redesign-v2*
*Completed: 2026-04-17*
