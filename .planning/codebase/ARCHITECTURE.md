# Architecture

**Analysis Date:** 2026-04-16

## Pattern Overview

**Overall:** Modular data-driven Next.js application with clear separation between data layer and presentation layer.

**Key Characteristics:**
- **Data-first design**: Feature matrix data sourced from JSON files in `analysis/` that drive all app behavior
- **Barrel exports**: `analysis/index.ts` re-exported by `lib/data.ts` for backward compatibility
- **Client-heavy UI**: Stateful client components for filtering, sorting, and interaction
- **Minimal server-side logic**: Auth and analytics routing only; no dynamic data computation on server
- **Computed bands**: Feature adoption bands calculated on import via `computeBands()` in `analysis/index.ts`

## Layers

**Data Layer (`analysis/`):**
- Purpose: Store and define feature matrix (61 features across 33 products with presence data)
- Location: `analysis/`
- Contains: Product definitions, feature definitions, feature presence JSON results, rubric documentation, screenshot evidence
- Depends on: TypeScript types only
- Used by: `lib/data.ts` re-exports all to app and pages

**Service Layer (`lib/`):**
- Purpose: Provide domain-specific helper functions for auth, scoring, analytics, and summaries
- Location: `lib/`
- Contains: `auth.ts` (session management), `scoring.ts` (score calculation), `analytics.ts` (event logging), `summary.ts` (narrative generation), `track.ts` (client-side event firing), `data.ts` (barrel re-export)
- Depends on: `analysis/` data layer, external packages (bcryptjs, @upstash/redis, resend)
- Used by: API routes and pages

**API Layer (`app/api/`):**
- Purpose: Handle authentication, analytics, and cross-check image serving
- Location: `app/api/`
- Contains: Login/logout/me routes (`auth/`), analytics POST/view routes (`analytics/`), email route, crosscheck image proxy
- Depends on: `lib/auth.ts`, `lib/analytics.ts`, data files
- Used by: Client-side fetch calls and external integrations

**UI Layer (`app/`):**
- Purpose: Render feature matrix, club details, and authentication flows
- Location: `app/` (pages and layout)
- Contains: Root layout (`layout.tsx`), feature matrix homepage (`page.tsx`), club detail page (`club/[id]/page.tsx`), analytics page
- Depends on: `lib/data.ts`, `lib/track.ts`, `lib/summary.ts`, client components
- Used by: Browser HTTP requests

## Data Flow

**Feature Matrix Display (Home Page):**

1. User visits `/`
2. `app/page.tsx` (client component) imports `FEATURES`, `CATEGORIES`, `PRODUCTS` from `lib/data.ts`
3. Features already have band, adoption, and adoptionPct computed from `analysis/index.ts::computeBands()`
4. Component manages local state: current filters (category, band, search), sorted feature list
5. Filter state triggers `trackEvent('filter', {...})` via `lib/track.ts`
6. Client-side fetch to `/api/analytics` sends event with authenticated email (from session cookie) or 'anonymous'
7. Server receives at `app/api/analytics/route.ts`, extracts email, calls `logEvent()` to Upstash Redis

**Club Detail Page:**

1. User navigates to `/club/[id]`
2. `app/club/[id]/page.tsx` (server component) finds product by ID from `PRODUCTS`
3. Calls `generateClubSummary(id)` from `lib/summary.ts`
4. Summary generation: fetches product scores via `getProductScores()`, categories via `CATEGORIES`, features via `FEATURES`
5. Builds narrative strings based on coverage %, ranking, category performance
6. Returns both summary and feature list filtered by product ID
7. Client components (`CategoryFilter.tsx`, `PageTracker.tsx`, `ScrollRestore.tsx`) manage interaction state

**Authentication Flow:**

1. User submits email + password on home page modal
2. POST to `/api/auth/login` with credentials
3. Server loads users from `data/users.json` via `lib/auth.ts::loadUsers()`
4. Verifies password with bcryptjs (from stored hash)
5. Creates session token via `createSessionToken(email)` (HMAC-signed payload)
6. Returns token in Set-Cookie header (HttpOnly, Max-Age 7 days)
7. Future requests send cookie; extracted by `getSessionFromCookie()` for authorization
8. Logout: POST to `/api/auth/logout` clears cookie
9. Current user fetched via `/api/auth/me` with session from cookie

**State Management:**

- **Server state**: Feature definitions + presence data in `analysis/homepage/results/*.json` (immutable, deployed with code)
- **User session state**: Cookie-based, validated at request time via HMAC
- **Page state**: React local state in client components (filters, selections, scroll position)
- **Analytics state**: Event log in Upstash Redis (read-only via `/api/analytics/view`)

## Key Abstractions

**Feature:**
- Purpose: Represents one scored element in the benchmark (e.g., "Language Switcher")
- Examples: `analysis/homepage/features.ts` (Feature definition), `analysis/homepage/results/*.json` (presence per club)
- Pattern: Import all JSON results, build `RESULTS` map keyed by product ID, populate `Feature.presence` object at runtime

**Product:**
- Purpose: Sports organization being analyzed (club, league, governing body)
- Examples: `analysis/products.ts` (static list of 33 products)
- Pattern: TypeScript union type with id, name, sport, type, logo

**Band:**
- Purpose: Adoption tier label for features (table_stakes, expected, competitive, innovation)
- Examples: Computed in `analysis/index.ts::computeBands()`
- Pattern: Based on adoption % with tier-based floor (Tier A ≥ expected band, Tier B ≥ competitive band, etc.)

**ClubSummary:**
- Purpose: Narrative description of a product's benchmark performance
- Examples: `lib/summary.ts::generateClubSummary()`
- Pattern: Generated on demand, uses category scores and missing features to build editorial-style text

**Category:**
- Purpose: Grouping of related features (12 categories: header_nav, hero, match_fixtures, etc.)
- Examples: `analysis/homepage/categories.ts`
- Pattern: Static list with name and color for UI rendering

## Entry Points

**Homepage:**
- Location: `app/page.tsx`
- Triggers: HTTP GET /
- Responsibilities: Render feature matrix with category/band/search filters, handle auth modal, track filter events

**Club Detail:**
- Location: `app/club/[id]/page.tsx`
- Triggers: HTTP GET /club/[id]
- Responsibilities: Fetch club summary, display feature list with category breakdown, show rankings

**Login API:**
- Location: `app/api/auth/login/route.ts`
- Triggers: HTTP POST /api/auth/login with {email, password}
- Responsibilities: Validate credentials, create session token, set cookie, log event

**Analytics API:**
- Location: `app/api/analytics/route.ts`
- Triggers: HTTP POST /api/analytics with {type, data}
- Responsibilities: Extract session email, append event to Redis list

**Analytics View:**
- Location: `app/api/analytics/view/route.ts`
- Triggers: HTTP GET /api/analytics/view (admin only)
- Responsibilities: Fetch recent events from Redis, return JSON list

## Error Handling

**Strategy:** Permissive client-side, strict server-side with graceful fallbacks.

**Patterns:**
- Analytics errors are silent (fire-and-forget; never break UX)
- Auth failures return 400/401 status with generic error message ("Invalid email or password")
- Missing product ID returns `notFound()` from `next/navigation`
- Session validation fails silently: missing cookie or invalid token → email = "anonymous"
- Redis unavailable in dev mode: console.log fallback in `lib/analytics.ts`
- User file not found: `loadUsers()` returns empty array, login fails with 401

## Cross-Cutting Concerns

**Logging:** Console.log for dev analytics fallback; Upstash Redis for production events

**Validation:** 
- Email/password required on login (400 if missing)
- Session token validated via HMAC signature
- Product ID must exist in `PRODUCTS` array

**Authentication:**
- Cookie-based with HMAC-signed tokens
- Password hashing via bcryptjs (salt 10)
- Session valid 7 days, HttpOnly + SameSite=Lax

**Analytics:**
- Every user interaction tracked (filters, page views, logins)
- Email extracted from session or "anonymous" if not authenticated
- Event type + metadata stored in Redis as JSON

---

*Architecture analysis: 2026-04-16*
