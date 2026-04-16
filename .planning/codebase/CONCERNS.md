# Technical Concerns

## Critical Issues

### Mutating imported module-level data
`lib/data.ts` calls `computeBands()` at module import time and **writes directly onto the `FEATURES` array items** (`f.adoption`, `f.adoptionPct`, `f.band`). This mutates shared module state on every import. Because the fields are typed as optional (`adoption?: number`, `adoptionPct?: number`, `band?: BandId`), all downstream code must non-null assert or handle `undefined`. In practice every consumer (`page.tsx`, `club/[id]/page.tsx`, `scoring.ts`) relies on these being set, but TypeScript allows accessing them without a guard — the compiler won't catch a regression if `computeBands()` is ever not called. The fix is to compute bands at data definition time (inline in the array literal) so the types can be non-optional.

### Non-null assertions throughout detail components
`FeatureDetail` in `app/page.tsx` (line 549–550) does `CATEGORIES.find(...)!` and `BAND_META.find(...)!` with a bang operator. If a `Feature.cat` or `Feature.band` value ever drifts out of sync with the lookup arrays, these throw a runtime `TypeError: Cannot read properties of undefined`. Same pattern appears in `TableRows` (line 471) and `ClubDetailPage` (line 58 in `club/[id]/page.tsx`). There is no guard or fallback rendering.

### `pName()` helper also uses a non-null assertion
In `FeatureDetail` (line 554): `const pName = (id: string) => PRODUCTS.find(p => p.id === id)!.name`. If `ALL_IDS` ever contains a stale ID not present in `PRODUCTS`, this crashes silently. The helper is called inside `.map()` with no error boundary.

### Scoring logic duplicated with divergent behaviour
`ProductDetail` in `app/page.tsx` (lines 643–656) and `lib/scoring.ts` (`getProductScores`) both compute `rawScore`, `weightedScore`, `maxWeighted`, and `coveragePct` independently. The implementations differ subtly: `page.tsx` uses `Math.round(f.weight * 0.5)` for partial, while `scoring.ts` also uses `Math.round(f.weight * 0.5)` — currently matching — but the duplication makes future drift likely. There is no single source of truth for the scoring formula.

### `adoptionPct` used as a CSS `width` without clamping
In `page.tsx` `FeatureDetail` (line 582): `style={{ width: \`${f.adoptionPct}%\` }}`. If `computeBands()` somehow produces a value > 100 (e.g., if partial scores push it over due to floating-point rounding with a large product set), the bar overflows its container with no `overflow: hidden` on `detail-freq-bar` itself. Minor but visually broken.

---

## Performance

### Large inline CSS file — no code splitting
All styles for both pages (matrix + club detail) live in one `globals.css` (~393 lines). This is loaded globally for every route. At this scale it is not a serious problem, but as the project grows, there is no scoping mechanism. Any unused styles for the club detail page are loaded on the matrix page and vice versa.

### `visibleFeats` filter runs on every keystroke with `FEATURES.find()` inside render
`handleCellMouseOver` calls `FEATURES.find(x => x.id === fid)` and `PRODUCTS.find(x => x.id === pid)` on every mouse-over event (line 162–163 in `page.tsx`). With 29 features × 26 products = 754 cells, this fires very frequently. These lookups should use a `useMemo`-cached `Map<string, Feature>` and `Map<string, Product>` for O(1) access instead of O(n) linear scan.

### `getRankedProducts()` in `scoring.ts` iterates all features for every product
`getProductScores` iterates all 29 features per product call; `getRankedProducts` calls it for all 26 products → 754 iterations per page load of any club detail page. Currently negligible but scales poorly if the dataset grows.

### `catCounts` and `bandSidebarCounts` use `FEATURES.filter()` inside `useMemo`
These fire once per mount and are stable (no deps), so they are fine currently. But `bandCounts` (line 107) also has no deps and rebuilds on every render incorrectly — the `useMemo` dep array is `[]` which is correct, but the comment "always based on full dataset" does not match the filtering: it iterates all features fine, but uses `BAND_META.forEach` then `FEATURES.forEach` with object mutation inside the memo, which is an anti-pattern.

### `TableRows` is a plain function, not a memoized component
`TableRows` is declared as a regular function (not `React.memo`) and accepts callback props that are `useCallback`-stabilised from the parent. Because it receives `feats` and `prods` arrays (new references whenever filters change), it will re-render correctly — but the grouping loop (`feats.forEach` + `CATEGORIES.find`) runs on every render even when only `selectedFeature` changes. Wrapping in `React.memo` with a custom comparator, or extracting the category-grouping step into a `useMemo`, would prevent re-rendering the entire table on panel selection changes.

---

## Technical Debt

### `capture.mjs`, `recapture.mjs`, `recapture2.mjs`, `recapture-f1.mjs` committed to repo root
These are Playwright/Puppeteer scraping scripts used during data collection. They are dead code from the research phase and have no role in the production app. They reference browser automation libraries not in `package.json` (implying they were run with a global install), and `recapture2.mjs` contains inline comments like `// Attempt multiple rounds of dismissal`. These should be moved to an `scripts/` or `tools/` directory at minimum, or removed entirely.

### `CONCEPT_VISUAL.html` in repo root
A static HTML prototype file committed alongside the Next.js app. It has no build integration and serves no current purpose.

### `analysis/` directory with three `.md` files
`analysis-batch1.md`, `analysis-batch2.md`, `analysis-batch3.md` are raw research notes committed to the production repo. They are useful context but clutter the project root.

### Feature data manually maintained in `lib/data.ts`
All 29 feature definitions with 26 presence values each (754 data points) are hand-coded. There is no validation that every `makePresence()` call only references IDs that exist in `PRODUCTS`. If a new product is added to `PRODUCTS`, existing `makePresence()` calls silently treat it as absent — which is correct by design — but removed products would leave stale IDs in `full`/`partial` arrays with no error.

### `LOCKED_TABS` in `page.tsx` are purely decorative UI
Eight "locked" nav tabs represent features that are described as requiring admin access, but the locking is purely cosmetic. The modal says "Request access from admin" but clicking the button simply closes the modal — there is no action, no API call, no mailto link. This is placeholder UI that communicates a false affordance to users.

### Hardcoded year "2026" in two places
`app/page.tsx` line 197 and `app/club/[id]/page.tsx` line 92 both hardcode `// 2026` in the logo text. This will become stale.

### `feature-matrix.md` and `brainstorm.md` in repo root
Committed markdown docs that overlap with `lib/data.ts` as a source of truth. If data changes in code, these docs go stale immediately and there is no sync mechanism.

---

## Accessibility

### Sidebar category and band items are `<div>` with `onClick` — not keyboard accessible
`cat-item` and `band-item` elements (lines 283–309 in `page.tsx`) use `onClick` on plain `<div>` elements with no `role`, `tabIndex`, or keyboard handler (`onKeyDown`). They cannot be reached or activated via keyboard navigation.

### Table feature names are `<td>` with `onClick` — not keyboard accessible
`td.feature-name` and `td.cell` elements both have `onClick` but no `role="button"`, no `tabIndex`, and no keyboard event handler. A keyboard-only user cannot activate feature or cell selection.

### Product column headers clickable but missing `aria-label`
`col-header` divs (line 325–329) are clickable to select a product but carry no accessible label beyond the rotated text. Screen readers may read the rotated product name but there is no indication the element is interactive.

### Locked modal does not trap focus
`locked-overlay` modal (lines 394–415) renders as `role="dialog" aria-modal="true"` correctly, but focus is not moved into the modal on open, and there is no focus trap. A keyboard user could tab behind the modal backdrop.

### Close button label is a unicode `×` character with no `aria-label`
`detail-close` button (line 559) renders `{'\u00D7'}` as its only content. Screen readers announce "times" or "multiplication sign". Should be `aria-label="Close"`.

### Color alone distinguishes presence states in the matrix
Full (blue checkmark), partial (faded blue checkmark), and absent (grey dot) states are distinguished by both symbol and color. However, the color contrast of `partial-check` at `opacity: .35` applied to `var(--accent)` (#4f6ef7 on #13131e background) is very low — likely below WCAG AA 4.5:1 for small text at that opacity.

### Missing `lang` on the `<html>` element… actually present
`app/layout.tsx` sets `lang="en"` — this is fine.

### `prefers-reduced-motion` is handled
`globals.css` lines 36–38 correctly disable animations for reduced-motion users.

---

## Missing Error Handling

### No 404 page for unknown club IDs at runtime
`ClubDetailPage` calls Next.js `notFound()` for unknown IDs, which is correct for static export — but `generateStaticParams` only lists the current 26 products. If someone navigates to `/club/some_new_id` and the app is not statically regenerated, the runtime behaviour depends on `dynamicParams` (unset, defaults to `true` in Next.js 15+) — meaning it will try to render and call `notFound()`, which requires a `not-found.tsx` page. There is none defined in the app directory; Next.js will fall back to a generic framework 404.

### `PRODUCTS.find()` result used without null check in `pName()` helper
Described under Critical Issues. No try/catch or fallback exists.

### Search input state divergence
`handleClearFilters` manually resets `searchInputRef.current.value = ''` (line 151) in addition to `setSearchText('')`. This imperative DOM mutation is needed because the `<input>` is uncontrolled (`onChange` updates state but `value` prop is not bound). If this ref is ever null (e.g., during SSR or if the input unmounts), the `if` guard catches it, but the real concern is that the uncontrolled/controlled divergence is a footgun — future developers may add `defaultValue` thinking it controls the input.

### No error boundary anywhere
There is no `ErrorBoundary` component wrapping the matrix or club detail pages. A runtime error in rendering (e.g., a null dereference in `FeatureDetail`) will crash the entire page with no recovery UI.

---

## Dependencies

### Next.js 16.2.2 — very recent, pre-stable
`next@16.2.2` is listed in `package.json`. As of the knowledge cutoff, Next.js 15 was the latest stable release. Version 16 may be a pre-release or canary. This could introduce instability or API changes not yet finalised. Worth verifying whether this is intentional or a version typo.

### React 19.2.4
`react@19.2.4` is also ahead of the last known stable (19.0.0 released late 2024). Likely stable but worth pinning to a known-good release in `package.json` rather than using exact versions that may have been pre-release.

### No `@types/react` pinning concern
`@types/react: "^19"` ranges across all React 19 minor/patch type updates — fine given React 19 is used, but could pick up breaking type changes on `npm install`.

### Only 3 runtime dependencies
`next`, `react`, `react-dom` — no unnecessary dependencies. This is a strength, not a concern.

### No automated dependency auditing configured
There is no `npm audit` step in CI (no CI config exists at all — no `.github/` directory). Vulnerabilities in transitive dependencies would not be caught automatically.

### No CI/CD configuration
No GitHub Actions, no test suite, no lint-on-commit hook. The `lint` script in `package.json` runs `eslint` but there is no evidence it is enforced anywhere.

---

## Quick Wins

1. **Convert sidebar `<div>` filters to `<button>` elements** — adds keyboard accessibility with two lines of change per item (`role` + `tabIndex` already not needed on `<button>`).

2. **Add `aria-label="Close"` to the detail panel close button** — one-line fix, meaningful screen reader improvement.

3. **Focus trap in the locked modal** — add `autoFocus` to the primary button inside `.locked-card` so focus moves on open.

4. **Cache `FEATURES` and `PRODUCTS` lookups as Maps** — add two `useMemo(() => new Map(...))` calls at the top of `FeatureMatrixPage` and use them in `handleCellMouseOver`, replacing O(n) `.find()` with O(1) map lookup.

5. **Make `Feature.band`, `adoption`, `adoptionPct` non-optional** by computing them inline in the array literal rather than via a post-hoc mutation function. This eliminates all `!` non-null assertions downstream and makes the type system useful.

6. **Remove or gitignore `capture.mjs`, `recapture*.mjs`, `CONCEPT_VISUAL.html`** — clean up repo root.

7. **Add a `not-found.tsx` page** under `app/` to provide a branded 404 experience when `notFound()` is triggered.

8. **Wrap the main page content in an `<ErrorBoundary>`** — prevents total white-screen on runtime errors.
