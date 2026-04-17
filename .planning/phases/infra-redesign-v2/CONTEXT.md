# Infra Phase — Visual Redesign v2 (Matrix Homepage + System-Wide Rollout)

> **Status:** Out-of-band infrastructure work, parallel to the v2–v11 product roadmap (ROADMAP.md Phases 1–6). Listed in ROADMAP.md §"Out-of-Band Infrastructure" alongside `infra-ci-cd` and `infra-users-admin`. Does not gate any numbered phase. **Does not change scoring data, JSON results, or feature definitions** — visual layer only.

**Gathered:** 2026-04-17
**Status:** Ready for planning
**Source of truth (Figma):**
- Main page — <https://www.figma.com/design/0H4RyhlgKKRwfc9CGlytzS/FC-Benchmark?node-id=43-36>
- DataCell component (8 states) — <https://www.figma.com/design/0H4RyhlgKKRwfc9CGlytzS/FC-Benchmark?node-id=45-5509>
- Sort component (3 states) — <https://www.figma.com/design/0H4RyhlgKKRwfc9CGlytzS/FC-Benchmark?node-id=45-5542>

<domain>
## Phase Boundary

This phase replaces the **visual layer** of FC Benchmark with the new Figma redesign and propagates the resulting design system across the rest of the app. Concretely:

1. **Design tokens** — replace the cool-blue palette in `app/globals.css` with the redesign's neutral-dark palette + single brand-orange accent. Add Suisse Int'l (body) + Roboto Mono (mono/captions) as the type stack.
2. **Atomic components** — extract `DataCell` (8 states), `SortHeader` (3 states), `MeterRow` (mini progress bar + %), `CategoryFilter` (collapsible list with feature counts), `TypeFilter` (checkboxes), `TopNav` (tab strip with `Unlock` accent tab), `HeaderBar` (logo + title + Get-in-touch CTA), `HoverTooltipCard` (feature description + tier badge + Yes/No scoring).
3. **Homepage refactor** — rebuild `app/page.tsx` matrix with the new components, add the **left sidebar** (Category collapse + Type filter), wire **column-selected state** (orange-brown gradient wash across the highlighted club's column) and the **per-cell hover tooltip**.
4. **System-wide extrapolation** — re-skin `/club/[id]`, `/admin/*`, and existing modals (sign-in, request-access, locked-content) to the new tokens. Apply the **single-orange-CTA-per-surface** rule.

**Not in scope:** changing feature scoring, adding/removing features, changing the underlying data model in `analysis/homepage/results/*.json` or `lib/scoring.ts`. Not rebuilding the Recharts dashboard from scratch — only re-theming it. Not touching the `analysis/` capture scripts.

</domain>

<decisions>
## Implementation Decisions

### Design Tokens (replaces current `:root` in `app/globals.css`)

- **D-01: Neutral-dark grayscale.** Replace `--bg #0d0d14` / `--bg2 #13131e` / `--bg3 #1a1a28` (blue-tinted) with **`--bg-page #0F0F0F`**, **`--bg-cell #1A1A1A`**, **`--bg-hover #383838`**. Replace `--border #252535` with **`--border #262626`**. No remaining blue cast anywhere in the chrome.
- **D-02: Single brand accent.** Replace `--accent #4f6ef7` (blue) with **`--accent #FF490C`** (humbleteam orange). All status colors (`--green`, `--yellow`, `--orange`, `--red`) stay only where data semantics require them (score meters, deltas) — chrome and CTAs unify on the single accent.
- **D-03: Selected-column tint.** New token **`--column-tint: rgb(51, 24, 15)`** (brown-orange wash). Applied as a `linear-gradient` overlay on cells in the currently-selected club column. Implementation: compose two gradients in the cell `backgroundImage` — base layer (`--bg-cell`) + tint overlay — matching the Figma reference code.
- **D-04: Text colors.** Primary text **white**, secondary **`#ABABAB`**. Replaces `--text #e8e8f0` / `--muted #6b6b8a`.
- **D-05: Cell metrics.** Fixed **`40px × 38px`** with **`12px`** padding, **`1px solid var(--border)`** on left/right/top borders only (continuous bottom comes from row stack). Letter-spacing **`-0.3px`** on body, **`-1px`** on mono.
- **D-06: Status semantics preserved.** The score meter (`MeterRow`) continues to colorize via `--green` / `--yellow` / `--orange` / `--red` per existing scoring tiers. Only the chrome accent changes.

### Typography

- **D-07: Body font is Suisse Int'l.** Sizes per Figma variable defs: H5 22/1.4 -2px, Body 16/24 -0.3px, Body S 14/1.4 -0.3px, Body XS 12/1.3 -0.3px.
- **D-08: Mono font is Roboto Mono Medium.** Used for captions (10/13 -1px) and links (12/13 -1px). Section headers (`HEADER & NAVIGATION`, etc.), score deltas (`+85`, `+62`), feature percentages, sort affordances.
- **D-09: Suisse Int'l licensing — DECISION PENDING.** Suisse Int'l is a paid font (Swiss Typefaces). Options:
  - **Option A** — license per-domain (~€500–€2k/year) and self-host as `@font-face`.
  - **Option B** — fall back to **Inter Tight** (free, very close metrics, available on Google Fonts and `next/font`). Picked as default for plan execution **unless owner approves Option A before plan 1**.
  - Either way, Roboto Mono is free (Google Fonts).
  - **Action**: Sergey confirms by start of plan 1; CONTEXT.md is updated with the chosen path before tokens land.

### Components (new `app/components/matrix/*`)

- **D-10: `<DataCell>`** — props: `selected: boolean`, `intermediate: boolean`, `state: 'default' | 'hover'`. 8 visual combinations from Figma node 45:5509. The check icon is a single SVG component reused across selected states. `intermediate` renders the check at 40% opacity (used when a feature is partially present per a future scoring extension; for v1 always `false`).
- **D-11: `<SortHeader>`** — props: `label: string`, `state: 'idle' | 'asc' | 'desc'`, `onSort: () => void`. Renders the label + sort arrows from Figma node 45:5542. Three icon variants supplied as inline SVG (no PNG fetch from Figma asset URLs — those expire in 7 days).
- **D-12: `<HeaderBar>`** — humbleteam wordmark + dot · centered "FC Benchmark" + date · `GET IN TOUCH` outlined CTA right. Date is the build/deploy date (from `process.env.BUILD_DATE` set in `next.config.ts`) — **not** dynamic per request (avoids hydration mismatch).
- **D-13: `<TopNav>`** — single horizontal tab strip across the full page width. Active tab gets bottom border in `--accent`. The `UNLOCK` tab is rendered with a special `<UnlockTab>` variant that has solid orange background. Locked tabs (matching v2–v11 milestones not yet shipped) render at 60% opacity and route to the locked-content modal on click — **reuses existing modal logic**.
- **D-14: `<CategoryFilter>`** — vertical list of feature categories. Each item: name + right-aligned count. Click toggles a section's visibility in the matrix. Wraps the existing category data already encoded in `analysis/homepage/features.ts` (no new data source).
- **D-15: `<TypeFilter>`** — three checkboxes: FC / Federation / League. Filters clubs by their `type` field already present in `analysis/homepage/results/*.json`. **If `type` is not yet on every club JSON**, the planner agent adds a derivation step (lookup table) before this component is wired.
- **D-16: `<HoverTooltipCard>`** — appears anchored to the hovered cell, **portaled** to `document.body` via `createPortal` to escape grid overflow. Shows: club name, feature description (from `features.ts`), `TIER:` badge in mono, scoring breakdown `Yes +N / No −N`. Closes on `mouseleave` after a 100ms grace period to let the cursor cross small gaps.

### Homepage Refactor

- **D-17: `app/page.tsx` is rebuilt** as a Server Component shell + Client Component matrix island. The Server Component loads scores + features + clubs (already done today). The Client Component owns: sort state, sidebar filters (category collapse, type filter), selected-column state, hover-tooltip state.
- **D-18: Selected-column state is `useState<string | null>`** for the active club id. Click on a club header cell or any cell in that column → that column becomes "selected" (column-tint gradient applied to all cells in the column). Click again → deselect.
- **D-19: Sort state is `useState<{ col: 'feature' | 'total' | clubId, dir: 'asc' | 'desc' | null }>`**. Default sort: features in their natural order from `features.ts` (no sort applied).
- **D-20: Sidebar filter state is local to the matrix island.** Category-collapse: a `Set<string>` of collapsed category names. Type-filter: a `Set<'fc' | 'federation' | 'league'>` of allowed types.
- **D-21: Tooltip uses fixed positioning + portal** as in D-16. The cell renders `data-feature` + `data-club` attributes; the tooltip reads them on `mouseenter` and looks up display content from in-memory feature/club maps. **No new server requests on hover.**

### System-Wide Extrapolation

- **D-22: `/club/[id]` page** — re-themed to the new tokens. Stat labels gain mono-caption treatment. Charts stay (don't redesign club page chart system). Single orange CTA: the "Back to matrix" button is white-outlined; only one true accent CTA per page (e.g., a hypothetical "Compare" button).
- **D-23: `/admin/*`** — adopt new tokens. The Recharts dashboard from commit `24b320b` (analytics dashboard redesign) is **re-themed only**: chart colors swap to `--accent` + grayscale grid lines. Admin tables get the new section-header mono-caption style. No structural changes to admin tabs.
- **D-24: Modals** (sign-in, request-access, locked-content) — black bg, `1px solid var(--border)` outline, **single orange CTA** per modal (e.g., "Sign in" or "Send request"). Cancel/secondary actions are text-only or white-outlined.
- **D-25: Single-orange-CTA-per-surface rule.** Documented in `CLAUDE.md` design section after rollout, so future contributors don't add orange to multiple buttons on the same screen.

### Verification

- **D-26: Visual regression by screenshot diff.** Capture the new homepage at 1440×900 and compare against the Figma reference (via Playwright). The diff doesn't have to be pixel-perfect — sub-2% Pixelmatch delta is acceptable; section structure and palette must match exactly.
- **D-27: Build must pass.** `npx next build` is the gate at the end of every plan, per `CLAUDE.md`. `npm test` (Vitest) must pass — no test logic depends on visual chrome, so existing tests should remain green.
- **D-28: Score data must be unchanged.** A pre/post `recalculate-scores.js` run produces an identical JSON output. If anything diverges, the redesign accidentally touched scoring — stop and revert.
- **D-29: Lighthouse a11y score ≥ 90 on the redesigned homepage.** Orange `#FF490C` on `#0F0F0F` is ~6:1 contrast (passes AA). Verify mid-grey text passes too. Keyboard nav: tabs, sort headers, sidebar filters, and cells must all be focusable.

### Claude's Discretion

- Exact pixel size of the sidebar (Figma is ~250px — Claude can pick any value in 220–280px that reads cleanly).
- Order in which atomic components land within plan 2 (parallelizable across one or two executors).
- Whether to colocate `app/components/matrix/*` per-component CSS files or keep one matrix.css.
- Animation timing for hover-tooltip fade-in / column-tint transition (default 120ms ease-out).
- Whether to add a small Storybook-style `/dev/components` route to preview each component in isolation, or rely on the live page for verification.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher, planner, executor) MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — current product context.
- `.planning/ROADMAP.md` — out-of-band infra entry for this phase.
- `CLAUDE.md` — commit / push / build / changelog rules. Every plan in this phase respects them.

### Prior infra precedent
- `.planning/phases/infra-ci-cd/` — pattern for an OOB infra phase.
- `.planning/phases/infra-users-admin/CONTEXT.md` — sibling OOB phase, same template structure.

### Existing codebase (authoritative for "what's there today")
- `.planning/codebase/STACK.md` — Next.js 15 + React 19, plain CSS, no Tailwind. Suisse Int'l + Roboto Mono will be added via `next/font` (Inter Tight as Suisse fallback per D-09).
- `.planning/codebase/STRUCTURE.md` — `app/components/` is the place for new matrix components.
- `.planning/codebase/CONVENTIONS.md` — plain-CSS-only, hand-written, minimal-deps aesthetic.

### Existing code this phase replaces or edits
- `app/globals.css` — `:root` block fully replaced. Existing utility classes preserved unless they reference removed tokens.
- `app/page.tsx` (1072 LOC) — refactored to use new components. Logic preserved; markup rebuilt.
- `app/club/[id]/page.tsx` — re-themed (token swap only).
- `app/admin/**` — re-themed; Recharts dashboard re-colored.
- Modal components in `app/` — re-themed.
- `app/layout.tsx` — `next/font` integration for Suisse Int'l (or Inter Tight) + Roboto Mono.
- `next.config.ts` — `BUILD_DATE` env var for HeaderBar (D-12).

### Reference assets (Figma)
- Cell component code (Tailwind, to be ported to plain CSS): see Figma node 45:5509 — 8 states encoded with two gradient overlays per state.
- Sort component code: see Figma node 45:5542 — 3 SVG variants.
- Variables block (Figma): tokens already cataloged in D-01 through D-08.

### External (web)
- Inter Tight (Suisse fallback): <https://fonts.google.com/specimen/Inter+Tight>
- Roboto Mono: <https://fonts.google.com/specimen/Roboto+Mono>
- next/font: <https://nextjs.org/docs/app/building-your-application/optimizing/fonts>
- Pixelmatch (visual regression): <https://github.com/mapbox/pixelmatch>

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`app/globals.css`** utility classes — `.hide`, layout helpers, etc. Keep; just swap their token references.
- **`app/page.tsx`** business logic — sort, filter, locked-content modal triggers, sign-in/request-access flow already wired to `authEmail` and `sendAccessRequest`. Preserve all of it.
- **`lib/scoring.ts`** — untouched. Score computation is data-layer; redesign is pure visual.
- **`lib/data.ts`** — untouched.
- **Modal CSS classes** — already defined in `app/globals.css` (per memory observation 1066). Only token swap needed.
- **Recharts dashboard** (commit 24b320b) — survives; re-themed.

### Established Patterns
- **No Tailwind, no shadcn, no CSS framework.** Plain CSS via `app/globals.css` and colocated CSS modules where helpful.
- **Server Components by default**, Client Components for interactivity. The matrix island (sort/filter/hover state) is the largest Client Component in the app.
- **TypeScript strict mode.**
- **Hand-written, minimal dependencies.** Adding only `next/font` integrations + (optionally) `pixelmatch` as devDep for visual regression.

### Integration Points
- `app/layout.tsx` — `next/font` declarations for Suisse Int'l (or Inter Tight) and Roboto Mono. CSS variables exposed via the `font.variable` API.
- `app/globals.css` — `:root` token rewrite + new utility classes (`.mono-caption`, `.cell-grid`, `.column-tint`).
- `app/components/matrix/*` — new directory for atomic components.
- `next.config.ts` — `env.BUILD_DATE = new Date().toISOString().slice(0,10)` for the HeaderBar.

</code_context>

<specifics>
## Specific Ideas

- **Plan order (parallelization-friendly):**
  1. Tokens + fonts (foundational; gate for all others)
  2. Atomic components (`DataCell`, `SortHeader`, `MeterRow`, `HeaderBar`, `TopNav`, `CategoryFilter`, `TypeFilter`) — single dev can build serially in one plan, OR split into 2 parallel plans (`2a` chrome / `2b` data cells)
  3. Hover tooltip + column-selected state (depends on `DataCell` from plan 2)
  4. Refactor `app/page.tsx` to consume plans 1–3
  5. Extrapolate to `/club`, `/admin`, modals
- **Visual regression artefact** — write the Pixelmatch diff PNG to `tests/visual/` and commit it on each plan close, so future drift is obvious in PR review.
- **Inter Tight fallback letter-spacing** is slightly wider than Suisse Int'l. If we go that route, override `letter-spacing: -0.32px` on body to compensate (visual eyeball check vs Figma in plan 1).
- **Keyboard nav** — `<DataCell>` should be focusable (`tabIndex={0}`) so the hover tooltip can also fire on `focus`. Useful both for a11y and for screenshot tests.
- **Mobile** is **out of scope for this phase** unless Sergey adds it explicitly. The matrix at 33 columns × 40px = 1320px will horizontally scroll on small viewports; the redesign's responsive behavior isn't specified in Figma.

</specifics>

<deferred>
## Deferred Ideas

### Visual / interaction
- Mobile layout for the matrix (responsive collapse, swipe-by-column). Likely a follow-up phase once the desktop redesign ships.
- Animated reveal of section headers on scroll.
- Sticky first column (feature names) when scrolling horizontally on narrow viewports.
- Dark/light theme toggle — not in Figma; redesign is dark-only.
- Per-cell click → opens a modal with full feature evidence (screenshot from `crosscheck/img/`). Already partially exists; not redesigned in this phase.

### Data / scoring
- "Intermediate" cell state (`selected && intermediate`) wired to a real partial-credit scoring extension. Component supports it; data layer doesn't yet.
- Deltas (`+85` style) animated on initial page load.

### System
- Storybook (or equivalent) for component previews. Optional `/dev/components` route during development; remove before ship.
- Visual regression in CI — Pixelmatch run on PR with screenshot artefact upload to GitHub.
- Design token export to a JSON/CSS bundle for downstream products (analysis tooling, marketing site).

### Branding
- Favicon + OG image refresh to match new palette. Currently uses `app/favicon.ico`.
- Custom 404 / loading screens themed to the redesign.

</deferred>

---

*Phase: infra-redesign-v2 (out-of-band)*
*Context gathered: 2026-04-17*
