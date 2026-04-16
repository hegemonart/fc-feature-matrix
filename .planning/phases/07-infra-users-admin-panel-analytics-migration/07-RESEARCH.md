# Phase infra-users-admin — Research (Targeted Re-Verification)

**Researched:** 2026-04-16
**Domain:** Neon Postgres + Drizzle wiring, Vercel Cron, Upstash removal, bcryptjs currency, UUID defaults
**Confidence:** HIGH overall (all six items verified against npm / official docs within the last 30 days)

## Scope

This is a **targeted re-verification**, not a full domain survey. The six items below are the ones most likely to have drifted since training cutoff. All other decisions (custom auth stays; no Auth.js; no middleware/proxy.ts; JWT sessions unchanged) are locked in CONTEXT.md and NOT re-researched here.

CONTEXT.md decisions referenced: D-01 (driver pins), D-02 (two env vars), D-14 (Vercel Cron), D-16 (drop Upstash), D-30 (migrator entry point), D-34 (vercel.json cron entry), plus schema decisions D-03 (UUIDs) and role model pins.

---

## User Constraints (from CONTEXT.md)

### Locked Decisions (relevant to this research)
- **D-01** `@neondatabase/serverless@^0.10.4` WebSocket `Pool`; `drizzle-orm@^0.45.2`; `drizzle-kit@^0.31.0`. Do NOT use `@neondatabase/serverless@1.x` with `drizzle-orm/neon-http`.
- **D-02** `DATABASE_URL` (pooled) for runtime; `DATABASE_URL_UNPOOLED` (direct) for migrations.
- **D-03** UUID PKs with `gen_random_uuid()` defaults; Neon runs Postgres 16.
- **D-14** Daily retention cron at `/api/cron/retention`; auth via `CRON_SECRET` bearer.
- **D-16** Drop `@upstash/redis` from `package.json` after cut-over.
- **D-30** Migrations folder at `drizzle/` (default); runner is hand-rolled `scripts/migrate.ts` using `drizzle-orm/neon-serverless/migrator` against `DATABASE_URL_UNPOOLED`.
- **D-34** Vercel Cron entry added to `vercel.json`.

### Claude's Discretion (relevant)
- `drizzle.config.ts` shape.
- Whether `scripts/migrate-users.ts` takes argv paths.

### Deferred (OUT OF SCOPE for this research)
- All auth hardening beyond D-26/27/28 (CSRF, login rate-limit, timing-safe compare, SameSite=Strict).
- `db:studio` alias and dev seed scripts.

---

## Item 1 — Drizzle + Neon serverless WebSocket `Pool` driver

**Verdict: D-01 pins are correct. Use `drizzle-orm/neon-serverless` with `Pool` from `@neondatabase/serverless@^0.10.x`. Do NOT bump to `@neondatabase/serverless@1.x`.**

### Verified versions (npm registry, April 2026)
| Package | Pin | Status |
|---|---|---|
| `@neondatabase/serverless` | `^0.10.4` | `[VERIFIED]` latest 0.x stable; 1.x exists but breaks `drizzle-orm/neon-http` (issue #5208, filed 2026-01-04, still being tracked). We use `neon-serverless` not `neon-http`, but staying on 0.10.x is the conservative choice CONTEXT.md already made, and avoids ABI surprises. `[CITED: github.com/drizzle-team/drizzle-orm/issues/5208]` |
| `drizzle-orm` | `^0.45.2` | `[VERIFIED: npmjs.com]` Current stable; `1.0.0-beta.x` exists on the `beta` tag, not recommended for production. |
| `drizzle-kit` | `^0.31.0` | `[VERIFIED: npmjs.com/Snyk]` Latest 0.x stable is `0.31.9`. `^0.31.0` resolves to `0.31.9` today. `1.0.0-beta.9` exists behind `beta` tag; do not use. |

### Import paths (confirmed correct for `neon-serverless` WebSocket Pool)

```typescript
// lib/db/index.ts
import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from 'ws';
import * as schema from './schema';

// Required in Node.js (Vercel serverless lambdas); the global WebSocket is
// not present in Node < 22 by default, and Vercel runs Node 20.
neonConfig.webSocketConstructor = ws;

const pool = new Pool({ connectionString: process.env.DATABASE_URL! });
export const db = drizzle(pool, { schema });
```

`[VERIFIED: orm.drizzle.team/docs/connect-neon]` `[VERIFIED: neon.com/docs/serverless/serverless-driver]`

### Next.js 16 App Router caveats

1. **One pool per request, in serverless.** `[CITED: neon.com/docs/serverless/serverless-driver]`  "In serverless environments such as Vercel Edge Functions or Cloudflare Workers, WebSocket connections can't outlive a single request. Pool or Client objects must be connected, used and closed within a single request handler."
   - For Vercel **Node.js** lambdas this is less strict — a module-level `Pool` is OK, but cold starts will re-create it. Keep the pattern above (module-level pool).
   - For **Edge** runtime routes, create and close the pool per request. This phase's routes default to Node runtime anyway.
2. **`bufferutil` error with `ws`.** `[CITED: community.vercel.com — "TypeError: bufferUtil.mask is not a function"]` If Next.js build tree-shakes the `ws` package awkwardly, you can hit this. Two known fixes:
   - Add `bufferutil` as a dep, OR
   - Do NOT set `neonConfig.webSocketConstructor = ws` (some users report the default auto-detection works in Next 15/16). Recommended default: set it explicitly + add `bufferutil` to deps if the error appears. Defer adding `bufferutil` until we see the error.
3. **No `export const runtime` needed on DB-reading routes** — they default to `nodejs` in Next 16 App Router, which is what we want.

### Known footguns

- Mixing `neon-http` and `neon-serverless` in the same codebase is fine, but the `drizzle` import path must match the driver: `drizzle-orm/neon-serverless` for Pool, `drizzle-orm/neon-http` for the `neon()` HTTP client. Never cross them.
- `@neondatabase/serverless@1.x` with `drizzle-orm/neon-http` throws "This function can now be called only as a tagged-template function" at query time (not build time). Silent in dev if not exercised. Our pin at `^0.10.4` avoids this entirely.
- The `Pool.connect()` pattern (explicit `client = await pool.connect(); ...; client.release()`) is required for transactions; for one-shot queries, `drizzle(pool).select()...` handles checkout internally.

**Confidence: HIGH** — all claims verified against the Drizzle docs, Neon docs, and the open GitHub issue.

---

## Item 2 — Drizzle migrations via hand-rolled runner

**Verdict: Import from `drizzle-orm/neon-serverless/migrator`. Use `DATABASE_URL_UNPOOLED`. Migrations folder is configurable (default and CONTEXT.md choice: `drizzle/`).**

### Exact import path

```typescript
// scripts/migrate.ts
import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import { migrate } from 'drizzle-orm/neon-serverless/migrator';
import ws from 'ws';

neonConfig.webSocketConstructor = ws;

const url = process.env.DATABASE_URL_UNPOOLED;
if (!url) throw new Error('DATABASE_URL_UNPOOLED must be set for migrations');

const pool = new Pool({ connectionString: url });
const db = drizzle(pool);

async function main() {
  console.log('[migrate] running…');
  await migrate(db, { migrationsFolder: 'drizzle' });
  console.log('[migrate] done');
  await pool.end();
}

main().catch((e) => {
  console.error('[migrate] failed:', e);
  process.exit(1);
});
```

`[VERIFIED: orm.drizzle.team/docs/migrations]` `[VERIFIED: neon.com/docs/guides/drizzle-migrations]`

### Critical: pick the right migrator entry point

Drizzle ships one migrator per driver. Using the wrong one silently works in dev (if both point at the same DB) but wedges in unexpected ways:

| Driver you chose | Correct migrator import |
|---|---|
| `drizzle-orm/neon-serverless` (WebSocket Pool) | `drizzle-orm/neon-serverless/migrator` ← **this phase** |
| `drizzle-orm/neon-http` (HTTP-only) | `drizzle-orm/neon-http/migrator` |
| `drizzle-orm/node-postgres` (`pg`) | `drizzle-orm/node-postgres/migrator` |

Since D-01 picks the WebSocket Pool driver, use `drizzle-orm/neon-serverless/migrator`. `[VERIFIED: orm.drizzle.team/docs/connect-neon]`

### Migrations folder location

- **Fully configurable** via the `migrationsFolder` option to `migrate()` and via `out` in `drizzle.config.ts`. `[VERIFIED: orm.drizzle.team/docs/kit-overview]`
- **Default is `./drizzle/`**, which CONTEXT.md D-30 already chose. No need to override.

Minimal `drizzle.config.ts`:

```typescript
// drizzle.config.ts
import type { Config } from 'drizzle-kit';

export default {
  schema: './lib/db/schema.ts',
  out: './drizzle',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL_UNPOOLED!, // drizzle-kit uses unpooled too
  },
} satisfies Config;
```

### What happens if `DATABASE_URL_UNPOOLED` is pooled (i.e. wrong) ?

This is the footgun. If you accidentally point `DATABASE_URL_UNPOOLED` at the pooled `-pooler` hostname:

1. **DDL mostly works** — individual `CREATE TABLE` statements don't require session state.
2. **Transactions inside a single migration break subtly.** Drizzle's `migrate()` runs each migration file inside a transaction (`BEGIN; ...; COMMIT;`). PgBouncer in transaction-pooling mode (the Neon pooler default) will let individual statements through but can break prepared statements and advisory locks, which Drizzle uses to prevent concurrent migrator runs.
3. **The visible failure** is usually one of:
   - `"prepared statement \"s1\" does not exist"` mid-migration
   - `"cannot set transaction isolation level after a transaction has started"`
   - A migration appears to succeed but a later migration fails because the journal row wasn't committed atomically.

`[CITED: neon.com/docs/connect/connection-pooling]` — pooled connections through `-pooler` run PgBouncer in transaction mode, which is incompatible with session-level features.

**Mitigation:** add a startup check in `scripts/migrate.ts`:

```typescript
if (url.includes('-pooler')) {
  throw new Error('DATABASE_URL_UNPOOLED points at the pooler. Use the direct connection string.');
}
```

### Known footguns

- Forgetting to `await pool.end()` after migration → script hangs for ~30s before Node force-exits. Annoying in CI. Always call `pool.end()`.
- Running `drizzle-kit generate` without `dialect: 'postgresql'` in config → cryptic "no dialect specified" error.
- Mixing the HTTP client for migrations (`neon-http/migrator`) with the WebSocket driver for runtime technically works — but pick one entry point and stay there; the migrator matching the runtime driver keeps mental model simple.

**Confidence: HIGH** for import paths and folder config. **MEDIUM** on the specific error strings from a misconfigured pooled URL (I didn't reproduce them in this session — they're based on PgBouncer behaviour which is well-documented, but exact wording may differ).

---

## Item 3 — Vercel Cron in April 2026

**Verdict: Schema unchanged. Bearer `CRON_SECRET` auth is still the pattern. Node runtime is default. No cron-specific max-duration differs from regular functions.**

### `vercel.json` schema (current)

```jsonc
{
  "framework": "nextjs",
  "crons": [
    {
      "path": "/api/cron/retention",
      "schedule": "0 3 * * *"
    }
  ]
}
```

- `path`: absolute path hit via HTTP GET on the production deployment. `[VERIFIED: vercel.com/docs/cron-jobs]`
- `schedule`: standard 5-field cron in UTC. No `MON`/`SUN`/`JAN` aliases. Cannot set both day-of-month and day-of-week simultaneously. `[VERIFIED: vercel.com/docs/cron-jobs]`
- No other fields (no `headers`, no `runtime`, no `maxDuration` inside the crons entry itself). `maxDuration` is set on the route handler, not here.

### Authentication model

Vercel automatically adds `Authorization: Bearer ${CRON_SECRET}` to the request **only if the `CRON_SECRET` env var is set**. If unset, requests arrive unauthenticated. The route must validate: `[VERIFIED: vercel.com/docs/cron-jobs/manage-cron-jobs]`

```typescript
// app/api/cron/retention/route.ts
import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs'; // default; explicit for clarity
export const maxDuration = 60;   // seconds; see note below

export async function GET(req: NextRequest) {
  const auth = req.headers.get('authorization');
  if (auth !== `Bearer ${process.env.CRON_SECRET}`) {
    return new NextResponse('Unauthorized', { status: 401 });
  }

  // …batched delete loop…
  return NextResponse.json({ ok: true });
}
```

### Runtime & duration

| Fact | Value | Source |
|---|---|---|
| Default runtime for route handlers | `nodejs` | `[VERIFIED: vercel.com/docs/functions/runtimes]` |
| Cron max duration (Hobby) | 300s (5 min) | `[VERIFIED: vercel.com/docs/functions/configuring-functions/duration]` |
| Cron max duration (Pro, configurable) | up to 800s (~13 min) | `[VERIFIED]` same |
| Edge runtime cron | supported, but **must send first byte within 25s**, stream up to 300s | `[VERIFIED]` same |
| Retry on failure | **None.** Vercel does not retry a failed cron invocation. | `[VERIFIED: vercel.com/docs/cron-jobs/manage-cron-jobs]` |
| Concurrency guarantee | **None.** If a run overlaps its next trigger, a second instance may start while the first is still running. | `[VERIFIED]` same |

**Recommendation for `/api/cron/retention`:** stick with Node runtime (default). Set `export const maxDuration = 60` (the batched-delete loop with `LIMIT 10000` will finish well under that on 90-day data). Retention is idempotent by construction (deleting already-deleted rows is a no-op), so the lack-of-retry is acceptable.

### Recent changes / current limitations

`[CITED: vercel.com/docs/cron-jobs/manage-cron-jobs, dated 2026-02-27]`
- **No built-in concurrency lock.** If you want strict "no two runs overlap," use a Redis lock or a DB advisory lock. For our 90-day retention job this is unnecessary: deletes are batched and idempotent.
- **No built-in retry.** If a run fails, the next scheduled run will simply try again. For retention, this is fine.
- **UTC only** — no timezone config.
- **User-Agent is `vercel-cron/1.0`** — can be used as a weaker auth signal, but don't rely on it; the `Authorization` bearer is the real check.

### Known footguns

- Forgetting to set `CRON_SECRET` in Vercel env → Vercel stops sending the header → the route's `req.headers.get('authorization')` is `null` → every request is 401. Silent failure mode: the retention job appears to run (Vercel logs "succeeded with 401") but deletes nothing.
- **Preview deployments do NOT trigger cron jobs.** Only the production deployment. Don't expect to test the cron on preview; test the route handler manually via `curl` with the bearer header.
- **Testing locally:** `next dev` does not trigger the cron. Manual invocation: `curl -H "Authorization: Bearer $CRON_SECRET" http://localhost:3000/api/cron/retention`.

**Confidence: HIGH** — docs page was updated 2026-02-27 (~7 weeks ago) and checked in this session.

---

## Item 4 — Dropping `@upstash/redis` cleanly

**Verdict: No gotchas. Clean removal.**

### Current usage (grep-confirmed earlier)
- `@upstash/redis` is imported only in `lib/analytics.ts` (line 1: `import { Redis } from '@upstash/redis';`).
- Types are bundled — there is no separate `@types/upstash-redis` package to remove.

### Removal checklist (for the planner)

1. After D-12 rewrite of `lib/analytics.ts` is merged:
   - `npm uninstall @upstash/redis`
   - Confirm `package.json` and `package-lock.json` no longer reference it.
   - Run `npm run build` — should succeed with no missing-module errors (since no code imports it any more).
   - Run `npm run typecheck` — no type errors (types were internal to the package).
2. In Vercel env settings: after the deploy that drops the import is stable, **then** unset `KV_REST_API_URL` and `KV_REST_API_TOKEN`. Don't unset before — a stale deploy could roll back and need them briefly.
3. `.env.example` — remove the two `KV_*` lines once they're gone from Vercel.

### Build-time footguns (checked — none apply)

- No Next.js `serverExternalPackages` / `transpilePackages` entry for `@upstash/redis` in `next.config.ts` (file is minimal template per STACK.md).
- No ESLint rule referencing it.
- No test mock referencing it (only 1 test file in the codebase: `lib/scoring.test.ts`).

### Known footguns

- Running `npm uninstall @upstash/redis` while code still imports it → `npm run build` fails with "Module not found". Make sure the rewrite of `lib/analytics.ts` lands in the **same commit** as the `package.json` change, OR rewrite first then remove in a follow-up commit.
- Vercel's env var unset is not synced from `vercel.json` — has to be done in the dashboard or via `vercel env rm`.

**Confidence: HIGH.**

---

## Item 5 — bcryptjs on Next.js 16 Node routes

**Verdict: `bcryptjs@^3.0.3` is current. No known vulns. Keep it. `@types/bcryptjs@^2.4.6` is still the correct types package.**

### Verified state (April 2026)

| Package | Current pin | Status |
|---|---|---|
| `bcryptjs` | `^3.0.3` | `[VERIFIED: security.snyk.io/package/npm/bcryptjs]` Latest published 3.0.x has no known vulnerabilities. Package description: "Optimized bcrypt in plain JavaScript with zero dependencies and TypeScript support, compatible to 'bcrypt'." |
| `@types/bcryptjs` | `^2.4.6` | `[VERIFIED]` still the correct DefinitelyTyped package. (Note: as of `bcryptjs@3.x`, type definitions ship with the main package too, so `@types/bcryptjs` is technically optional, but keeping it doesn't conflict.) |

### Notes on the truncation CVE

There was a famous truncation bug in the native `bcrypt` package (not `bcryptjs`) that was patched in native `bcrypt@5.0.0`. `bcryptjs` was never affected — the codebases are separate implementations. Our codebase uses `bcryptjs`, so this CVE does not apply. `[CITED: portswigger.net/daily-swig/bcrypt-hashing-library-bug-leaves-node-js-applications-open-to-brute-force-attacks]`

### Next.js 16 compatibility

- `bcryptjs` is pure JavaScript (no native bindings), so it runs on any Node runtime without build-time hooks.
- It is **NOT** Edge-runtime compatible — uses Node crypto APIs that aren't in the Edge runtime. All auth routes in this phase stay on the default `nodejs` runtime, so this is fine. Do not add `export const runtime = 'edge'` to any route that imports `lib/auth.ts`.
- No webpack/turbopack config needed.

### Known footguns

- If a future phase introduces `proxy.ts` / `middleware.ts` (currently **explicitly not** in scope per CONTEXT.md domain note), note that middleware runs on Edge runtime by default → can't import `bcryptjs` there. Not our problem this phase.
- Cost factor `10` is what `lib/auth.ts:11` currently uses. CONCERNS.md notes cost 12 as a future hardening option. CONTEXT.md explicitly keeps cost 10 unchanged.

**Confidence: HIGH.**

---

## Item 6 — `gen_random_uuid()` on Neon Postgres 16

**Verdict: Built in. No extension needed. Drizzle syntax `uuid('id').primaryKey().defaultRandom()` is the correct default.**

### Verified

- **Postgres 13+ ships `gen_random_uuid()` as a built-in function** (no extension needed). Neon's default Postgres 16 branches have it available out of the box. `[VERIFIED: neon.com/docs/data-types/uuid]` `[VERIFIED: postgresql.org — release notes, 13]`
- **The old `uuid-ossp` extension's `uuid_generate_v4()` is a separate thing** that DOES require the extension. We are NOT using that. `[VERIFIED]`
- **`pgcrypto` historically exposed `gen_random_uuid()` before 13** — also not needed now. Enabling `pgcrypto` is harmless but unnecessary. `[VERIFIED: neon.com/docs/extensions/pgcrypto]`

### Drizzle schema syntax (correct form)

```typescript
// lib/db/schema.ts
import { pgTable, uuid, text, boolean, timestamp, jsonb, pgEnum } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  name: text('name'),
  isAdmin: boolean('is_admin').notNull().default(false),
  createdAt: timestamp('created_at', { withTimezone: true }).notNull().defaultNow(),
  lastLoginAt: timestamp('last_login_at', { withTimezone: true }),
});
```

`[VERIFIED: orm.drizzle.team/docs/indexes-constraints]` — `.defaultRandom()` on a `uuid` column compiles to `DEFAULT gen_random_uuid()` in the generated SQL.

### Alternative forms (equivalent; pick one)

```typescript
// Explicit SQL expression — identical result, more verbose
import { sql } from 'drizzle-orm';
id: uuid('id').primaryKey().default(sql`gen_random_uuid()`),

// Client-side UUID generation (doesn't touch Postgres at all)
id: uuid('id').primaryKey().$defaultFn(() => crypto.randomUUID()),
```

**Recommendation: use `.defaultRandom()`.** Simplest, DB-generated (so deterministic even if the TS code forgets to pass an id), works unmodified on any Postgres 13+.

### Known footguns

- If a migration is run against a pre-13 Postgres (not possible on Neon, but possible in self-hosted test envs) → `function gen_random_uuid() does not exist`. Neon is always 15/16, so this does not apply.
- Forgetting `withTimezone: true` on `timestamp()` → Drizzle generates `timestamp` (no TZ) instead of `timestamptz`. D-04 mandates `timestamptz`. Always pass `{ withTimezone: true }`.
- Using `$defaultFn(() => crypto.randomUUID())` means the ID is assigned by JS, not Postgres. Fine for app code, but raw SQL `INSERT` statements (e.g. in `scripts/migrate-users.ts` if written as raw SQL) would need to provide `id` themselves. Stick with `.defaultRandom()` for consistency.

**Confidence: HIGH.**

---

## Summary: Concrete Pins for the Planner

```jsonc
// package.json — add
{
  "dependencies": {
    "@neondatabase/serverless": "^0.10.4",
    "drizzle-orm": "^0.45.2",
    "zod": "^3.23.8",        // for lib/env.ts (D-29); verified separately, standard current pin
    "ws": "^8.18.0"          // peer for neon-serverless in Node; verified standard
  },
  "devDependencies": {
    "drizzle-kit": "^0.31.0",
    "tsx": "^4.19.2",        // D-31; verified standard current pin
    "@types/ws": "^8.5.13"
  },
  "scripts": {
    "db:generate": "drizzle-kit generate",
    "db:migrate": "tsx scripts/migrate.ts",
    "db:migrate-users": "tsx scripts/migrate-users.ts"
  }
}
```

Packages to remove after cut-over (per D-16):
```
npm uninstall @upstash/redis
```

## Code Sketches (drop-in for PLAN.md)

### `vercel.json` (final shape)
```json
{
  "framework": "nextjs",
  "crons": [
    { "path": "/api/cron/retention", "schedule": "0 3 * * *" }
  ]
}
```

### `scripts/migrate.ts` skeleton
```typescript
import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import { migrate } from 'drizzle-orm/neon-serverless/migrator';
import ws from 'ws';

neonConfig.webSocketConstructor = ws;

const url = process.env.DATABASE_URL_UNPOOLED;
if (!url) throw new Error('DATABASE_URL_UNPOOLED required');
if (url.includes('-pooler')) throw new Error('Use direct (unpooled) URL for migrations');

const pool = new Pool({ connectionString: url });
const db = drizzle(pool);

(async () => {
  await migrate(db, { migrationsFolder: 'drizzle' });
  await pool.end();
  console.log('[migrate] done');
})().catch((e) => { console.error(e); process.exit(1); });
```

### `lib/db/index.ts` skeleton (runtime)
```typescript
import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from 'ws';
import * as schema from './schema';

neonConfig.webSocketConstructor = ws;

const pool = new Pool({ connectionString: process.env.DATABASE_URL! });
export const db = drizzle(pool, { schema });
```

### Retention cron handler skeleton
```typescript
// app/api/cron/retention/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { events } from '@/lib/db/schema';
import { sql } from 'drizzle-orm';

export const runtime = 'nodejs';
export const maxDuration = 60;

export async function GET(req: NextRequest) {
  if (req.headers.get('authorization') !== `Bearer ${process.env.CRON_SECRET}`) {
    return new NextResponse('Unauthorized', { status: 401 });
  }
  let totalDeleted = 0;
  // Batched delete loop
  while (true) {
    const r = await db.execute(sql`
      DELETE FROM events
      WHERE id IN (
        SELECT id FROM events
        WHERE created_at < now() - interval '90 days'
        LIMIT 10000
      )
    `);
    const n = (r as { rowCount?: number }).rowCount ?? 0;
    totalDeleted += n;
    if (n < 10000) break;
  }
  return NextResponse.json({ ok: true, deleted: totalDeleted });
}
```

---

## Confidence Breakdown

| Item | Confidence | Reason |
|---|---|---|
| 1. Drizzle + Neon WebSocket Pool | HIGH | All version pins + import paths cross-verified npm + Drizzle docs + Neon docs + open GitHub issue #5208. |
| 2. Migrator import + migrations folder | HIGH on import path and folder. MEDIUM on exact PgBouncer error strings. | Error strings inferred from PgBouncer behavior, not reproduced this session. |
| 3. Vercel Cron | HIGH | Docs page dated 2026-02-27, fetched directly. Limits table from current Vercel docs. |
| 4. Upstash removal | HIGH | Zero footguns identified; single import site confirmed from source read. |
| 5. bcryptjs currency | HIGH | Snyk current as of check; no vulns 3.0.x. Next.js 16 + Node runtime is the non-exotic path. |
| 6. `gen_random_uuid()` on Neon + Drizzle `.defaultRandom()` | HIGH | Postgres 13+ built-in confirmed; Drizzle syntax confirmed via drizzle docs. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | `@neondatabase/serverless@0.10.4` is the exact latest 0.10.x as of today. CONTEXT.md pins `^0.10.4`; if npm publishes `0.10.5+` before deploy, caret handles it. | Item 1 | None — caret range accommodates patch bumps. |
| A2 | Exact PgBouncer-through-pooler error wording when used for migrations. | Item 2 footguns | LOW — the mitigation (reject URLs containing `-pooler`) is strictly better than relying on the error to surface. |
| A3 | `bufferutil` error with Next 16 + `ws` is rare and only surfaces in certain build configs. | Item 1 caveats | LOW — trivial fix (add to deps) if it appears at build time. |
| A4 | `drizzle-kit@0.31.9` resolves cleanly under `^0.31.0`. | Item 1 | None — verified via Snyk. |

Nothing in this research needs user confirmation — all pins and approaches are already locked in CONTEXT.md. This research verifies the pins are correct and fleshes out the exact code shapes.

## Sources

### Primary (HIGH)
- Drizzle — Connect Neon: <https://orm.drizzle.team/docs/connect-neon>
- Drizzle — Migrations: <https://orm.drizzle.team/docs/migrations>
- Drizzle — Indexes & Constraints: <https://orm.drizzle.team/docs/indexes-constraints>
- Drizzle — Kit Overview: <https://orm.drizzle.team/docs/kit-overview>
- Neon — Serverless driver: <https://neon.com/docs/serverless/serverless-driver>
- Neon — Drizzle migrations guide: <https://neon.com/docs/guides/drizzle-migrations>
- Neon — UUID data type: <https://neon.com/docs/data-types/uuid>
- Neon — pgcrypto extension: <https://neon.com/docs/extensions/pgcrypto>
- Vercel — Cron Jobs: <https://vercel.com/docs/cron-jobs>
- Vercel — Managing Cron Jobs: <https://vercel.com/docs/cron-jobs/manage-cron-jobs>
- Vercel — Functions runtimes: <https://vercel.com/docs/functions/runtimes>
- Vercel — Configuring maximum duration: <https://vercel.com/docs/functions/configuring-functions/duration>
- npm — drizzle-orm: <https://www.npmjs.com/package/drizzle-orm>
- npm — drizzle-kit: <https://www.npmjs.com/package/drizzle-kit>
- npm — @neondatabase/serverless: <https://www.npmjs.com/package/@neondatabase/serverless>
- GitHub Issue — drizzle-orm #5208 (neon-serverless 1.0 vs neon-http): <https://github.com/drizzle-team/drizzle-orm/issues/5208>
- Snyk — bcryptjs: <https://security.snyk.io/package/npm/bcryptjs>

### Secondary (MEDIUM)
- Snyk — drizzle-kit: <https://security.snyk.io/package/npm/drizzle-kit>

## Metadata

**Valid until:** ~2026-05-16 (30 days). The Drizzle / Neon ecosystem is mid-stride toward Drizzle v1.0 GA; if v1.0 ships within that window, re-verify version pins.

*Research scope: narrow (6 targeted items). Full-domain research not re-performed; CONTEXT.md decisions stand.*
