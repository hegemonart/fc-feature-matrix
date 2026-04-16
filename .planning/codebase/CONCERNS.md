# Codebase Concerns

**Analysis Date:** 2026-04-16

## Tech Debt

**Hardcoded Auth Secret in Development:**
- Issue: `lib/auth.ts` contains a fallback auth secret `'fc-benchmark-dev-secret-change-in-prod'` used when `AUTH_SECRET` env var is missing
- Files: `lib/auth.ts` (line 4)
- Impact: In production without the env var set, session tokens would use a known secret, compromising session integrity and allowing token forgery
- Fix approach: Remove fallback, make `AUTH_SECRET` required in production via build-time validation or startup checks

**In-Memory Rate Limiting Is Not Persistent:**
- Issue: `app/api/email/route.ts` uses a Map for rate limiting that only lives in memory for a single process instance
- Files: `app/api/email/route.ts` (lines 10-20)
- Impact: On Vercel with serverless functions, each invocation gets a new process; rate limiting resets per request. Distributed spam becomes trivial. Also leaks memory indefinitely if Map never clears old IPs
- Fix approach: Replace with Redis-backed rate limiting (similar to analytics logging) or use a service like Upstash with proper TTL

**User Store Requires Manual JSON Edits:**
- Issue: No user management API exists. Adding/removing/changing users requires directly editing `data/users.json`
- Files: `lib/auth.ts` (loadUsers function), `data/users.json`
- Impact: Operational friction; no audit trail of user changes; risky for manual edits in production. Adding users via shell/GUI would be better
- Fix approach: Build a user management endpoint (POST/DELETE) with audit logging

**No Input Validation on Email Route:**
- Issue: `app/api/email/route.ts` accepts arbitrary feature/source values without sanitization
- Files: `app/api/email/route.ts` (lines 36-37)
- Impact: Email body could contain injection attacks, extremely long strings, or malicious content. Low risk to the app but poor hygiene
- Fix approach: Add schema validation (e.g., zod) to limit feature/source to reasonable lengths and character sets

## Known Bugs

**Analytics Silently Fails on Upstash Connection Issues:**
- Symptoms: `logEvent()` catches all errors and logs to console, but app continues. Users may think analytics work when they don't
- Files: `lib/analytics.ts` (lines 52-54)
- Trigger: Upstash KV_REST_API_URL/KV_REST_API_TOKEN missing, network error, or Upstash rate limit hit
- Workaround: Check browser console or server logs for `[analytics] Failed to log event` messages. No user-facing error.

**Email Endpoint Doesn't Validate Resend API Key:**
- Symptoms: If RESEND_API_KEY is missing, `new Resend()` succeeds, but `resend.emails.send()` fails silently with a 500
- Files: `app/api/email/route.ts` (lines 40-59)
- Trigger: Missing/invalid RESEND_API_KEY in .env
- Workaround: Check server logs for `Email send failed` errors

**Scoring Calculations Don't Account for Missing Data in Results JSON:**
- Symptoms: If a club's result JSON is missing a feature key, that feature counts as 'absent' even if it was never analyzed
- Files: `lib/scoring.ts`, `analysis/homepage/features.ts` (buildPresence function)
- Trigger: Incomplete analysis or JSON from old rubric version with fewer features
- Workaround: Ensure all result JSONs are synchronized with current feature set before release

## Security Considerations

**User Credentials Stored in Committed JSON File:**
- Risk: Password hashes are in `data/users.json` which is committed to Git. While bcrypt hashes are strong, this is poor practice (should be in a database with proper access controls)
- Files: `data/users.json` (committed to repo)
- Current mitigation: Hashes are bcrypt with cost factor 10, not plaintext
- Recommendations: (1) Move users.json to .gitignore and use database on production; (2) Add comments to data/users.json explaining this is dev-only; (3) Rotate the hashes if the repo is public

**IP Address Stored in Email from Rate Limiter:**
- Risk: Emails to hi@humbleteam.com include the user's IP, which could be sensitive in some jurisdictions (GDPR implications if EU traffic)
- Files: `app/api/email/route.ts` (line 51)
- Current mitigation: Only the "hi@humbleteam.com" team receives this
- Recommendations: (1) Add privacy notice; (2) Hash IP instead of sending raw; (3) Omit if user opts out

**Session Token Uses HMAC-SHA256, Not Cryptographic Signing:**
- Risk: Token format is `email:timestamp:signature`. If an attacker knows an email, they can guess valid timestamps and forge tokens (birthday attack feasible on 64-bit signature space)
- Files: `lib/auth.ts` (lines 21-27)
- Current mitigation: 7-day expiry limits window; HttpOnly and SameSite cookies provide some XSS/CSRF protection
- Recommendations: (1) Use RS256 (RSA) or EdDSA instead of HMAC; (2) Add a user ID or nonce to token; (3) Increase signature entropy or use proper JWT library

**No CORS Headers Defined:**
- Risk: Analytics and email endpoints accept POST from any origin. Could be abused to spam email endpoint from competitor sites
- Files: `app/api/email/route.ts`, `app/api/analytics/route.ts`
- Current mitigation: Rate limiting on email endpoint (but broken in serverless); analytics logged per-user
- Recommendations: Add explicit CORS headers or require origin validation

## Performance Bottlenecks

**All Features Computed on Every Club Detail Page Load:**
- Problem: `/club/[id]` generates category breakdowns, ranked products, and feature lists on every request, even for static content
- Files: `app/club/[id]/page.tsx` (lines 44-75)
- Cause: Page is dynamic (async component) but all data comes from static analysis. Could be pre-built at build time
- Improvement path: (1) Move category/rank computations to build-time exports; (2) Use generateStaticParams + ISR to pre-generate all club pages; (3) Cache aggregated data in Redis

**Summary Generation Is Verbose Text Processing:**
- Problem: `generateClubSummary()` runs complex conditional logic with many string concatenations on page load
- Files: `lib/summary.ts` (entire file, ~200 lines of editorial logic per request)
- Cause: Summary is generated on-demand rather than at build time
- Improvement path: (1) Pre-generate summaries as JSON during analysis; (2) Cache at build time; (3) Or defer to a static summary API endpoint

**No Caching Headers on Image Endpoint:**
- Problem: `app/api/crosscheck-img/route.ts` sets `max-age=86400` (1 day) but no Etag or Last-Modified header
- Files: `app/api/crosscheck-img/route.ts` (lines 23-26)
- Cause: Browser cache works but can't revalidate efficiently; CDN caching also suboptimal
- Improvement path: Add Etag or Last-Modified header; consider moving images to a CDN bucket instead

**Lazy Initialization of Redis Connection:**
- Problem: Redis client initialized on first analytics call, not at startup. Errors surfaced slowly
- Files: `lib/analytics.ts` (lines 8-16)
- Cause: "Fail quietly" pattern makes issues hard to debug
- Improvement path: (1) Initialize at app startup with error if missing; (2) Or use a fallback persistence layer (e.g., database)

## Fragile Areas

**Feature Presence Map Building via Manual Imports:**
- Files: `analysis/homepage/features.ts` (lines 12-43, 46-83)
- Why fragile: Each new club requires (1) adding its result JSON import, (2) adding entry to RESULTS object. Easy to miss either step. Results in undefined feature presence
- Safe modification: (1) Auto-discover result files instead of manual imports; (2) Validate RESULTS object keys match ALL_IDS in test; (3) Add build-time check that all products have results
- Test coverage: No tests currently exist for this synchronization

**Summary Generation Has Many Editorial Rules:**
- Files: `lib/summary.ts` (lines 61-198)
- Why fragile: Large `if/else if` chain with hardcoded thresholds (75%, 60%, 45%, etc.). Adding a new narrative category requires careful placement to avoid contradictions
- Safe modification: (1) Refactor into smaller, testable functions; (2) Extract thresholds to constants at top of file; (3) Add test cases for edge cases (0%, 100%, exactly at threshold)
- Test coverage: No unit tests; only manual verification

**Category Filter State Management:**
- Files: `app/club/[id]/CategoryFilter.tsx` (lines 37-44)
- Why fragile: Uses useState with Set<CategoryId>. Toggle logic has potential edge cases if activeCats gets out of sync with catScores
- Safe modification: (1) Use useCallback for toggle function; (2) Validate activeCats keys exist in catScores on render; (3) Add tests for toggle behavior
- Test coverage: No tests; only manual browser testing

## Scaling Limits

**Hardcoded Product List Requires Rebuild:**
- Current capacity: 33 clubs
- Limit: Adding a new club requires: edit products.ts, add import + RESULTS entry in features.ts, rerun score recalculation, rebuild app
- Scaling path: (1) Load products from JSON/database; (2) Make features auto-discover result files; (3) Use on-demand static generation for new clubs

**Rate Limiter Per-Process:**
- Current capacity: Single request per IP tracked per process
- Limit: Serverless = new process per request = rate limiting ineffective
- Scaling path: Move to Redis or third-party rate limit service (e.g., Upstash with dedicated rate-limit endpoint)

**Redis Event Store Has Manual Trim:**
- Current capacity: 10,000 events max (line 4 of analytics.ts)
- Limit: Once limit hit, oldest events deleted. No pagination or archival
- Scaling path: (1) Implement event archival/export; (2) Use Redis Streams instead of List; (3) Add separate analytics database

**User Store Cannot Handle Many Users:**
- Current capacity: ~4 users in data/users.json
- Limit: File-based storage becomes unmaintainable; no indexing or query API
- Scaling path: Migrate to PostgreSQL or similar with bcrypt password verification

## Dependencies at Risk

**Upstash Redis SDK (`@upstash/redis`):**
- Risk: Optional dependency for analytics. If missing, analytics silently falls back to console.log. No explicit warning that analytics aren't working
- Impact: Production may have zero analytics visibility without obvious failure
- Migration plan: (1) Make explicit check on startup if using Redis; (2) Or add verbose startup message listing disabled features; (3) Or use Vercel KV instead (same API)

**Resend Email SDK (`resend`):**
- Risk: Optional email functionality. Errors caught and swallowed. If key invalid, silent failure
- Impact: Access requests silently fail to reach the team
- Migration plan: (1) Add health check endpoint that tests email connectivity; (2) Use more robust email library with retry logic; (3) Or fall back to mailto: if Resend fails

**BCryptJS (`bcryptjs`):**
- Risk: No known critical issues, but library is old (v3.0.3). Check npm audit regularly
- Impact: Password storage security
- Migration plan: Keep up to date; consider scrypt or argon2 in future

## Missing Critical Features

**No User Registration Endpoint:**
- Problem: Only hardcoded users can log in. New team members require manual edit to data/users.json
- Blocks: Self-serve access; team growth without engineer involvement
- Suggested implementation: POST /api/auth/register with email, password, and admin approval workflow

**No Password Reset:**
- Problem: Users who forget passwords cannot recover
- Blocks: Account lockout is permanent
- Suggested implementation: Email-based reset token sent to registered email

**No Logout Endpoint Return Value:**
- Problem: POST /api/auth/logout returns 200 OK but doesn't indicate whether session was valid. Client has no way to know if they were logged in
- Blocks: UI clarity on logout status
- Suggested implementation: Return {wasLoggedIn: boolean}

**No Session Validation Endpoint:**
- Problem: Client has no way to check if current session is valid without trying to fetch protected data
- Blocks: Pre-render logic; hydration on login pages
- Suggested implementation: GET /api/auth/me that returns current user or 401

**No Audit Logging:**
- Problem: No record of who logged in when, what they accessed, or who edited user data
- Blocks: Security investigation; compliance reporting
- Suggested implementation: Write audit log to database on login/logout/user-edit events

## Test Coverage Gaps

**No Unit Tests for Scoring Logic:**
- What's not tested: `getProductScores()` asymmetric weighting, edge cases (all features absent/full, negative scores)
- Files: `lib/scoring.ts`
- Risk: Score recalculation errors go unnoticed; publishing wrong rankings
- Priority: High

**No Tests for Summary Generation:**
- What's not tested: All 8+ narrative branches in `generateClubSummary()`, edge cases (0%, 100%, exactly at thresholds), text correctness
- Files: `lib/summary.ts`
- Risk: Misleading conclusions published (e.g., "table stakes gap" when actually none exist)
- Priority: High

**No Tests for Auth Logic:**
- What's not tested: Session token signing/parsing, edge cases (empty email, huge timestamp), password hash verification
- Files: `lib/auth.ts`
- Risk: Token forgery or parse failures go unnoticed until production
- Priority: High

**No Tests for Analytics Event Logging:**
- What's not tested: Redis connection failures, event serialization, rate limiting of requests
- Files: `lib/analytics.ts`, `app/api/analytics/route.ts`
- Risk: Silent failures; false sense of data collection
- Priority: Medium

**No E2E Tests:**
- What's not tested: Full user flow (login → browse club → logout), cross-page navigation, pagination, category filtering
- Files: Entire app
- Risk: UI bugs only caught in manual testing
- Priority: Medium

**No Tests for Feature Presence Sync:**
- What's not tested: Mismatch between result JSON and feature keys, missing result files
- Files: `analysis/homepage/features.ts`
- Risk: Incomplete data published silently
- Priority: High

---

*Concerns audit: 2026-04-16*
