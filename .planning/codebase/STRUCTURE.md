# Directory Structure

## Root Layout

```
fc-feature-matrix/
├── app/                    # Next.js App Router — pages, layouts, global styles
├── lib/                    # Shared data and utility modules
├── analysis/               # Markdown research notes (not deployed)
├── .planning/              # Planning documents (not deployed)
├── .claude/                # Claude Code config (launch.json, settings)
├── CONCEPT_VISUAL.html     # Static HTML prototype (pre-migration artefact)
├── DESIGN.md               # Design decisions doc
├── PROJECT_CONTEXT.md      # Project background and goals
├── README.md               # Project readme
├── brainstorm.md           # Ideation notes
├── feature-matrix.md       # Raw feature data scratch pad
├── capture.mjs             # One-off screenshot/capture script
├── recapture.mjs           # Screenshot recapture utility
├── recapture2.mjs          # Screenshot recapture variant
├── recapture-f1.mjs        # F1-specific recapture script
├── next.config.ts          # Next.js config (minimal, no custom options)
├── next-env.d.ts           # Next.js TypeScript env types (auto-generated)
├── tsconfig.json           # TypeScript config with path alias @/ → root
├── vercel.json             # Vercel deploy config: { "framework": "nextjs" }
├── package.json            # Dependencies: next 16.2.2, react 19.2.4
└── package-lock.json
```

## Source Layout

```
app/
├── layout.tsx              # Root layout — sets <html lang="en">, page title/description metadata
├── page.tsx                # Main matrix page — entire interactive UI (client component, ~780 lines)
├── globals.css             # All styles — CSS custom properties, component classes, responsive rules
├── favicon.ico
└── club/
    └── [id]/
        └── page.tsx        # Club detail page — async Server Component, SSG for all 26 product IDs

lib/
├── data.ts                 # Single source of truth — types, CATEGORIES, PRODUCTS, FEATURES, helpers
└── scoring.ts              # Pure scoring functions — getProductScores(), getRankedProducts()
```

## Key Files

| File | Role |
|---|---|
| `app/page.tsx` | The entire interactive feature matrix UI. Contains `FeatureMatrixPage` (root client component), `TableRows` (table body renderer), `FeatureDetail` (right-panel feature drilldown), `ProductDetail` (right-panel product drilldown). All in one file, ~780 lines. |
| `app/club/[id]/page.tsx` | Per-club deep-dive page. Async Server Component. Computes coverage score, category breakdown, must-have gaps, differentiators, and all-products ranking at render time. Uses `generateStaticParams()` to pre-render all 26 club pages at build. |
| `app/layout.tsx` | Root layout. Imports `globals.css`. Sets site-wide `<title>` and `<description>` metadata. Wraps all pages in `<html><body>`. |
| `app/globals.css` | All CSS for the entire application. Dark theme tokens as CSS custom properties (`--bg`, `--accent`, `--green`, etc.). Styles for both the matrix shell (`.matrix-shell` — `overflow: hidden; height: 100vh`) and club detail shell (`.club-detail-shell` — natural scroll). No Tailwind, no CSS modules. |
| `lib/data.ts` | Core data module. Exports TypeScript types (`PresenceStatus`, `CategoryId`, `BandId`, `Feature`, `Product`, etc.), constants (`CATEGORIES` — 5 categories, `PRODUCTS` — 26 products, `FEATURES` — 29 features), the `makePresence()` helper, and `computeBands()` which auto-classifies each feature into a band based on adoption percentage. |
| `lib/scoring.ts` | Two pure functions consumed by both the matrix page and club detail pages: `getProductScores(pid)` returns coverage %, raw score, weighted score; `getRankedProducts()` returns all products sorted by coverage %. |
| `next.config.ts` | Minimal Next.js config — no custom settings. |
| `vercel.json` | Single-line Vercel config: `{ "framework": "nextjs" }`. |
| `tsconfig.json` | TypeScript config with `@/` path alias mapping to the project root, enabling `import { ... } from '@/lib/data'`. |

## Routing

The app has three routes total:

| Route | File | Type | What it renders |
|---|---|---|---|
| `/` | `app/page.tsx` | Client Component (CSR) | Interactive feature matrix — full-viewport table of 29 features × up to 26 products with sidebar filters, search, detail panels, flow nav with locked tabs, hover tooltips, and a "locked modal" for restricted analysis views. |
| `/club/[id]` | `app/club/[id]/page.tsx` | Server Component (SSG) | Per-club analysis page. Shows coverage ring chart, raw/weighted scores, global rank, all-products ranking bar chart, category breakdown grid, must-have missing features, differentiators, and full "already working" feature list. Pre-rendered at build for all 26 IDs via `generateStaticParams()`. |
| `/_not-found` | Next.js built-in | — | Auto-handled by `notFound()` call in the club page when an unknown product ID is requested. |

**Valid club IDs** (26 total): `real_madrid`, `fc_barcelona`, `bayern_munich`, `psg`, `liverpool`, `man_city`, `arsenal`, `man_united`, `tottenham`, `chelsea`, `inter_milan`, `bvb_dortmund`, `atletico_madrid`, `aston_villa`, `ac_milan`, `juventus`, `newcastle`, `vfb_stuttgart`, `sl_benfica`, `west_ham`, `uefa`, `f1`, `motogp`, `nba`, `mls`, `mlb`.

There are no API routes.
