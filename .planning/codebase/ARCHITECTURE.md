# Architecture

## Overview

FC Feature Matrix is a Next.js 16 (App Router) web application that benchmarks the homepage UX of 26 sports websites — primarily European football clubs plus leagues and governing bodies (UEFA, F1, NBA, MLS, MLB). The app renders a large interactive feature matrix (features vs. products) with filtering, detail panels, and per-club deep-dive pages.

The dataset (26 products × 29 features) is entirely static — hardcoded in `lib/data.ts`. There is no backend, no database, and no API calls at runtime. All data is compiled into the bundle at build time.

## Rendering Strategy

**Main matrix page (`/`)** — fully client-side rendered (`'use client'` directive). All interactivity (filtering, search, detail panels, tooltips, locked modals) is handled via React state in the browser. The page is a single large component tree rendered on the client.

**Club detail pages (`/club/[id]`)** — statically generated (SSG) at build time. `generateStaticParams()` emits one static page for each of the 26 product IDs. The component is an `async` Server Component with no client-side state; all computation (scores, rankings, category breakdowns) runs at build time. `generateMetadata()` produces per-page `<title>` tags.

**Deployment** — Vercel with `"framework": "nextjs"`. The `next.config.ts` is minimal with no custom configuration. Static generation means zero server compute at request time for the club pages.

## Data Flow

1. **Source of truth**: `lib/data.ts` exports typed constants — `CATEGORIES`, `PRODUCTS`, `FEATURES`, `BAND_META`, `ALL_IDS`.
2. **Feature presence** is encoded via `makePresence(full[], partial[])`, a helper that initialises all 26 product IDs to `'absent'` then marks overrides. Each `Feature.presence` is a `Record<string, PresenceStatus>` where keys are product IDs.
3. **Band assignment** is computed at module load time (`computeBands()`) — each feature's `adoptionPct` is derived from its presence record, then bucketed into one of four bands (`table_stakes` ≥90%, `expected` 70–89%, `competitive` 40–69%, `innovation` <40%).
4. **Scoring** is extracted into `lib/scoring.ts` — `getProductScores(pid)` and `getRankedProducts()` are pure functions imported by both the main page and the club detail page.
5. **Main page**: data flows downward as props. `FeatureMatrixPage` holds all filter/selection state and computes `visibleProds` and `visibleFeats` via `useMemo`. These are passed to `TableRows`, `FeatureDetail`, and `ProductDetail` as plain props.
6. **Club detail page**: imports data and scoring functions directly; performs all derivation (category scores, must-have gaps, differentiators) inline in the async Server Component body before returning JSX.

## State Management

No global state library (no Redux, Zustand, Context). All state is local React `useState` in `FeatureMatrixPage`:

| State var | Type | Purpose |
|---|---|---|
| `filterType` | `string` | 'all' / 'club' / 'league' filter |
| `filterSport` | `string` | 'all' / 'football' / 'other' filter |
| `searchText` | `string` | Feature name/desc search |
| `activeCat` | `CategoryId \| null` | Sidebar category filter |
| `activeBand` | `BandId \| null` | Sidebar band filter |
| `selectedFeature` | `string \| null` | Opens feature detail panel |
| `selectedProduct` | `string \| null` | Opens product detail panel |
| `lockedModalVisible` | `boolean` | "Analysis Restricted" modal |
| `lockedFlowName` | `string` | Name of locked tab for modal copy |
| `tooltipVisible` | `boolean` | Cell hover tooltip |
| `tooltipData` | object \| null | Feature/product/status for tooltip |

Derived data (`visibleProds`, `visibleFeats`, band counts, category counts) is memoised with `useMemo`. Event handlers are stabilised with `useCallback`. The tooltip position is managed imperatively via a `useRef` to avoid re-renders on mouse move.

The club detail page (`/club/[id]`) has zero client state — it is a pure async Server Component.

## Key Patterns

**Inline sub-components**: `TableRows`, `FeatureDetail`, and `ProductDetail` are defined in the same file as `FeatureMatrixPage` (all in `app/page.tsx`). They are plain function components, not exported, and receive everything via props — no hooks, no context.

**Presence encoding**: the `makePresence` helper inverts the typical approach — you declare which products have a feature, not which features a product has. This keeps the feature definitions readable and prevents accidental omissions.

**Band auto-classification**: bands are not manually assigned per feature. `computeBands()` calculates adoption across all 26 products and classifies features automatically, ensuring the legend thresholds (≥90%, 70–89%, 40–69%, <40%) are always accurate.

**Imperative tooltip positioning**: rather than using state for tooltip coordinates (which would trigger re-renders on every `mousemove`), the position is written directly to `tooltipRef.current.style`. Visibility is still state-driven but the position update is fire-and-forget.

**CSS custom properties**: all theme tokens are defined as CSS variables in `globals.css`. No CSS-in-JS, no Tailwind. Class names are plain strings applied inline. The dark theme uses a deep navy/charcoal palette.

**Static site with dynamic UX**: the architecture separates the "static data product" (club pages, SSG) from the "interactive tool" (matrix page, CSR). The matrix must be CSR because it has rich interactive state; the club pages have no interactivity and benefit from static generation for fast load and SEO.
