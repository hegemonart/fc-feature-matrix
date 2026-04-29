# 02-21 — Matrix Unification Design Notes

**Date:** 2026-04-29
**Plan:** 02-21
**Type:** Out-of-band tactical UI refactor
**Scope:** Make `/hospitality` render the same matrix shell as `/`, just with hospitality data + 8 hospitality categories + active-tab highlight on the Hospitality pill.

---

## 1. Current Architecture (Discovery Output)

### `/` (homepage)

- `app/page.tsx` — RSC shell. Pre-computes `scores` via `getProductScores` from `lib/scoring.ts`, passes `PRODUCTS` + `FEATURES` + `scores` + `buildDate` into `<MatrixIsland />`.
- `app/MatrixIsland.tsx` — 1185-LOC client island. Owns:
  - HeaderBar (with auth controls)
  - TopNav (with active tab `"home"`, `lockedTabs = LOCKED_TABS.map(t => t.id)`, `unlockTab="unlock"`)
  - Sidebar with `<CategoryFilter>` + `<TypeFilter>` + Clear filters button
  - Table wrapper containing `<thead>` (col header + Total Score row) + `<tbody>` of `<TableRows>` (memoized component)
  - Detail panel (FeatureDetail / ProductDetail)
  - Three locked modals (locked, login, coming-soon)
  - Portaled HoverTooltipCard

  All chrome is data-driven from `features` + `products` props except for:
  - `LOCKED_TABS` — hardcoded module-level constant (8 entries; includes `hospitality`)
  - `CATEGORIES` — imported from `@/lib/data` (but currently homepage-only — see §3 below)
  - `handleTabClick` — has special branch for `tabId === 'hospitality'` routing authed users to `/hospitality`

### `/hospitality` (current)

- `app/hospitality/page.tsx` — RSC shell. Filters `PRODUCTS` to 5 pilot ids, computes `scores` inline (does NOT call `getProductScores` since that's homepage-FEATURES-locked, D-20 invariant), passes into `<HospitalityIsland />`.
- `app/hospitality/HospitalityIsland.tsx` — 150-LOC client island. Renders:
  - `<HeaderBar />`
  - `<nav.hospitality-subnav>` with "Back to homepage matrix" link + "Pilot: 5 clubs" mono-caption
  - Plain `<table data-matrix="hospitality">` with feature col + 5 club cols + 55 feature rows
  - No sidebar, no top-nav, no tooltip, no detail panel.

This page intentionally diverged from the matrix shell — Plan 02-13 shipped it as a minimal pilot view. The scope of 02-21 is to undo that divergence: reuse `<MatrixIsland>` itself.

### Data layer

- `lib/data.ts` re-exports `PRODUCTS`, `FEATURES`, `CATEGORIES`, `BAND_META`, types, and `HOSPITALITY_FEATURES` (Plan 02-13).
- `analysis/index.ts` only exports `CATEGORIES` from `analysis/homepage/categories.ts`. **No hospitality categories exist as `Category[]` objects yet**, even though all 8 `CategoryId` values are declared in `analysis/types.ts`.
- `analysis/hospitality/features.ts` references `'package_discovery'`, `'pricing_transparency'`, `'food_beverage'`, `'match_selector_ux'`, `'enquiry_friction'`, `'premium_amenities'`, `'post_booking_comms'`, `'booking_confirmation'` — 8 distinct CategoryIds.
- `bandToMeterBand`, `computeBands`, `BAND_META` — homepage-features-driven; hospitality features have `band` undefined (computeBands only iterates homepage `FEATURES`).

---

## 2. Target Architecture

### `<MatrixIsland>` becomes area-aware

Add prop:

```ts
export interface MatrixIslandProps {
  area?: 'homepage' | 'hospitality';   // default 'homepage'
  products: Product[];
  features: Feature[];
  scores: Record<string, number>;
  buildDate: string;
  /** Optional: subset of CATEGORIES applicable for this area's features. */
  categories?: { id: CategoryId; name: string; color: string }[];
}
```

Internal changes:

- Active tab in `<TopNav>` is derived from `area`:
  - `area === 'homepage'` → `activeTab = 'home'`
  - `area === 'hospitality'` → `activeTab = 'hospitality'`
- `lockedTabs` are computed by removing the active-area's tab id from `LOCKED_TABS.map(t => t.id)` PLUS removing `'hospitality'` for any authed/premium/admin user (since they can navigate there).
- `handleTabClick`:
  - If clicked id matches current `area`, no-op (preserves homepage behavior).
  - If id is `'home'`, route to `/`.
  - If id is `'hospitality'` and authed-tier user, route to `/hospitality`.
  - Otherwise, existing locked / coming-soon modal logic.
- `categoryItems` derivation now uses `categories` prop (if provided) — falls back to imported `CATEGORIES` for back-compat.
- `featureMap` / `clubMap` / `scoringMap` for tooltip — already pure-derived from `features` + `products` props; no change needed.
- `productScores` recompute — already pure-derived from `features` + `products` + `activeCat`; no change.
- `productAdoption / band` — bands come from `f.band` field set by `computeBands`. Hospitality features have `band` undefined, which the meter row handler defaults to `'bottom'` via `bandToMeterBand`. Acceptable for this plan; future cleanup can compute hospitality bands.
- Tracking call `trackEvent('page_view', { path: '/' })` becomes `trackEvent('page_view', { path: area === 'hospitality' ? '/hospitality' : '/' })`.
- Login form helper text — currently `"Access all {features.length} features across {products.length} products"` — derives from props so it auto-updates per area.

### Shell HTML structure (unchanged behaviour)

Keeps the existing `<div class="matrix-shell">` with:

```
HeaderBar
TopNav (active tab = area-dependent)
.main
  .sidebar (categories + types + clear)
  .table-wrapper
    .table-container
      <table>
        <thead>...</thead>
        <tbody><TableRows /></tbody>
      </table>
  .detail-panel
LOCKED_OVERLAY x3
HoverTooltipCard (portaled)
```

### `app/page.tsx`

Unchanged externally; just stays the homepage RSC. Optionally pass `area="homepage"` explicitly for clarity, but default works.

### `app/hospitality/page.tsx`

Replaces `<HospitalityIsland>` with `<MatrixIsland area="hospitality" ... />`.

- Continues to filter `PRODUCTS` to 5 pilot ids (or pass full `PRODUCTS` and let TypeFilter narrow — but pilot view should keep the explicit 5-club display per Plan 02-13's spec).
- Continues to compute `scores` inline (D-20 invariant).
- Passes `categories` prop pointing to a NEW hospitality categories module (see §3).

### `app/hospitality/HospitalityIsland.tsx`

Becomes a thin re-export / deprecation stub — keeps the symbol so existing tests don't immediately break, but the file is no longer used by `app/hospitality/page.tsx`. We will update tests instead and DELETE this file.

---

## 3. New Asset: `analysis/hospitality/categories.ts`

Currently no `Category[]` array exists for hospitality. The 8 hospitality CategoryIds are declared in `analysis/types.ts` but unused as Category objects. We need this file so `<CategoryFilter>` can render a sidebar list with names/colors.

```ts
export const HOSPITALITY_CATEGORIES: Category[] = [
  { id: 'package_discovery',    name: 'Package Discovery',     color: '#06b6d4' },
  { id: 'pricing_transparency', name: 'Pricing Transparency',  color: '#8b5cf6' },
  { id: 'food_beverage',        name: 'Food & Beverage',       color: '#22c55e' },
  { id: 'match_selector_ux',    name: 'Match Selector UX',     color: '#3b82f6' },
  { id: 'enquiry_friction',     name: 'Enquiry Friction',      color: '#ef4444' },
  { id: 'premium_amenities',    name: 'Premium Amenities',     color: '#f97316' },
  { id: 'post_booking_comms',   name: 'Post-Booking Comms',    color: '#ec4899' },
  { id: 'booking_confirmation', name: 'Booking Confirmation',  color: '#a855f7' },
];
```

Re-export from `lib/data.ts` as `HOSPITALITY_CATEGORIES`. Does NOT touch `analysis/homepage/` (D-31 invariant).

---

## 4. Backwards Compatibility & Invariants

- **D-20 / D-31 score invariant**: not violated. We do not modify `lib/scoring.ts`, `analysis/homepage/features.ts`, or any `analysis/homepage/results/*.json`. Hospitality scores are still computed inline in `app/hospitality/page.tsx`.
- **Single-orange-CTA**: MatrixIsland already has 0 `.locked-btn` in default render (only inside the modals which are hidden by default). Modals render at most one orange CTA each. Hospitality view will show 0 orange CTAs in the matrix chrome (single-orange CTA invariant satisfied — modals are hidden until triggered).
- **Type stack**: All new code uses the existing CSS classes / vars; no new `font-family` declarations.
- **Homepage visual baseline**: `app/page.tsx` continues to call `<MatrixIsland />` with no `area` prop. Default value is `'homepage'`. All existing behaviour is identical → `tests/visual/homepage.spec.ts` should pass without snapshot updates.
- **Hospitality visual baseline**: WILL be updated since `/hospitality` now looks fundamentally different (full matrix shell instead of minimal table). Documented in commit message.
- **Tests for HospitalityIsland**: Replaced by tests for area-aware MatrixIsland. The wiring tests for `HOSPITALITY_FEATURES` (Task 1 group) stay — they don't depend on the component. The handleTabClick fixture tests stay verbatim. The component-rendering tests get rewritten to render `<MatrixIsland area="hospitality" />`.

---

## 5. Key Design Decisions

1. **Default `area="homepage"`**. Keeps `app/page.tsx` unchanged.
2. **Pilot products filter stays in `app/hospitality/page.tsx`**. The page-level RSC narrows to 5 clubs before passing into MatrixIsland. From MatrixIsland's perspective, "products" is just the products array — it doesn't know or care whether it's full set or pilot set.
3. **Categories prop is OPTIONAL** with import-fallback. This means MatrixIsland keeps importing `CATEGORIES` from `@/lib/data` for `area="homepage"`, but uses the prop for `"hospitality"`. Simpler than refactoring the homepage call signature.
4. **Hospitality features show no `band` on adoption-meter**. Acceptable — `bandToMeterBand` defaults to `'bottom'`. The matrix is functional. Future Plan can add `computeBands` to hospitality features.
5. **No type-filter changes**. The 5 pilot products are all `type: 'club'`, so the type filter has no practical effect. We leave it visible (chrome unchanged).
6. **Detail panel clicks for hospitality features show `FeatureDetail`** which iterates `f.presence` against full `ALL_IDS` → most clubs are 'absent'. Acceptable for pilot.
7. **Delete `app/hospitality/HospitalityIsland.tsx`**. Update its tests to point at the new MatrixIsland. Keeps the file count clean.

---

## 6. Strategy for Stable Homepage Visual Baseline

Risks:

- Adding any new state/effect to MatrixIsland that fires only when `area="homepage"` would be unnecessary churn — we minimize it.
- Active-tab default behavior: previously `activeTab="home"` was hardcoded. Switching to a derived-from-area version keeps the same string for area=homepage.
- LOCKED_TABS list rendering: previously every entry was rendered as a "locked rail" tab. With area-aware logic, when `area="hospitality"`, the `'hospitality'` entry should NOT appear in the locked rail (it's the active pill). When `area="homepage"`, the `'hospitality'` entry should still appear in the locked rail visually but be CLICKABLE-NOT-LOCKED (router push). The current code already handles the click semantics — we just need to remove `'hospitality'` from `lockedTabs` for authed users, OR keep it in `lockedTabs` but the click handler routes anyway (current behavior).

  Decision: keep `lockedTabs` membership unchanged for homepage view (preserves visual baseline). Just on `/hospitality`, the active tab IS `hospitality`, so it's filtered out of the rail by `<TopNav>`'s existing `activeTab` filter.

- The TopNav `tabs` array — same construction (Homepage + LOCKED_TABS + Unlock). No drift.

Conclusion: homepage baseline can remain stable.

---

## 7. Files Touched

Created:
- `analysis/hospitality/categories.ts` (NEW)
- `tests/components/MatrixIsland.test.tsx` (NEW, area-aware)
- `.planning/phases/02-hospitality-pilot/02-21-DESIGN-NOTES.md` (this file)
- `.planning/phases/02-hospitality-pilot/02-21-MATRIX-UNIFICATION-SUMMARY.md` (after implementation)

Modified:
- `app/MatrixIsland.tsx` — adds `area` prop, derives `activeTab`, threads `categories` prop, adapts `trackEvent` path.
- `app/hospitality/page.tsx` — swaps to MatrixIsland.
- `lib/data.ts` — re-exports `HOSPITALITY_CATEGORIES`.
- `tests/components/HospitalityIsland.test.tsx` — rewritten to test MatrixIsland in area="hospitality" mode (or split into MatrixIsland.test.tsx + a feature-wiring file).
- `tests/visual/hospitality-tab.spec.ts` + snapshot — updated baseline.

Deleted:
- `app/hospitality/HospitalityIsland.tsx` — replaced by MatrixIsland.

---

## 8. Test Plan

1. `npx tsc --noEmit` clean.
2. `npx next build` clean.
3. `npm test` — vitest passes. New MatrixIsland.test.tsx covers:
   - `area="homepage"` renders homepage features count.
   - `area="hospitality"` renders 55 hospitality feature rows.
   - `area="hospitality"` renders 8 hospitality categories in sidebar.
   - Active tab styling (whichever tab id matches `area`).
   - Tab-click decision tree preserved.
4. `npx playwright test tests/visual/homepage.spec.ts` — passes WITHOUT snapshot update.
5. `npx playwright test tests/visual/hospitality-tab.spec.ts --update-snapshots` — once, after manual visual review.
6. `git diff --quiet analysis/homepage/` exit 0.
7. `git diff --quiet lib/scoring.ts` exit 0.
8. `git diff --quiet scanner/` exit 0.
