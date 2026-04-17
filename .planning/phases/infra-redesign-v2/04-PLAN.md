---
phase: infra-redesign-v2
plan_id: 04
wave: 2
depends_on: [01, 02, 03]
files_modified:
  - app/page.tsx
  - app/MatrixIsland.tsx
  - app/MatrixIsland.module.css
  - app/globals.css
  - tests/visual/homepage.spec.ts
  - tests/visual/homepage-1440x900.png
  - CHANGELOG.md
  - README.md
autonomous: true
decisions_addressed: [D-17, D-18, D-19, D-20, D-21, D-29]
must_haves:
  - '`app/page.tsx` is a Server Component shell that loads scores + features + clubs via `lib/data.ts` / `lib/scoring.ts` and passes them as serializable props into a new `<MatrixIsland>` Client Component (D-17). `''use client''` is removed from `app/page.tsx` itself.'
  - '`app/MatrixIsland.tsx` is the Client Component that owns all interactive state: sort, sidebar filters, column-selected, hover-tooltip. It imports the 9 matrix components + 2 hooks from plans 02–03 (`<DataCell>`, `<SortHeader>`, `<MeterRow>`, `<HeaderBar>`, `<TopNav>`, `<CategoryFilter>`, `<TypeFilter>`, `<HoverTooltipCard>`, `useColumnSelection`, `useHoverTooltip`).'
  - 'Every state hook from the old `app/page.tsx` is preserved verbatim (RESEARCH.md "Current Homepage Structural Map"): `filterTypes`, `activeCat`, `selectedFeature`, `selectedProduct`, `adoptionSort`, `featureAlphaSort`, `scoreSort`, `authed`, `authEmail`, `isAdmin`, `isPremium`, all login/locked/coming-soon modal state. `selectedProduct` doubles as the column-tint source (D-18); `useColumnSelection` is used for the new toggle semantics but is wired through `selectedProduct` so the existing Product-detail panel keeps working. If a conflict appears, prefer a single source of truth: `selectedProduct` stays the authoritative state and `useColumnSelection` becomes a thin helper over it.'
  - 'Sort state uses the contract `{ col: ''feature'' | ''total'' | clubId, dir: ''asc'' | ''desc'' | null }` with desc → asc → null cycle (D-19). Default: features in their natural order from `features.ts` (no sort applied).'
  - 'Sidebar filter state is local to the Client Component: `collapsedCats: Set<string>` (category collapse), `filterTypes: Set<ProductType>` (type filter). The existing clear-btn resets both (D-20).'
  - 'Tooltip uses the portaled `<HoverTooltipCard>` + `useHoverTooltip` from plan 03. Cells pass `data-feature` + `data-club` attrs (already set by `<DataCell>` in plan 02). `onMouseEnter` / `onFocus` both call `handleCellEnter` so keyboard users get the tooltip (D-21). No new server requests on hover.'
  - 'All existing auth/login/locked-modal/coming-soon handlers preserved verbatim: `handleLogin`, `handleLogout`, `sendAccessRequest`, `handleTabClick`, `handleShowFeatureDetail`, `handleShowProductDetail`, `handleCloseDetail`, `handleClearFilters`. `handleCellMouseOver` body is replaced with a call to the new `handleCellEnter`; `handleCellMouseMove` is deleted (anchor-rect positioning obviates cursor-follow); `handleTableMouseLeave` delegates to `handleCellLeave` (100ms grace via the hook).'
  - '`<nav.flow-nav>` markup is replaced by `<TopNav>`. The old `.locked-zone` markup + its animated-border CSS (`app/globals.css` lines ~252–256) are deleted wholesale (RESEARCH.md P9) — `<TopNav>` locked-tab opacity replaces the visual.'
  - 'The double Total-Score row (one in `<thead>`, one in `<tfoot>` — RESEARCH.md P7) is preserved: sticky top + sticky bottom totals. The refactor does NOT collapse them into one.'
  - 'Existing in-file helpers `TableRows`, `FeatureDetail`, `ProductDetail` are preserved. `TableRows` internals are rewritten to render the new components; `FeatureDetail` / `ProductDetail` get a token-swap only (class references to removed `--bg` / `--bg2` / `--bg3` are updated to `--bg-page` / `--bg-cell`).'
  - '`tests/visual/homepage.spec.ts` is un-skipped. Baseline PNG `tests/visual/homepage-1440x900.png` is captured via `npx playwright test --update-snapshots` against a local `npm run dev` build at `http://localhost:3000`; the baseline is committed. Subsequent CI runs enforce `maxDiffPixelRatio: 0.02` (D-26 satisfied). The spec uses `animations: ''disabled''` and awaits `document.fonts.ready` before the screenshot (RESEARCH.md "Pitfall flagged in research").'
  - 'Lighthouse a11y score ≥ 90 verified manually at phase gate (D-29). This plan does not yet capture the Lighthouse report — that happens at phase gate in plan 05.'
  - '`npx next build` + `npm test` + `npx playwright test --grep @smoke` all green.'
  - '`analysis/homepage/results/*.json` + scoring `.ts` untouched (`git diff --quiet analysis/ lib/scoring.ts`).'
  - 'CHANGELOG.md v6.3 major entry — homepage refactor is a visible, system-level change.'
  - 'README.md rankings table + coverage numbers untouched (scoring didn''t change); project-structure diagram updated to list `app/MatrixIsland.tsx` + `app/components/matrix/*`.'
---

<objective>
Refactor `app/page.tsx` to consume plans 01–03. The 1072-LOC Client Component becomes a Server Component shell (`app/page.tsx`) + a Client Component matrix island (`app/MatrixIsland.tsx`) per D-17. The island wires up the nine atomic components and two hooks built in plans 02–03 — sort state, sidebar filters, column-selected, hover-tooltip (D-18–D-21). Every auth / login-modal / locked-content / coming-soon / access-request handler is preserved verbatim per RESEARCH.md structural map. The old `.locked-zone` animated border is deleted in this plan once `<TopNav>` replaces the markup (RESEARCH.md P9). The double Total-Score row (thead + tfoot sticky-top + sticky-bottom) is explicitly preserved (RESEARCH.md P7). The homepage visual-regression spec (scaffolded-and-skipped in plan 01) is unskipped here, a baseline PNG is captured + committed, and `maxDiffPixelRatio: 0.02` becomes the gate (D-26 satisfied).

Decisions landed: D-17, D-18, D-19, D-20, D-21, D-29 (keyboard-focus tooltip path for a11y).
</objective>

<tasks>

<task>
  <id>04-01</id>
  <description>Create `app/MatrixIsland.tsx` as a `'use client'` component that takes `{ products, features, scores, featuresByCategory, categories }` as props (serializable from the Server Component shell). Copy every state hook + handler from the current `app/page.tsx` verbatim into this file EXCEPT: (a) delete `handleCellMouseMove` (cursor-follow positioning is gone); (b) rewrite `handleCellMouseOver(fid, pid, el)` to call the new `useHoverTooltip.handleCellEnter(fid, pid, el)`; (c) rewrite `handleTableMouseLeave()` to delegate to `useHoverTooltip.handleCellLeave()` (100ms grace). Import `useColumnSelection` and `useHoverTooltip` from plan 03. `selectedProduct` stays the authoritative state for both the detail panel AND column-tint. Wire the `fetch('/api/auth/me')` mount effect + `trackEvent('page_view')` UNCHANGED. Do NOT render markup yet — this task is the state/handler scaffold only. Export `MatrixIsland` as default.</description>
  <files>app/MatrixIsland.tsx</files>
  <commit>feat(infra-redesign-v2-04): scaffold MatrixIsland client component with preserved state (D-17)</commit>
  <automated>npx tsc --noEmit</automated>
</task>

<task>
  <id>04-02</id>
  <description>Build the render tree inside `<MatrixIsland>` per RESEARCH.md "Render tree (current → new)". Replace `<header>` → `<HeaderBar buildDate={process.env.BUILD_DATE ?? ''} />`. Replace `<nav.flow-nav>` → `<TopNav tabs={...} activeTab="home" unlockTab="UNLOCK" lockedTabs={[...milestones v3–v11...]} onTabClick={handleTabClick} />` — the existing `handleTabClick` branching (isAdmin/isPremium/authed/guest) handles whether to open the locked-content modal. Replace sidebar Category block → `<CategoryFilter categories={derivedCategories} collapsed={collapsedCats} onToggle={...}/>`. Replace sidebar Type block → `<TypeFilter selected={filterTypes} onChange={setFilterTypes}/>` (remember D-15 correction — read `PRODUCTS[].type`, which the Server Component shell will pass in as `products`). Replace `<th className="sortable">` blocks → `<SortHeader>` × 3. Replace `<td className="cell">` rendering inside `TableRows` → `<DataCell selected={isSelected(clubId)} intermediate={false} state="default" featureId={...} clubId={...} value={...} onMouseEnter={...} onMouseLeave={...} onFocus={...} onBlur={...} />`. Replace `<div.freq-bar-wrap>` → `<MeterRow band={...} value={...} />`. Replace `<div.cell-tooltip>` → `<HoverTooltipCard data={tooltipData} features={featureMap} clubs={clubMap} scoring={scoreMap} />`. **Preserve the thead + tfoot Total-Score rows** per RESEARCH.md P7. **Preserve** `<preview-blur-overlay>` (guest CTA). **Preserve** `<div.detail-panel>` rendering `FeatureDetail` / `ProductDetail` unchanged. **Preserve** the three `<div.locked-overlay>` modals verbatim — their chrome will be re-skinned in plan 05 via token swap only.</description>
  <files>app/MatrixIsland.tsx, app/MatrixIsland.module.css</files>
  <commit>feat(infra-redesign-v2-04): wire MatrixIsland render tree to new components (D-17, D-18, D-21)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>04-03</id>
  <description>Collapse `app/page.tsx` into a Server Component shell. Remove `'use client'`. Do the server-side data loads (`getProductScores`, `getRankedProducts`, feature + club map derivation — whatever lives in `lib/data.ts` and `lib/scoring.ts`). Pass the derived props into `<MatrixIsland {...props} />`. Preserve imports needed for `metadata` export if any. The resulting `app/page.tsx` should be under ~80 LOC — pure server data assembly + one JSX node. `FeatureDetail` / `ProductDetail` / `TableRows` move into `app/MatrixIsland.tsx` (or into a new `app/matrix/*.tsx` file — Claude's Discretion; prefer keeping them colocated in `MatrixIsland.tsx` unless the file blows past 600 LOC).</description>
  <files>app/page.tsx</files>
  <commit>refactor(infra-redesign-v2-04): app/page.tsx becomes a Server Component shell (D-17)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>04-04</id>
  <description>Delete the `.locked-zone` animated-border rules from `app/globals.css` (lines ~252–256 — RESEARCH.md P9). Delete `.cell-tooltip` and `.tt-*` classes (lines ~336–346) — the portaled `<HoverTooltipCard>` replaces them (plan 03). Audit `app/globals.css` for any other references to the deleted tokens (`--bg`, `--bg2`, `--bg3` — which no longer exist after plan 01) and rebind them to the new equivalents (`--bg-page`, `--bg-cell`). Run `grep -n "var(--bg[123]\b" app/globals.css` to confirm zero matches after cleanup. The legacy `--bg1` alias from plan 01 stays (`.login-input` depends on it).</description>
  <files>app/globals.css</files>
  <commit>refactor(infra-redesign-v2-04): remove .locked-zone and .cell-tooltip rules; rebind legacy token refs</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>04-05</id>
  <description>Unskip `tests/visual/homepage.spec.ts`. Edit to: (a) remove the `.skip`; (b) add `animations: 'disabled'` to the screenshot call; (c) await `page.waitForFunction(() => document.fonts.ready)` before the assertion to freeze font swap (RESEARCH.md pitfall); (d) mask the HeaderBar build-date span via `mask: [page.locator('[data-build-date]')]` so baseline doesn't break when BUILD_DATE changes per commit. Update `<HeaderBar>` to emit `data-build-date` on its date span (one-line edit in `app/components/matrix/HeaderBar.tsx`). Start the dev server (`npm run dev &`), run `npx playwright test --update-snapshots tests/visual/homepage.spec.ts` to capture baseline `tests/visual/homepage.spec.ts-snapshots/homepage-1440x900.png` (or whatever Playwright's default snapshot path is — do NOT override it), kill the dev server, and commit the baseline PNG. Re-run `npx playwright test tests/visual/homepage.spec.ts` in headless mode to confirm the diff is zero.</description>
  <files>tests/visual/homepage.spec.ts, app/components/matrix/HeaderBar.tsx</files>
  <commit>test(infra-redesign-v2-04): capture homepage visual-regression baseline (D-26 gate armed)</commit>
  <automated>npx playwright test tests/visual/homepage.spec.ts</automated>
</task>

<task>
  <id>04-06</id>
  <description>Wave-2 quality gate + docs. Run `npm test && npx playwright test && npx next build` — all three must be green. Confirm `git diff --quiet analysis/homepage/results/ lib/scoring.ts` (D-28 invariant). Add CHANGELOG.md v6.3 major entry: "Homepage refactor — app/page.tsx split into Server Component shell + Client Component MatrixIsland wired to new atomic components (DataCell / SortHeader / MeterRow / HeaderBar / TopNav / CategoryFilter / TypeFilter / HoverTooltipCard). Keyboard-focusable cells; portaled tooltip; column-tint on selected club. Visual-regression baseline captured at 1440×900." Keep under 300 chars — trim as needed. Update README.md project-structure diagram to list `app/MatrixIsland.tsx` + `app/components/matrix/*`.</description>
  <files>CHANGELOG.md, README.md</files>
  <commit>docs(infra-redesign-v2-04): changelog v6.3 + README structure for MatrixIsland</commit>
  <automated>npm test &amp;&amp; npx playwright test &amp;&amp; npx next build</automated>
</task>

</tasks>

<verification>
- Wave merge: `npm test &amp;&amp; npx playwright test --grep @smoke &amp;&amp; npx next build` green.
- Phase-gate prerequisite: visual baseline PNG committed, `maxDiffPixelRatio: 0.02` enforced in CI.
- Manual smoke: `/` renders the new matrix; clicking a club column shows column-tint; hovering a cell shows portaled tooltip; Tab-key focus fires tooltip (D-21 a11y); sign-in / locked-content / coming-soon modals still work (logic unchanged — only chrome restyled by plan 05).
- `git diff --quiet analysis/homepage/results/ lib/scoring.ts` returns 0 (D-28).
- Decision-verification rows appended to VALIDATION.md.
</verification>
