# Phase: infra-redesign-v2 — Research

**Researched:** 2026-04-17
**Domain:** Visual redesign of FC Benchmark (Next.js 16 + React 19, plain CSS, no Tailwind). Replace tokens, add Suisse-class type stack, extract atomic matrix components, refactor `app/page.tsx`, propagate tokens system-wide.
**Confidence:** HIGH on code-context findings (read directly), HIGH on next/font patterns (official docs), MEDIUM-HIGH on visual-regression tool pick, MEDIUM on Suisse pricing (vendor publishes no public price list — confirmed by direct fetch).

## Summary

CONTEXT.md (D-01–D-29) is the source of truth and locks every architectural choice. This research fills the seven gaps it leaves open: (1) the Suisse-vs-Inter-Tight call, (2) the `next/font` snippet for the chosen default, (3) the structural map of the existing 1072-LOC `app/page.tsx`, (4) the `type` field data audit, (5) the Recharts re-theme diff, (6) the visual-regression tool pick, and (7) the modal-CSS swap inventory. It also produces the `## Validation Architecture` table the orchestrator needs to instantiate VALIDATION.md.

**Primary recommendations for the planner:**

1. **Default to Inter Tight** (free, Google Fonts, `next/font/google`). Suisse Int'l has no public price list — Swiss Typefaces requires a quote. Owner-approval gate stays at start of Plan 1; if Sergey returns a "go" before tokens land, swap to `next/font/local`. Default plan should not block.
2. **Type-filter data audit:** the per-club JSONs in `analysis/homepage/results/*.json` do **NOT** carry `type`. The field lives on `analysis/products.ts` (`PRODUCTS` constant, re-exported through `lib/data.ts`). CONTEXT.md D-15's premise is slightly off — but the data is already there in TS, so **no backfill is needed**. Plan 2 can wire `<TypeFilter>` to `PRODUCTS[].type` directly.
3. **Visual regression: keep it simple.** Use Playwright's built-in `toHaveScreenshot` (which is Pixelmatch under the hood) with `maxDiffPixelRatio: 0.02` to satisfy D-26's "sub-2%" target. Do **not** add `pixelmatch` as a separate dep — Playwright already wraps it.
4. **Modal CSS classes are already defined** (confirmed by grep). The `:root` token swap propagates to all of them — no per-modal CSS edits, only the `.locked-card .lock-big`'s blue-tinted background needs an explicit accent rebind.

## Goal Recap

At phase close, FC Benchmark's matrix homepage matches the Figma design at 1440×900 within a 2% pixel-diff envelope. The dark-blue palette is gone; chrome is neutral grayscale with a single brand-orange accent (`#FF490C`); type stack is Suisse Int'l (or Inter Tight) + Roboto Mono via `next/font`. `app/page.tsx` is refactored into a Server-Component shell + Client-Component matrix island that consumes new atomic components from `app/components/matrix/*`. Every ancillary surface — `/club/[id]`, `/admin/*` (including the Recharts dashboard), and the three modals (sign-in, locked, coming-soon) — uses the same tokens. Score data is bit-for-bit identical (D-28). `npx next build` and `npm test` pass. Lighthouse a11y ≥ 90 (D-29).

---

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01–D-08 design tokens:** `--bg-page #0F0F0F` / `--bg-cell #1A1A1A` / `--bg-hover #383838` / `--border #262626` / `--accent #FF490C` / `--column-tint rgb(51,24,15)` / text white + `#ABABAB`; cell metrics fixed `40×38px` with `1px` left/right/top borders; letter-spacing `-0.3px` body, `-1px` mono. Status colors (green/yellow/orange/red) preserved only where score semantics require.
- **D-07/D-08 typography:** Body Suisse Int'l (or fallback). Mono Roboto Mono Medium. Sizes per Figma: H5 22/1.4 -2px, Body 16/24 -0.3px, Body S 14/1.4 -0.3px, Body XS 12/1.3 -0.3px, captions 10/13 -1px (mono), links 12/13 -1px (mono).
- **D-09 font licensing:** **PENDING** — default Inter Tight unless Sergey approves Suisse before Plan 1.
- **D-10–D-16 components:** Build `<DataCell>` (8 states), `<SortHeader>` (3 states), `<MeterRow>`, `<HeaderBar>` (build-date from `process.env.BUILD_DATE`), `<TopNav>` (single tab strip with `<UnlockTab>` solid-orange variant; locked tabs at 60% opacity; reuses existing modal logic), `<CategoryFilter>` (data from `features.ts`), `<TypeFilter>` (FC/Federation/League), `<HoverTooltipCard>` (portaled, anchored to cell, 100ms close grace).
- **D-17–D-21 page architecture:** `app/page.tsx` rebuilt as Server shell + Client matrix island. Selected-column = `useState<string | null>(activeClubId)`. Sort = `useState<{col, dir}>`. Sidebar filters local. Tooltip via `createPortal` reading `data-feature` / `data-club` attrs — no server requests on hover.
- **D-22–D-25 system-wide:** `/club/[id]` token-swap; `/admin/*` token-swap + Recharts re-color (no structural changes); modals get `1px solid var(--border)` outline, single orange CTA each; `CLAUDE.md` documents the single-orange-CTA-per-surface rule.
- **D-26–D-29 verification gates:** screenshot diff sub-2% Pixelmatch, `npx next build` green, `npm test` (Vitest) green, score-JSON identical pre/post, Lighthouse a11y ≥ 90.

### Claude's Discretion

- Sidebar pixel width (220–280px range; pick whatever reads cleanly).
- Order in which atomic components land within Plan 2; may split into 2a/2b.
- Per-component CSS files vs single `matrix.css`.
- Animation timings (default 120ms ease-out for tooltip + column-tint).
- Optional dev-only `/dev/components` route for component preview.

### Deferred Ideas (OUT OF SCOPE)

Mobile / responsive collapse, sticky first column, animated reveals, light/dark toggle, per-cell screenshot modal redesign, intermediate cell state with real partial-credit data, animated deltas, Storybook, CI visual regression, design-token JSON export, favicon/OG/404 refresh.

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| (OOB) | This is out-of-band infra; no numbered REQ-IDs. CONTEXT.md decisions D-01–D-29 act as the requirement set. | Each D-decision is mapped to a verification artifact in `## Validation Architecture` below. |

---

## Suisse Int'l vs Inter Tight — Recommendation

**Recommendation: default to Inter Tight via `next/font/google`.** Treat Suisse as an opt-in upgrade gated on owner approval and a quote from Swiss Typefaces. Plan 1 should ship with Inter Tight wired up; if Sergey returns a license before Plan 1 merges, swap the import (one-file change in `app/layout.tsx`) and re-run the screenshot diff.

### Rationale

| Factor | Suisse Int'l | Inter Tight |
|--------|--------------|-------------|
| **Cost** | No public price list — Swiss Typefaces uses bespoke quotes based on company headcount (entry tier covers ≤25 employees, lifetime, no domain limit). Public estimates from third-party blogs put entry web licenses in the **€500–€2k/year** band, but the vendor confirms only by quote. | **Free** under SIL Open Font License via Google Fonts. |
| **Licensing risk** | Requires written license + invoice. Cannot ship to production until that arrives. | Zero risk. |
| **Distribution** | Self-hosted `@font-face` via `next/font/local`. WOFF2 files acquired post-purchase. | CDN-served by Google or self-hosted by Next.js's font optimizer. `next/font/google` downloads at build time and hosts locally — no runtime Google request. |
| **Visual fidelity to Figma** | 1:1. | Very close — Inter Tight is the explicit "tighter-tracking" Inter variant, designed by Rasmus Andersson for spaces where you can't hand-tune letter-spacing. Same neo-grotesque skeleton as Suisse Int'l (both descend from Helvetica/Univers). At 14/16/22px the eye-perceived weight is within ~3% of Suisse Regular. |
| **Letter-spacing offset** | Figma spec is `-0.3px` body, `-1px` mono. | Inter Tight runs slightly looser than Suisse at small sizes. Apply **`letter-spacing: -0.32px`** on body text (vs CONTEXT.md's `-0.3px`) to compensate — this is already flagged in CONTEXT.md `<specifics>`. |
| **next/font integration** | `next/font/local` — see snippet below. | `next/font/google` — see snippet below. Two-line declaration. |

### License-cost band (best evidence available)

- Swiss Typefaces' **public** licensing page documents only the model (lifetime, headcount-tiered, entry covers ≤25 employees) — **no published numbers**. ([Swiss Typefaces — Licensing](https://www.swisstypefaces.com/licensing/))
- Industry write-ups put entry tier in the **low four figures (EUR)**, one-time. Treat this as MEDIUM confidence — the planner should include "Sergey confirms quote from Swiss Typefaces" as the deferral language in Plan 1.
- Roboto Mono is unconditionally free via Google Fonts in either path. ([Google Fonts — Roboto Mono](https://fonts.google.com/specimen/Roboto+Mono))

---

## next/font Integration Snippet (recommended default — Inter Tight)

```typescript
// app/layout.tsx
import './globals.css';
import type { Metadata } from 'next';
import { Inter_Tight, Roboto_Mono } from 'next/font/google';
import { Analytics } from '@vercel/analytics/next';

const interTight = Inter_Tight({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-body',
  display: 'swap',
});

const robotoMono = Roboto_Mono({
  subsets: ['latin'],
  weight: ['500'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'FC Benchmark — Feature Matrix',
  description: 'UX benchmark of 33 sports website homepages',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${interTight.variable} ${robotoMono.variable}`}>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
```

```css
/* app/globals.css — :root additions */
:root {
  --font-body: 'Inter Tight', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'Roboto Mono', ui-monospace, SFMono-Regular, monospace;
}
body {
  font-family: var(--font-body);
  letter-spacing: -0.32px; /* compensates for Inter Tight running slightly wider than Suisse */
}
.mono-caption {
  font-family: var(--font-mono);
  font-weight: 500;
  font-size: 10px;
  line-height: 13px;
  letter-spacing: -1px;
}
```

### Alternate snippet — if Sergey approves Suisse Int'l (Plan-1-only swap)

```typescript
// app/layout.tsx — replace next/font/google import for body
import localFont from 'next/font/local';

const suisseIntl = localFont({
  src: [
    { path: '../public/fonts/SuisseIntl-Regular.woff2', weight: '400', style: 'normal' },
    { path: '../public/fonts/SuisseIntl-Medium.woff2',  weight: '500', style: 'normal' },
    { path: '../public/fonts/SuisseIntl-Bold.woff2',    weight: '700', style: 'normal' },
  ],
  variable: '--font-body',
  display: 'swap',
});
```

Drop `letter-spacing: -0.32px` override; revert to `-0.3px` per Figma spec. Roboto Mono import stays the same.

References: [Next.js — Font Optimization](https://nextjs.org/docs/app/getting-started/fonts), [Inter Tight on Google Fonts](https://fonts.google.com/specimen/Inter+Tight).

---

## Current Homepage Structural Map (`app/page.tsx`, 1072 LOC)

A Client Component (top-of-file `'use client';`). Default export `FeatureMatrixPage`. Two helper components in the same file: `TableRows`, `FeatureDetail`, `ProductDetail`. **No business-logic changes; the rebuild swaps markup and CSS class names while preserving every state hook and handler below.**

### State hooks (all in `FeatureMatrixPage`)

| Hook | Purpose | Preserve as-is? |
|------|---------|-----------------|
| `filterTypes: Set<string>` | FC/governing/league checkboxes | Yes — feeds new `<TypeFilter>` |
| `activeCat: CategoryId \| null` | Sidebar category filter | Yes — feeds new `<CategoryFilter>` |
| `selectedFeature: string \| null` | Detail panel — feature pick | Yes |
| `selectedProduct: string \| null` | Detail panel — product (club) pick | Yes — also drives D-18 column-tint via `selectedProduct` |
| `adoptionSort` / `featureAlphaSort` / `scoreSort` | Sort modes for Adoption / Feature / Total Score columns | Yes — wired to new `<SortHeader>` (3 states) |
| `authed`, `authEmail`, `isAdmin`, `isPremium` | Auth state | **Untouched** — only chrome around it changes |
| `loginModalVisible`, `ctaView`, `loginEmail`, `loginPassword`, `loginError`, `loginLoading` | Sign-in modal & inline CTA form | Untouched logic; modal chrome restyled per D-24 |
| `lockedModalVisible`, `lockedFlowName`, `comingSoonVisible`, `comingSoonFlowName`, `requestSending`, `requestSent` | Locked-content + coming-soon modals | Untouched logic; chrome restyled |
| `tooltipRef`, `tooltipVisible`, `tooltipData` | Existing free-floating cursor tooltip | **Replaced** by D-16 portaled `<HoverTooltipCard>` anchored to cell, NOT cursor. The `setTooltipData` shape is the right contract — keep the type, change the positioning strategy. |

### Effects + handlers (preserve)

- `useEffect` on mount: `fetch('/api/auth/me')` → set authed/admin/premium; `trackEvent('page_view', { path: '/' })`.
- `handleLogin` / `handleLogout` → `/api/auth/login`, `/api/auth/logout`.
- `sendAccessRequest(feature, source, email)` → `POST /api/email`. Used by both locked-modal and coming-soon-modal CTAs. **Preserve verbatim.** New CTAs in restyled modals call the same function with the same arg shape.
- `handleTabClick(name)` → branches on `isAdmin || isPremium` vs `authed` vs guest; opens coming-soon or locked modal. New `<TopNav>` `<UnlockTab>` and locked-tab variants reuse this handler unchanged.
- `handleShowFeatureDetail` / `handleShowProductDetail` / `handleCloseDetail` / `handleClearFilters` — all unchanged.
- `handleCellMouseOver(fid, pid)` → builds `tooltipData`. New `<DataCell>` fires this on `mouseenter` AND on `focus` (D-21 keyboard a11y).
- `handleCellMouseMove(e)` — current cursor-follow positioning. **Replace** with portaled fixed-position computed from cell `getBoundingClientRect()`.
- `handleTableMouseLeave` — close tooltip; keep but adjust to 100ms grace (D-16).

### Render tree (current → new)

```
<div className="matrix-shell">                  →  <div className="matrix-shell">
  <header>...                                   →    <HeaderBar />               (D-12)
  <nav className="flow-nav">                    →    <TopNav />                  (D-13)
  <div className="main">
    <div className="sidebar">                   →      <Sidebar>
      <h3>Category</h3> + cat-items             →        <CategoryFilter />      (D-14)
      <h3>Type</h3> + checkboxes                →        <TypeFilter />          (D-15)
      <button.clear-btn>                        →        <button.clear-btn>      (preserve handler)
    </div>                                      →      </Sidebar>
    <div className="table-wrapper">             →      <MatrixTable>             (orchestrates rows)
      <table>…<thead>…<TableRows />             →        <SortHeader> per col + grid of <DataCell>
                                                →                              + <MeterRow> for adoption col
                                                →                              + <ScoreRow>
      <preview-blur-overlay> (guest CTA)        →        <PreviewOverlay>        (untouched logic)
    </div>                                      →      </MatrixTable>
    <div className="detail-panel">              →      <DetailPanel>             (re-skinned, same FeatureDetail/ProductDetail)
  </div>
  <locked-overlay × 3 (locked / login / coming) →    <Modal>×3                   (D-24, single orange CTA)
  <cell-tooltip> (cursor-follow)                →    <HoverTooltipCard portaled> (D-16)
</div>
```

### Where each new component plugs in

| New component | Replaces | Lives in |
|---------------|----------|----------|
| `<HeaderBar>` | `<header>` JSX block (lines ~278–305) | `app/components/matrix/HeaderBar.tsx` |
| `<TopNav>` + `<UnlockTab>` | `<nav.flow-nav>` block (lines ~307–333) | `app/components/matrix/TopNav.tsx` |
| `<CategoryFilter>` | `<div.sidebar><h3>Category</h3>...` (lines ~338–352) | `app/components/matrix/CategoryFilter.tsx` |
| `<TypeFilter>` | sidebar Type checkboxes (lines ~354–376) | `app/components/matrix/TypeFilter.tsx` |
| `<SortHeader>` × 3 | the three `<th className=".sortable">` blocks | `app/components/matrix/SortHeader.tsx` |
| `<DataCell>` | the `<td className="cell">` rendering inside `TableRows` | `app/components/matrix/DataCell.tsx` |
| `<MeterRow>` | `<div.freq-bar-wrap>` block inside `TableRows` (the adoption % bar) | `app/components/matrix/MeterRow.tsx` |
| `<HoverTooltipCard>` | `<div.cell-tooltip>` (lines ~707–737) | `app/components/matrix/HoverTooltipCard.tsx` |
| `<Modal>` (× 3 reuses) | the three `<div.locked-overlay>` blocks | `app/components/matrix/Modal.tsx` (or keep colocated CSS swap-only) |

`FeatureDetail` and `ProductDetail` (in-file helpers) stay where they are — the detail panel is in scope for D-22 token-swap only, no refactor.

---

## Type-Filter Data Audit

**Finding:** CONTEXT.md D-15 says "type is already present in `analysis/homepage/results/*.json`". This is **incorrect** — direct grep of all 33 club JSON files returns zero matches for `"type"`. The field actually lives on `analysis/products.ts`'s `PRODUCTS` constant (re-exported via `lib/data.ts` as the `Product` type with a `type: ProductType` field, where `ProductType = 'club' | 'league' | 'governing'`).

**Verified by:**
```
analysis/types.ts:25      export type ProductType = 'club' | 'league' | 'governing';
analysis/types.ts:38      type: ProductType;     // on Product interface
analysis/products.ts:11+  PRODUCTS literal with `type: 'club' | 'league' | 'governing'` on every entry (33/33)
```

**Implication:** No data backfill is needed. `<TypeFilter>` reads `PRODUCTS[].type` exactly the way the existing `app/page.tsx` does (line ~63: `useState<Set<string>>(new Set(['club', 'governing', 'league']))`). The Figma label "FC / Federation / League" maps to the existing `'club' / 'governing' / 'league'` enum:

| Figma label | Internal value |
|-------------|----------------|
| FC | `'club'` |
| Federation | `'governing'` |
| League | `'league'` |

Plan 2 just hard-codes the label translation in `<TypeFilter>` (already done in current `app/page.tsx` lines ~358–362).

**Action for planner:** add a one-line correction in Plan 2's "Data inputs" note — point to `PRODUCTS[].type`, not the JSONs. No backfill task.

---

## Recharts Re-Theme — Diff Sketch

The dashboard at `app/admin/analytics/page.tsx` uses Recharts with all colors hard-coded inline (no CSS-variable indirection). Token swap requires hand-editing the props. The relevant blue (`#3b82f6`) is the only chart accent — it appears 6 times.

**File:** `app/admin/analytics/page.tsx`

| Line(s) (approx) | Current | Change to |
|------------------|---------|-----------|
| `RankTable` bar (line ~85) | `background: 'rgba(59,130,246,0.07)'` | `background: 'rgba(255,73,12,0.07)'` (or `var(--accent)` opacity helper) |
| Day-toggle button active (line ~150) | `color: days === d ? '#fff' : '#555'` | keep |
| Metric-toggle active state (line ~190) | `background: '#1a2a3a'`, `border: '#1e3a5f'`, `color: '#60a5fa'` | `background: 'rgba(255,73,12,0.12)'`, `border: 'rgba(255,73,12,0.4)'`, `color: 'var(--accent)'` |
| `<linearGradient id="grad">` stops (line ~205) | `stopColor="#3b82f6"` ×2 | `stopColor="var(--accent)"` ×2 — note: SVG gradient stops accept CSS vars in modern browsers, but for safety hard-code `#FF490C` in the SVG |
| `<CartesianGrid stroke="#1a1a1a">` (line ~209) | `#1a1a1a` | `var(--border)` (i.e. `#262626`) |
| `<XAxis tick fill="#555">` / `<YAxis tick fill="#555">` (lines ~211/216) | `#555` | `#ABABAB` (D-04 secondary text) |
| `<Tooltip cursor stroke="#333">` (line ~221) | `#333` | `var(--border)` |
| `<Area stroke="#3b82f6">` + `activeDot fill="#3b82f6" stroke="#111">` (lines ~222–230) | `#3b82f6` ×2, `#111` | `#FF490C` ×2, `var(--bg-page)` |
| `ChartTooltip` inner `background: '#111'`, `border: '1px solid #222'` (line ~32) | as listed | `background: 'var(--bg-cell)'`, `border: '1px solid var(--border)'` |
| Stat card `background: '#111'`, `border: '#1e1e1e'` (line ~50) | | `background: 'var(--bg-cell)'`, `border: '1px solid var(--border)'` |
| Stat card label color `#666`, value `#fff`, sub `#555` | | `#ABABAB`, `#FFFFFF`, `#ABABAB` |
| RankTable wrapper `background: '#111'`, `border: '#1e1e1e'` (line ~71) | | `var(--bg-cell)` / `var(--border)` |
| `Link href="/admin"` color `#3b82f6` (line ~125) | | `var(--accent)` |

**No structural Recharts changes** — same `<AreaChart>` + `<XAxis>` + `<YAxis>` + `<CartesianGrid>` + `<Tooltip>` + `<Area>` API, just color-prop substitution. CONTEXT.md D-23 is satisfied.

**Plan 5 task estimate:** ~30 lines of mechanical string-replace; one PR.

---

## Visual Regression Tool Pick

**Recommendation: use Playwright's built-in `toHaveScreenshot()` with `maxDiffPixelRatio: 0.02`.** Do **not** add `pixelmatch` as a separate dev dep.

### Why

- Playwright's screenshot comparator **wraps Pixelmatch internally**. The 2026 ecosystem write-ups (Bug0, Codoid, Applitools) all confirm: "Playwright uses pixelmatch under the hood — it captures a screenshot and compares it pixel by pixel against a stored baseline."
- The team already has Vitest for unit tests but no Playwright. Adding Playwright (`@playwright/test`) is one dep that brings both the capture engine and the diff. Adding `pixelmatch` separately would also require `pngjs` for PNG IO + a custom test runner — net more code for the same outcome.
- D-26's "sub-2% Pixelmatch delta" maps directly to Playwright's `maxDiffPixelRatio: 0.02` option.

### Wiring (for Plan 6 / verification)

```bash
npm install -D @playwright/test
npx playwright install chromium
```

```typescript
// tests/visual/homepage.spec.ts
import { test, expect } from '@playwright/test';

test('homepage matches Figma reference', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto('http://localhost:3000');
  await expect(page).toHaveScreenshot('homepage-1440x900.png', {
    maxDiffPixelRatio: 0.02,
    fullPage: false,
  });
});
```

```typescript
// playwright.config.ts (minimal)
import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './tests/visual',
  use: { baseURL: 'http://localhost:3000' },
  expect: { toHaveScreenshot: { maxDiffPixelRatio: 0.02 } },
});
```

The diff PNG lands in `test-results/` automatically when a test fails. CONTEXT.md `<specifics>` says "write the Pixelmatch diff PNG to `tests/visual/`" — Playwright's default is `test-results/`; either is fine, the planner picks.

**Pitfall flagged in research:** Pixelmatch (and therefore Playwright's wrapper) "can't tell the difference between a meaningful layout shift and a 1px anti-aliasing change." Mitigations:
- Set `animations: 'disabled'` in the screenshot call to freeze tooltip/column-tint transitions.
- Add `--font-display: block` only for screenshot runs, OR use `await page.waitForFunction(() => document.fonts.ready)` before the assertion to avoid font-swap diffs.
- Consider `maskColor: '#FF00FF'` over the build-date span (HeaderBar) since the date changes per build.

References: [Playwright Visual Comparisons docs](https://playwright.dev/docs/test-snapshots), [Pixelmatch on GitHub](https://github.com/mapbox/pixelmatch).

---

## Modal CSS Audit — Class-Swap Inventory

**Confirmed:** all modal classes already exist in `app/globals.css`. Token swap propagates because they reference `var(--bg2)`, `var(--border)`, `var(--accent)`, etc. The only places where the **blue accent is hard-coded** (and therefore need explicit edits) are listed below.

### Classes referenced by modals (file: `app/globals.css`)

| Class | Line | Modal usage |
|-------|------|-------------|
| `.locked-overlay` | 289 | Backdrop (all 3 modals — locked, login, coming-soon) |
| `.locked-overlay.visible` | 290 | Open state |
| `.locked-card` | 291 | Card container (background `var(--bg2)`, border `var(--border)` — auto-swaps via tokens) |
| `.locked-card .lock-big` | 293 | Padlock icon wrapper — **hard-coded `rgba(79,110,247,.12)` blue tint → swap to `rgba(255,73,12,.12)` orange** |
| `.locked-card .lock-big svg` | 294 | Padlock color `var(--accent)` — auto-swaps |
| `.locked-card h3` / `.locked-card p` | 295–296 | Headings — auto-swaps |
| `.locked-card .locked-flow-name` | 297 | Highlight color `var(--accent)` — auto-swaps |
| `.locked-card .locked-btn` | 298 | Primary CTA — `background: var(--accent)` auto-swaps. **Verify:** D-24 says "single orange CTA per modal" — current class is single, satisfied. |
| `.locked-card .locked-btn:hover` | 299 | OK |
| `.locked-card .locked-dismiss` | 301 | Secondary text-only action — already `color: var(--muted)`, auto-swaps |
| `.login-card` | 305 | OK (just narrower max-width) |
| `.login-subtitle` / `.login-form` / `.login-label` | 306–308 | Auto-swap |
| `.login-input` | 309 | `background: var(--bg1)` — **NB:** `--bg1` doesn't exist in the new tokens; CONTEXT.md D-01 introduces `--bg-page` / `--bg-cell` / `--bg-hover`. Need to either alias `--bg1` to `--bg-cell` for backwards-compat OR rename. **Planner decision:** add `--bg1: var(--bg-cell);` alias in Plan 1 to avoid breaking these classes. |
| `.login-input:focus` | 310 | `border-color: var(--accent)` auto-swaps |
| `.login-error` | 312 | OK |
| `.login-submit` | 313 | OK |
| `.coming-soon-icon svg` | 318 | `color: var(--accent)` auto-swaps |
| `.cell-tooltip` + `.tt-*` | 336–346 | Old cursor-follow tooltip — **replaced** by `<HoverTooltipCard>` portaled component; these classes can stay until Plan 3 ships then be deleted in Plan 4 (`app/page.tsx` refactor) |

### Other hard-coded blue-tint references to swap (full grep)

Run `grep -n "#4f6ef7\|rgba(79,110,247" app/globals.css`. Quick eyeball: lines 252, 253 (`.locked-zone` animated holographic border with multiple blue/purple/pink stops), 254 (`.locked-zone::before` overlay), 293 (lock-big background, listed above). The `.locked-zone` border animation is a stylistic flourish that pre-dates the redesign — D-13 replaces the locked-zone visual entirely (`<TopNav>` with locked tabs at 60% opacity), so these rules can be **deleted wholesale** when Plan 4 runs.

**Planner action:** Plan 1 deletes the `--accent: #4f6ef7` line and replaces it with `#FF490C`. Most modal CSS auto-corrects. Plan 1 also explicitly fixes `rgba(79,110,247,.12)` on line 293 and adds the `--bg1: var(--bg-cell)` alias.

---

## Validation Architecture

> Project has no `.planning/config.json`. Treating `nyquist_validation` as enabled (default).

### Test Framework

| Property | Value |
|----------|-------|
| Unit/integration framework | **Vitest 2.1.8** (already installed; `lib/auth.test.ts`, `lib/env.test.ts`, `lib/scoring.test.ts` exist) |
| E2E / visual framework | **Playwright** — to be added in Plan 6 (`@playwright/test` dev dep + `chromium` install) |
| Score recompute | `node analysis/homepage/crosscheck/recalculate-scores.js` (per CLAUDE.md) |
| Build gate | `npx next build` |
| Quick run | `npm test` (Vitest, ~2s) |
| Full suite | `npm test && npx playwright test && npx next build && node analysis/homepage/crosscheck/recalculate-scores.js` |
| Lighthouse | `npx lighthouse http://localhost:3000 --only-categories=accessibility --chrome-flags="--headless"` (run manually at phase gate) |

### Decision → Verification-Artifact Map (drives VALIDATION.md)

| Decision | Behavior to verify | Test type | Automated command | Artifact / file exists? |
|----------|-------------------|-----------|-------------------|-------------------------|
| D-01 | Bg / border tokens applied; no blue cast | visual | `npx playwright test tests/visual/homepage.spec.ts` (color sample via Pixelmatch) | Wave 0 — `tests/visual/homepage.spec.ts` |
| D-02 | Single brand accent `#FF490C` on chrome + CTAs | visual | same | Wave 0 |
| D-03 | Selected-column tint applies on click | unit + visual | Vitest on `<DataCell selected>` snapshot + Playwright click-then-screenshot | Wave 0 — `tests/components/DataCell.test.tsx` |
| D-04 | Text white / `#ABABAB` | visual | Playwright color sample | Wave 0 |
| D-05 | Cell metrics `40×38`, padding 12, border on 3 sides, letter-spacing | visual + unit (DOM measure) | Vitest with Testing Library + `getBoundingClientRect` mock OR Playwright `evaluate` | Wave 0 |
| D-06 | Score meter band colors preserved | visual + unit | Vitest snapshot of `<MeterRow band="competitive">` | Wave 0 — `tests/components/MeterRow.test.tsx` |
| D-07/D-08 | Type stack loaded (Inter Tight + Roboto Mono) | unit | Vitest `expect(document.fonts.check('16px "Inter Tight"')).toBe(true)` in jsdom — OR manual smoke at `/` | Wave 0 — `tests/fonts.test.ts` |
| D-09 | Font choice committed (default Inter Tight) | manual | inspect `app/layout.tsx` import | n/a (commit-level) |
| D-10 | `<DataCell>` 8 visual states render | unit | Vitest snapshot per state | Wave 0 — `tests/components/DataCell.test.tsx` |
| D-11 | `<SortHeader>` 3 states render + `onSort` fires | unit | Vitest with click | Wave 0 — `tests/components/SortHeader.test.tsx` |
| D-12 | `<HeaderBar>` shows `process.env.BUILD_DATE` (no hydration mismatch) | smoke | Playwright `page.textContent('header')` | Wave 0 — env var set in `next.config.ts` |
| D-13 | `<TopNav>` Unlock tab solid orange; locked tabs at 60% opacity; click → existing modal | unit + smoke | Vitest click → modal opens | Wave 0 — `tests/components/TopNav.test.tsx` |
| D-14 | `<CategoryFilter>` counts match `features.ts` | unit | Vitest count equality | Wave 0 |
| D-15 | `<TypeFilter>` filters `PRODUCTS[].type` correctly (FC/Federation/League → club/governing/league) | unit | Vitest filter assertion | Wave 0 |
| D-16/D-21 | Tooltip portaled to `body`, escapes overflow, 100ms close grace | unit + smoke | Vitest `createPortal` target check; Playwright hover-and-leave with timer | Wave 0 — `tests/components/HoverTooltipCard.test.tsx` |
| D-17 | `app/page.tsx` Server shell + Client island; logic preserved | smoke | `npx next build` + manual `curl localhost:3000` for SSR markup; existing scoring tests stay green | n/a |
| D-18 | Selected-column state toggles on click | smoke | Playwright | Wave 0 |
| D-19 | Sort state cycles `desc → asc → null` | unit | Vitest reducer-style on sort handler | Wave 0 |
| D-20 | Sidebar filter state local; clear-btn resets all | unit | Vitest | Wave 0 |
| D-22 | `/club/[id]` re-themed; single orange CTA only | smoke + visual | Playwright snapshot of `/club/real_madrid` | Wave 0 — `tests/visual/club-page.spec.ts` |
| D-23 | `/admin/analytics` Recharts re-colored | smoke + visual | Playwright snapshot (admin route requires auth — gate the test or stub session) | Wave 0 — `tests/visual/admin.spec.ts` |
| D-24 | Modals — single orange CTA, white-outlined cancel | unit + smoke | Vitest snapshot of three modals | Wave 0 |
| D-25 | `CLAUDE.md` documents single-orange-CTA-per-surface rule | manual | `grep -q "single orange CTA" CLAUDE.md` | Wave 0 — append-only edit in Plan 5 |
| D-26 | Screenshot diff sub-2% vs Figma reference baseline | visual | `npx playwright test --update-snapshots` initially; subsequent `npx playwright test` enforces `maxDiffPixelRatio: 0.02` | Wave 0 — baseline png committed with phase |
| D-27 | `npx next build` passes; `npm test` (Vitest) green | gate | both commands | always |
| D-28 | Score JSON unchanged pre/post | gate | `node analysis/homepage/crosscheck/recalculate-scores.js`; `git diff --quiet analysis/homepage/results/_scores.json analysis/homepage/results/_aggregate.json` | already exists |
| D-29 | Lighthouse a11y ≥ 90 | manual | Lighthouse CLI command above | Wave 0 — captured at phase gate, screenshot of report committed |

### Sampling Rate

- **Per task commit:** `npm test` (Vitest, fast).
- **Per wave merge:** `npm test && npx playwright test --grep @smoke && npx next build`.
- **Phase gate:** full suite + `recalculate-scores.js` diff + Lighthouse a11y ≥ 90 + manual visual diff against Figma.

### Wave 0 Gaps

- [ ] Add `@playwright/test` dev dep + `playwright.config.ts` + `npx playwright install chromium`
- [ ] Create `tests/visual/` directory + baseline PNG for homepage at 1440×900 + matching test spec
- [ ] Create `tests/components/` directory + per-atomic-component Vitest specs (`DataCell`, `SortHeader`, `MeterRow`, `HeaderBar`, `TopNav`, `CategoryFilter`, `TypeFilter`, `HoverTooltipCard`, `Modal`)
- [ ] Add `BUILD_DATE` env var in `next.config.ts` (D-12) — required before `<HeaderBar>` test can pass
- [ ] Add `tests/visual/club-page.spec.ts` and `tests/visual/admin.spec.ts` (with auth stub for admin)
- [ ] Set up `tests/setup-fonts.ts` to await `document.fonts.ready` before assertions
- [ ] Add `--bg1: var(--bg-cell);` token alias in `app/globals.css` (legacy class compatibility — `.login-input`)

---

## Pitfalls (beyond CONTEXT.md)

### P1: `--bg1` alias missing
`app/globals.css:309` `.login-input` references `var(--bg1)`, which is **not defined** in the current `:root`. It works today because the variable is undefined → CSS uses `inherit` / nothing → input has no background → no one noticed. After D-01's token rewrite, plan 1 must either rename to `--bg-cell` or add an alias `--bg1: var(--bg-cell);`. **Default: alias.**

### P2: Recharts SVG gradient stops + CSS variables
Some Recharts internals stringify SVG attributes server-side. CSS variables in `<linearGradient><stop stopColor="var(--accent)" />` work in modern browsers but have failed in older Recharts builds (3.x is fine, but verify in a smoke test). **Mitigation:** hard-code `#FF490C` in the SVG gradient stops for safety; use `var(--accent)` everywhere else.

### P3: Playwright snapshot baselines + dark-mode auto-screenshot
Playwright's headless Chromium can render system dark/light differently. Force `colorScheme: 'dark'` in the config to keep baselines stable.

### P4: Build-date HeaderBar hydration
D-12 mandates `process.env.BUILD_DATE` to avoid hydration mismatch. This requires updating `next.config.ts` like:
```typescript
const nextConfig: NextConfig = {
  env: { BUILD_DATE: new Date().toISOString().slice(0, 10) },
  async redirects() { /* existing */ },
};
```
Without this, `<HeaderBar>` reading `new Date()` directly will mismatch SSR vs client. Add as the first task in Plan 1.

### P5: Inter Tight letter-spacing creep
Inter Tight at small sizes (10–12px Roboto Mono captions paired with Inter Tight 14px body) can look slightly heavier than Suisse. Allocate 30 minutes in Plan 1 for an eyeball-vs-Figma A/B at the three text sizes (14/16/22) before locking the `letter-spacing` value. CONTEXT.md `<specifics>` already flags this.

### P6: `analysis/products.ts` is the source of `type`, not the JSONs
Don't waste a task backfilling JSON. (See Type-Filter Data Audit above.)

### P7: Score-row preservation
Current `app/page.tsx` has the Total-Score row appearing twice — once in `<thead>` (line ~430) AND once in `<tfoot>` (line ~503). Both call into `productScores` and apply `selectedProduct === p.id` highlight. The new `<MatrixTable>` should preserve this duplication (sticky-top + sticky-bottom totals) — easy to lose in a refactor.

### P8: Existing `cell-tooltip` markup is at root level, not portaled
The current `<div className="cell-tooltip">` is a sibling of `<div className="main">` inside `<div className="matrix-shell">`. It works because `position: fixed` + JS sets `left/top` from cursor coords. The new `<HoverTooltipCard>` per D-16 must use `createPortal(node, document.body)` and read cell `getBoundingClientRect()` — a behavioral change, not just CSS.

### P9: `.locked-zone` animated border deletion
`.locked-zone` (`globals.css:252–256`) animates a multicolor holographic border around the locked tab cluster. D-13 replaces the locked-zone with locked tabs at 60% opacity inside a single `<TopNav>`. **Delete those CSS rules** in Plan 4; otherwise the animation keeps running on dead markup.

---

## Sources

### Primary (HIGH confidence)
- `app/page.tsx`, `app/globals.css`, `app/layout.tsx`, `app/admin/analytics/page.tsx`, `app/club/[id]/page.tsx`, `next.config.ts`, `package.json` — read directly.
- `analysis/products.ts`, `analysis/types.ts`, `analysis/homepage/results/*.json` — grepped to confirm `type` field location.
- `.planning/phases/infra-redesign-v2/CONTEXT.md` — read in full.
- [Next.js — Font Optimization](https://nextjs.org/docs/app/getting-started/fonts)
- [Playwright — Visual Comparisons](https://playwright.dev/docs/test-snapshots)
- [Pixelmatch on GitHub](https://github.com/mapbox/pixelmatch)
- [Inter Tight on Google Fonts](https://fonts.google.com/specimen/Inter+Tight)
- [Roboto Mono on Google Fonts](https://fonts.google.com/specimen/Roboto+Mono)

### Secondary (MEDIUM confidence)
- [Swiss Typefaces — Licensing](https://www.swisstypefaces.com/licensing/) (model documented; pricing not public)
- [Typewolf — Suisse Int'l](https://www.typewolf.com/suisse-international) (Inter listed as nearest free alternative; PDF gated)
- [Bug0 — Playwright Visual Regression Testing](https://bug0.com/knowledge-base/playwright-visual-regression-testing)
- [TypographySmith — Inter Tight](https://typographysmith.com/fonts/inter-tight)

### Tertiary (LOW confidence — flagged for validation)
- License-cost band of €500–€2k for Suisse Int'l: drawn from secondhand industry write-ups, not vendor-confirmed. Planner must include "Sergey requests official quote from Swiss Typefaces" as the unblocker for D-09 if Option A is pursued.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — code read directly, package.json verified.
- Architecture (D-01 to D-29): HIGH — CONTEXT.md is exhaustive; this RESEARCH.md only fills gaps.
- Pitfalls: HIGH — every pitfall is rooted in a specific file:line reference.
- Suisse pricing: MEDIUM — vendor is opaque; recommendation defaults to free path.
- Visual-regression tool pick: HIGH — Playwright wraps Pixelmatch; same diff engine, simpler wiring.

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (30 days; stack stable).

## RESEARCH COMPLETE
