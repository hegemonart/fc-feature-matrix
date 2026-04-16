# Codebase Structure

**Analysis Date:** 2026-04-16

## Directory Layout

```
fc-feature-matrix/
├── analysis/                      # Data layer (features, products, scoring rubric)
│   ├── index.ts                   # Barrel export + computeBands()
│   ├── types.ts                   # Shared TypeScript types
│   ├── products.ts                # 33 products (clubs, leagues, governing bodies)
│   ├── CLAUDE.md                  # Data layer documentation
│   └── homepage/                  # Homepage feature analysis
│       ├── HOME-PAGE.md           # Feature rubric (source of truth)
│       ├── features.ts            # 61 features with presence maps
│       ├── categories.ts          # 12 feature categories with colors
│       ├── results/               # One JSON per club + aggregate
│       │   ├── real_madrid.json
│       │   └── ... (32 more clubs)
│       ├── screenshots/           # Full-page PNGs (visual audit reference)
│       │   ├── 01-real_madrid.png
│       │   └── ...
│       └── crosscheck/            # Browser verification tooling
│           ├── CLAUDE.md          # Cross-check procedure docs
│           ├── recalculate-scores.js
│           ├── capture_elements.py
│           └── img/               # 536 element-level screenshot evidence
│
├── app/                           # Next.js pages and API routes
│   ├── layout.tsx                 # Root layout with Analytics component
│   ├── page.tsx                   # Feature matrix homepage (client component)
│   ├── globals.css                # Global styles
│   ├── api/                       # API routes
│   │   ├── auth/
│   │   │   ├── login/route.ts     # POST login with email/password
│   │   │   ├── logout/route.ts    # POST logout (clear session)
│   │   │   └── me/route.ts        # GET current authenticated user
│   │   ├── analytics/
│   │   │   ├── route.ts           # POST event logging
│   │   │   └── view/route.ts      # GET recent events (admin)
│   │   ├── email/route.ts         # Email sending (Resend)
│   │   └── crosscheck-img/route.ts # Image proxy for crosscheck evidence
│   ├── club/
│   │   └── [id]/
│   │       ├── page.tsx           # Club detail page (server component)
│   │       ├── CategoryFilter.tsx  # Client component: category filter
│   │       ├── PageTracker.tsx     # Client component: scroll tracking
│   │       └── ScrollRestore.tsx   # Client component: scroll position restore
│   └── analytics/
│       └── page.tsx               # Analytics dashboard page
│
├── lib/                           # Service layer (helpers, utilities)
│   ├── data.ts                    # Barrel re-export from analysis/
│   ├── auth.ts                    # Session + password helpers
│   ├── analytics.ts               # Redis event logging
│   ├── scoring.ts                 # Feature coverage calculation
│   ├── summary.ts                 # Club narrative generation
│   └── track.ts                   # Client-side analytics (fire-and-forget)
│
├── data/                          # User authentication store
│   └── users.json                 # Stored users with hashed passwords
│
├── public/                        # Static assets
│   └── img/
│       └── logos/                 # 33 product logos (SVG)
│           ├── real_madrid.svg
│           └── ...
│
├── .planning/                     # GSD project planning
│   ├── config.json
│   ├── STATE.md
│   ├── ROADMAP.md
│   └── codebase/                  # This analysis
│       ├── ARCHITECTURE.md
│       ├── STRUCTURE.md
│       ├── CONVENTIONS.md (if generated)
│       └── TESTING.md (if generated)
│
├── package.json                   # Dependencies + scripts
├── tsconfig.json                  # TypeScript config (strict mode, path alias @/*)
├── next.config.ts                 # Next.js config (minimal)
├── vercel.json                    # Vercel deployment config
└── README.md                      # Project documentation
```

## Directory Purposes

**`analysis/`:**
- Purpose: Data layer — feature definitions, product list, presence data, rubric documentation
- Contains: TypeScript exports (types, features, products), JSON files (results per club), PNG screenshots, Python capture scripts, cross-check tooling
- Key files: `types.ts` (Feature interface), `products.ts` (33 org list), `homepage/features.ts` (feature definitions with imports), `homepage/categories.ts` (12 categories)

**`analysis/homepage/results/`:**
- Purpose: Club-specific feature presence data (one JSON per product)
- Contains: 33 JSON files (e.g., `real_madrid.json`, `fc_barcelona.json`)
- Structure: `{ "features": { "feature_key": true/false, ... } }`
- Imported by: `analysis/homepage/features.ts` to build presence maps

**`analysis/homepage/crosscheck/img/`:**
- Purpose: Element-level screenshot evidence for TRUE features
- Contains: 536 PNG files named `{club_id}_{feature_key}.png`
- Used for: Visual audit verification (not consumed by app)

**`app/`:**
- Purpose: Next.js pages and API routes
- Contains: React components (.tsx), API route handlers (.ts)
- Structure: Pages in directories, API routes under `api/`, shared components in `club/[id]/`

**`app/api/auth/`:**
- Purpose: Authentication endpoints
- Files: `login/route.ts` (POST), `logout/route.ts` (POST), `me/route.ts` (GET)
- Flow: Login validates against `data/users.json`, returns session cookie; logout clears cookie; me returns current user from cookie

**`app/api/analytics/`:**
- Purpose: Event logging and retrieval
- Files: `route.ts` (POST events), `view/route.ts` (GET events)
- Flow: POST logs events to Upstash Redis with email + timestamp; view fetches recent events

**`app/club/[id]/`:**
- Purpose: Club detail page and sub-components
- Files: `page.tsx` (server component), `CategoryFilter.tsx` (client), `PageTracker.tsx` (client), `ScrollRestore.tsx` (client)

**`lib/`:**
- Purpose: Reusable service functions
- Files: `data.ts` (barrel), `auth.ts` (HMAC + bcryptjs), `analytics.ts` (Redis), `scoring.ts` (calculation), `summary.ts` (narrative), `track.ts` (client-side event fire)

**`data/`:**
- Purpose: User credential store
- Files: `users.json` only
- Structure: Array of `{ email, passwordHash, name? }`

**`public/img/logos/`:**
- Purpose: Product logos (SVG files)
- Contains: 33 logos corresponding to products in `analysis/products.ts`
- Naming: `{product_id}.svg` (e.g., `real_madrid.svg`, `fc_barcelona.svg`)

## Key File Locations

**Entry Points:**
- `app/layout.tsx`: Root layout wrapping all pages; imports Vercel Analytics
- `app/page.tsx`: Feature matrix homepage; client component with state, filters, modal auth
- `app/club/[id]/page.tsx`: Club detail server component; fetches product and summary

**Configuration:**
- `tsconfig.json`: Path alias `@/*` → root, strict mode enabled
- `package.json`: Dependencies (Next.js 16, React 19, bcryptjs, @upstash/redis, resend)
- `next.config.ts`: Minimal config
- `vercel.json`: Deployment target

**Core Logic:**
- `analysis/index.ts`: Band computation on import, barrel exports
- `analysis/homepage/features.ts`: Feature definitions + presence data assembly
- `lib/auth.ts`: Session token creation (HMAC), password hashing/verification, cookie helpers
- `lib/scoring.ts`: Coverage % and weighted score calculation
- `lib/summary.ts`: Narrative generation (headline, overview, strengths, priorities, conclusion)
- `app/api/auth/login/route.ts`: Credential validation, session creation
- `app/api/analytics/route.ts`: Event logging to Redis

**Testing:**
- No tests in current structure (no test files found in repo)

## Naming Conventions

**Files:**
- Pages: `page.tsx` (Next.js convention)
- API routes: `route.ts` in directory matching path (e.g., `app/api/auth/login/route.ts` → POST /api/auth/login)
- Data files: `*.json` in `analysis/homepage/results/` named by product ID (e.g., `real_madrid.json`)
- Screenshots: `NN-{name}.png` in `analysis/homepage/screenshots/` (e.g., `01-real_madrid.png`)
- Element screenshots: `{club_id}_{feature_key}.png` in `analysis/homepage/crosscheck/img/`

**Directories:**
- Camel case for feature directories: `analysis/homepage/`, `app/api/auth/`
- Bracket syntax for dynamic routes: `app/club/[id]/`
- Nested routes under `api/`: `app/api/analytics/view/route.ts` → GET /api/analytics/view

**Functions:**
- camelCase: `computeBands()`, `createSessionToken()`, `getProductScores()`, `generateClubSummary()`
- Verb-first for handlers: `loadUsers()`, `logEvent()`, `trackEvent()`, `getSessionFromCookie()`
- Async functions: all named action functions (auth, analytics)

**Types:**
- PascalCase with descriptive suffix: `StoredUser`, `Feature`, `Product`, `Category`, `AnalyticsEvent`, `ClubSummary`
- Union types: `PresenceStatus`, `CategoryId`, `BandId`, `TierId`, `ProductType`, `SportType`

**Variables:**
- camelCase constants: `COOKIE_NAME`, `EVENTS_KEY`, `MAX_AGE`, `SECRET`
- Object keys match API/JSON: `email`, `password`, `passwordHash`, `presence`, `adoption`

## Where to Add New Code

**New Feature (in feature matrix):**
- Add feature definition to `analysis/homepage/HOME-PAGE.md` (rubric)
- Add `feat(...)` call in `analysis/homepage/features.ts`
- Add presence data to each JSON in `analysis/homepage/results/` (all 33 clubs)
- Recalculate scores: `node analysis/homepage/crosscheck/recalculate-scores.js`

**New Club/Product:**
- Add product to `analysis/products.ts`
- Take homepage screenshot → `analysis/homepage/screenshots/NN-name.png`
- Create JSON result file → `analysis/homepage/results/{id}.json`
- Add import + RESULTS entry in `analysis/homepage/features.ts`
- Recalculate scores: `node analysis/homepage/crosscheck/recalculate-scores.js`

**New Page Type (e.g., player page):**
- Create directory: `analysis/player/` (mirror of `analysis/homepage/`)
- Add rubric: `analysis/player/PLAYER-PAGE.md`
- Add types/categories/features: `analysis/player/features.ts`, `analysis/player/categories.ts`
- Add results: `analysis/player/results/`
- Create page: `app/player/[id]/page.tsx`
- Import from `analysis/player/` (separate barrel)

**New API Endpoint:**
- Create directory under `app/api/{resource}/`
- Add `route.ts` with request handler: `export async function POST(req: NextRequest) { ... }`
- Call service functions from `lib/` (auth, analytics, etc.)

**Shared Utilities:**
- If used by multiple pages/routes: add to `lib/`
- If used only within one page: define in that page's component file
- Never add to `lib/` if it's data-specific to one analysis folder

**Styling:**
- Global styles: `app/globals.css`
- Page-specific: inline `<style>` tags in components (no CSS modules in use)

## Special Directories

**`.next/`:**
- Purpose: Next.js build output
- Generated: Yes (from `npm run build`)
- Committed: No (in .gitignore)

**`node_modules/`:**
- Purpose: npm dependencies
- Generated: Yes (from `npm install`)
- Committed: No (in .gitignore)

**`.planning/`:**
- Purpose: GSD project state and planning documents
- Generated: Yes (by `/gsd:*` commands)
- Committed: Yes (planning files tracked, not outputs)

**`.claude/`:**
- Purpose: Claude Code configuration (GSD framework, hooks, agents)
- Generated: No (committed from global setup)
- Committed: Yes (project-specific worktrees may be local-only)

**`concept/`:**
- Purpose: Separate Next.js project (design concept)
- Generated: No (committed separately)
- Committed: Yes (independent monorepo-style)

---

*Structure analysis: 2026-04-16*
