# Integrations

## External Services

| Service | Purpose | How integrated |
|---|---|---|
| Vercel | Hosting and deployment | `vercel.json` declares `"framework": "nextjs"`; Vercel auto-detects and runs `next build` + serves the output |

No other external services are integrated. There is no analytics, no error tracking (Sentry etc.), no A/B testing, no CDN configuration, no CMS, no headless API, and no third-party scripts loaded.

## APIs Consumed

None. The application makes no outbound HTTP requests at runtime. All data is hardcoded in `lib/data.ts` as TypeScript constants (PRODUCTS, FEATURES, CATEGORIES, BAND_META). There are no `fetch()` calls, no SDK clients, and no API route handlers (`app/api/` does not exist).

The three `.mjs` files in the repo root (`capture.mjs`, `recapture.mjs`, `recapture-f1.mjs`) appear to be standalone data-capture scripts used during the research/authoring phase, not part of the deployed application.

## Data Sources

| Source | Type | Details |
|---|---|---|
| `lib/data.ts` | Static TypeScript constants | Single source of truth — 26 products (football clubs, leagues, governing bodies), 29 features across 5 categories, presence matrix (full/partial/absent) for every product–feature pair, band metadata |
| `lib/scoring.ts` | Derived/computed | Utility functions (`getProductScores`, `getRankedProducts`) that compute coverage percentages, raw scores, and weighted scores from `lib/data.ts` at render time |
| `analysis/*.md` | Research notes | Three markdown files (`analysis-batch1.md`, `analysis-batch2.md`, `analysis-batch3.md`) containing the manual audit notes used to populate `lib/data.ts`; not read by the app at runtime |

Band classification (table_stakes / expected / competitive / innovation) is computed dynamically on import via `computeBands()` in `lib/data.ts` based on adoption percentages across the 26 products.

## Auth / Identity

None. The application has no authentication layer, no user accounts, no sessions, no cookies, and no login flow. It is a fully public, read-only benchmarking tool. The "locked" tab modals visible in the UI are purely decorative UX elements — clicking them shows a hardcoded "Analysis Restricted" dialog with no actual access-control logic behind it.
