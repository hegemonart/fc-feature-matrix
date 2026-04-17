---
phase: infra-redesign-v2
plan_id: 03
wave: 1
depends_on: [01, 02]
files_modified:
  - app/components/matrix/HoverTooltipCard.tsx
  - app/components/matrix/HoverTooltipCard.module.css
  - app/components/matrix/types.ts
  - app/components/matrix/useColumnSelection.ts
  - app/components/matrix/useHoverTooltip.ts
  - tests/components/HoverTooltipCard.test.tsx
  - tests/components/useColumnSelection.test.tsx
  - tests/components/useHoverTooltip.test.tsx
  - CHANGELOG.md
autonomous: true
decisions_addressed: [D-03, D-16]
must_haves:
  - '`<HoverTooltipCard>` renders via `createPortal(node, document.body)` so it escapes the matrix grid `overflow: hidden` (D-16). Anchored to the hovered cell — position computed from `cell.getBoundingClientRect()`, NOT cursor coordinates (RESEARCH.md P8 — behavioral change from current `cell-tooltip`).'
  - 'Tooltip content: club name, feature description (looked up from `analysis/homepage/features.ts`), `TIER:` badge in `.mono-caption`, scoring breakdown `Yes +N / No −N`. Lookup uses in-memory feature/club maps passed as props (no server requests on hover — D-21).'
  - 'Closes on `mouseleave` after a 100ms grace period to let the cursor cross small gaps (D-16). Uses `setTimeout` cleared on re-`mouseenter`.'
  - '`useColumnSelection` hook owns `selectedClubId: string | null` state and `setSelectedClubId(id)` toggle — clicking the same id deselects (D-18). Returns `{selectedClubId, isSelected, toggle}`. Plan 04 wires it into the matrix island.'
  - '`useHoverTooltip` hook owns `tooltipData: { featureId, clubId, anchorRect } | null`. Exposes `handleCellEnter(featureId, clubId, el)` that reads `el.getBoundingClientRect()` and stores it; `handleCellLeave()` schedules a 100ms close; `handleCellReenter()` cancels the scheduled close. Plan 04 wires this into the cell `onMouseEnter` / `onFocus` props.'
  - 'Vitest specs cover: portal target is `document.body`, position computed from `getBoundingClientRect`, 100ms close grace (use fake timers), grace cancellation on re-enter, cell selection toggle (click same id deselects), keyboard focus fires the same handler as hover (D-21 a11y).'
  - 'Column-tint visual contract: `<DataCell selected>` (built in plan 02) consumes `--column-tint` via the gradient overlay defined in plan 01. The `useColumnSelection` hook returns `isSelected(clubId)` so the parent passes `selected={isSelected(clubId)}` to every cell in the active column. No CSS change in this plan — only state plumbing.'
  - '`app/components/matrix/types.ts` (created in plan 02) gets `HoverTooltipProps` and `TooltipData` types appended (additive only — no breaking change to plan 02 contracts).'
  - '`npx next build` + `npm test` green.'
  - 'CHANGELOG.md v6.2 minor entry.'
---

<objective>
Build the two pieces of cross-cell interactivity that depend on the `<DataCell>` contract from plan 02 but don't belong inside the cell itself: the portaled hover tooltip (D-16) and the column-selection state plumbing (D-03 visual + D-18 state). This plan stays at the component / hook layer — it does NOT wire anything into `app/page.tsx` (that's plan 04). Splitting this off from plan 02 lets it run in parallel with the atomic-components plan once the `DataCellProps` contract is committed (plan 02-01 lands the contract first).

Decisions landed: D-03 (selected-column tint state plumbing — token already exists from plan 01), D-16 (portaled tooltip with 100ms grace).
</objective>

<tasks>

<task>
  <id>03-01</id>
  <description>Append `HoverTooltipProps` and `TooltipData` to `app/components/matrix/types.ts` (additive only). `TooltipData = { featureId: string; clubId: string; anchorRect: DOMRect } | null`. `HoverTooltipProps = { data: TooltipData; features: Map<string, FeatureMeta>; clubs: Map<string, ClubMeta>; scoring: Map<string, { yes: number; no: number }> }`. `FeatureMeta` mirrors what `analysis/homepage/features.ts` already exports (description + tier); re-use the existing type if exported, otherwise derive a `Pick`.</description>
  <files>app/components/matrix/types.ts</files>
  <commit>feat(infra-redesign-v2-03): append HoverTooltipProps + TooltipData contracts (D-16)</commit>
  <automated>npx tsc --noEmit</automated>
</task>

<task>
  <id>03-02</id>
  <description>Build `<HoverTooltipCard>` (`HoverTooltipCard.tsx` + `HoverTooltipCard.module.css`). Renders via `createPortal(node, document.body)` so it escapes grid overflow. When `data` is null → returns null. When data is present → reads `anchorRect` and positions itself with `position: fixed; top: rect.bottom + 8px; left: rect.left;` (with viewport-clamp logic so it doesn't overflow on right edge). Card chrome: `background: var(--bg-cell); border: 1px solid var(--border); padding: 12px 16px; min-width: 240px; max-width: 320px;`. Content: club name (body-S), feature description (body-XS, muted), `TIER:` badge in `.mono-caption`, score breakdown `Yes +N / No −N` in `.mono-caption`. 120ms ease-out fade-in (Claude's Discretion default). Use `useEffect` to attach a `mousemove`/`scroll`/`resize` listener that re-reads the anchor rect (or simpler: re-position only on data change — pick the simpler unless tests expose flakiness).</description>
  <files>app/components/matrix/HoverTooltipCard.tsx, app/components/matrix/HoverTooltipCard.module.css</files>
  <commit>feat(infra-redesign-v2-03): &lt;HoverTooltipCard&gt; portaled to document.body (D-16)</commit>
  <automated>npx tsc --noEmit</automated>
</task>

<task>
  <id>03-03</id>
  <description>Build `useHoverTooltip` hook (`useHoverTooltip.ts`) — owns `tooltipData: TooltipData` state. Exposes `handleCellEnter(featureId, clubId, el)` which clears any pending close timer, reads `el.getBoundingClientRect()`, and sets `tooltipData = { featureId, clubId, anchorRect }`. Exposes `handleCellLeave()` which schedules `setTooltipData(null)` after a 100ms timeout via `setTimeout` and stores the timer id in a ref. Exposes `clearTooltip()` for unmount cleanup. The hook does NOT touch DOM directly except via the passed `el` reference. Returns `{ tooltipData, handleCellEnter, handleCellLeave, clearTooltip }`.</description>
  <files>app/components/matrix/useHoverTooltip.ts</files>
  <commit>feat(infra-redesign-v2-03): useHoverTooltip hook with 100ms close grace (D-16)</commit>
  <automated>npx tsc --noEmit</automated>
</task>

<task>
  <id>03-04</id>
  <description>Build `useColumnSelection` hook (`useColumnSelection.ts`) — owns `selectedClubId: string | null` (D-18). Exposes `toggle(clubId)`: if `selectedClubId === clubId` → set null; else → set clubId. Exposes `isSelected(clubId): boolean` returning `selectedClubId === clubId`. Returns `{ selectedClubId, isSelected, toggle }`. The hook does NOT touch CSS — it only plumbs state. Plan 04 wires `selected={isSelected(clubId)}` to every `<DataCell>` in the active column.</description>
  <files>app/components/matrix/useColumnSelection.ts</files>
  <commit>feat(infra-redesign-v2-03): useColumnSelection hook for column-tint state (D-03, D-18 state plumbing)</commit>
  <automated>npx tsc --noEmit</automated>
</task>

<task>
  <id>03-05</id>
  <description>Write `tests/components/HoverTooltipCard.test.tsx`. Tests: (a) renders nothing when `data` is null; (b) when `data` is present, the rendered DOM target is `document.body` (use `render` from `@testing-library/react` and assert via `document.body.contains(screen.getByRole('tooltip'))` after adding `role="tooltip"` to the card root); (c) `top` and `left` style values reflect `anchorRect.bottom + 8` and `anchorRect.left`; (d) club name + feature description + tier badge + score breakdown all appear in the output; (e) test fixture passes a deterministic `Map` so the assertion is stable.</description>
  <files>tests/components/HoverTooltipCard.test.tsx</files>
  <commit>test(infra-redesign-v2-03): &lt;HoverTooltipCard&gt; portal + position + content specs (D-16)</commit>
  <automated>npm test -- --run tests/components/HoverTooltipCard.test.tsx</automated>
</task>

<task>
  <id>03-06</id>
  <description>Write `tests/components/useHoverTooltip.test.tsx` using `renderHook` + `vi.useFakeTimers()`. Tests: (a) `handleCellEnter` immediately sets `tooltipData` with the rect; (b) `handleCellLeave` schedules a null after 100ms — `vi.advanceTimersByTime(99)` keeps data, `vi.advanceTimersByTime(2)` clears it; (c) `handleCellEnter` while a close is pending cancels the timer (re-enter grace); (d) `clearTooltip` synchronously nulls data and cancels timers.</description>
  <files>tests/components/useHoverTooltip.test.tsx</files>
  <commit>test(infra-redesign-v2-03): useHoverTooltip 100ms grace + cancel-on-reenter (D-16)</commit>
  <automated>npm test -- --run tests/components/useHoverTooltip.test.tsx</automated>
</task>

<task>
  <id>03-07</id>
  <description>Write `tests/components/useColumnSelection.test.tsx` using `renderHook`. Tests: (a) initial `selectedClubId` is null, `isSelected(any)` is false; (b) `toggle('real_madrid')` sets selectedClubId, `isSelected('real_madrid')` is true, `isSelected('barca')` is false; (c) `toggle('real_madrid')` again clears it; (d) `toggle('barca')` after `toggle('real_madrid')` switches selection (no multi-select).</description>
  <files>tests/components/useColumnSelection.test.tsx</files>
  <commit>test(infra-redesign-v2-03): useColumnSelection toggle + isSelected (D-18 state)</commit>
  <automated>npm test -- --run tests/components/useColumnSelection.test.tsx</automated>
</task>

<task>
  <id>03-08</id>
  <description>Wave-1 quality gate for plan 03. Run `npx next build` (catches type errors). Run `npm test` (all 3 specs from this plan + plans 01–02 specs + existing). Add CHANGELOG.md v6.2 minor entry: "HoverTooltipCard portaled to body with 100ms close grace + useColumnSelection / useHoverTooltip state hooks. Cross-cell interactivity layer ready for app/page.tsx refactor." Keep under 300 chars.</description>
  <files>CHANGELOG.md</files>
  <commit>docs(infra-redesign-v2-03): changelog v6.2 + close interactivity-layer plan</commit>
  <automated>npm test &amp;&amp; npx next build</automated>
</task>

</tasks>

<verification>
- Wave merge: `npm test &amp;&amp; npx next build` green.
- HoverTooltipCard portal target proven to be `document.body`.
- 100ms close grace + cancel-on-reenter both proven via fake-timer assertions.
- `useColumnSelection.toggle(sameId)` proven to deselect (D-18 click-again-deselect contract).
- `analysis/homepage/results/*.json` unchanged.
- Decision-verification rows appended to VALIDATION.md.
</verification>
