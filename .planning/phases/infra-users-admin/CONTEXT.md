# Infra Phase — Users, Admin Panel & Analytics Migration

> **Status:** Out-of-band infrastructure work, parallel to the v2–v11 product roadmap (ROADMAP.md Phases 1–6). Listed in ROADMAP.md §"Out-of-Band Infrastructure" alongside the completed `infra-ci-cd` phase. Does not gate any numbered phase.

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase moves three things off filesystem / Redis storage and into **Neon Postgres**, and wraps them in a single **/admin** surface:

1. **Users** — from `data/users.json` (committed to git, 5 entries, requires redeploy to add a user) to a `users` table with an `is_admin` boolean. Admins can create / edit / delete users from the admin panel at runtime.
2. **Analytics events** — from the Upstash Redis list `analytics:events` (capped at 10k via LTRIM) to a Postgres `events` table with 90-day rolling retention via Vercel Cron.
3. **Access requests** — from fire-and-forget Resend emails to a `access_requests` table backing an admin triage UI (grant → creates user; dismiss → marks closed).

Three targeted auth security bugs are fixed opportunistically while `lib/auth.ts` and `/api/auth/login` are being touched. All other auth hardening (CSRF, login rate-limit, timing-safe compare) is deferred.

**Not in scope:** introducing Auth.js, adding a `proxy.ts`/`middleware.ts`, OAuth, self-service signup, self-service password reset, 2FA, email verification, account lockout, per-user analytics drilldown, extended_access role.

</domain>

<decisions>
## Implementation Decisions

### DB & Schema

- **D-01: Neon Postgres + Drizzle ORM.** Runtime driver is `@neondatabase/serverless` WebSocket `Pool`. Pin `@neondatabase/serverless@^0.10.4` (not 1.x — breaks `drizzle-orm/neon-http`). Pin `drizzle-orm@^0.45.2`, `drizzle-kit@^0.31.0`.
- **D-02: Two env vars.** `DATABASE_URL` (pooled, runtime) + `DATABASE_URL_UNPOOLED` (direct, migrations only).
- **D-03: UUID primary keys with `gen_random_uuid()` defaults** on all three new tables. Postgres 13+ has `gen_random_uuid()` built-in; Neon runs 16.
- **D-04: All timestamps are `timestamp with time zone` (timestamptz).** Stored UTC.
- **D-05: `events.type` is a Postgres enum** `event_type` with values matching current usage: `('login', 'logout', 'page_view', 'tab_click', 'feature_click', 'product_click')`. Start with the types already used by `trackEvent()` call sites; add via `ALTER TYPE ... ADD VALUE` later if needed.

**`users` schema:**
| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | `default gen_random_uuid()` |
| `email` | text | UNIQUE, lowercased at insert/lookup |
| `password_hash` | text | bcryptjs, cost 10 (unchanged from today) |
| `name` | text | nullable; optional display name (current users.json has it) |
| `is_admin` | boolean | NOT NULL default false |
| `created_at` | timestamptz | NOT NULL default now |
| `last_login_at` | timestamptz | nullable |

**`events` schema:**
| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | default gen_random_uuid() |
| `user_id` | uuid | nullable, FK `users(id)` ON DELETE SET NULL |
| `user_email` | text | nullable — denormalized snapshot; preserved even after a user is deleted (matches current analytics UI which shows email) |
| `type` | event_type | NOT NULL |
| `data` | jsonb | nullable; arbitrary event payload (current `trackEvent` passes `featureId`, `productId`, etc.) |
| `user_agent` | text | nullable — currently captured on login |
| `created_at` | timestamptz | NOT NULL default now; btree index |

**`access_requests` schema:**
| Column | Type | Notes |
|---|---|---|
| `id` | uuid PK | default gen_random_uuid() |
| `email` | text | NOT NULL — requester's email |
| `source` | text | nullable — e.g. the feature name or tab clicked |
| `message` | text | nullable — any free-form text from the request |
| `ip` | text | nullable — stored for rate-limit audit |
| `user_agent` | text | nullable |
| `status` | text | NOT NULL default `'pending'`; values `'pending' | 'granted' | 'dismissed'` (CHECK constraint; low enough cardinality we skip a Postgres enum for this one) |
| `granted_user_id` | uuid | nullable, FK `users(id)` ON DELETE SET NULL — if admin clicked "Grant" this links to the created user |
| `created_at` | timestamptz | NOT NULL default now |
| `resolved_at` | timestamptz | nullable — set when status flips to granted or dismissed |

### Role Model

- **D-06: `is_admin` boolean on users table.** No extended_access, no role enum. Seed: every row imported from `data/users.json` whose email ends with `@humbleteam.com` gets `is_admin = true`; everyone else gets `is_admin = false`. Current admins after migration: `sergey@humbleteam.com`, `admin@humbleteam.com`.
- **D-07: `@humbleteam.com` email-domain check is removed after seeding.** Runtime authorization uses ONLY `is_admin`. New admins are promoted through the admin panel, not by email domain.

### Users Migration

- **D-08: One-shot migration from `data/users.json` to Postgres.** A `scripts/migrate-users.ts` reads the JSON, inserts rows with `ON CONFLICT (email) DO NOTHING`, idempotent. Run once manually before the deploy.
- **D-09: `data/users.json` is deleted from the repo after migration.** Add to `.gitignore` for safety. `loadUsers()` in `lib/auth.ts` is replaced with a DB query.
- **D-10: `loadUsers()`, `saveUser()` (if they existed), and the `data/users.json` file are all removed in the same commit** that introduces the DB-backed user store. No dual-read phase — the migration step runs before the deploy, so post-deploy all code reads from the DB.

### Analytics Migration

- **D-11: Cut-over migration.** Existing Redis events are abandoned (not imported). Post-deploy, `logEvent()` writes to Postgres; `getEvents()` reads from Postgres. The Redis list is left alone for reference but no code reads it.
- **D-12: `lib/analytics.ts` is rewritten** to talk to Postgres instead of Upstash. Keeps the same `logEvent(type, email, data)` and `getEvents(opts)` surface so `lib/track.ts`, `/api/analytics/route.ts`, `/api/analytics/view/route.ts`, and `app/analytics/page.tsx` keep working with minimal edits.
- **D-13: `user_email` is captured on write** (denormalised). This matches current analytics-UI behaviour which displays `email`. If a user is deleted, historical events still show who did what.
- **D-14: 90-day rolling retention.** A Vercel Cron job at `/api/cron/retention` deletes events older than 90 days in batched `DELETE ... WHERE created_at < now() - interval '90 days' RETURNING 1 LIMIT 10000` loops. Authed via `CRON_SECRET` bearer. Scheduled daily in `vercel.json`.
- **D-15: `/api/analytics` POST requires an authenticated session.** Current behaviour logs anonymous writes as `email: 'anonymous'` — that goes away. Unauthed POST returns 401. Fixes the obvious DoS/spam vector while we're here.
- **D-16: Drop Upstash Redis dependency once cut over.** Remove `@upstash/redis` from `package.json`. Unset `KV_REST_API_URL` / `KV_REST_API_TOKEN` in Vercel env after deploy confirms stability.

### Access-Request Triage

- **D-17: New `access_requests` table backs a dedicated admin tab.** `POST /api/email` writes a row first, then fires the Resend email (existing flow unchanged). On Resend failure, the row still exists for triage — the UI handles that case.
- **D-18: Admin actions.**
  - **Grant**: opens a small form (prefill email from request; admin types a password or clicks "Generate" for a random 16-char password); on submit: creates user with that password, sets `access_requests.status='granted'`, `granted_user_id` FK, `resolved_at=now()`. Optional: emails the new user their credentials via Resend (stretch; see deferred).
  - **Dismiss**: sets `status='dismissed'`, `resolved_at=now()`. No email sent.
  - Both actions are admin-only, logged to `events` with a new type (see D-25).
- **D-19: Existing `/api/email` rate limit (5/min per IP) is preserved.** `access_requests` INSERT happens only if rate limit passes.

### Admin Panel UX

- **D-20: New top-level `/admin` route.** Server-rendered layout `app/admin/layout.tsx` with a shared admin backstop: redirects to `/` with the login modal if the session's user is not `is_admin`. All admin reads use Drizzle directly from server components; all admin writes go through `/api/admin/*` route handlers.
- **D-21: Three tabs:**
  - `/admin` → `/admin/users` (default)
  - `/admin/users` — table of all users (email, name, is_admin, created, last_login) with inline "make admin" / "remove admin" toggles, "Reset password" modal, double-confirm delete (type email to confirm)
  - `/admin/analytics` — the moved-over analytics dashboard
  - `/admin/requests` — access-request triage table with Grant / Dismiss actions
- **D-22: Safety rails (enforced in SQL, not just UI):**
  - Admin cannot delete their own user row.
  - Demoting or deleting cannot reduce the admin count below 1. Enforced via atomic conditional update / transaction.
  - Delete flow requires typing the user's email to confirm.
- **D-23: UI style matches existing app.** Plain CSS using the tokens in `app/globals.css`; no Tailwind, no shadcn, no new CSS framework. The admin tables are straightforward HTML tables. **Recharts** may be used inside `/admin/analytics` for the trend chart; nothing else uses Recharts.
- **D-24: `/analytics` is redirected to `/admin/analytics`.** Next.js redirect in `next.config.ts` (permanent `308`). Existing bookmarks keep working.

### Observability

- **D-25: New event types logged for admin actions:**
  - `admin_user_created`, `admin_user_deleted`, `admin_user_promoted`, `admin_user_demoted`, `admin_password_reset`, `admin_request_granted`, `admin_request_dismissed`.
  - Added to the `event_type` enum in the initial migration.
  - Logged by `/api/admin/*` route handlers with `data: { target_email, actor_email, ... }`.

### Auth Security Fixes (scope-limited)

These are fixed while we're already editing `lib/auth.ts` and `/api/auth/login`. Everything else in CONCERNS.md stays deferred.

- **D-26: `AUTH_SECRET` is required in production.** `lib/env.ts` zod schema marks it required; removes the hardcoded fallback from `lib/auth.ts:4`. In dev, the env validator either uses a documented dev default or instructs the user to set it in `.env.local`.
- **D-27: Session token age is enforced in `parseSessionToken()`.** Tokens older than `MAX_AGE` (7 days — unchanged) are rejected. Implementation: parse the timestamp field already present in the token (`email:timestamp:hmac`), compare to `Date.now()`, reject if exceeded.
- **D-28: `/api/analytics` POST requires auth** (duplicate of D-15 for completeness). Closes the DoS/spam vector on event ingestion.

**Explicitly deferred:** CSRF on `/api/auth/login`, rate limit on `/api/auth/login`, timing-safe compare for missing-user login attempts, SameSite=Strict cookie flag. These are called out in a follow-up note in the phase's README so they aren't forgotten.

### Infrastructure

- **D-29: Env validation via zod in `lib/env.ts`.** Required (prod): `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `AUTH_SECRET`, `RESEND_API_KEY`, `CRON_SECRET`. Keep `KV_REST_API_URL` / `KV_REST_API_TOKEN` as *optional* during the transition (dropped from the schema in the cleanup commit after cut-over).
- **D-30: Migrations live at `drizzle/` (default).** Hand-rolled runner at `scripts/migrate.ts` using `drizzle-orm/neon-serverless/migrator` against `DATABASE_URL_UNPOOLED`. `drizzle-kit` in devDeps only.
- **D-31: `tsx` as the TypeScript runner** for `scripts/migrate.ts`, `scripts/migrate-users.ts`, and any future db scripts.
- **D-32: Stay on npm** (matches existing `package-lock.json`). Add new scripts: `db:generate`, `db:migrate`, `db:migrate-users`.
- **D-33: `.env.example` gets the new vars** (`DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `CRON_SECRET`). `AUTH_SECRET` and `RESEND_API_KEY` are already used — document them if not yet in `.env.example`.
- **D-34: Vercel Cron entry** added to `vercel.json` for `/api/cron/retention` (daily).
- **D-35: Keep using Vitest.** Add tests for: the last-admin guardrail (SQL-level), env validator (fails fast on missing vars), session-age enforcement in `parseSessionToken`. No test infrastructure change — Vitest already wired.

### Claude's Discretion

- Exact copy on the admin-panel tables and buttons.
- Exact UI layout of `/admin/users` (single table vs split "admins / members" sections).
- `drizzle.config.ts` shape and whether to add `db:studio`.
- Random-password generation strategy for the "Grant with generated password" button.
- Whether `scripts/migrate-users.ts` reads `data/users.json` from disk or expects paths via argv.
- File organisation inside `lib/db/` (single `schema.ts` is fine for three tables).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents (researcher, planner, executor) MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — current product context (v1 Validated, v2–v11 Active). This phase doesn't touch v2–v11; it's infra.
- `.planning/ROADMAP.md` — 6 flow-expansion phases, untouched.

### Prior infra precedent
- `.planning/phases/infra-ci-cd/PLAN.md` — pattern for an out-of-band infra phase (PLAN.md + VERIFICATION.md, no roadmap entry).
- `.planning/phases/infra-ci-cd/VERIFICATION.md` — VERIFICATION.md structure (goal-backward check table).

### Existing codebase (authoritative for "what's there today")
- `.planning/codebase/STACK.md` — `next-auth` is NOT installed; auth is custom. Lists current deps to reuse / drop.
- `.planning/codebase/INTEGRATIONS.md` — Upstash Redis + Resend + Vercel Analytics + GitHub Actions CI wiring.
- `.planning/codebase/ARCHITECTURE.md` — current rendering model, per-route auth pattern (NO middleware/proxy), data flow for auth + analytics.
- `.planning/codebase/STRUCTURE.md` — directory layout this phase must fit into.
- `.planning/codebase/CONVENTIONS.md` — code-style expectations for new TS files.
- `.planning/codebase/CONCERNS.md` — authoritative source for the auth + analytics security issues this phase does / doesn't address.
- `.planning/codebase/TESTING.md` — Vitest already wired; add new tests beside `lib/scoring.test.ts`.

### Existing code this phase replaces or edits
- `lib/auth.ts` — password helpers (keep), session helpers (keep, add age validation in `parseSessionToken`), `loadUsers()` + `data/users.json` (remove; replace with DB query).
- `lib/analytics.ts` — rewritten. Same exports: `logEvent`, `getEvents`, `AnalyticsEvent`.
- `lib/track.ts` — unchanged (client-side fire-and-forget; server contract stays the same).
- `app/api/auth/login/route.ts`, `app/api/auth/logout/route.ts`, `app/api/auth/me/route.ts` — edits: users lookup goes through DB.
- `app/api/analytics/route.ts` — require auth; write to Postgres via `logEvent`.
- `app/api/analytics/view/route.ts` — replace `@humbleteam.com` domain check with `is_admin` check; read from Postgres via `getEvents`.
- `app/api/email/route.ts` — insert `access_requests` row before sending Resend email.
- `app/analytics/page.tsx` — relocate under `/admin/analytics`; logic unchanged.
- `next.config.ts` — add redirect `/analytics → /admin/analytics`.
- `vercel.json` — add cron entry for `/api/cron/retention`.
- `package.json` — add new deps + scripts; drop `@upstash/redis` after cut-over.
- `data/users.json` — deleted from repo + from `lib/auth.ts` reads.

### External (web)
- Drizzle + Neon: <https://orm.drizzle.team/docs/connect-neon>
- Drizzle migrations: <https://orm.drizzle.team/docs/migrations>
- Neon serverless driver: <https://neon.com/docs/serverless/serverless-driver>
- Vercel Cron: <https://vercel.com/docs/cron-jobs>
- Recharts (React 19 compatible v3+): <https://recharts.org>

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`lib/auth.ts`** — password hashing, session signing, cookie helpers are fine. Keep everything except `loadUsers()` and the default secret fallback. Add an age check in `parseSessionToken`.
- **`lib/track.ts`** — client-side `trackEvent` is correct; don't change.
- **`app/analytics/page.tsx`** — UI is fine; relocate under `/admin/analytics` and re-point fetch URL (`/api/analytics/view` stays the same).
- **`app/api/email/route.ts`** — keep the Resend flow; just add a DB insert for triage.
- **Vitest infrastructure** — already wired, including CI. Extend it.
- **`app/globals.css`** — theme tokens and CSS custom properties to reuse for admin UI.

### Established Patterns
- **No middleware.** Per-route auth via `getSessionFromCookie(req.headers.get('cookie'))` in API handlers. `/admin/*` layout does the same thing server-side for pages.
- **Server Components for static/data-driven pages**, Client Components for interactive ones. Admin layout + list pages are Server Components; admin action buttons are client islands.
- **TypeScript strict mode**, path alias `@/*`, plain CSS only.
- **Hand-written, minimal dependencies** — match this aesthetic when adding new code.

### Integration Points
- `package.json` — new deps: `@neondatabase/serverless`, `drizzle-orm`, `zod`. Remove `@upstash/redis` at cut-over. DevDeps: `drizzle-kit`, `tsx`.
- `.env.local` / `.env.example` — new vars documented in D-33.
- `vercel.json` — new `crons` entry (see D-34).
- `next.config.ts` — new `redirects()` entry (D-24).

</code_context>

<specifics>
## Specific Ideas

- Write a short `README.md` in `.planning/phases/infra-users-admin/` that lists the deferred auth-hardening follow-ups (CSRF, login rate-limit, timing-safe compare) so they're tracked.
- The `admin@humbleteam.com` seed user should stay — it's the break-glass account.
- When deleting a user, also delete any pending `access_requests` linked to their email (or leave them, since `granted_user_id` is nullable). Leave them — audit trail.
- The retention cron should log its work to `events` as `type: 'retention_run'` with `data: { deleted_count, oldest_kept, run_duration_ms }`. Useful audit signal. (Requires adding that to the enum.)

</specifics>

<deferred>
## Deferred Ideas

### Auth hardening — explicitly out of scope for this phase
- CSRF protection on `/api/auth/login` — Origin/Referer check or CSRF token
- Rate-limit on `/api/auth/login` (currently only `/api/email` is rate-limited)
- Timing-safe compare on missing-user login paths (run bcrypt against a dummy hash)
- SameSite=Strict cookie flag evaluation
- Account lockout after N failures

### Admin panel v2
- Disabled user state (soft-disable without delete)
- Per-user analytics drilldown (click a user → see their full activity trail)
- Admin-action audit trail in a dedicated `admin_actions` table (today we log to `events`)
- Bulk actions (disable N users, export CSV)

### Analytics v2
- Per-feature trend charts (currently aggregate only)
- Date-range picker (currently 7/30/90 presets only — per the related milestone; this phase doesn't add the dashboard enhancement)
- Export to CSV

### DevEx
- `npm run db:studio` alias for `drizzle-kit studio`
- `db:seed:dev` with fake test users for local
- CI migration step (GitHub Action or Vercel preview hook)

### Infrastructure
- Drop `@upstash/redis` dependency from `package.json` (the cleanup commit after cut-over — could also be part of this phase; flagged for planner)

</deferred>

---

*Phase: infra-users-admin (out-of-band)*
*Context gathered: 2026-04-17*
