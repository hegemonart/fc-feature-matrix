# Codebase Structure

**Analysis Date:** 2026-04-16

## Directory Layout

```
.
├── app/                          # Next.js App Router (pages, layouts, API routes)
│   ├── page.tsx                  # Main matrix view (Client Component, CSR)
│   ├── layout.tsx                # Root layout with metadata
│   ├── analytics/
│   │   └── page.tsx              # Analytics dashboard (Client Component, auth-gated)
│   ├── club/
│   │   └── [id]/
│   │       ├── page.tsx          # Product detail (Server Component, SSG)
│   │       ├── CategoryFilter.tsx # Client component for category filtering
│   │       ├── ScrollRestore.tsx  # Client component for scroll state
│   │       └── PageTracker.tsx    # Client component for analytics
│   └── api/
│       ├── auth/
│       │   ├── login/route.ts     # POST: email/password → session cookie
│       │   ├── logout/route.ts    # POST: clear session cookie
│       │   └── me/route.ts        # GET: return auth status
│       ├── analytics/
│       │   ├── route.ts           # POST: log event to Redis
│       │   └── view/route.ts      # GET: retrieve events (admin-only)
│       ├── email/route.ts         # POST: send access request via Resend
│       └── crosscheck-img/route.ts # GET: serve evidence images
│
├── lib/                           # Business logic and utilities
│   ├── data.ts                    # Re-export from analysis/
│   ├── scoring.ts                 # getProductScores(), getRankedProducts()
│   ├── summary.ts                 # generateClubSummary() for club detail pages
│   ├── auth.ts                    # Session token, password hashing, cookie helpers
│   ├── analytics.ts               # logEvent(), getEvents() (Redis integration)
│   ├── track.ts                   # Client-side trackEvent() helper
│   └── scoring.test.ts            # Tests for scoring logic
│
├── analysis/                      # Data layer (features, products, results)
│   ├── index.ts                   # Barrel export + band computation (runs on import)
│   ├── types.ts                   # TypeScript types (Feature, Product, Category, etc.)
│   ├── products.ts                # 33 products (clubs, leagues, governing bodies)
│   ├── CLAUDE.md                  # Documentation for analysis folder structure
│   │
│   └── homepage/                  # Homepage feature matrix analysis
│       ├── HOME-PAGE.md           # Feature rubric (source of truth)
│       ├── PLAYBOOK-*.md          # Methodology docs
│       ├── features.ts            # 60 features with tier, weights, presence maps
│       ├── categories.ts          # 12 categories with colors
│       ├── results/               # Analysis results (one JSON per product)
│       │   ├── real_madrid.json   # { product_id, features: { feature_id: boolean } }
│       │   ├── fc_barcelona.json
│       │   ├── ... (33 product results)
│       │   ├── _scores.json       # Ranked scores (auto-generated)
│       │   ├── _aggregate.json    # Full feature×product matrix (auto-generated)
│       │   └── _results.json      # Metadata (auto-generated)
│       ├── screenshots/           # Homepage PNGs for visual reference
│       │   ├── 01-real-madrid.png
│       │   └── ... (33 screenshots)
│       └── crosscheck/            # Browser verification tooling
│           ├── CLAUDE.md          # Cross-check agent instructions
│           ├── img/               # Evidence images (element-level crops)
│           │   ├── real_madrid_hero_carousel.png
│           │   └── ... (536 images)
│           ├── recalculate-scores.js
│           └── capture_elements.py
│
├── data/                          # Runtime data files
│   └── users.json                 # [{ email, passwordHash }] — loaded at auth time
│
├── public/                        # Static assets
│   ├── img/
│   │   ├── logo.svg
│   │   └── logos/                 # Product logos (38 SVG/PNG files)
│   │       ├── real_madrid.png
│   │       └── ...
│   └── favicon.ico
│
├── .github/
│   └── workflows/                 # CI/CD
│       └── *.yml
│
├── .planning/                     # GSD planning documents
│   ├── phases/
│   └── codebase/                  # Codebase map (this folder)
│
├── next.config.ts                 # Next.js config
├── tsconfig.json                  # TypeScript config
├── package.json                   # Dependencies
├── package-lock.json
└── .env.local (not committed)    # Environment variables (AUTH_SECRET, KV_REST_API_*, RESEND_API_KEY)
```

## Directory Purposes

**`app/`:**
- Purpose: Next.js App Router — pages, layouts, API routes
- Contains: React components (Client & Server), API handlers
- Key files: `page.tsx` (main matrix), `club/[id]/page.tsx` (detail), `api/auth/*`, `api/analytics/*`

**`lib/`:**
- Purpose: Shared business logic and utilities
- Contains: Scoring, summaries, auth, analytics, tracking functions
- No UI components here, only functions and types

**`analysis/`:**
- Purpose: Feature matrix data layer
- Contains: Product definitions, 60 feature specs with tier/weights, 33 JSON analysis results per product
- Key file: `homepage/features.ts` imports all `results/*.json` files and builds presence maps

**`analysis/homepage/results/`:**
- Purpose: Store per-product analysis results
- One JSON file per product (e.g., `real_madrid.json`)
- Format: `{ product_id, screenshot, analyzed_at, total_score, features: { feature_id: boolean } }`
- Auto-generated aggregates: `_scores.json`, `_aggregate.json`, `_results.json`
- **35 files total:** 33 products + 2 auto-generated

**`analysis/homepage/crosscheck/img/`:**
- Purpose: Evidence images (cropped element screenshots)
- Format: PNG, named `${product_id}_${feature_id}.png`
- **536 files** — evidence for "full" presence markers in the matrix
- Served via `/api/crosscheck-img?file=...` and displayed in matrix tooltips

**`data/`:**
- Purpose: Runtime data (not version-controlled secrets)
- Files: `users.json` — array of `{ email, passwordHash }` loaded by `loadUsers()` in `lib/auth.ts`

**`public/`:**
- Purpose: Static assets served by Next.js
- Contains: Logo, product logos (38 files), favicon
- Product logos: Named `${product_id}.png` or `.svg`, referenced in `products.ts` with `logo` field

## Key File Locations

**Entry Points:**
- `app/page.tsx` — Main matrix (Client Component, CSR)
- `app/club/[id]/page.tsx` — Product detail (Server Component, SSG)
- `app/analytics/page.tsx` — Analytics dashboard (Client Component)
- `app/layout.tsx` — Root layout with metadata

**Configuration:**
- `tsconfig.json` — TypeScript compiler options (path aliases: `@/lib`, `@/analysis`)
- `next.config.ts` — Next.js configuration
- `package.json` — Dependencies (see STACK.md)

**Core Logic:**
- `lib/scoring.ts` — Feature scoring system (`getProductScores()`, `getRankedProducts()`)
- `lib/summary.ts` — Summary text generation (`generateClubSummary()`)
- `lib/auth.ts` — Session management (token creation/parsing, password hashing)
- `lib/analytics.ts` — Event logging to Redis (`logEvent()`, `getEvents()`)
- `analysis/index.ts` — Band computation (runs on import)
- `analysis/homepage/features.ts` — 60 feature definitions with presence maps

**Testing:**
- `lib/scoring.test.ts` — Jest tests for scoring logic

**Data Pipeline:**
- `analysis/homepage/HOME-PAGE.md` — Feature rubric (source of truth)
- `analysis/homepage/features.ts` — Feature definitions with imports from `results/`
- `analysis/homepage/results/*.json` — Per-product analysis results
- `analysis/homepage/categories.ts` — Category definitions

## Naming Conventions

**Files:**
- **PascalCase** for React components: `CategoryFilter.tsx`, `PageTracker.tsx`
- **camelCase** for utilities/non-components: `scoring.ts`, `auth.ts`, `track.ts`
- **UPPERCASE** for constants/exports: `HOME-PAGE.md`, `CLAUDE.md`
- **snake_case** for product IDs: `real_madrid`, `fc_barcelona` (matching JSON filenames)

**Directories:**
- **lowercase** for most directories: `lib/`, `app/`, `analysis/`
- **square brackets** for dynamic routes: `[id]` in `app/club/[id]/`
- **Feature-based structure** in API: `app/api/auth/`, `app/api/analytics/`

**Functions:**
- **camelCase**: `getProductScores()`, `generateClubSummary()`, `logEvent()`
- **Boolean predicates start with "is" or "get"**: `isRateLimited()`, `getSessionFromCookie()`

**Types:**
- **PascalCase**: `Feature`, `Product`, `Category`, `AnalyticsEvent`
- **"Status" suffix for unions**: `PresenceStatus`, `TierId`, `BandId`

**Variables:**
- **camelCase**: `featureId`, `productScores`, `selectedFeature`
- **UPPERCASE for constants**: `MAX_EVENTS`, `RATE_LIMIT`, `PRODUCTS`

## Where to Add New Code

**New Feature (e.g., new analytics view):**
- Component: `app/new-view/page.tsx` (or `app/api/new-view/route.ts` for API)
- Business logic: Add to `lib/` (e.g., `lib/new-feature.ts`)
- Tests: `lib/new-feature.test.ts`

**New Component (e.g., reusable modal):**
- Implementation: `app/components/MyModal.tsx` or create `app/club/[id]/MyModal.tsx` if page-specific
- Co-locate with where it's used to avoid prop drilling

**New Product Analysis Page (e.g., player pages):**
- Rubric: Create `analysis/player-page/PLAYER-PAGE.md`
- Features: `analysis/player-page/features.ts` with imports from `results/`
- Results: `analysis/player-page/results/*.json` (per-player)
- Screenshots: `analysis/player-page/screenshots/`
- Crosscheck: `analysis/player-page/crosscheck/`
- Update barrel: Export from `analysis/index.ts` and re-export in `lib/data.ts`

**Utilities (helpers, calculations):**
- Location: `lib/` directory
- Naming: `lib/[feature-name].ts` (e.g., `lib/ranking.ts`, `lib/validation.ts`)
- Export from barrel if widely used

**API Routes:**
- Location: `app/api/[feature]/route.ts` or `app/api/[feature]/[endpoint]/route.ts`
- Auth enforcement: Call `getSessionFromCookie(req.headers.get('cookie'))` at route start
- Error handling: Return appropriate status codes (400 for bad input, 401 for auth, 500 for server error)

**Tests:**
- Location: Co-located with source (e.g., `lib/scoring.test.ts` next to `lib/scoring.ts`)
- Pattern: Jest test files named `*.test.ts`
- Run: `npm test` (see package.json for test script)

## Special Directories

**`analysis/homepage/results/`:**
- Purpose: JSON storage for analysis results
- Auto-generated: `_scores.json`, `_aggregate.json`, `_results.json` (created by `recalculate-scores.js`)
- How to add: Run analysis for new product, import in `features.ts`, recalculate scores
- Committed: Yes (human-written JSON files)

**`analysis/homepage/crosscheck/img/`:**
- Purpose: Evidence images (PNG crops of homepage elements)
- Naming: `${product_id}_${feature_key}.png` (e.g., `real_madrid_language_switcher.png`)
- How to add: Run `capture_elements.py` to auto-generate from homepage
- Committed: Yes (binary PNG files)

**`.planning/codebase/`:**
- Purpose: Codebase documentation (this folder)
- Contents: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, STACK.md, INTEGRATIONS.md, CONCERNS.md
- Committed: Yes

**`data/`:**
- Purpose: Runtime data (users list)
- Generated: No, manually maintained
- Committed: Likely yes (see `.gitignore` for confirmation)

---

*Structure analysis: 2026-04-16*
