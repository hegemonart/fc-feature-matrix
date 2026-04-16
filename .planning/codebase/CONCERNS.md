# Codebase Concerns

**Analysis Date:** 2026-04-16

## Auth Layer

**Hardcoded default AUTH_SECRET (`lib/auth.ts:4`):**
- Issue: Line 4 uses fallback secret `'fc-benchmark-dev-secret-change-in-prod'` when `AUTH_SECRET` env var is missing
- Files: `lib/auth.ts:4`
- Impact: In production, if `AUTH_SECRET` is not explicitly set, all session tokens are signed with a publicly known default secret. Any attacker can forge valid session tokens and impersonate any user
- Fix approach: Make `AUTH_SECRET` required in production. Validate on startup: throw error if missing when `NODE_ENV === 'production'`. Add env validation schema (zod/joi) to fail fast on misconfiguration

**Session token timestamp not validated (`lib/auth.ts:30-41`):**
- Issue: `parseSessionToken()` extracts and validates the HMAC signature but does NOT check the timestamp in the token against current time
- Files: `lib/auth.ts:30-41`
- Impact: A 7-day-old cookie is valid forever. No expiration enforcement on token age. Combined with hardcoded secret, an attacker can forge a token dated in 1970 and it will be accepted
- Fix approach: Add age validation in `parseSessionToken()`: parse the timestamp field, check `Date.now() - tokenTimestamp < MAX_AGE * 1000`, return null if expired. Also add an optional `tokenExpiredAt` field to return for debugging

**No CSRF protection on login POST (`app/api/auth/login/route.ts:5`):**
- Issue: Login endpoint accepts POST without validating referer/origin headers or CSRF tokens
- Files: `app/api/auth/login/route.ts:5`
- Impact: A cross-site request from `evil.com` can trigger login on behalf of a user (e.g. in a hidden iframe with email+password in form data). Session cookie gets set on the user's browser
- Fix approach: Add Origin/Referer validation. Check `req.headers.get('origin')` matches expected domain(s). Or implement CSRF token in login form (session-per-request CSRF token stored in a separate cookie)

**User enumeration via login endpoint (`app/api/auth/login/route.ts:14-16`):**
- Issue: Error message distinguishes between "user not found" and "invalid password" — both return 401 with same message `"Invalid email or password"` (good), but timing attacks are possible
- Files: `app/api/auth/login/route.ts:14-21`
- Impact: Low — error message is generic. However, `bcrypt.compare()` on line 18 is slower for wrong passwords than for missing users (no hash verification for missing users). Attacker can measure response time to guess valid emails
- Fix approach: Always run `bcrypt.compare()` even for missing users (compare input against a dummy hash or fixed hash), to make timing consistent. Or use `timing-safe-compare` library

**Session cookie uses SameSite=Lax, not Strict (`lib/auth.ts:46`):**
- Issue: `sessionCookieHeader()` sets `SameSite=Lax` on session cookies
- Files: `lib/auth.ts:46`
- Impact: SameSite=Lax allows the cookie to be sent on top-level navigations from other sites (e.g. clicking a link from `evil.com` to `app.local`). Not a direct CSRF vector (Lax doesn't apply to form submissions), but weakens protection. SameSite=Strict would prevent all cross-site cookie transmission
- Fix approach: Evaluate threat model. If users may navigate from external links, SameSite=Lax is acceptable. If stricter isolation needed, switch to Strict (may break federated authentication flows if used). Current choice is reasonable for internal app

**No rate limiting on login (`app/api/auth/login/route.ts`)**:
- Issue: Login endpoint allows unlimited password guessing attempts
- Files: `app/api/auth/login/route.ts:5-33`
- Impact: Attacker can brute-force passwords. With 5 users and weak passwords, compromise is feasible
- Fix approach: Add per-IP or per-email rate limiting (similar to `/api/email` which already has it). Lock account after N failed attempts. Implement progressive delays (exponential backoff)

---

## User Store

**User data committed to git (`data/users.json`):**
- Issue: `data/users.json` contains 5 users with bcrypt password hashes, emails, and names — all committed to the git repository
- Files: `data/users.json` (full contents visible in any git clone)
- Impact: Password hashes are not secrets (bcrypt is designed to resist offline cracking), but the user list itself (email + name + hash tuples) is sensitive metadata. Git history is permanent — once committed, hashes exist forever even if file is deleted
- Fix approach: Move `data/users.json` to `.gitignore`. Store in a secrets manager (Vercel Secrets, AWS Secrets Manager, HashiCorp Vault). Load on startup from env var or secure store. For initial setup, provide a script to seed users from stdin or env vars

**Synchronous disk reads on every request (`lib/auth.ts:74-83`):**
- Issue: `loadUsers()` reads `data/users.json` from disk synchronously using `fs.readFileSync()` on every login/request
- Files: `lib/auth.ts:74-83`, called from `app/api/auth/login/route.ts:12`
- Impact: I/O blocking. With 5 users, latency is low, but scales poorly. If user list grows to 1000+ or disk is slow, every login blocks the event loop
- Fix approach: Cache users in memory (with a TTL, e.g. 60 seconds). Or use async I/O (`fs.promises.readFile()`). Or migrate to a database

**No concurrency control on user writes:**
- Issue: No `saveUser()` function exists yet, but if one were added, concurrent writes would not be protected. Multiple requests could simultaneously read, modify, and write the JSON file, causing lost updates
- Files: `lib/auth.ts` (missing saveUser implementation)
- Impact: Race conditions if user registration / password reset endpoints are added
- Fix approach: Implement atomic writes: read → modify → write atomically (use fs transactions, or write to temp file + rename). Or migrate to a database with transaction support

**User additions require redeploy (`data/users.json`):**
- Issue: Adding a new user requires editing `data/users.json` and redeploying the app
- Files: `data/users.json`
- Impact: Operational friction. No self-service signup or admin UX to add users at runtime
- Fix approach: Implement user management API: `POST /api/admin/users` to create users (gated behind admin auth). Or integrate with an external auth provider (Auth0, Firebase, Cognito)

---

## Analytics Layer

**Redis list capped at 10,000 events with no overflow strategy (`lib/analytics.ts:4, 51`):**
- Issue: Events are stored in Redis list `analytics:events`, trimmed to max 10,000 items via `ltrim()` on line 51
- Files: `lib/analytics.ts:4, 50-51`
- Impact: Old events are silently dropped once the list reaches 10k. No warning or audit trail. Analytics are lossy — can't reconstruct historical activity beyond the 10k-event window
- Fix approach: Log trimming events. Consider archiving old events to a persistent store (S3, database) before trimming. Or increase cap based on expected event volume and retention requirements

**Analytics endpoint accepts unauthenticated requests (`app/api/analytics/route.ts`):**
- Issue: `POST /api/analytics` accepts requests from anonymous users (logs them as `'anonymous'` on line 14). No auth required
- Files: `app/api/analytics/route.ts:5-21`
- Impact: Any user (authenticated or not) can log arbitrary events. An attacker can spam the Redis list with junk data, polluting analytics or performing DoS. However, read endpoint (`/api/analytics/view`) IS properly gated to `@humbleteam.com`
- Fix approach: Require authentication for write access as well. Either check session cookie, or implement an API key. Or accept unauthenticated write but implement stricter rate limiting per IP

**No authentication required to POST events (`app/api/analytics/route.ts:5-21`):**
- Issue: The endpoint accepts `type` and `data` from any request, logs event with email from session (or 'anonymous'), but does not validate request source
- Files: `app/api/analytics/route.ts`
- Impact: Users on the public homepage can submit arbitrary event data. Mixed with the lack of rate limiting on the analytics endpoint, an attacker can spam events: `trackEvent('page_view', { fake: 'data' })`
- Fix approach: Add CORS restrictions if analytics are supposed to be internal-only. Or implement per-IP rate limiting for the analytics endpoint (separate from email rate limit). Current implementation is acceptable if analytics are informational only

**Fixed analytics key makes multi-tenant usage impossible (`lib/analytics.ts:3`):**
- Issue: All events go to a single Redis key: `'analytics:events'`
- Files: `lib/analytics.ts:3`
- Impact: If the app ever scales to multiple organizations or workspaces, analytics are global. Can't isolate per-tenant
- Fix approach: Use a composite key: `analytics:events:{workspace_id}` or `analytics:events:{org_id}`. This is forward-looking; current single-tenant design is fine

---

## Main Matrix Page

**Monolithic page component at 1045 lines (`app/page.tsx`):**
- Issue: The homepage is a single client component with 1045 lines of code, handling state, rendering, auth modals, locked flows, tooltips, filters, sorting, and analytics all in one file
- Files: `app/page.tsx`
- Impact: Hard to test, reuse, or extend. Many interconnected state variables (filterTypes, activeCat, selectedFeature, selectedProduct, adoptionSort, featureAlphaSort, scoreSort, authed, authEmail, loginModalVisible, ctaView, loginEmail, loginPassword, loginError, loginLoading, lockedModalVisible, lockedFlowName, comingSoonVisible, requestSending, requestSent, etc.). Changes to one feature risk breaking others
- Fix approach: Extract components: `<LoginModal>`, `<LockedFlowModal>`, `<CategoryFilter>`, `<FeatureTooltip>`, `<MatrixGrid>`, `<SortControls>`. Move business logic to custom hooks. Use context or state management library (Zustand, Jotai) for global state

**No error boundaries or fallback UI for matrix load (`app/page.tsx:51-100`):**
- Issue: The page assumes `PRODUCTS`, `FEATURES`, `CATEGORIES` load successfully from `lib/data`. If these fail, there's no error UI
- Files: `app/page.tsx`, depends on `lib/data.ts`
- Impact: Blank page or JS errors if data import fails. Users see nothing instead of a helpful error message
- Fix approach: Add try-catch around data imports. Render an error state: "Failed to load data. Please refresh the page."

---

## Data Pipeline

**35 JSON result files, fragile coupling to feature definitions (`analysis/homepage/results/*.json`, `analysis/homepage/features.ts`):**
- Issue: Each club has a result JSON (e.g. `real_madrid.json`). The `features.ts` imports all of them and constructs feature maps. If a feature key changes or is removed, old JSONs become invalid
- Files: `analysis/homepage/results/*.json` (35 files), `analysis/homepage/features.ts`
- Impact: Schema mismatch risk. If a feature key is renamed in the rubric, old JSONs don't auto-migrate. The `recalculate-scores.js` script will skip missing keys silently
- Fix approach: Add validation: schema check in `features.ts` to ensure all imported JSONs have expected keys. Or add a migration script to rename keys when the rubric changes

**recalculate-scores.js regex parsing is fragile (`analysis/homepage/crosscheck/recalculate-scores.js:18-25`):**
- Issue: The script uses a regex to parse `feat()` calls from `features.ts`: `/feat\(\s*'[^']+'\s*,\s*'([^']+)'\s*,\s*[^)]*,\s*'[A-F]'\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)/g`
- Files: `analysis/homepage/crosscheck/recalculate-scores.js:18-25`
- Impact: If the `feat()` call format changes (whitespace, parameter order, comments inside calls), the regex breaks silently and parses zero features, resulting in all scores being reset to 0. No warning unless run manually
- Fix approach: Replace regex parsing with TypeScript/Node import and reflection (use actual `features.ts` exports). Or add validation: if `featureCount === 0 && fileSize > 1000 bytes`, error and exit (line 30-33 already does this, good!)

---

## CI/CD

**CI workflow exists but branch protection unknown (`.github/workflows/ci.yml`):**
- Issue: Pipeline runs linting, typecheck, tests, and build on every push/PR to `master`. However, GitHub repo settings for branch protection are not visible in the codebase
- Files: `.github/workflows/ci.yml:1-33`
- Impact: It's unclear if CI must pass before merge. If not enforced, broken code can be merged
- Fix approach: Verify in GitHub Settings → Branches → Branch protection rule on `master`: (1) "Require status checks to pass before merging", (2) "Require branches to be up to date before merging", (3) "Dismiss stale pull request approvals". This is a GitHub UI config, not a code change, but critical to verify

**No deployment gate between staging and production (`.github/workflows/ci.yml`):**
- Issue: CI runs tests and builds, but there's no separate deployment job. Vercel auto-deploys on push to `master`
- Files: `.github/workflows/ci.yml`, `vercel.json`
- Impact: No manual approval step. If CI passes but introduces a subtle bug, it goes straight to production
- Fix approach: Add a GitHub Actions deployment job that requires manual approval. Or use Vercel's GitHub app to gate deployments by PR environment checks

---

## Environment Variables & Configuration

**No centralized env validation (`lib/auth.ts:4`, `lib/analytics.ts:12-16`, `app/api/email/route.ts:6`):**
- Issue: Environment variables are accessed ad-hoc throughout the codebase without a schema. `AUTH_SECRET` has a hardcoded fallback, `KV_REST_API_URL/TOKEN` are optional (return null if missing), `RESEND_API_KEY` is used without existence check
- Files: `lib/auth.ts:4`, `lib/analytics.ts:12-16`, `app/api/email/route.ts:6`
- Impact: Misconfigured env vars are discovered at runtime, when code path is reached. E.g. if `RESEND_API_KEY` is missing, email sends fail at runtime instead of failing on startup
- Fix approach: Create `lib/env.ts` with a Zod schema:
  ```typescript
  const envSchema = z.object({
    AUTH_SECRET: z.string().min(32, 'AUTH_SECRET must be ≥32 chars'),
    KV_REST_API_URL: z.string().url().optional(),
    KV_REST_API_TOKEN: z.string().optional(),
    RESEND_API_KEY: z.string().optional(),
    NODE_ENV: z.enum(['development', 'production']).default('development'),
  });
  export const env = envSchema.parse(process.env);
  ```
  Call this on app startup (in `next.config.ts` or root layout) to fail fast if missing required vars

**No .env.example file for documentation:**
- Issue: No template showing which env vars are required and their formats
- Files: Missing `.env.example`
- Impact: Developers and ops don't know what to set. Easy to forget `AUTH_SECRET` and hit the hardcoded fallback in production
- Fix approach: Create `.env.example` with all required and optional vars and brief descriptions

---

## Security Observations

**HttpOnly, Path, SameSite are set correctly on session cookies:**
- Good: `sessionCookieHeader()` sets `HttpOnly` (prevents JS access), `Path=/` (applies to all routes), `SameSite=Lax` (prevents cross-site form submission CSRF)
- No action needed

**HMAC-SHA256 signature on tokens is cryptographically sound:**
- Good: Tokens are signed with `createHmac('sha256', SECRET)`, not just concatenated or base64 encoded
- The vulnerability is only the hardcoded default, not the algorithm itself

**Bcrypt password hashing with cost 10 is acceptable:**
- Good: `bcrypt.hash(password, 10)` on line 11. Cost 10 takes ~100ms to verify, reasonable for login (not so expensive it breaks auth, not so cheap it enables fast brute-forcing)
- Consider cost 12 (400ms) if brute-force protection is a priority

---

## Missing Critical Features

**No password reset endpoint:**
- Issue: Users cannot reset forgotten passwords
- Impact: Locked out users must contact admin to manually reset
- Fix approach: Implement `/api/auth/reset-password` with email-based token (signed, time-limited). Send reset link via Resend

**No user registration endpoint:**
- Issue: New users cannot sign up; only admins can edit `data/users.json`
- Impact: Not self-serve. Operational burden
- Fix approach: Implement `/api/auth/register` with rate limiting and email verification. Or remove this feature entirely if it's intentionally admin-only

**No session revocation endpoint:**
- Issue: If a session is leaked, there's no way to invalidate it before MAX_AGE (7 days)
- Impact: Compromised sessions are valid for up to 7 days
- Fix approach: Implement a token blacklist (Redis set: `revoked_tokens:{token_hash}`) checked on every request. Or use short-lived tokens + refresh tokens

**No audit logging for auth events:**
- Issue: `logEvent('login', ...)` and `logEvent('logout', ...)` are called (good), but no dedicated auth audit log
- Impact: Hard to detect brute-force attempts or suspicious logins in real-time
- Fix approach: Store auth events in a separate Redis set or database table. Alert on repeated failed logins from same IP

---

## Test Coverage

**Only 1 test file, limited coverage (`lib/scoring.test.ts`):**
- Issue: `lib/scoring.test.ts` has 21 lines (small test suite). No tests for auth, analytics, email, or the main page component
- Files: `lib/scoring.test.ts`
- Impact: Auth logic, analytics storage, email sending are untested. Changes to these systems risk silent failures
- Fix approach: Add test suites: `lib/auth.test.ts`, `app/api/auth/login/route.test.ts`, `lib/analytics.test.ts`, `app/api/email/route.test.ts`. Use vitest + mocks for Redis and Resend. Target ≥80% coverage for critical paths

---

## Performance Concerns

**No database indexes or query optimization:**
- Issue: Analytics queries filter by `type` and `email` in-memory after fetching 500+ events from Redis
- Files: `lib/analytics.ts:59-86`
- Impact: With 10k events, filtering is O(n). Queries slow down as analytics grow
- Fix approach: Use Redis sorted sets or hash tables for indexed access. Or migrate to a real analytics database (ClickHouse, TimescaleDB)

**Typescript compilation not cached in CI:**
- Issue: CI runs `npm run typecheck` (tsc --noEmit) on every push, recompiling from scratch
- Files: `.github/workflows/ci.yml:25-26`
- Impact: CI takes longer than necessary. Minimal impact for this project size, but scales poorly
- Fix approach: Use `tsc --incremental` or GitHub Actions caching for `node_modules/.tsc-cache`

---

## Fragile Areas

**Club detail page may be fragile to missing data (`app/club/[id]/page.tsx:242`):**
- Issue: The page renders a club detail view. If a club ID in the URL doesn't exist in `PRODUCTS`, the page may render with missing/undefined data
- Files: `app/club/[id]/page.tsx`
- Impact: 404 or broken layout if invalid club ID
- Fix approach: Add validation: fetch product by ID, return `notFound()` if not found. Verify features are present in FEATURES map before rendering

---

## Summary Table

| Area | Severity | Issue | Files | Mitigation |
|------|----------|-------|-------|-----------|
| **Auth** | **Critical** | Hardcoded default AUTH_SECRET | `lib/auth.ts:4` | Make AUTH_SECRET required; validate on startup |
| **Auth** | **High** | Session timestamp not validated | `lib/auth.ts:30-41` | Add expiration check in `parseSessionToken()` |
| **Auth** | **High** | No CSRF protection on login POST | `app/api/auth/login/route.ts:5` | Validate Origin header or implement CSRF tokens |
| **Auth** | **Medium** | No rate limiting on login | `app/api/auth/login/route.ts` | Add per-IP/per-email rate limiting |
| **Auth** | **Medium** | Timing attack on password verification | `app/api/auth/login/route.ts:14-21` | Always run bcrypt.compare() even for missing users |
| **User Store** | **High** | User data committed to git | `data/users.json` | Move to .gitignore; load from secrets manager |
| **User Store** | **Medium** | Synchronous disk I/O on every login | `lib/auth.ts:74-83` | Cache users in memory or use async I/O |
| **User Store** | **Medium** | No concurrency control on writes | `lib/auth.ts` (missing) | Use atomic file writes or migrate to database |
| **Analytics** | **Medium** | Redis cap at 10k events with no archive | `lib/analytics.ts:4, 51` | Archive old events or increase cap; log trimming events |
| **Analytics** | **Medium** | No auth on analytics write endpoint | `app/api/analytics/route.ts` | Require authentication or strict rate limiting |
| **Page** | **Medium** | 1045-line monolithic component | `app/page.tsx` | Extract sub-components; use custom hooks |
| **Data Pipeline** | **Low** | Fragile regex parsing in recalculate-scores.js | `analysis/homepage/crosscheck/recalculate-scores.js:18-25` | Use TS imports + reflection instead of regex |
| **Env Config** | **High** | No centralized env validation | Multiple files | Create `lib/env.ts` with Zod schema |
| **Env Config** | **Medium** | No .env.example | Missing file | Create template for documentation |
| **CI/CD** | **Medium** | Branch protection status unknown | GitHub Settings (not in code) | Verify master branch protection is enforced |
| **Features** | **Medium** | No password reset endpoint | Missing | Implement email-based reset with signed tokens |
| **Features** | **Medium** | No user registration endpoint | Missing | Implement signup flow or document admin-only design |
| **Features** | **Medium** | No session revocation | Missing | Add token blacklist (Redis) or short-lived tokens |
| **Tests** | **Medium** | Very limited test coverage | `lib/scoring.test.ts` | Add test suites for auth, analytics, email |

---

*Concerns audit: 2026-04-16*
