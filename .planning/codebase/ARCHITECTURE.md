# Architecture

**Analysis Date:** 2026-04-16

## Pattern Overview

**Overall:** Hybrid rendering with client-side interactivity on the homepage, server-rendered detail pages, API routes for auth/analytics, and a data pipeline from analysis layer to UI.

**Key Characteristics:**
- Main matrix (`app/page.tsx`) is a **Client Component** (CSR) with stateful filtering, sorting, and sidebar navigation
- Detail pages (`app/club/[id]/page.tsx`) are **Server Components** (SSG via `generateStaticParams()`) with pre-computed scores and rankings
- Analytics page (`app/analytics/page.tsx`) is a **Client Component** with protected access
- Authentication enforced via cookie-based sessions checked in API routes
- Data originates in `analysis/` folder (JSON results per product), flows through `lib/` barrel export to React components
- No `middleware.ts` — auth gating happens per-route in API handlers via `getSessionFromCookie()`

## Layers

**Data Layer (`analysis/`):**
- Purpose: Feature matrix definitions and per-product analysis results
- Location: `analysis/homepage/`
- Contains: 
  - `features.ts` — 60 features (id, name, tier, weights) with presence maps keyed by product ID
  - `categories.ts` — 12 categories with display colors
  - `products.ts` — 33 products (clubs, leagues, governing bodies)
  - `results/*.json` — One JSON file per product with boolean `features` object
  - `index.ts` — Barrel export + band computation (runs on import, mutates `f.band` and `f.adoptionPct` for each feature)
- Depends on: JSON files in `results/` folder
- Used by: `lib/data.ts` (re-export), then consumed by all pages and API routes

**Lib Layer (`lib/`):**
- Purpose: Business logic for scoring, summary generation, auth, analytics, event tracking
- Location: `lib/` (7 files)
- Contains:
  - `data.ts` — Re-exports from `analysis/` (backward compatibility)
  - `scoring.ts` — `getProductScores(pid)` and `getRankedProducts()` (computed from `FEATURES` + `presence` maps)
  - `summary.ts` — `generateClubSummary(pid)` (generates natural language narrative)
  - `auth.ts` — Password hashing (bcryptjs), session token creation/parsing (HMAC-SHA256), cookie helpers, `loadUsers()` from `data/users.json`
  - `analytics.ts` — `logEvent()` to Redis/console, `getEvents()` with filtering
  - `track.ts` — Client-side `trackEvent()` fire-and-forget to `/api/analytics`

**API Layer (`app/api/`):**
- Purpose: Backend endpoints for auth, analytics event ingestion, email requests, image serving
- Location: `app/api/`
- Routes:
  - `auth/login/route.ts` — POST, validates email/password, sets session cookie (HttpOnly, 7 days)
  - `auth/logout/route.ts` — POST, clears session cookie
  - `auth/me/route.ts` — GET, returns `{ authenticated, email }` from cookie token
  - `analytics/route.ts` — POST, logs event to Redis/console (requires cookie for email resolution)
  - `analytics/view/route.ts` — GET, returns filtered events (requires `@humbleteam.com` email)
  - `email/route.ts` — POST, sends access request via Resend SMTP with rate limiting (5/min per IP)
  - `crosscheck-img/route.ts` — GET, serves PNG evidence images from `analysis/homepage/crosscheck/img/`

**UI Layer (`app/`):**
- Purpose: React components (Client and Server Components) for matrix view, detail panels, auth modals
- Location: `app/`
- Entry points:
  - `page.tsx` — **Client Component**, main matrix with state (filters, selected feature/product, modals)
  - `club/[id]/page.tsx` — **Server Component** (SSG), detail view for one product with score ring, category breakdown
  - `analytics/page.tsx` — **Client Component**, event log viewer (Humbleteam-only)
  - `layout.tsx` — Root layout with metadata + Vercel Analytics

## Data Flow

**Feature Data to Matrix UI:**

1. `analysis/index.ts` imports all `analysis/homepage/results/*.json` files
2. `index.ts` calls `computeBands()` on import, which:
   - Calculates `adoption = count('full') / totalProducts`
   - Sets `f.adoptionPct = Math.round(adoption * 100)`
   - Computes `f.band` based on adoption + tier floor (tier A→expected min, tier B→competitive min, C-F→pure adoption)
3. `lib/data.ts` re-exports `FEATURES`, `PRODUCTS`, `CATEGORIES`, `ALL_IDS`
4. `app/page.tsx` (Client Component) imports and:
   - Renders table rows from `FEATURES` filtered by category/type
   - Computes product scores in `useMemo`: `score = sum(feature.presence[pid] === 'full' ? weightYes : weightNo)`
   - Sorts products by score or name
   - Tooltip on cell mouseover loads `tooltipData` with feature metadata + weight

**Auth State to UI:**

1. On mount, `useEffect` calls `GET /api/auth/me`
2. API route reads cookie header, calls `getSessionFromCookie()` (parses HMAC token)
3. Returns `{ authenticated: true, email }` or `{ authenticated: false }`
4. Component sets `authed` state → locks/unlocks UI features:
   - If unauthenticated: matrix blurred, sign-in overlay shown, locked tabs visibly disabled
   - If authenticated: full matrix visible, locked tabs become "coming soon" modals

**Analytics Event Flow:**

1. Client fires events via `trackEvent('feature_click', { featureId, featureName })` in response to user action
2. `lib/track.ts` POSTs to `/api/analytics` with `{ type, data }`
3. `/api/analytics/route.ts` reads cookie, calls `logEvent(type, email, data)`
4. `lib/analytics.ts` creates event object + pushes to Redis list (or logs to console if no Redis)
5. Admin views events at `/analytics/page.tsx`:
   - Client fetches `/api/analytics/view?limit=200&type=...&email=...`
   - API gate requires `@humbleteam.com` email (from cookie)
   - Returns filtered event array

**Product Detail Page (SSG):**

1. `generateStaticParams()` returns `[{ id: 'real_madrid' }, { id: 'fc_barcelona' }, ...]` (one per product)
2. On build, Next.js pre-renders `app/club/[id]/page.tsx` for each product ID
3. Component calls `getProductScores(pid)` → returns coverage%, raw score, weighted score
4. Calls `getRankedProducts()` → returns all products sorted by coverage (computed once per render)
5. Renders static score ring (SVG with stroke-dasharray), ranking table, category breakdown (CategoryFilter client component)

## Key Abstractions

**Feature Scoring:**

- Purpose: Compute total score for a product across all features
- Examples: `lib/scoring.ts` — `getProductScores(pid)`
- Pattern: Iterate `FEATURES`, sum `feature.presence[pid] === 'full' ? weightYes : weightNo`
- Weights are asymmetric (e.g., tier A: +1 for yes, -3 for no) to penalize missing must-haves more than missing innovations

**Session Token:**

- Purpose: Stateless auth token stored in HttpOnly cookie
- Implementation: `lib/auth.ts`
  - Create: `createSessionToken(email)` → `${email}:${timestamp}:${HMAC-SHA256(payload)}`
  - Parse: `parseSessionToken(token)` → validates HMAC, extracts email
  - Cookie: `sessionCookieHeader(token)` → `fc_session=${token}; HttpOnly; Path=/; Max-Age=604800`
- No database lookup on every request (HMAC validates token integrity)

**Presence Map:**

- Purpose: Map product ID → presence status ('full', 'absent') for each feature
- Structure: `Feature.presence: Record<string, PresenceStatus>`
- Built from: `analysis/homepage/results/*.json` files which have `{ features: { feature_id: boolean } }`
- Consumed by: All scoring, UI rendering, analytics

**Band Computation:**

- Purpose: Classify features into maturity bands (table_stakes, expected, competitive, innovation) based on adoption rate + tier floor
- Runs: Once on `analysis/index.ts` import via `computeBands()`
- Tier floor prevents absurd labels: tier A (must-have) always ≥ "expected", tier B always ≥ "competitive"
- Used for: Color coding in matrix, filtering in product detail

## Entry Points

**`app/page.tsx` — Main Matrix:**
- Triggers: User navigates to `/`
- Rendering: Client Component (initial hydration, then interactive)
- Responsibilities:
  - Render 60×33 feature×product table with sorting, filtering, detail panels
  - Manage auth state (login/logout, login modal)
  - Handle tooltips, modals (locked features, coming soon, access requests)
  - Track events (page view, clicks)
- No `getSessionFromCookie` call here — auth check delegated to `useEffect` → `/api/auth/me`

**`app/club/[id]/page.tsx` — Product Detail:**
- Triggers: User navigates to `/club/real_madrid` (SSG, pre-rendered at build time)
- Rendering: Server Component (async, computations run on server)
- Responsibilities:
  - Compute scores and ranking (read-only, no state needed)
  - Render score ring, rank table, category filter (CategoryFilter is client component)
  - Show summary text generated by `generateClubSummary()`

**`app/api/auth/me/route.ts` — Session Check:**
- Triggers: `useEffect` on mount in `page.tsx`
- Responsibility: Read cookie, validate token, return auth status
- Session enforcement: If cookie missing or invalid HMAC, return `{ authenticated: false }`

**`app/api/analytics/route.ts` — Event Ingestion:**
- Triggers: `trackEvent()` fired from client
- Responsibility: Parse event, get email from cookie (default 'anonymous'), push to Redis
- No auth gate here (unauthenticated users can log events, just as 'anonymous')

**`app/api/analytics/view/route.ts` — Event Retrieval:**
- Triggers: Admin user at `/analytics` page calls `fetch('/api/analytics/view?...')`
- Auth gate: Requires `@humbleteam.com` email in session cookie
- Returns: Filtered event array from Redis

## Error Handling

**Strategy:** Fail gracefully, avoid breaking user experience

**Patterns:**

- **Missing session:** Return `{ authenticated: false }` in `/api/auth/me`, UI shows login overlay
- **Redis unavailable:** `lib/analytics.ts` checks `getRedis()` → if null, logs to console instead
- **Analytics failure:** `trackEvent()` wraps fetch in try/catch, silently fails (never breaks app)
- **Email send failure:** Rate limited, but on error returns 500 to client; client shows alert but doesn't crash
- **Invalid tier/band:** Summary generation and band computation have fallbacks (use 'innovation' band if tier not recognized)

## Cross-Cutting Concerns

**Logging:**
- Server: Console logs analytics failures, auth errors via `console.error()`
- Client: No error logging (fire-and-forget events)

**Validation:**
- Password: Validated with bcryptjs in `/api/auth/login`
- Email: Simple presence check in login route, domain check in `/api/analytics/view`
- Presence map: Built from JSON, no runtime validation

**Authentication:**
- Mechanism: HMAC-signed token stored in HttpOnly cookie
- Session check: Every API route that needs auth calls `getSessionFromCookie(req.headers.get('cookie'))`
- Enforcement: If token invalid or missing, return 401 or false auth status
- **No middleware.ts** — gating is per-route, not centralized

---

*Architecture analysis: 2026-04-16*
