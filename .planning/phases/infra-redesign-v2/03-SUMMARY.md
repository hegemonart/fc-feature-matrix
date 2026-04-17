---
phase: infra-redesign-v2
plan: 03
subsystem: infra
tags: [matrix-components, hover-tooltip, portal, column-selection, react-hooks, vitest, fake-timers, accessibility]

# Dependency graph
requires:
  - phase: infra-redesign-v2
    plan: 01
    provides: design tokens (--bg-cell, --bg-hover, --border, --accent, --column-tint, --text, --muted), .mono-caption helper, jsdom env
  - phase: infra-redesign-v2
    plan: 02
    provides: app/components/matrix/types.ts contract (extended additively here), <DataCell> with data-feature/-club hooks, tests/setup-rtl.ts global cleanup, vitest jsdom + setupFiles wiring
provides:
  - <HoverTooltipCard> portaled to document.body via createPortal — anchored to cell.getBoundingClientRect() (NOT cursor, per RESEARCH P8 behavioral change)
  - useHoverTooltip hook — owns tooltipData, exposes handleCellEnter / handleCellLeave / clearTooltip with TOOLTIP_CLOSE_GRACE_MS = 100 grace period
  - useColumnSelection hook — owns selectedClubId, exposes toggle() (click-same-deselects per D-18) + isSelected()
  - app/components/matrix/types.ts extended (additively) with FeatureMeta, ClubMeta, CellScoring, TooltipData, HoverTooltipProps
  - Test scaffolding patterns: renderHook + vi.useFakeTimers() for grace-period assertions, custom getBoundingClientRect mock helper for jsdom
affects: [infra-redesign-v2-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "react-dom createPortal(node, document.body) for tooltip — escapes any matrix overflow:hidden (D-16)"
    - "Anchor-based positioning from el.getBoundingClientRect() captured at mouseenter — replaces legacy cursor-follow (RESEARCH P8)"
    - "useRef<NodeJS.Timeout>-pattern for cancellable setTimeout in custom hooks"
    - "renderHook + vi.useFakeTimers + vi.advanceTimersByTime for deterministic timing tests (no real setTimeout in tests)"
    - "Custom DOMRect helper (makeCell / makeRect) for jsdom which doesn't compute real layout"
    - "Defensive lookup-or-null on tooltip content maps so missing data renders silently rather than crashing"

key-files:
  created:
    - app/components/matrix/HoverTooltipCard.tsx
    - app/components/matrix/HoverTooltipCard.module.css
    - app/components/matrix/useHoverTooltip.ts
    - app/components/matrix/useColumnSelection.ts
    - tests/components/HoverTooltipCard.test.tsx
    - tests/components/useHoverTooltip.test.tsx
    - tests/components/useColumnSelection.test.tsx
    - .planning/phases/infra-redesign-v2/03-SUMMARY.md
  modified:
    - app/components/matrix/types.ts (additive: FeatureMeta, ClubMeta, CellScoring, TooltipData, HoverTooltipProps)
    - CHANGELOG.md (v7.2 entry)

key-decisions:
  - "Tooltip content sourced from in-memory Map<string, *> props — no server requests on hover (D-21). scoring map keyed by '${clubId}:${featureId}' for O(1) lookup."
  - "Defensive lookup: when feature/club/score lookup misses, render nothing rather than a broken card. Plan 04 should guarantee map completeness; the fallback prevents jsdom test fragility and production crashes from late data."
  - "Math.abs() applied to score.no in render — features.ts stores weightNo as a signed negative (e.g. -3); the '−' glyph in the template provides the visual sign. Avoids 'No −-3' display bug. (Rule 1 deviation, fold-in commit.)"
  - "Bumped CHANGELOG to v7.2 (not v6.2 as the plan literal said) — same sequencing logic as plan 02. Baseline was v7.1 after plan 02."
  - "useColumnSelection.toggle uses functional setState ((curr) => curr === id ? null : id) instead of reading selectedClubId from closure — guarantees correctness under React 18 batched updates and avoids stale-closure bugs."
  - "Portal target read at render time with typeof document !== 'undefined' guard — keeps the component SSR-safe so plan 04's Server-Component-shell + Client-island split (D-17) works without extra dynamic imports."

patterns-established:
  - "useRef + useCallback + useEffect cleanup is the canonical timer-owning hook pattern in this codebase — useHoverTooltip is the reference"
  - "Test fixture helpers (makeCell, makeRect) live inline in spec files for now; if reused across plan 04 tests, promote to tests/helpers/dom.ts"
  - "Component data contracts use Map<string, T> for O(1) lookup over arrays — avoids O(n) Array.find() in render hot path"

requirements-completed: [D-03, D-16, D-18, D-21]

# Metrics
duration: ~6min
completed: 2026-04-17
---

# Phase infra-redesign-v2 Plan 03: HoverTooltipCard + Column-Selection State Summary

**Cross-cell interactivity layer shipped: portaled `<HoverTooltipCard>` (createPortal to document.body, anchored from `cell.getBoundingClientRect()` — NOT cursor, per RESEARCH P8) plus `useHoverTooltip` (100ms close grace, cancel-on-reenter) and `useColumnSelection` (D-18 click-toggle deselect) hooks. 15 new Vitest specs (90/90 total green), build clean, D-28 invariant intact.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-04-17T04:40:31Z
- **Completed:** 2026-04-17T04:46:30Z
- **Tasks:** 8/8
- **Tests:** 90 total (75 baseline + 15 new across 3 spec files)
- **Files created:** 8 (4 source + 3 spec + 1 SUMMARY)
- **Files modified:** 2 (types.ts additive extension, CHANGELOG.md v7.2 entry)

## Accomplishments

- **`app/components/matrix/types.ts` extended (additive only)** — `FeatureMeta`, `ClubMeta`, `CellScoring`, `TooltipData`, `HoverTooltipProps`. Plan 02 contracts untouched. `TooltipData` carries the captured `anchorRect: DOMRect`. `scoring: Map<string, CellScoring>` keyed by `${clubId}:${featureId}` for O(1) lookup.
- **`<HoverTooltipCard>`** — `createPortal(node, document.body)` per D-16 escapes any matrix `overflow: hidden`. Position computed from `anchorRect.bottom + 8` / `anchorRect.left` (RESEARCH P8 — anchored to cell, NOT cursor; behavioral change from legacy `cell-tooltip`). Right-edge viewport-clamp keeps wide-right cells visible. Card chrome uses plan 01 tokens (`--bg-cell` / `--border` / `--text` / `--muted` / `--accent`). 120ms ease-out fade-in. SSR-safe with `typeof document` guard. `role="tooltip"` + `data-testid="hover-tooltip-card"` for spec assertions.
- **`useHoverTooltip` hook** — owns `tooltipData` state. `handleCellEnter(featureId, clubId, el)` cancels pending close, captures `el.getBoundingClientRect()`, sets state. `handleCellLeave()` schedules `setTooltipData(null)` after `TOOLTIP_CLOSE_GRACE_MS = 100ms` via `setTimeout` stored in a `useRef`. `clearTooltip()` for synchronous unmount/external clears. `useEffect` cleanup so stray timers don't fire on unmounted components (avoids React state-on-unmounted warnings).
- **`useColumnSelection` hook** — owns `selectedClubId: string | null` (D-18). `toggle(clubId)` uses functional setState `(curr) => curr === clubId ? null : clubId` for click-same-deselects semantics under React 18 batched updates. `isSelected(clubId)` returns boolean. Initial value override supported (`useColumnSelection('psg')`). No CSS — visual rendering is owned by `<DataCell selected={...}>` from plan 02 plus `--column-tint` from plan 01.
- **3 spec files added (15 tests)**:
  - `HoverTooltipCard.test.tsx` (6) — null-data renders nothing; portal target is `document.body`; `top = rect.bottom + 8` / `left = rect.left`; right-edge clamp; full content (club name + description + TIER:B + Yes +6 / No −3); defensive missing-feature renders nothing
  - `useHoverTooltip.test.tsx` (4) — `vi.useFakeTimers()` based: immediate enter; 99ms keeps / 101ms clears; cancel-on-reenter; clearTooltip cancels pending
  - `useColumnSelection.test.tsx` (5) — initial null; toggle sets; toggle-same deselects; toggle-other switches; initial-value override
- **All gates green:** `npm test` shows 15/15 spec files / 90/90 tests pass; `npx next build` compiles clean; `git diff --quiet HEAD analysis/homepage/results/` returns clean (D-28 invariant verified).

## Task Commits

1. **Task 03-01: types.ts contracts (additive)** — `553ac3d` (feat)
2. **Task 03-02: <HoverTooltipCard> portaled** — `fd214cc` (feat)
3. **Task 03-03: useHoverTooltip 100ms grace** — `6c87d3d` (feat)
4. **Task 03-04: useColumnSelection toggle** — `74bb949` (feat)
5. **Task 03-05: HoverTooltipCard specs (+ Math.abs fix folded in)** — `f58fc9d` (test)
6. **Task 03-06: useHoverTooltip specs (fake timers)** — `9fadec1` (test)
7. **Task 03-07: useColumnSelection specs** — `4d92577` (test)
8. **Task 03-08: changelog v7.2 + plan close** — `8227cf8` (docs)

**Plan metadata:** (created after this SUMMARY)

## Files Created/Modified

### Created (8)

**Source (4)** — `app/components/matrix/`:
- `HoverTooltipCard.tsx` (~95 lines)
- `HoverTooltipCard.module.css` (~80 lines)
- `useHoverTooltip.ts` (~88 lines)
- `useColumnSelection.ts` (~43 lines)

**Tests (3)** — `tests/components/`:
- `HoverTooltipCard.test.tsx` (6 tests)
- `useHoverTooltip.test.tsx` (4 tests, fake timers)
- `useColumnSelection.test.tsx` (5 tests)

**Other (1)**:
- `.planning/phases/infra-redesign-v2/03-SUMMARY.md` — this file

### Modified (2)

- `app/components/matrix/types.ts` — appended `FeatureMeta`, `ClubMeta`, `CellScoring`, `TooltipData`, `HoverTooltipProps` (additive — plan 02 contracts intact)
- `CHANGELOG.md` — v7.2 entry at top (under 300 chars)

## Decisions Made

- **In-memory Map<string, T> for content lookup, not on-hover fetch.** D-21 explicitly forbids server requests on hover. Maps are passed as props from the parent (matrix island in plan 04) which already loads scores + features + clubs server-side. `scoring` is keyed `${clubId}:${featureId}` for O(1); `features` and `clubs` keyed by id. Avoids the 33×58 = 1914 cell-render Array.find() cost.
- **Defensive lookup-misses render nothing.** If any of `feature`/`club`/`score` lookup returns undefined, the card returns null (no portal). Two reasons: (a) jsdom tests can deliberately omit fixtures to assert the "missing" path without crashing the test runner, (b) production resilience — if plan 04 ever ships incomplete maps, the worst case is no tooltip rather than a TypeError.
- **`Math.abs()` on signed score values in render template.** `analysis/homepage/features.ts` stores `weightNo` as a signed negative integer (`-3`, `-1`, etc.). The template `Yes +N / No −N` provides the visual sign with the `+` and `−` glyphs. Without `Math.abs()`, the rendered output was `No −-3`. This is a Rule 1 (Bug) auto-fix — folded into the test commit (`f58fc9d`) since the test exposed it.
- **CHANGELOG bumped to v7.2, not v6.2 as plan literal said.** Plan 03 was written assuming the project was at v6.x; plan 02 already bumped to v7.1 (continuing the v7.0 baseline from plan 01). Continuing the sequence as v7.2 (minor — interactivity hooks don't change rubric or data model, fits CLAUDE.md classification of minor). Documented for traceability.
- **Functional setState in `useColumnSelection.toggle`.** `setSelectedClubId((curr) => curr === clubId ? null : clubId)` — not `setSelectedClubId(selectedClubId === clubId ? null : clubId)`. The functional form guarantees correctness under React 18 batched updates and prevents a stale-closure bug if `toggle` is called twice in quick succession.
- **Portal target guarded with `typeof document !== 'undefined'`.** Keeps `<HoverTooltipCard>` SSR-safe so plan 04's Server-Component-shell + Client-Component-island split (D-17) works without `dynamic(import, { ssr: false })` ceremony. The Server pass renders `null`, the Client pass mounts the portal — no hydration mismatch because Server output (`null`) and Client output (portal-into-body) are siblings, not children.
- **`Map<string, T>` over `Record<string, T>` in props.** Maps preserve key-existence semantics and have a clean `.get()`/`.has()` API. They also signal "lookup table" to readers. Negligible perf difference at 33-club / 58-feature scale.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `Math.abs()` on signed score values to avoid 'No −-3' rendering**
- **Found during:** Task 03-05 (HoverTooltipCard tests)
- **Issue:** `analysis/homepage/features.ts` stores `weightNo` as a signed negative integer (e.g. `-3`). The template `No −{score.no}` rendered as `No −-3` because the `−` glyph provided one minus sign and the negative value provided another.
- **Fix:** Wrapped both score values in `Math.abs()` in the render template — `Yes +{Math.abs(score.yes)}` / `No −{Math.abs(score.no)}`. The visual sign now lives entirely in the literal `+` and `−` characters, decoupled from the storage sign convention.
- **Files modified:** `app/components/matrix/HoverTooltipCard.tsx`
- **Verification:** Test `renders club name, feature description, TIER badge, and score breakdown` now passes — confirmed `No −3` matches the expected pattern. All 6 spec assertions green.
- **Committed in:** `f58fc9d` (folded into the task 03-05 test commit since the test surfaced the bug).

**Total deviations:** 1 auto-fixed (1 bug).
**Impact on plan:** Single-line fix, no scope creep, no architectural change. Plan executed otherwise exactly as written.

## Authentication Gates

None. Plan stayed entirely at the component/hook layer — no DB, no API routes, no external service calls.

## Issues Encountered

- **CHANGELOG version mismatch.** Plan literal said v6.2; project was at v7.1 (plan 02). Bumped to v7.2 (minor) to keep sequencing — same logic plan 02 used. Documented in Decisions Made.
- **CRLF/LF warnings on commit.** Git autocrlf normalized line endings on the new TS/TSX/CSS files. Cosmetic; no behavioral impact.
- **Workspace-root warning during `npx next build`.** Multiple lockfiles (parent repo + worktree) — known issue from plan 01, untouched.

## User Setup Required

None. No new dependencies, no env vars, no external services. All hooks + components run in the existing Vitest jsdom env wired by plan 02.

## Next Phase Readiness

- **Plan 04 (`app/page.tsx` refactor)** can now:
  - Import `<HoverTooltipCard>`, `useHoverTooltip`, `useColumnSelection` from `app/components/matrix/`
  - Build the in-memory `features: Map<string, FeatureMeta>`, `clubs: Map<string, ClubMeta>`, `scoring: Map<string, CellScoring>` server-side and pass them to `<HoverTooltipCard>`
  - Wire `<DataCell>` props as: `onMouseEnter={(e) => handleCellEnter(featureId, clubId, e.currentTarget)}` / `onMouseLeave={handleCellLeave}` / `onFocus={(e) => handleCellEnter(featureId, clubId, e.currentTarget)}` (D-21 a11y — focus mirrors hover)
  - Wire `<DataCell selected={isSelected(clubId)}>` for every cell in the active column
  - Wire column-header click → `toggle(clubId)` for selection plumbing
- **D-28 invariant verified:** `git diff --quiet HEAD analysis/homepage/results/` returns clean. Zero scoring data touched.
- **D-29 a11y readiness:** Both hooks support keyboard parity — `handleCellEnter` is invoked from both `onMouseEnter` and `onFocus` in plan 04, and the tooltip's `role="tooltip"` is correctly anchored to the focused cell via the captured rect.

## Self-Check: PASSED

- All 8 created files exist on disk:
  - `app/components/matrix/HoverTooltipCard.tsx` — FOUND
  - `app/components/matrix/HoverTooltipCard.module.css` — FOUND
  - `app/components/matrix/useHoverTooltip.ts` — FOUND
  - `app/components/matrix/useColumnSelection.ts` — FOUND
  - `tests/components/HoverTooltipCard.test.tsx` — FOUND
  - `tests/components/useHoverTooltip.test.tsx` — FOUND
  - `tests/components/useColumnSelection.test.tsx` — FOUND
  - `.planning/phases/infra-redesign-v2/03-SUMMARY.md` — FOUND (this file)
- All 8 task commits exist in `git log --oneline`: 553ac3d, fd214cc, 6c87d3d, 74bb949, f58fc9d, 9fadec1, 4d92577, 8227cf8.
- `npm test`: 15 files / 90 tests pass (75 baseline + 15 new).
- `npx next build`: passes (clean compile, all 33 club static pages built).
- D-28 invariant verified: `git diff --quiet HEAD analysis/homepage/results/` returns clean.
- `app/components/matrix/types.ts` extension is additive only — `DataCellProps`, `SortHeaderProps`, `MeterRowProps`, `HeaderBarProps`, `TopNavProps`, `CategoryFilterProps`, `TypeFilterProps` all unchanged.
- Portal target proven via test: `document.body.contains(screen.getByRole('tooltip'))` returns true.
- 100ms grace + cancel-on-reenter both proven via `vi.advanceTimersByTime` assertions.
- `useColumnSelection.toggle(sameId)` proven to deselect (D-18 contract).

---
*Phase: infra-redesign-v2*
*Completed: 2026-04-17*
