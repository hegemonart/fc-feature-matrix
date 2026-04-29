---
phase: 02-hospitality-pilot
plan: 13
subsystem: app/hospitality + analysis/hospitality + lib/data
tags: [hospitality, ui, route, design-system, visual-regression, pilot]
dependency-graph:
  requires: [02-12 (results JSON)]
  provides: [/hospitality route, HOSPITALITY_FEATURES export, hospitality visual baseline]
  affects: [app/MatrixIsland.tsx handleTabClick, analysis/hospitality/features.ts buildPresence]
tech-stack:
  added: []
  patterns:
    - RSC → Client Island (mirrors infra-redesign-v2-04 homepage pattern)
    - Inline weighted-score tally in Server Component to preserve D-20 score invariant
    - Visual regression baseline via Playwright (mirrors homepage.spec.ts)
key-files:
  created:
    - app/hospitality/page.tsx
    - app/hospitality/HospitalityIsland.tsx
    - tests/components/HospitalityIsland.test.tsx
    - tests/visual/hospitality-tab.spec.ts
    - tests/visual/hospitality-tab.spec.ts-snapshots/hospitality-1440x900-win32.png
  modified:
    - analysis/hospitality/features.ts
    - lib/data.ts
    - app/MatrixIsland.tsx
    - app/globals.css
decisions:
  - "buildPresence keys PILOT_RESULTS by products.ts canonical IDs (man_city) not JSON product_id slugs (mancity) — products.ts is the canonical source"
  - "Inline weighted-score tally in app/hospitality/page.tsx — does NOT modify lib/scoring.ts (D-20 score invariant)"
  - "Hospitality stays in LOCKED_TABS array; only handleTabClick is special-cased — preserves unauthed locked-modal flow"
  - "Single-orange-CTA invariant: /hospitality has zero var(--accent) backgrounds in chrome. Back link is text-only/outlined"
  - "No axe-core dep added; a11y posture asserted via in-DOM Playwright assertions (semantic table, alt text, aria attributes)"
metrics:
  duration: ~30min
  completed: 2026-04-28
---

# Phase 02 Plan 13: Hospitality Packages UI tab unlock Summary

Unlocked the Hospitality Packages tab end-to-end for authenticated users by wiring `analysis/hospitality/features.ts buildPresence()` to the 5 pilot result JSONs (Plan 02-12 outputs), creating a `/hospitality` Server Component + Client island that renders the 5-club × 55-feature matrix with an explicit "Pilot: 5 clubs" mono-caption chip, and special-casing the LOCKED_TABS click handler so authed users (signed-in / premium / admin) navigate to `/hospitality` while unauthed users still see the locked modal — all while preserving the single-orange-CTA, design-token, type-stack, and score-data invariants from CLAUDE.md.

## Outcomes

- **/hospitality route**: Server Component (`app/hospitality/page.tsx`) loads `HOSPITALITY_FEATURES` + filters PRODUCTS to 5 pilot clubs (Man City, Tottenham, Real Madrid, PSG, Chelsea), pre-computes weighted scores INLINE (does NOT call `lib/scoring.getProductScores` — that's hardcoded to homepage `FEATURES`; D-20 forbids modifying it), and passes serializable props to `<HospitalityIsland>`.
- **Client island** (`app/hospitality/HospitalityIsland.tsx`): renders semantic `<table>` with sticky feature col + 5 product cols + 55 feature rows. Each cell exposes `data-feature` / `data-club` / `data-present` attributes for testability. Score row formats positive (`+12`) and negative (`-79`) inline. Header strip contains `<HeaderBar>` (reused) + a `<nav>` strip with text-only "Back to homepage matrix" link (NOT orange) and the `mono-caption` "Pilot: 5 clubs" chip on the right.
- **`buildPresence()` rewire** (`analysis/hospitality/features.ts`): replaced placeholder always-absent stub with 5 JSON imports + `PILOT_RESULTS` map keyed by products.ts canonical IDs (`man_city`, `tottenham`, `real_madrid`, `psg`, `chelsea`). Mirrors the homepage features.ts pattern. Non-pilot product IDs stay 'absent' until Phase 2.5 expands coverage.
- **`HOSPITALITY_FEATURES` re-export** (`lib/data.ts`): adds `export { FEATURES as HOSPITALITY_FEATURES } from '@/analysis/hospitality/features';`. Homepage `FEATURES` export untouched (D-20 score invariant).
- **MatrixIsland tab routing** (`app/MatrixIsland.tsx`): `handleTabClick` special-cases `tabId === 'hospitality'` BEFORE the existing `isAdmin / isPremium / authed` branches: any authed tier navigates to `/hospitality` via `router.push`. Unauthed users fall through to the existing locked-modal path (preserves preview-mode UX exactly). Adds `useRouter` import from `next/navigation`. LOCKED_TABS array unchanged.
- **Hospitality CSS** (`app/globals.css`): hospitality-* styles use ONLY design tokens (`--bg-page`, `--bg-cell`, `--border`, `--text`, `--muted`, font CSS vars). Zero hex literals in chrome. Zero `var(--accent)` background elements (single-orange-CTA invariant intact).
- **Test coverage** (`tests/components/HospitalityIsland.test.tsx`, 19 tests):
  - 7 features-wiring tests: HOSPITALITY_FEATURES length 55, HP01..HP55 IDs, buildPresence reads pilot JSONs, sanity at-least-one-full check, non-pilot products stay absent
  - 6 island-render tests: Pilot:5-clubs chip, 5 cols + 55 rows, back-link non-orange, single-orange-CTA invariant (≤1 .locked-btn), data-present cell attributes, Total Score row formatting
  - 6 handleTabClick decision-tree tests: authed/premium/admin → /hospitality; unauthed → locked modal; non-hospitality LOCKED_TABS clicks unchanged for all auth tiers
- **Visual baseline + a11y** (`tests/visual/hospitality-tab.spec.ts`, 2 specs):
  - visual: full-page screenshot at 1440×900, animations: 'disabled', `waitForFunction(fonts.ready)`, `maxDiffPixelRatio: 0.02` (config), masks `[data-build-date]`. Baseline PNG captured at `tests/visual/hospitality-tab.spec.ts-snapshots/hospitality-1440x900-win32.png` (62 KB).
  - a11y posture: in-DOM assertions on Pilot:5-clubs label, back-link href + non-orange invariant, single-orange-CTA invariant, semantic `<table>`, 6 thead cols + 55 tbody rows, 5 logo `alt` texts. No axe-core dep added (avoids architectural Rule 4 escalation).

## Verification gates

| Gate                                       | Result |
|--------------------------------------------|--------|
| `npx tsc --noEmit`                         | PASS (no output) |
| `npx next build`                           | PASS (`/hospitality` static prerender) |
| `npx vitest run` (full suite)              | PASS (17 files, 118 tests) |
| `npx playwright test tests/visual/hospitality-tab.spec.ts` | PASS (2/2) |
| `git diff --quiet analysis/homepage/`      | exit 0 — D-20 intact |
| `git diff --quiet lib/scoring.ts`          | exit 0 — score invariant intact |
| Single-orange-CTA invariant                | PASS — zero `.locked-btn` on /hospitality (≤ 1) |

## Pilot subset

| Pilot Club  | products.ts ID | results JSON ID | Total Score (computed) |
|-------------|----------------|-----------------|------------------------|
| Real Madrid | real_madrid    | realmadrid      | -92  |
| PSG         | psg            | psg             | -125 |
| Man City    | man_city       | mancity         | -99  |
| Tottenham   | tottenham      | tottenham       | -57  |
| Chelsea     | chelsea        | chelsea         | -79  |

Other 28 clubs in PRODUCTS render with all-absent presence (pilot-coverage-only). Phase 2.5 will expand coverage.

## Commits

| Hash    | Message |
|---------|---------|
| d1ef3c9 | feat(02-13): wire hospitality buildPresence to pilot result JSONs |
| 8db6e0e | feat(02-13): export HOSPITALITY_FEATURES from lib/data.ts |
| d47e217 | test(02-13): hospitality features wiring + HOSPITALITY_FEATURES export |
| 0a3b05e | feat(02-13): /hospitality route — Server Component + Client island |
| 69df345 | feat(02-13): MatrixIsland routes hospitality tab to /hospitality for authed users |
| c51f447 | test(02-13): HospitalityIsland render + handleTabClick decision-tree |
| 7e2f64b | test(02-13): visual baseline + a11y posture for /hospitality |

## Deviations from Plan

None functional. Two minor pragmatic notes:

1. **a11y check uses Playwright DOM assertions, not axe-core.** The plan suggested axe-playwright but that's not in `package.json` deps, and adding it would be a Rule 4 architectural change (new dependency). Instead, the spec asserts the equivalent posture directly: semantic table, alt text on logos, aria-labelled nav, single-orange-CTA invariant. If axe-core is desired later, install `@axe-core/playwright` and extend the spec — the existing structure is compatible.
2. **Inline weighted-score tally instead of refactoring `lib/scoring.ts`.** Plan called this out as the safe path; chose it explicitly to keep the D-20 / score-data invariant green. `git diff --quiet lib/scoring.ts` exits 0.

## Authentication gates

None hit during execution. Hospitality unlock is purely client-side gating via the existing auth state in MatrixIsland.

## Threat Flags

None — no new network endpoints, no auth paths, no schema changes. Existing trust boundaries preserved: hospitality tab special-cased only for authed tiers (`authed || isPremium || isAdmin`), unauthed users still see the locked modal (T-13-03 mitigation as planned).

## Subscription cost

$0 — UI-only work. No third-party services touched.

## Self-Check: PASSED

- FOUND: app/hospitality/page.tsx
- FOUND: app/hospitality/HospitalityIsland.tsx
- FOUND: tests/components/HospitalityIsland.test.tsx
- FOUND: tests/visual/hospitality-tab.spec.ts
- FOUND: tests/visual/hospitality-tab.spec.ts-snapshots/hospitality-1440x900-win32.png
- FOUND: commits d1ef3c9, 8db6e0e, d47e217, 0a3b05e, 69df345, c51f447, 7e2f64b
- VERIFIED: D-20 invariant (analysis/homepage/ untouched)
- VERIFIED: score invariant (lib/scoring.ts untouched)
- VERIFIED: 118/118 vitest, 2/2 playwright visual, npx tsc --noEmit clean, npx next build clean
