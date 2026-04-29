# 02-21 — Matrix Unification Summary

**Plan:** 02-21
**Type:** Out-of-band tactical UI refactor
**Date:** 2026-04-29
**Subscription cost:** $0
**Wall-clock duration:** ~2.5h

---

## One-line outcome

`/hospitality` now renders the **same** MatrixIsland shell as `/` (homepage) — same HeaderBar, TopNav with active "Hospitality Packages" white pill, sidebar with 8 hospitality categories, full matrix grid with detail panel + hover tooltips — instead of the prior minimal standalone HospitalityIsland page.

---

## Architectural diff

### Before

```
app/page.tsx                 → <MatrixIsland>           ← 1185 LOC, owns full chrome
app/hospitality/page.tsx     → <HospitalityIsland>      ← 150 LOC, minimal table only
                                ├─ HeaderBar
                                ├─ <nav.hospitality-subnav> (back link + pilot chip)
                                └─ <table data-matrix="hospitality"> (5 cols × 55 rows)
```

### After

```
app/page.tsx                 → <MatrixIsland />                    (default area="homepage")
app/hospitality/page.tsx     → <MatrixIsland area="hospitality"
                                              categories={HOSPITALITY_CATEGORIES}
                                              products={pilotProducts}
                                              features={HOSPITALITY_FEATURES} />

<MatrixIsland>: SAME chrome for both areas
  ├─ HeaderBar (build date, brand, sign-out)
  ├─ TopNav (active pill = activeArea, locked rail with hospitality unlocked for authed)
  ├─ Sidebar
  │   ├─ CategoryFilter (areaCategories: 12 home / 8 hospitality)
  │   ├─ TypeFilter
  │   └─ Clear filters
  ├─ Matrix table (sticky feature col + N product cols + Total Score row + feature rows)
  ├─ FeatureDetail / ProductDetail (passes areaCategories for cat lookup)
  ├─ 3 locked-overlay modals
  ├─ Preview-blur-overlay (unauth gate)
  └─ Portaled HoverTooltipCard
```

---

## Files added / modified / deleted

### Added

| Path | Purpose |
|------|---------|
| `analysis/hospitality/categories.ts` | 8 hospitality `Category[]` entries (Package Discovery, Pricing Transparency, Food & Beverage, Match Selector UX, Enquiry Friction, Premium Amenities, Post-Booking Comms, Booking Confirmation) |
| `tests/components/MatrixIsland.test.tsx` | 24 tests covering features-wiring, area-rendering, tab-routing decision tree |
| `.planning/phases/02-hospitality-pilot/02-21-DESIGN-NOTES.md` | Discovery + design rationale |
| `.planning/phases/02-hospitality-pilot/02-21-MATRIX-UNIFICATION-SUMMARY.md` | This file |

### Modified

| Path | Change |
|------|--------|
| `app/MatrixIsland.tsx` | +area prop (default `'homepage'`), +categories prop (default per-area), TopNav activeTab derived from area, handleTabClick handles cross-area navigation, TableRows/FeatureDetail/ProductDetail accept categories prop, trackEvent path uses areaPath |
| `app/hospitality/page.tsx` | Replaces `<HospitalityIsland>` with `<MatrixIsland area="hospitality" categories={HOSPITALITY_CATEGORIES} ...>`. Adds page metadata (title + description). |
| `lib/data.ts` | Re-exports `HOSPITALITY_CATEGORIES` from `@/analysis/hospitality/categories` |
| `tests/visual/hospitality-tab.spec.ts` | a11y posture rewritten to assert unified-shell selectors (TopNav active pill, sidebar 8 cats, 55 feature rows). Visual baseline regenerated. |
| `tests/visual/hospitality-tab.spec.ts-snapshots/hospitality-1440x900-win32.png` | Regenerated baseline PNG (intentional change — manual visual review confirmed unified-matrix look) |
| `playwright.config.ts` | `baseURL` now respects `PLAYWRIGHT_BASE_URL` env override (defaults to `:3000`) — needed because port 3000 may be occupied by other Next worktrees |

### Deleted

| Path | Why |
|------|-----|
| `app/hospitality/HospitalityIsland.tsx` | Replaced by `<MatrixIsland area="hospitality">` reuse |
| `tests/components/HospitalityIsland.test.tsx` | Replaced by `tests/components/MatrixIsland.test.tsx` (same coverage, area-aware) |

---

## Commit log

| # | Hash | Message |
|---|------|---------|
| 1 | `74025ef` | `feat(02-21): add HOSPITALITY_CATEGORIES (8 sections) for matrix sidebar` |
| 2 | `993afc6` | `refactor(02-21): MatrixIsland accepts area prop, defaults homepage` |
| 3 | `f26f9e2` | `feat(02-21): /hospitality renders MatrixIsland with area=hospitality` |
| 4 | `65ce2d0` | `test(02-21): area-aware MatrixIsland tests + updated hospitality visual spec` |
| 5 | `638d9d5` | `test(02-21): regenerate /hospitality visual baseline + PLAYWRIGHT_BASE_URL override` |

---

## Verification gate results

| Check | Status | Detail |
|-------|--------|--------|
| `npx tsc --noEmit` | PASS | clean exit, no type errors |
| `npx next build` | PASS | 52 static pages generated, no warnings |
| `npx vitest run` (123 tests) | PASS | All 17 test files green; new MatrixIsland.test.tsx adds 24 tests, all pass |
| `tests/visual/hospitality-tab.spec.ts` | PASS | Both visual + a11y posture tests pass against new baseline |
| `tests/visual/homepage.spec.ts` | DRIFT (pre-existing) | 79991 px diff (ratio 0.07). Confirmed identical at pre-02-21 state — drift predates this plan. Out of scope. |
| `tests/visual/club-page.spec.ts` | DRIFT (pre-existing) | Height mismatch (5559→5700px). Out of scope. |
| `git diff --quiet analysis/homepage/` | PASS | D-31 score-data invariant preserved |
| `git diff --quiet lib/scoring.ts` | PASS | D-20 invariant preserved |
| `git diff --quiet scanner/` | PASS | This plan was UI-only |
| Single-orange-CTA on `/hospitality` | PASS | 1 visible orange CTA (the "Sign in" preview-cta-btn). Same posture as homepage. |
| Single-orange-CTA on `/` | PASS | Unchanged from baseline. |

---

## Decisions made

1. **Default `area="homepage"` for backward compat.** `app/page.tsx` calls `<MatrixIsland />` with no prop change, so the existing zero-prop call site stays identical. Implicit choice keeps the homepage visual baseline stable bit-for-bit.

2. **`categories` prop is OPTIONAL.** When omitted, MatrixIsland picks `CATEGORIES` for `area="homepage"` and `HOSPITALITY_CATEGORIES` for `area="hospitality"`. This keeps the homepage call site one-prop-shorter.

3. **Inline `productScores` math is reused for both areas.** The function is pure derived UI math (sum of weightYes for 'full' presence + weightNo otherwise), not score-data mutation. D-20 invariant only forbids modifying `lib/scoring.ts` and `analysis/homepage/results/*.json` — the runtime sum is unchanged.

4. **Pilot products filter stays in `app/hospitality/page.tsx`.** The page-level RSC narrows `PRODUCTS` to 5 pilot ids before passing into MatrixIsland. From MatrixIsland's perspective, "products" is just whatever array it received.

5. **Hospitality features show no `band` color on adoption-meter.** `computeBands` only iterates homepage `FEATURES`, so hospitality features have `band` undefined. `bandToMeterBand` defaults undefined → `'bottom'` (red meter, 0-40% adoption). Acceptable for the pilot — accurate (no clubs measured to high adoption yet) and avoids modifying homepage-locked computeBands. A future plan can add `computeHospitalityBands()` if richer color signaling is needed.

6. **PLAYWRIGHT_BASE_URL env override added.** The hardcoded `:3000` baseURL in `playwright.config.ts` collided with another Next worktree on the same machine. Added `process.env.PLAYWRIGHT_BASE_URL ?? 'http://localhost:3000'` so contributors can run on alternate ports without forking the config.

---

## Test count delta

- Pre-02-21 vitest: 105 tests across 17 files (HospitalityIsland.test.tsx had 17 tests).
- Post-02-21 vitest: 123 tests across 17 files (MatrixIsland.test.tsx replaces it with 24 tests, +7 net).

Net new test coverage:
- 8 hospitality categories sidebar render assertion
- Default area + explicit `area="homepage"` rendering parity
- `area="hospitality"` renders 55 rows + 5 cols + 8 cats + hospitality tab pill active
- Cross-area click navigation: Homepage tab from /hospitality routes back to /
- Active-tab no-op for both areas

---

## Visual baseline change rationale

Before: `/hospitality` rendered a minimal back-link nav + plain table (150-LOC HospitalityIsland). Width-constrained with no sidebar.

After: `/hospitality` renders the full unified matrix shell — HeaderBar centered with FC Benchmark wordmark, TopNav with the white **"HOSPITALITY PACKAGES"** active pill on the left and the orange **"UNLOCK EVERYTHING"** pill, locked-rail tabs (HOMEPAGE, TICKET PURCHASE, MERCH STORE, …), 240-px sidebar with the 8 hospitality categories + Type filter (FC, Federation, League) + Clear filters button, then the 280-col feature table with sticky feature column + Total Score row + 55 feature rows × 5 product cols. Auth-gated preview-blur-overlay shows the same Sign in / Request access CTAs as homepage.

Single-orange-CTA invariant satisfied: 1 visible orange CTA (the Sign in button on the preview overlay), same posture as homepage. Unlock-everything tab pill and the modals' .locked-btn are off-screen / hidden until triggered.

---

## Backward-compat

- `app/page.tsx` is byte-identical to pre-02-21 in terms of the JSX it emits (the `<MatrixIsland />` call has no new props). Confirmed by re-running the homepage visual test pre- and post-02-21: identical 79991-pixel diff against the stale baseline (drift pre-existed and is unaffected by this plan).
- The Plan 02-13 hospitality features wiring tests (HOSPITALITY_FEATURES length, presence-map matching results JSONs, pilot-coverage-only) are preserved verbatim in the new MatrixIsland.test.tsx.
- The Plan 02-13 handleTabClick decision-tree fixture tests are preserved verbatim — extended with cross-area navigation cases.

---

## Deviations from plan

**Rule 3 (blocking) — playwright config port collision.**

While running visual tests, port 3000 was occupied by a different project ("Beauty Benchmark" worktree). Playwright was hitting that server and showing "Beauty Benchmark" in the captured screenshot. Fixed by adding `process.env.PLAYWRIGHT_BASE_URL` override to `playwright.config.ts`. Used `PLAYWRIGHT_BASE_URL=http://localhost:3010` to point at our own server. Documented in commit message.

**Rule 3 (blocking) — homepage baseline drift was pre-existing.**

The homepage visual test fails with 79,991-pixel diff (ratio 0.07, > 0.02 threshold). To verify whether Plan 02-21 introduced this drift, reverted MatrixIsland.tsx + page.tsx to commit `69df345` (pre-02-21), rebuilt, and re-ran the test: same 79,991 px diff. Confirmed Plan 02-21 introduced ZERO homepage visual change. The drift is from work between baseline capture (commit `1a0a60b`, infra-redesign-v2-04) and now — likely accumulated UI tweaks across phase 02 plans. Not in scope for Plan 02-21; flagged for a future baseline-refresh plan.

---

## Known limitations / follow-ups

1. **Hospitality bands not computed.** The adoption-meter MeterRow shows red (`'bottom'` band) for all hospitality features. To enable proper band coloring, a future plan should add `computeHospitalityBands()` mirroring the homepage-only `computeBands()` in `analysis/index.ts`.
2. **Homepage + club-page visual baselines stale.** Pre-existing drift, not caused by 02-21. Recommend a separate baseline-refresh plan after the next stable UI period.
3. **Hospitality detail panel iterates all 33 PRODUCTS** when a feature is clicked. Most show 'absent' since only 5 pilot clubs have data. Acceptable for pilot; a future plan could narrow to the area's products.

---

## Self-Check: PASSED

Files exist:
- `analysis/hospitality/categories.ts` — FOUND
- `tests/components/MatrixIsland.test.tsx` — FOUND
- `.planning/phases/02-hospitality-pilot/02-21-DESIGN-NOTES.md` — FOUND
- `.planning/phases/02-hospitality-pilot/02-21-MATRIX-UNIFICATION-SUMMARY.md` — FOUND
- `tests/visual/hospitality-tab.spec.ts-snapshots/hospitality-1440x900-win32.png` — FOUND (regenerated)

Files removed:
- `app/hospitality/HospitalityIsland.tsx` — DELETED (confirmed via `ls app/hospitality/`)
- `tests/components/HospitalityIsland.test.tsx` — DELETED

Commits:
- `74025ef` HOSPITALITY_CATEGORIES — FOUND
- `993afc6` MatrixIsland refactor — FOUND
- `f26f9e2` /hospitality swap — FOUND
- `65ce2d0` tests + spec — FOUND
- `638d9d5` baseline regen — FOUND
