---
phase: infra-redesign-v2
plan: 04
subsystem: infra
tags: [server-component, client-component, react-19, next-15, matrix-refactor, hover-tooltip, column-selection, visual-regression, playwright]

# Dependency graph
requires:
  - phase: infra-redesign-v2
    plan: 01
    provides: design tokens (--bg-page/cell/hover/--accent/--column-tint/--text/--muted), .mono-caption helper, Inter Tight + Roboto Mono via next/font, BUILD_DATE env, Playwright + visual-regression scaffold
  - phase: infra-redesign-v2
    plan: 02
    provides: 7 atomic matrix components (DataCell/SortHeader/MeterRow/HeaderBar/TopNav/CategoryFilter/TypeFilter) + types.ts contract
  - phase: infra-redesign-v2
    plan: 03
    provides: HoverTooltipCard (portaled), useHoverTooltip + useColumnSelection hooks, FeatureMeta/ClubMeta/CellScoring/TooltipData type extensions
provides:
  - app/page.tsx as Server Component shell (1072 LOC -> 36 LOC) loading PRODUCTS/FEATURES/scores from lib/data + lib/scoring
  - app/MatrixIsland.tsx as Client Component island (~865 LOC) owning ALL interactive state from legacy app/page.tsx — preserved verbatim per RESEARCH.md "Current Homepage Structural Map"
  - Render tree wired to all 9 atomic components + 2 hooks from plans 02-03
  - Visual-regression baseline tests/visual/homepage.spec.ts-snapshots/homepage-1440x900-win32.png at 1440x900, maxDiffPixelRatio 0.02 enforced
  - .locked-zone animated rainbow border + .cell-tooltip CSS removed (RESEARCH P9), legacy var(--bg|bg2|bg3) consumer refs rebound to var(--bg-page|bg-cell|bg-hover)
affects: [infra-redesign-v2-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Server Component shell + Client Component island split — page.tsx loads serializable props on the server, MatrixIsland owns all useState/useEffect/useMemo"
    - "selectedProduct as single source of truth for both detail panel + column-tint (D-18) — useColumnSelection from plan 03 referenced for parity, isSelected helper reads selectedProduct directly"
    - "Tooltip lookup maps (Map<string, FeatureMeta/ClubMeta/CellScoring>) built in useMemo, passed to portaled HoverTooltipCard — no server requests on hover (D-21)"
    - "BUILD_DATE resolved on the server (process.env.BUILD_DATE) and passed as prop — Client component never reaches into process.env (avoids hydration mismatch)"
    - "Anchor-rect tooltip positioning — onMouseEnter and onFocus both call handleCellEnter so keyboard users get the tooltip too (D-21 a11y)"
    - "Playwright visual baseline pattern: setViewportSize -> goto -> waitForLoadState networkidle -> waitForFunction document.fonts.ready -> screenshot with animations:'disabled' + mask:[data-build-date]"

key-files:
  created:
    - app/MatrixIsland.tsx
    - app/MatrixIsland.module.css
    - tests/visual/homepage.spec.ts-snapshots/homepage-1440x900-win32.png
    - .planning/phases/infra-redesign-v2/04-SUMMARY.md
  modified:
    - app/page.tsx (1072 LOC -> 36 LOC; Server Component shell)
    - app/globals.css (remove .locked-zone + .cell-tooltip; rebind 50+ var(--bg|bg2|bg3) refs)
    - tests/visual/homepage.spec.ts (unskipped, animations:'disabled', fonts.ready, mask, viewport 1440x900)
    - CHANGELOG.md (v8.0)
    - README.md (project structure with MatrixIsland + components/matrix/*)

key-decisions:
  - "Server/Client split: app/page.tsx is a Server Component that pre-computes per-product weighted scores + reads BUILD_DATE; MatrixIsland is a 'use client' island. All 20+ state hooks + handlers preserved verbatim from legacy app/page.tsx."
  - "selectedProduct stays AUTHORITATIVE for column-tint (D-18) — useColumnSelection from plan 03 referenced but isSelected delegates directly to selectedProduct comparison. Avoids divergence with the existing Product-detail panel (single source of truth)."
  - "Sort cycle desc -> asc -> null (D-19) — onScoreSort cycles per spec; onAdoptionSort follows asc -> desc -> null per legacy semantics (preserved). featureAlphaSort stays a boolean toggle."
  - "Category filter remap: legacy activeCat (single-select category to focus) maps to <CategoryFilter collapsed={Set of all-except-active}> so the existing category-spotlight UX is preserved through the new component contract."
  - "TableRows wraps <DataCell> inside the existing <td> so table layout stays valid; <DataCell> div carries the tabIndex/focus/hover semantics. .cell class kept on <td> for spacing parity until plan 05 token swap."
  - "MeterRow band mapping: bandToMeterBand maps analysis BandId (table_stakes|expected|competitive|innovation) to MeterRow's MeterBand contract (competitive|mid|weak|bottom)."
  - "v8.0 (major) per CLAUDE.md — homepage refactor is a structural visible change."

patterns-established:
  - "Server Component data assembly + Client Component island: the canonical pattern for any page that needs both SSR and rich interactivity. Adopt for /club/[id] and /admin/* in plan 05."
  - "Anchor-rect + portal tooltip: cells fire onMouseEnter and onFocus -> handleCellEnter(fid, cid, e.currentTarget). Tooltip positions via getBoundingClientRect() at enter-time."
  - "Visual baseline gate via Playwright: animations:'disabled' + waitForFunction(document.fonts.ready) + mask:[data-build-date] eliminates the three known sources of false positives."

requirements-completed: []

# Metrics
duration: 12min
completed: 2026-04-17
---

# Phase infra-redesign-v2 Plan 04: Homepage Server/Client Split + Visual Baseline Summary

**1072-LOC monolithic Client Component split into a 36-LOC Server shell + 865-LOC <MatrixIsland>, wired to all 9 atomic components + 2 hooks from plans 02-03; visual baseline locked at 1440x900 with maxDiffPixelRatio 0.02.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-04-17T04:52:48Z
- **Completed:** 2026-04-17T05:04:10Z
- **Tasks:** 6
- **Files modified:** 7 (5 source/test, 2 docs)

## Accomplishments
- `app/page.tsx` collapsed from 1072 LOC to 36 LOC and converted to a Server Component shell that pre-computes per-product weighted scores and passes serializable props into `<MatrixIsland>`.
- `app/MatrixIsland.tsx` (Client Component) owns every interactive state hook from the legacy file verbatim, plus the new `useColumnSelection` + `useHoverTooltip` from plan 03. All auth / login-modal / locked-content / coming-soon / access-request handlers preserved 1:1.
- 9 atomic components (`DataCell`, `SortHeader`, `MeterRow`, `HeaderBar`, `TopNav`, `CategoryFilter`, `TypeFilter`, `HoverTooltipCard`, plus the 2 hooks) wired into the render tree. `<thead>` and `<tfoot>` Total-Score rows preserved per RESEARCH P7.
- `.locked-zone` animated rainbow border + particles + `.unlock-cta` gradient + `.cell-tooltip` CSS deleted (RESEARCH P9). 50+ legacy `var(--bg|bg2|bg3)` consumer refs rebound to the new tokens.
- Visual-regression baseline captured at 1440x900 with `animations: 'disabled'`, `document.fonts.ready` await, and `[data-build-date]` mask. `maxDiffPixelRatio: 0.02` gate is now armed.
- Quality gates green: `npx next build` passes, `npm test` 90/90, `npx playwright test` 1/1.

## Task Commits

Each task was committed atomically:

1. **Task 04-01: Scaffold MatrixIsland with preserved state** — `25b2d13` (feat)
2. **Task 04-02: Wire MatrixIsland render tree to new components** — `85295ef` (feat)
3. **Task 04-03: app/page.tsx becomes Server Component shell** — `b0f4d8a` (refactor)
4. **Task 04-04: Remove .locked-zone + .cell-tooltip; rebind legacy tokens** — `070de0b` (refactor)
5. **Task 04-05: Capture homepage visual-regression baseline** — `1a0a60b` (test)
6. **Task 04-06: Changelog v8.0 + README structure** — `807153d` (docs)

**Plan metadata commit follows.**

## Files Created/Modified

### Created
- `app/MatrixIsland.tsx` — Client Component island (~865 LOC); owns all interactive state, wires every atomic component + hook
- `app/MatrixIsland.module.css` — layout shell stub (component-level styling lives in `app/components/matrix/*.module.css`)
- `tests/visual/homepage.spec.ts-snapshots/homepage-1440x900-win32.png` — visual-regression baseline (~204 KB)
- `.planning/phases/infra-redesign-v2/04-SUMMARY.md` — this file

### Modified
- `app/page.tsx` — 1072 LOC -> 36 LOC; removed `'use client'`; loads PRODUCTS/FEATURES/scores; renders `<MatrixIsland>`
- `app/globals.css` — deleted `.locked-zone` + `.cell-tooltip` blocks (~38 LOC removed); rebound ~50 `var(--bg|bg2|bg3)` consumer refs to `var(--bg-page|bg-cell|bg-hover)`; kept `--bg1` alias (`.login-input` consumer)
- `tests/visual/homepage.spec.ts` — unskipped; added `animations: 'disabled'` + `document.fonts.ready` await + `[data-build-date]` mask + explicit 1440x900 viewport + `@smoke` tag
- `CHANGELOG.md` — v8.0 (major: homepage refactor is a structural visible change per CLAUDE.md)
- `README.md` — project-structure diagram updated to list `app/MatrixIsland.tsx` + every file under `app/components/matrix/`

## Deviations from Plan

### Rule 3 — Blocking auto-fixes

**1. [Rule 3 - Blocking] Server Component conversion split into one combined check**
- **Found during:** Task 04-02
- **Issue:** Task 04-02's automated check is `npx next build`, but the build fails until `app/page.tsx` is also updated to render `<MatrixIsland>` (legacy file still has `'use client'` and would compile but render the old Client Component instead). Task 04-03 was the actual rewrite.
- **Fix:** Updated `app/page.tsx` to render `<MatrixIsland>` immediately, then committed Task 02 (MatrixIsland) and Task 03 (page.tsx Server shell) as separate commits in sequence. Build was verified after both files were in place.
- **Files modified:** `app/MatrixIsland.tsx`, `app/page.tsx` (split across two commits)
- **Commits:** `85295ef` (task 02), `b0f4d8a` (task 03)

### Versioning deviation
- Plan text said "CHANGELOG.md v6.3" but the current CHANGELOG head is v7.2 (newer than the plan's snapshot). Per CLAUDE.md rule "Major changes (x.0)" and the plan's directive that this is a "visible, system-level change", bumped to **v8.0** rather than the literal v6.3 the plan specified. Confirmed in commit message.

### Snapshot path deviation
- Plan suggested baseline path `tests/visual/homepage-1440x900.png`. Playwright's default convention places snapshots under `tests/visual/{spec-name}-snapshots/{name}-{platform}.png` — actual path is `tests/visual/homepage.spec.ts-snapshots/homepage-1440x900-win32.png`. Plan explicitly said "do NOT override it" so the default location was used. The `-win32` suffix means CI on Linux will need to capture its own baseline (or use a Docker-based runner) — flagged for plan 05 / CI hookup.

### Out of scope (deferred)
- **Lighthouse a11y >= 90 (D-29):** Plan explicitly defers this to plan 05 ("This plan does not yet capture the Lighthouse report — that happens at phase gate in plan 05"). Not attempted here.
- **Mobile responsiveness:** Out of phase scope per CONTEXT.md.

## Verification Evidence

**Build (D-27):**
```
✓ Generating static pages using 11 workers (51/51) in 576ms
✓ Compiled successfully
```

**Vitest:** `15 passed (15) — 90 passed (90)`

**Playwright:** `1 passed (2.5s) — homepage matches visual baseline @smoke`

**D-28 invariant (scoring data unchanged):**
```
$ git diff --quiet HEAD analysis/homepage/results/  # exit 0
$ git diff --quiet HEAD lib/scoring.ts              # exit 0
```

**Type check:** `npx tsc --noEmit` clean.

**Legacy token audit:**
```
$ grep -c 'var(--bg2)\|var(--bg3)\|var(--bg)\b' app/globals.css
0  # consumer refs all rebound; only --bg1 (legacy alias for .login-input) remains by design
```

## Self-Check: PASSED

- File `app/MatrixIsland.tsx` — FOUND
- File `app/MatrixIsland.module.css` — FOUND
- File `app/page.tsx` (Server shell, 36 LOC) — FOUND
- File `tests/visual/homepage.spec.ts-snapshots/homepage-1440x900-win32.png` — FOUND
- Commit `25b2d13` (Task 04-01) — FOUND
- Commit `85295ef` (Task 04-02) — FOUND
- Commit `b0f4d8a` (Task 04-03) — FOUND
- Commit `070de0b` (Task 04-04) — FOUND
- Commit `1a0a60b` (Task 04-05) — FOUND
- Commit `807153d` (Task 04-06) — FOUND
- `npx next build` — PASSED
- `npm test` — 90/90 PASSED
- `npx playwright test` — 1/1 PASSED
- D-28 invariant — PASSED
