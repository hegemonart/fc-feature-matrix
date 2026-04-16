# Infra Phase — Users, Admin Panel & Analytics Migration

> **Status:** Out-of-band infrastructure work, parallel to the v2–v11 product roadmap. Listed in ROADMAP.md §"Out-of-Band Infrastructure" alongside the completed `infra-ci-cd` phase. Does not gate any numbered phase.

## Goal

Users move from `data/users.json` (committed to git, redeploy required to change) to Neon Postgres. A new `/admin` panel lets any admin create, promote, reset, and delete users — plus triage access requests and view analytics — at runtime. Analytics events migrate from Upstash Redis to Postgres with 90-day rolling retention. Three load-bearing auth security bugs are fixed while the auth code is being edited.

## Why now

- `data/users.json` adding a user requires a git commit + Vercel redeploy. With 5 users today and demand from three external clubs (Brentford, Chelsea) this friction compounds.
- `lib/auth.ts:4` has a hardcoded fallback `'fc-benchmark-dev-secret-change-in-prod'` — in production, any missing `AUTH_SECRET` silently signs session tokens with a publicly visible secret.
- `parseSessionToken()` never checks the token's age — a 7-day cookie is valid forever.
- `/api/analytics` POST accepts anonymous events — a trivial DoS / pollution vector.
- Upstash Redis list is capped at 10k events (LTRIM) with no retention policy or time-based filter; analytics UI can't ask "what happened in the last 30 days?" accurately.
- The flow-expansion phases (1–6) will add more capture scripts and more data — they benefit from a stable admin + analytics foundation underneath.

## Scope

See [`CONTEXT.md`](CONTEXT.md) for the 35 locked decisions (D-01..D-35) that drive this plan. See [`RESEARCH.md`](RESEARCH.md) for version-pin verification and code skeletons.

| Layer | What ships |
|---|---|
| DB | Neon Postgres (pooled + unpooled URLs); Drizzle schema for `users`, `events`, `access_requests`; `event_type` enum; committed SQL migration in `drizzle/` |
| Runtime DB client | `lib/db/index.ts` (WebSocket `Pool`), `lib/db/schema.ts` (single file, three tables) |
| Env | `lib/env.ts` (zod-validated, typed), `.env.example` with `DATABASE_URL`, `DATABASE_URL_UNPOOLED`, `AUTH_SECRET`, `RESEND_API_KEY`, `CRON_SECRET` |
| Scripts | `scripts/migrate.ts` (hand-rolled runner with `-pooler` guard), `scripts/migrate-users.ts` (one-shot users.json → DB, idempotent) |
| Auth | `lib/auth.ts` without default-secret fallback, with token-age validation; `app/api/auth/{login,logout,me}/route.ts` DB-backed |
| Analytics | `lib/analytics.ts` rewritten against Postgres (same exports); `/api/analytics` POST requires auth; `/api/analytics/view` uses `is_admin` check not `@humbleteam.com` |
| Admin panel | `/admin/layout.tsx` (server admin backstop), `/admin/users`, `/admin/analytics`, `/admin/requests` |
| Admin writes | `/api/admin/users/route.ts` (+ `[id]/route.ts`), `/api/admin/requests/route.ts` — atomic SQL guardrails for last-admin + self-delete |
| Access requests | `access_requests` table; `/api/email/route.ts` inserts row before Resend call; grant/dismiss via admin API |
| Redirect | `/analytics` → `/admin/analytics` (308) via `next.config.ts` |
| Retention | `/api/cron/retention/route.ts` (Node runtime, `CRON_SECRET` bearer, batched `DELETE ... LIMIT 10000`); `vercel.json` daily cron |
| Cleanup | Delete `data/users.json`, uninstall `@upstash/redis`, drop unused env keys |
| Tests | Vitest: last-admin guardrail (SQL), env validator, `parseSessionToken` age check |

## Commit groups (in execution order)

Each group is one or more commits. Groups 1–3 are strictly sequential. Groups 4–7 parallelise in any order once 3 lands. Group 8 (tests + Redis uninstall) goes last.

---

### Group 1 — Dependencies & configuration (prep)

No runtime code yet — only installs deps and lays down the config skeleton so subsequent groups compile.

| File | Purpose |
|---|---|
| `package.json` | **Add deps:** `@neondatabase/serverless@^0.10.4`, `drizzle-orm@^0.45.2`, `zod@^3.24`. **Add devDeps:** `drizzle-kit@^0.31.0`, `tsx@^4.19`. **Add scripts:** `db:generate` = `drizzle-kit generate`, `db:migrate` = `tsx scripts/migrate.ts`, `db:migrate-users` = `tsx scripts/migrate-users.ts`. Do NOT uninstall `@upstash/redis` yet (still used by existing `lib/analytics.ts`). |
| `drizzle.config.ts` | New. `schema: './lib/db/schema.ts'`, `out: './drizzle'`, `dialect: 'postgresql'`, `dbCredentials: { url: process.env.DATABASE_URL_UNPOOLED! }`, `verbose: true`, `strict: true`. |
| `.env.example` | Commit (or update if exists). Add `DATABASE_URL=`, `DATABASE_URL_UNPOOLED=`, `AUTH_SECRET=`, `RESEND_API_KEY=`, `CRON_SECRET=`. Each with a short comment. |
| `.gitignore` | Confirm `.env.local` + `.env*.local` already excluded (Next.js default — verify, don't duplicate). |
| `lib/env.ts` | New. Zod schema validating all required env vars. In production, missing `AUTH_SECRET` / `DATABASE_URL` / `CRON_SECRET` throws. In dev, `AUTH_SECRET` can fall back to a dev default documented in `.env.example`. Export `env` object. |
| `tsconfig.json` | Verify `"include"` covers `scripts/**/*` (it may already via default). |

**Pre-flight (operator):** Create a Neon project + dev branch, put `DATABASE_URL` (pooled, ends `-pooler`) and `DATABASE_URL_UNPOOLED` (direct, no `-pooler`) into `.env.local`.

---

### Group 2 — DB client + schema + first migration

Depends on Group 1 (deps installed).

| File | Purpose |
|---|---|
| `lib/db/index.ts` | New. Imports `Pool, neonConfig` from `@neondatabase/serverless`, `drizzle` from `drizzle-orm/neon-serverless`, `ws` from `ws`, schema from `./schema`. Sets `neonConfig.webSocketConstructor = ws`. Exports singleton `pool` and `db = drizzle(pool, { schema })`. See `RESEARCH.md §1` for the canonical snippet. |
| `lib/db/schema.ts` | New. Single file with three tables and the `event_type` enum. Exact columns per CONTEXT.md §D-09, §D-10, §D-18. All PKs `uuid('id').primaryKey().defaultRandom()`. All timestamps `timestamp({ withTimezone: true }).defaultNow().notNull()`. Index on `events.created_at`. FKs: `events.user_id` + `access_requests.granted_user_id` both `.references(() => users.id, { onDelete: 'set null' })`. |
| `drizzle/0000_initial.sql` | Generated by `npm run db:generate`. Reviewed + committed verbatim. Must contain: `CREATE TYPE event_type ...`, `CREATE TABLE users ...`, `CREATE TABLE events ...`, `CREATE TABLE access_requests ...`, `CREATE INDEX events_created_at_idx ...`, CHECK constraint on `access_requests.status` for `('pending','granted','dismissed')`. |
| `drizzle/meta/_journal.json` | Auto-generated by drizzle-kit. Commit. |

**Operator runs once:** `npm run db:migrate` against the Neon dev branch — confirms migration applies cleanly.

---

### Group 3 — Migration scripts

Depends on Group 2.

| File | Purpose |
|---|---|
| `scripts/migrate.ts` | New. Per `RESEARCH.md §2`. Reads `DATABASE_URL_UNPOOLED`, **rejects** URLs containing `-pooler` with an actionable error ("Migrations require the direct connection; use the -pooler-less URL"). Imports `migrate` from `drizzle-orm/neon-serverless/migrator`. Runs `migrate(db, { migrationsFolder: './drizzle' })`. Exits 0 on success, 1 on any error, always closes the pool. |
| `scripts/migrate-users.ts` | New. One-shot. Reads `data/users.json`, for each entry: `db.insert(users).values({ email: email.toLowerCase(), passwordHash, name, isAdmin: email.endsWith('@humbleteam.com') }).onConflictDoNothing({ target: users.email })`. Logs per-row whether inserted or skipped. Idempotent — safe to re-run. |

**Operator runs once:** `npm run db:migrate-users` — confirms 5 users land in DB, 2 admins (`sergey@`, `admin@humbleteam.com`).

---

### Group 4 — Auth refactor (parallel with 5, 6, 7 once 3 lands)

| File | Purpose |
|---|---|
| `lib/auth.ts` | Edit: (1) remove `|| 'fc-benchmark-dev-secret-change-in-prod'` fallback — `SECRET` now comes from `env.AUTH_SECRET`; (2) in `parseSessionToken`, extract the timestamp (already encoded as `email:timestamp:hmac`), reject if `Date.now() - tokenTimestamp > MAX_AGE * 1000`; (3) delete `loadUsers`, `getUsersFilePath`, `StoredUser` interface, and the `require('fs')` / `require('path')` calls. Replace with a new helper `getUserByEmail(email: string): Promise<User | null>` that selects from `users` via Drizzle. |
| `app/api/auth/login/route.ts` | Edit: `loadUsers()` → `getUserByEmail(email.toLowerCase())`. On successful login: `UPDATE users SET last_login_at = now() WHERE id = ?` before returning. The `logEvent('login', ...)` call stays (the analytics rewrite in Group 5 keeps the signature). |
| `app/api/auth/me/route.ts` | Edit: after verifying the cookie, look up the user's current `is_admin` via DB (cheap query by email). Return `{ authenticated, email, isAdmin }` so the client doesn't have to infer from email domain. |
| `app/api/auth/logout/route.ts` | No change. |
| `data/users.json` | **Delete** in the same commit. Add `data/users.json` to `.gitignore` for safety. Pre-flight: confirm `npm run db:migrate-users` ran and DB has all 5 users — the deletion is irreversible on master. |
| `app/page.tsx` (client) | Small edit: wherever the client code checks admin via `email.endsWith('@humbleteam.com')`, switch to `user.isAdmin` from the `/api/auth/me` response. |

---

### Group 5 — Analytics rewrite (parallel with 4, 6, 7)

| File | Purpose |
|---|---|
| `lib/analytics.ts` | **Rewritten end-to-end.** Same exports (`logEvent`, `getEvents`, `AnalyticsEvent`). `logEvent(type, email, data)` does `db.insert(events).values({ userEmail: email, type, data, userAgent: data.userAgent ?? null })` where `type` is cast to the enum. `getEvents({ limit, type, email })` runs a single SELECT with optional WHERE clauses, ordered by `created_at DESC`. Drop all Upstash calls; drop the `lib/analytics.ts:4` MAX_EVENTS constant (retention now handled by cron). Keep the client-console fallback for dev only as a `console.log` when `env.DATABASE_URL` is not set. |
| `app/api/analytics/route.ts` | Edit: after reading the cookie, if `getSessionFromCookie(...)` returns null, **return 401** (today it logs `email: 'anonymous'`). Otherwise call `logEvent(type, session.email, data)`. |
| `app/api/analytics/view/route.ts` | Edit: replace `email.endsWith('@humbleteam.com')` check with `user.isAdmin` (look up via `getUserByEmail` from session). Call `getEvents(opts)` — signature unchanged. |
| `lib/track.ts` | **No change.** Client contract is stable. |

---

### Group 6 — Admin panel: Users tab (parallel with 4, 5, 7)

| File | Purpose |
|---|---|
| `app/admin/layout.tsx` | New. Server Component. Reads session via `getSessionFromCookie`; looks up user's `is_admin`; if not admin (or unauth), `redirect('/')`. Renders a shared admin chrome: nav with links to `/admin/users`, `/admin/analytics`, `/admin/requests`, and a sign-out button. Uses existing CSS tokens from `app/globals.css`. |
| `app/admin/page.tsx` | New. Server component that `redirect('/admin/users')`. |
| `app/admin/users/page.tsx` | New. Server Component. Fetches `db.select().from(users).orderBy(users.createdAt)` and renders a table: email, name, is_admin, created, last_login, actions. Actions column is a client island. |
| `app/admin/users/_actions.tsx` | New. Client Component (`'use client'`). Renders the admin-action buttons inline per row: **Toggle admin**, **Reset password** (opens a small modal), **Delete** (opens modal that requires typing the user's email). **Add user** form at the top of the list (email + password or "Generate"). All actions POST/PATCH/DELETE to `/api/admin/users/...`. |
| `app/api/admin/users/route.ts` | New. `POST` creates a user (validate email + password length ≥ 12 via zod; hash with bcryptjs cost 10; INSERT with conflict check on email); `GET` optional to return the list if we want a client-side refresh. Requires `session.isAdmin`. On success, call `logEvent('admin_user_created', session.email, { target_email })`. |
| `app/api/admin/users/[id]/route.ts` | New. `PATCH` toggles `is_admin` (see guardrail below) and/or resets password. `DELETE` deletes a user (see guardrails). Every write is atomic SQL: the last-admin guardrail uses a single conditional update — e.g. `UPDATE users SET is_admin = false WHERE id = ? AND (SELECT count(*) FROM users WHERE is_admin = true) > 1`. If `rowCount === 0`, return 409 with message "Cannot demote the last admin." Similarly for delete. Self-delete refused if `id === session.userId`. |
| `app/page.tsx` | Small edit: add an "Admin" link in the header for users where `isAdmin === true`. |

---

### Group 7 — Admin panel: Analytics + Requests + redirects (parallel with 4, 5, 6)

| File | Purpose |
|---|---|
| `app/admin/analytics/page.tsx` | **Move** `app/analytics/page.tsx` here. Logic unchanged. Update the fetch URL (it's the same `/api/analytics/view`). |
| `app/analytics/page.tsx` | **Delete.** |
| `next.config.ts` | Add `async redirects()` with one entry: `{ source: '/analytics', destination: '/admin/analytics', permanent: true }` (308). |
| `app/admin/requests/page.tsx` | New. Server Component. Fetches `db.select().from(accessRequests).orderBy(accessRequests.createdAt.desc())`. Renders table: email, source, status, created, resolved, actions. Client island for Grant / Dismiss. |
| `app/admin/requests/_actions.tsx` | New. Client Component. Grant opens modal (prefill email, admin types password or clicks "Generate" random 16-char), POSTs to `/api/admin/requests/[id]`. Dismiss POSTs directly with confirm. |
| `app/api/admin/requests/[id]/route.ts` | New. `POST` with `{ action: 'grant', password?: string }` or `{ action: 'dismiss' }`. Grant: inside a transaction: create user (hash password), update `access_requests` row (`status='granted'`, `granted_user_id=new.id`, `resolved_at=now()`). Logs `admin_request_granted` event. Dismiss: `UPDATE access_requests SET status='dismissed', resolved_at=now()`. Logs `admin_request_dismissed`. Requires `session.isAdmin`. |
| `app/api/email/route.ts` | Edit: before calling `resend.emails.send(...)`, insert a row into `access_requests` with email, source, ip, user_agent, status='pending'. Keep the existing rate limit (`5/min per IP`). If Resend fails, the row is still there for triage — that's the intent. |

---

### Group 8 — Retention cron (parallel with 4, 5, 6, 7)

| File | Purpose |
|---|---|
| `app/api/cron/retention/route.ts` | New. Per `RESEARCH.md §3`. `export const runtime = 'nodejs'`. `GET` (Vercel Cron uses GET by default). Check `Authorization` header matches `Bearer ${env.CRON_SECRET}` exactly (constant-time compare acceptable but not strictly required — the secret is uniform). Loop: `DELETE FROM events WHERE created_at < now() - interval '90 days' RETURNING 1 LIMIT 10000` until `rowCount === 0` or a 15-second wall-clock budget elapses. Log a single summary event `{ type: 'retention_run', data: { deleted_count, duration_ms } }` via `logEvent(null, null, ...)` — means extending the `event_type` enum. |
| `lib/db/schema.ts` | Edit: extend `event_type` enum with `'retention_run'`. Generate a follow-up migration `drizzle/0001_retention_event_type.sql` using `ALTER TYPE event_type ADD VALUE 'retention_run'` (drizzle-kit generates this; verify the SQL before committing). |
| `vercel.json` | Edit: add `"crons": [{ "path": "/api/cron/retention", "schedule": "17 3 * * *" }]` (once a day at 03:17 UTC — off-peak, deterministic). |
| `lib/env.ts` | Edit: add `CRON_SECRET` to the zod schema (required in prod). |

**Operator action post-deploy:** Set `CRON_SECRET` in Vercel envs (all 3 environments — Production, Preview, Development if used).

---

### Group 9 — Tests + cleanup (after 4–8 complete)

| File | Purpose |
|---|---|
| `lib/auth.test.ts` | New. Vitest. Tests `parseSessionToken` rejects tokens older than `MAX_AGE`, accepts fresh tokens, rejects tampered HMAC. Uses frozen time via `vi.useFakeTimers`. No DB needed. |
| `lib/env.test.ts` | New. Tests the zod schema: missing `AUTH_SECRET` throws in prod; missing `DATABASE_URL` throws always; valid envs pass. |
| `tests/admin-guardrails.test.ts` | New. Vitest. Requires a test DB. Inserts two admins; demotes one; the conditional update returns `rowCount=1`. Demote the other; returns `rowCount=0`. Same for delete. Same for `id=self`. Uses transactions + rollback so test is self-contained. Gated on `DATABASE_URL` env — skip with a warning if not set (so CI without a DB still passes the other tests). |
| `package.json` | **Uninstall** `@upstash/redis` (`npm uninstall @upstash/redis`). Verify no remaining imports with `grep -r "@upstash/redis" app lib scripts`. |
| `lib/analytics.ts` | Drop any residual Upstash import (should already be gone after Group 5). |
| CI | Expect `.github/workflows/ci.yml` to pass without edits: lint + typecheck + test (new tests run) + build. |

**Operator action post-deploy:** After a few days of observing the app healthy on Postgres, remove the `KV_REST_API_URL` and `KV_REST_API_TOKEN` env vars from Vercel to eliminate drift.

---

## Out of scope (deferred — deliberately)

All listed in `CONTEXT.md §deferred`:
- CSRF on `/api/auth/login` (Origin/Referer check or CSRF token)
- Rate limit on `/api/auth/login` (only `/api/email` is rate-limited today)
- Timing-safe compare on missing-user login paths (run bcrypt against a dummy hash)
- SameSite=Strict cookie flag evaluation
- Account lockout after N failures
- Disabled user state (soft-disable)
- Per-user analytics drilldown
- Dedicated `admin_actions` table
- Bulk admin actions (disable N users, export CSV)
- Per-feature trend charts, date-range picker, CSV export (analytics v2)
- `npm run db:studio`, dev seed scripts, CI migration step
- Recharts integration — not needed by this phase's success criteria; admin-analytics keeps the existing chart-less table UI

Each is a potential follow-up in its own right.

## Reuse

- `lib/auth.ts` password + session + cookie helpers (kept as-is; only `loadUsers` and the default-secret fallback removed; token-age check added)
- `lib/track.ts` (no changes)
- `app/analytics/page.tsx` UI (relocated)
- `app/api/email/route.ts` rate limiter (kept)
- `app/globals.css` theme tokens — admin panel uses them directly, no new CSS framework
- Vitest + `npm test` — already wired by `infra-ci-cd`
- `eslint.config.mjs` — no changes needed; new files obey existing rules

## Risks

| Risk | Mitigation |
|---|---|
| `DATABASE_URL_UNPOOLED` accidentally points at the pooled hostname → migrations break in subtle ways (prepared-statement errors, broken advisory locks) | `scripts/migrate.ts` refuses any URL containing `-pooler` with an actionable error (`RESEARCH.md §2`) |
| Neon WebSocket driver not given a `ws` constructor → runtime error at first query on Vercel | `lib/db/index.ts` sets `neonConfig.webSocketConstructor = ws` unconditionally |
| `data/users.json` deleted before migration ran → login breaks for everyone | Pre-flight checklist in Group 3 says "confirm DB has all 5 users" before deletion. Deletion is its own commit after `npm run db:migrate-users` is verified. |
| Extending `event_type` enum at runtime (Group 8 adds `'retention_run'`) → `ALTER TYPE ... ADD VALUE` cannot run inside a transaction in some Postgres clients | Generated via `drizzle-kit generate` — outputs the right SQL; the migration runner runs it outside a transaction (default) |
| Vercel Cron runs with no `CRON_SECRET` set → silent 401 and no retention ever happens | `lib/env.ts` marks `CRON_SECRET` required in production — fails fast if missing |
| Admin guardrail has a TOCTOU race (parallel demote requests could leave zero admins) | Single-statement conditional `UPDATE ... WHERE ... AND (SELECT count(*) FROM users WHERE is_admin) > 1`. Test in Group 9 verifies. |
| Client-side admin check (`user.isAdmin` from `/api/auth/me`) can be spoofed in devtools | All admin enforcement is server-side (`/admin/layout.tsx` + `/api/admin/*` routes). Client check is purely to show/hide the link. |
| `/analytics` 308 redirect caches aggressively and makes reverting painful | 308 is correct (method-preserving, permanent) — we're sure. If we ever want `/analytics` back, we'd just remove the redirect. |
| Build fails because `@upstash/redis` is uninstalled before all analytics imports are gone | Uninstall is Group 9 (last). A `grep -r '@upstash/redis' app lib scripts` in the uninstall commit catches any leftover. |

## Verification checklist (for the VERIFICATION.md phase report after shipping)

Must all be TRUE before this phase is marked complete:

1. `npm run db:migrate` applies cleanly against a fresh Neon branch; `users`, `events`, `access_requests` tables exist; `event_type` enum has six values (including `retention_run`); `events.created_at` has a btree index
2. `npm run db:migrate-users` is idempotent: runs twice, second run is a no-op
3. `data/users.json` does not exist at repo root; `git log --all --full-history -- data/users.json` shows the delete commit
4. `/` works as before (matrix renders, auth modal appears for unauthed)
5. `/admin` is 302 for unauth users, shown for `is_admin = true`
6. `/admin/users` lets an admin: create a user with a min-12-char password; toggle `is_admin`; reset a password; delete with email confirmation
7. Attempting to demote the only remaining admin returns 409 with message "Cannot demote the last admin"
8. Attempting to delete your own account returns 409 with message "Cannot delete your own account"
9. `/admin/requests` shows any access request created via the "Request access" UX; Grant creates a user and flips the row to `granted`; Dismiss flips to `dismissed`
10. `/admin/analytics` shows events; `/analytics` redirects to it with 308
11. `curl -X POST /api/analytics` (no cookie) returns 401
12. `curl /api/cron/retention` (no bearer) returns 401; with `Authorization: Bearer $CRON_SECRET` runs and returns `{ ok: true, deleted_count: N }`
13. `lib/auth.ts` has no `'fc-benchmark-dev-secret-change-in-prod'` substring
14. `parseSessionToken` returns null for a token whose timestamp is `Date.now() - 8*24*60*60*1000`
15. `npm test` passes — all three new test files green; existing `lib/scoring.test.ts` still green
16. `npm run lint`, `npm run typecheck`, `npm run build` all exit 0
17. `grep -r '@upstash/redis' package.json app lib scripts` returns no matches
18. CI pipeline green on the phase PR
19. Vercel preview deployment loads the app, login works against the Neon dev branch, analytics dashboard renders at least one event after a round-trip

## Follow-ups (not in this phase)

- Build the deferred auth hardening set as its own `infra-auth-hardening` phase (CSRF, login rate-limit, timing-safe compare, SameSite=Strict)
- Per-user analytics drilldown (flagged in CONTEXT.md §deferred)
- Recharts-based trend chart for `/admin/analytics` (currently keeping the existing table UI; chart is a v2 polish)
- Drop `KV_REST_API_URL` / `KV_REST_API_TOKEN` env vars in Vercel a week after deploy stability
- Consider moving `access_requests` IP storage behind GDPR data-retention review if it ever becomes a real concern (audit trail only, not used for decisioning)
