---
phase: infra-redesign-v2
plan_id: 02
wave: 1
depends_on: [01]
files_modified:
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
  - .planning/phases/infra-redesign-v2/CONTEXT.md
  - CHANGELOG.md
autonomous: true
decisions_addressed: [D-05, D-06, D-10, D-11, D-12, D-13, D-14, D-15]
must_haves:
  - '`app/components/matrix/types.ts` exports the contracts: `DataCellProps` (`selected`, `intermediate`, `state`, `featureId`, `clubId`, `value`, `onMouseEnter`, `onMouseLeave`, `onFocus`, `onBlur`), `SortHeaderProps` (`label`, `state: idle | asc | desc`, `onSort`), `MeterRowProps` (`band: competitive | mid | weak | bottom`, `value`, `meterColor`), `HeaderBarProps` (`buildDate`), `TopNavProps` (`tabs`, `activeTab`, `onTabClick`, `unlockTab?: string`, `lockedTabs?: string[]`), `CategoryFilterProps` (`categories`, `collapsed`, `onToggle`), `TypeFilterProps` (`selected: Set<"club"|"governing"|"league">`, `onChange`).'
  - '`<DataCell>` renders all 8 visual combinations of `selected × intermediate × state` per Figma node 45:5509. Cell metrics fixed `40px × 38px`, padding `12px`, `1px solid var(--border)` left/right/top borders only, letter-spacing `-0.3px`. `tabIndex={0}` so focus mirrors hover (D-21 a11y). Selected state composes the column-tint gradient overlay over `--bg-cell` (D-03 token from plan 01).'
  - '`<SortHeader>` renders three states (`idle | asc | desc`) with inline-SVG arrow variants from Figma node 45:5542. Click cycles desc → asc → null and fires `onSort()`. No PNG fetched from Figma asset URLs (those expire in 7 days).'
  - '`<MeterRow>` renders the mini progress bar (D-06) preserving the existing `--green / --yellow / --orange / --red` band semantics from `lib/scoring.ts` tier mapping. Color band passed in as a prop; component does not import scoring logic.'
  - '`<HeaderBar>` renders humbleteam wordmark + dot, centered "FC Benchmark" + `{buildDate}`, right-aligned outlined `GET IN TOUCH` CTA. `buildDate` prop sourced from `process.env.BUILD_DATE` (D-12; var was added in plan 01-03).'
  - '`<TopNav>` renders a single horizontal tab strip; active tab gets `border-bottom: 2px solid var(--accent)`; locked tabs render at `opacity: 0.6` and call `onTabClick` (parent decides whether to open the locked-content modal — preserves existing handler logic per RESEARCH.md). `<UnlockTab>` (sub-component) renders solid `var(--accent)` background.'
  - '`<CategoryFilter>` reads category names + counts from `analysis/homepage/features.ts` (no new data source). Each item: name + right-aligned count; click toggles a category in the `collapsed` set passed up through `onToggle`.'
  - '`<TypeFilter>` renders three checkboxes labeled FC / Federation / League, internal values `club` / `governing` / `league`. Reads from `analysis/products.ts` `PRODUCTS[].type` (NOT from `analysis/homepage/results/*.json` — see CONTEXT.md correction). On change, fires `onChange(Set<...>)` with the active type set.'
  - 'Per-component Vitest spec exists for each of the 7 components, covering all decision-mapped behaviors in VALIDATION.md (8 DataCell snapshots, 3 SortHeader states + click, MeterRow per-band snapshot, HeaderBar buildDate render, TopNav active/locked/unlock variants + click, CategoryFilter count equality vs `features.ts`, TypeFilter filter assertion).'
  - 'CONTEXT.md D-15 is corrected in the same commit that wires `<TypeFilter>` — the parenthetical "(already present in `analysis/homepage/results/*.json`)" is replaced with "(already present on `analysis/products.ts` `PRODUCTS[].type` — re-exported via `lib/data.ts`)". A note in the corrected entry references RESEARCH.md "Type-Filter Data Audit".'
  - '`npx next build` + `npm test` green.'
  - 'CHANGELOG.md v6.1 entry — minor.'
---

<objective>
Build the seven atomic matrix components per Figma. Every component lives in `app/components/matrix/` with a colocated `*.module.css` (Claude's Discretion: per-component CSS modules over a single matrix.css for clearer ownership). Each component ships with a Vitest spec under `tests/components/`. Land the contracts file (`types.ts`) FIRST so plan 03 (`<HoverTooltipCard>` + column-selected state) can import `DataCellProps` without re-deriving it. This plan does not yet wire the components into `app/page.tsx` — that's plan 04. This plan also corrects CONTEXT.md D-15 in the same commit that wires `<TypeFilter>`, per the planning-context quality-gate requirement.

Decisions landed: D-05 (cell metrics), D-06 (meter band semantics preserved), D-10 (DataCell 8 states), D-11 (SortHeader 3 states), D-12 (HeaderBar with `BUILD_DATE`), D-13 (TopNav + UnlockTab + locked tab opacity), D-14 (CategoryFilter from `features.ts`), D-15 (TypeFilter from `PRODUCTS[].type` — corrected).
</objective>

<tasks>

<task>
  <id>02-01</id>
  <description>Create `app/components/matrix/types.ts` exporting all seven prop interfaces listed in must_haves. This file is the contract source of truth — plan 03 imports `DataCellProps` from here, plan 04 imports all of them. Define `CategoryItem` and `Tab` helper types. Re-export the existing `ProductType` (`club | governing | league`) from `analysis/types.ts` rather than redefining. No component implementations yet.</description>
  <files>app/components/matrix/types.ts</files>
  <commit>feat(infra-redesign-v2-02): define matrix component prop contracts (D-10–D-15)</commit>
  <automated>npx tsc --noEmit</automated>
</task>

<task>
  <id>02-02</id>
  <description>Build `<DataCell>` (`DataCell.tsx` + `DataCell.module.css`) with all 8 visual combinations of `selected × intermediate × state` per Figma node 45:5509. Fixed metrics `40×38`, padding `12px`, `1px solid var(--border)` on left/right/top, letter-spacing `-0.3px`. The check icon is a single inline SVG component reused across selected variants. `intermediate` renders the check at 40% opacity (always `false` in v1 — wire it now for forward compat). When `selected={true}`, compose two backgrounds: base `var(--bg-cell)` + `linear-gradient(var(--column-tint), var(--column-tint))` overlay (matching the Figma reference; tokens were defined in plan 01-01). `tabIndex={0}` so focus mirrors hover. Forward `onMouseEnter`/`onMouseLeave`/`onFocus`/`onBlur` to parent; the cell does NOT own tooltip state itself (plan 03 handles that). Add `data-feature` and `data-club` attributes for the portaled tooltip in plan 03 to read. Write `tests/components/DataCell.test.tsx` with 8 snapshot tests (one per state combo) + a focus-fires-mouseEnter test.</description>
  <files>app/components/matrix/DataCell.tsx, app/components/matrix/DataCell.module.css, tests/components/DataCell.test.tsx</files>
  <commit>feat(infra-redesign-v2-02): &lt;DataCell&gt; with 8 visual states (D-05, D-10)</commit>
  <automated>npm test -- --run tests/components/DataCell.test.tsx</automated>
</task>

<task>
  <id>02-03</id>
  <description>Build `<SortHeader>` (`SortHeader.tsx` + `SortHeader.module.css`) with 3 states (`idle | asc | desc`) per Figma node 45:5542. Three inline SVG arrow variants — no PNG fetches from Figma asset URLs (those expire in 7 days). Click handler fires `onSort()`; the parent owns the `desc → asc → null` cycle. Mono-caption label per D-08 spec (10/13/-1px). Write `tests/components/SortHeader.test.tsx` rendering all 3 states + a click-fires-`onSort` assertion using `fireEvent.click`.</description>
  <files>app/components/matrix/SortHeader.tsx, app/components/matrix/SortHeader.module.css, tests/components/SortHeader.test.tsx</files>
  <commit>feat(infra-redesign-v2-02): &lt;SortHeader&gt; with 3 states + click handler (D-11)</commit>
  <automated>npm test -- --run tests/components/SortHeader.test.tsx</automated>
</task>

<task>
  <id>02-04</id>
  <description>Build `<MeterRow>` (`MeterRow.tsx` + `MeterRow.module.css`) — mini progress bar + percentage caption. Width-driven by `value` (0–100). Color comes via the `band` prop and resolves to `var(--green | --yellow | --orange | --red)` per existing `lib/scoring.ts` tier mapping (D-06 — band semantics preserved as-is). Component does NOT import from `lib/scoring.ts` to keep it pure-visual; the parent (plan 04) does the band classification and passes it in. Caption uses `.mono-caption` (defined in plan 01-02). Write `tests/components/MeterRow.test.tsx` with one snapshot per band (`competitive | mid | weak | bottom`) — 4 snapshots total.</description>
  <files>app/components/matrix/MeterRow.tsx, app/components/matrix/MeterRow.module.css, tests/components/MeterRow.test.tsx</files>
  <commit>feat(infra-redesign-v2-02): &lt;MeterRow&gt; preserves score-band colors (D-06)</commit>
  <automated>npm test -- --run tests/components/MeterRow.test.tsx</automated>
</task>

<task>
  <id>02-05</id>
  <description>Build `<HeaderBar>` (`HeaderBar.tsx` + `HeaderBar.module.css`) — humbleteam wordmark + dot · centered "FC Benchmark" + `{buildDate}` · right-aligned outlined `GET IN TOUCH` CTA (the only orange element on the bar — single-orange-CTA-per-surface rule per D-25 will be documented in plan 05). `buildDate` prop is consumed from `process.env.BUILD_DATE` (D-12; env var defined in plan 01-03). The component does NOT call `new Date()` — that would trigger hydration mismatch (RESEARCH.md P4). Write `tests/components/HeaderBar.test.tsx` rendering with `buildDate="2026-04-17"` and asserting the date string is in the output.</description>
  <files>app/components/matrix/HeaderBar.tsx, app/components/matrix/HeaderBar.module.css, tests/components/HeaderBar.test.tsx</files>
  <commit>feat(infra-redesign-v2-02): &lt;HeaderBar&gt; with build-date span (D-12)</commit>
  <automated>npm test -- --run tests/components/HeaderBar.test.tsx</automated>
</task>

<task>
  <id>02-06</id>
  <description>Build `<TopNav>` (`TopNav.tsx` + `TopNav.module.css`) — single horizontal tab strip across full page width. Active tab gets `border-bottom: 2px solid var(--accent)`. The `<UnlockTab>` sub-component (also exported from `TopNav.tsx`) renders with solid `var(--accent)` background. Locked tabs render at `opacity: 0.6` and on click fire `onTabClick(name)` — the parent (plan 04) decides whether to open the locked-content modal, which preserves the existing `handleTabClick` branching from `app/page.tsx`. The component does NOT itself open any modal. Write `tests/components/TopNav.test.tsx` with three test groups: (a) active-tab gets accent border, (b) locked-tab opacity is 0.6 and click fires `onTabClick`, (c) Unlock variant has the orange-background class.</description>
  <files>app/components/matrix/TopNav.tsx, app/components/matrix/TopNav.module.css, tests/components/TopNav.test.tsx</files>
  <commit>feat(infra-redesign-v2-02): &lt;TopNav&gt; + &lt;UnlockTab&gt; with locked-tab opacity (D-13)</commit>
  <automated>npm test -- --run tests/components/TopNav.test.tsx</automated>
</task>

<task>
  <id>02-07</id>
  <description>Build `<CategoryFilter>` (`CategoryFilter.tsx` + `CategoryFilter.module.css`) — vertical list of feature categories. Each row: name + right-aligned count. Click toggles a category in the `collapsed` set via `onToggle(categoryId)`. Categories + counts are derived from `analysis/homepage/features.ts` (no new data source — D-14). The component receives derived `CategoryItem[]` as a prop; it does NOT import `features.ts` directly so the test can pass mock data. The parent (plan 04) does the derivation. Write `tests/components/CategoryFilter.test.tsx`: render with 4 fake categories, assert each name + count appears, then click one and assert `onToggle` fires with the right id. A separate test imports `analysis/homepage/features.ts` and asserts the derived `CategoryItem[]` count equals the sum of features per category — guarantees D-14 contract.</description>
  <files>app/components/matrix/CategoryFilter.tsx, app/components/matrix/CategoryFilter.module.css, tests/components/CategoryFilter.test.tsx</files>
  <commit>feat(infra-redesign-v2-02): &lt;CategoryFilter&gt; sourced from features.ts (D-14)</commit>
  <automated>npm test -- --run tests/components/CategoryFilter.test.tsx</automated>
</task>

<task>
  <id>02-08</id>
  <description>Build `<TypeFilter>` (`TypeFilter.tsx` + `TypeFilter.module.css`) — three checkboxes labeled "FC / Federation / League", internal values `club / governing / league`. Reads from `analysis/products.ts` `PRODUCTS[].type` (NOT from `analysis/homepage/results/*.json` — RESEARCH.md "Type-Filter Data Audit"). The component does NOT import `PRODUCTS` directly — the parent passes `selected: Set<ProductType>` and `onChange` as props (test isolation). On checkbox toggle, fire `onChange` with the new set. **In the same commit, correct CONTEXT.md D-15:** open `.planning/phases/infra-redesign-v2/CONTEXT.md`, find the D-15 entry that says "Filters clubs by their `type` field already present in `analysis/homepage/results/*.json`", and replace with "Filters clubs by their `type` field already present on `analysis/products.ts` `PRODUCTS` (re-exported via `lib/data.ts` as the `Product` type — see RESEARCH.md "Type-Filter Data Audit"). FC/Federation/League maps to club/governing/league." Write `tests/components/TypeFilter.test.tsx` with: (a) renders three checkboxes with correct labels, (b) clicking one fires `onChange` with the updated `Set`, (c) imports `PRODUCTS` from `analysis/products.ts` and asserts that filtering `PRODUCTS` by a `Set<ProductType>` produces the expected subset for each enum value.</description>
  <files>app/components/matrix/TypeFilter.tsx, app/components/matrix/TypeFilter.module.css, tests/components/TypeFilter.test.tsx, .planning/phases/infra-redesign-v2/CONTEXT.md</files>
  <commit>feat(infra-redesign-v2-02): &lt;TypeFilter&gt; sourced from PRODUCTS[].type + correct CONTEXT.md D-15 (D-15)</commit>
  <automated>npm test -- --run tests/components/TypeFilter.test.tsx</automated>
</task>

<task>
  <id>02-09</id>
  <description>Wave-1 quality gate. Run `npx next build` to confirm no atomic component breaks the build (none are wired into a route yet, so this catches type errors only). Run `npm test` to confirm all 7 component specs pass alongside existing `lib/*.test.ts`. Add CHANGELOG.md v6.1 entry at top — minor: "Atomic matrix components (DataCell · SortHeader · MeterRow · HeaderBar · TopNav · CategoryFilter · TypeFilter) shipped with per-component Vitest specs. CONTEXT.md D-15 corrected to reference PRODUCTS[].type." Keep under 300 chars.</description>
  <files>CHANGELOG.md</files>
  <commit>docs(infra-redesign-v2-02): changelog v6.1 + close atomic-components plan</commit>
  <automated>npm test &amp;&amp; npx next build</automated>
</task>

</tasks>

<verification>
- Wave merge: `npm test` (all 7 component specs + existing tests) + `npx next build` green.
- All 8 visual states of `<DataCell>` are reachable in the snapshot suite.
- `<TypeFilter>` test imports `PRODUCTS` and proves the filter math against real data (proof of D-15 contract).
- `<CategoryFilter>` test imports `features.ts` and proves count equality (proof of D-14 contract).
- CONTEXT.md D-15 entry no longer references `analysis/homepage/results/*.json`.
- `analysis/homepage/results/*.json` unchanged — `git diff --quiet analysis/homepage/results/`.
- Decision-verification rows appended to VALIDATION.md.
</verification>
