# Roadmap: FC Benchmark — Flow Expansion (v2–v11)

## Overview

v1 shipped a validated homepage benchmark (61 features × 33 clubs). This roadmap expands the tool to 9 additional fan touchpoints. Each milestone follows the same delivery pattern: build capture automation → define feature rubric → run club captures → unlock UI tab. Phases are grouped by shared infrastructure and flow complexity, not by milestone number. The reusable flow automation layer is built once in Phase 1 (as part of the first real flow — Ticket Purchase), then adapted for each subsequent flow type. Matchday stands alone in Phase 7 because it requires scheduling infrastructure that no other phase needs.

## Phases

- [ ] **Phase 1: Flow Automation Layer + Ticket Purchase** - Build multi-page flow capture script and deliver the first complete flow benchmark (v2)
- [ ] **Phase 2: App Home** - Manual capture process + rubric + UI tab for club mobile app home screens (v3)
- [ ] **Phase 3: Merch + Subscriptions** - Two e-commerce flows using the established automation layer (v5 + v6)
- [ ] **Phase 4: Hospitality + Sponsorship** - Premium and brand-visibility flows (v7 + v8)
- [ ] **Phase 5: Past Seasons + Between Season** - Content and archive flows (v9 + v11)
- [ ] **Phase 6: Matchday** - Match schedule API, cron-triggered capture system, and matchday benchmark (v10)
- [ ] **Phase 7: Infra — Users, Admin Panel & Analytics Migration** - Out-of-band infra (parallel to v2–v11, does not gate any flow phase): migrate users to Postgres, migrate analytics from Redis to Postgres, build /admin panel (users / analytics / access-request triage), fix 3 load-bearing auth security bugs

## Phase Details

### Phase 1: Flow Automation Layer + Ticket Purchase
**Goal**: Analysts can run automated multi-page flow captures for any club's ticketing flow and view scored results in the Ticket Purchase tab
**Depends on**: Nothing (builds on v1 Python capture scripts)
**Requirements**: TKT-01, TKT-02, TKT-03, TKT-04, TKT-05, TKT-06, TKT-07, TKT-08
**Success Criteria** (what must be TRUE):
  1. Running the flow capture script for any club navigates its ticketing site, screenshots 5–15 steps, and saves cropped evidence to `analysis/ticket/crosscheck/img/`
  2. The script handles cookie consent dialogs and login walls without manual intervention
  3. Per-club override configs allow non-standard ticketing flows to complete without crashing
  4. A feature rubric (TICKET-FLOW.md) defines every scoreable element of the ticket purchase UX
  5. The Ticket Purchase tab in the app is unlocked with real per-club scores and screenshot evidence
**Plans**: TBD

### Phase 2: App Home
**Goal**: Analysts can view scored app home benchmarks for all clubs in a new App Home tab, backed by standardized manual screenshots
**Depends on**: Phase 1
**Requirements**: APP-01, APP-02, APP-03, APP-04, APP-05, APP-06
**Success Criteria** (what must be TRUE):
  1. A documented manual capture process specifies which clubs, which apps, viewport size, and file format — any analyst can follow it without guesswork
  2. All captured screenshots are stored consistently in `analysis/app-home/crosscheck/img/` at a standard format and resolution
  3. A feature rubric (APP-HOME.md) covers hero, navigation, content blocks, and personalization dimensions
  4. The App Home tab is unlocked in the UI with per-club scores derived from the manual captures
**Plans**: TBD

### Phase 3: Merch + Subscriptions
**Goal**: Both the Merch Store and Subscriptions tabs are unlocked with complete per-club flow benchmarks
**Depends on**: Phase 1
**Requirements**: MERCH-01, MERCH-02, MERCH-03, MERCH-04, SUBS-01, SUBS-02, SUBS-03, SUBS-04
**Success Criteria** (what must be TRUE):
  1. The merch capture script navigates a full browse → jersey → add-to-cart → checkout flow and saves step evidence per club
  2. Geo-restrictions and IP-blocking on club stores are handled (proxy config or documented manual fallback)
  3. The subscription capture script screenshots paywall-adjacent pages and correctly notes what is gated versus visible
  4. Both MERCH-FLOW.md and SUBS-FLOW.md rubrics are defined with clear scoring criteria
  5. Both tabs are unlocked in the app with real per-club data
**Plans**: TBD

### Phase 4: Hospitality + Sponsorship
**Goal**: Both the Hospitality Packages and Sponsorship Visibility tabs are unlocked with complete per-club benchmarks
**Depends on**: Phase 1
**Requirements**: HOSP-01, HOSP-02, HOSP-03, SPON-01, SPON-02, SPON-03
**Success Criteria** (what must be TRUE):
  1. The hospitality capture script navigates VIP/premium package flows and captures package tiers, amenities listings, and booking UX per club
  2. HOSPITALITY-FLOW.md rubric covers package tier structure, amenities detail, and booking experience quality
  3. The sponsorship capture script screenshots homepage and key pages focused on sponsor placements (logo positions, kit sponsors, digital ad units)
  4. SPONSORSHIP.md rubric scores brand integration quality, placement prominence, and sponsor variety
  5. Both tabs are unlocked in the app with per-club scores and evidence
**Plans**: TBD

### Phase 5: Past Seasons + Between Season
**Goal**: Both the Past Seasons and Between Season tabs are unlocked, completing coverage of archive and off-season fan touchpoints
**Depends on**: Phase 1
**Requirements**: PAST-01, PAST-02, PAST-03, BTWN-01, BTWN-02, BTWN-03
**Success Criteria** (what must be TRUE):
  1. The past seasons capture script navigates archive/history/stats sections and screenshots match archives, season reviews, historical stats, and legends content per club
  2. PAST-SEASONS.md rubric defines scoring criteria across archive depth, navigation quality, and stats richness
  3. Between-season captures are taken during known off-season windows and include transfer news, pre-season content, fan engagement, and retention mechanics
  4. BETWEEN-SEASON.md rubric scores content freshness, engagement mechanics, and off-season UX quality
  5. Both tabs are unlocked with per-club results and timed evidence
**Plans**: TBD

### Phase 6: Matchday
**Goal**: The Matchday Experience tab is unlocked with automatically captured, time-stamped evidence gathered at T-10min, T+30min, and T+90min relative to real match kickoffs for all 33 clubs
**Depends on**: Phase 1
**Requirements**: MDAY-01, MDAY-02, MDAY-03, MDAY-04, MDAY-05, MDAY-06, MDAY-07
**Success Criteria** (what must be TRUE):
  1. The system fetches upcoming match schedules from football-data.org for all 33 clubs and stores them in a queryable format
  2. A cron job automatically triggers screenshot captures at T-10min, T+30min, and T+90min for each match — no manual intervention required on match days
  3. Each triggered capture screenshots the homepage and key fan-facing pages, saving time-stamped evidence to `analysis/matchday/crosscheck/img/`
  4. Clubs not covered by the API have a documented manual fallback process that still produces evidence in the same format
  5. MATCHDAY.md rubric covers live score widgets, stadium info, transport links, and real-time update patterns
  6. The Matchday Experience tab is unlocked with per-club scores averaged across captured matches, with linked time-stamped evidence
**Plans**: TBD

### Phase 7: Infra — Users, Admin Panel & Analytics Migration
**Goal**: Users are stored in Neon Postgres (not `data/users.json`), admins can create / edit / delete users and triage access requests from `/admin` without a redeploy, and analytics events live in Postgres with 90-day rolling retention. Three load-bearing auth security bugs fixed opportunistically.
**Depends on**: Nothing (out-of-band; does not gate Phases 1–6)
**Parallelism**: Can ship at any time in parallel with the flow-expansion phases
**Requirements**: — (no REQ-IDs — infra phase, like infra-ci-cd)
**Context**: `.planning/phases/infra-users-admin/CONTEXT.md` — full decision log and scope
**Success Criteria** (what must be TRUE):
  1. `data/users.json` is deleted from the repo; `lib/auth.ts` reads users from Postgres via Drizzle; the 5 existing users (including `is_admin = true` for `@humbleteam.com` addresses) are present in the DB after running the one-shot migration script
  2. `/admin/users` (server-rendered, admin-only) lists all users, can add a new user via email + password (or generated password), toggle `is_admin`, reset password, and delete with double-confirmation; SQL-level guardrails prevent deleting your own account or demoting/deleting the last admin
  3. `/admin/requests` shows incoming access requests with Grant (creates user + marks row granted) and Dismiss actions; `/api/email` inserts into `access_requests` before firing the Resend email
  4. `lib/analytics.ts` is rewritten against Postgres; `logEvent()` and `getEvents()` keep their signatures; `/api/analytics` POST requires an authenticated session; `/analytics` 308-redirects to `/admin/analytics`; the Vercel Cron at `/api/cron/retention` deletes events older than 90 days in batches, authed via `CRON_SECRET`
  5. Auth security fixes landed: `AUTH_SECRET` is required in production (zod env validator throws without it), `parseSessionToken()` rejects tokens older than `MAX_AGE` based on the timestamp already encoded in the token, `/api/analytics` POST returns 401 when unauthenticated
  6. `@upstash/redis` is removed from `package.json`; `vitest` test suite still passes; CI (`.github/workflows/ci.yml`) is green on the phase PR
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6. Phase 7 is out-of-band infrastructure — it can ship in parallel with any of the numbered phases and has no dependency on them.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Flow Automation Layer + Ticket Purchase | 0/TBD | Not started | - |
| 2. App Home | 0/TBD | Not started | - |
| 3. Merch + Subscriptions | 0/TBD | Not started | - |
| 4. Hospitality + Sponsorship | 0/TBD | Not started | - |
| 5. Past Seasons + Between Season | 0/TBD | Not started | - |
| 6. Matchday | 0/TBD | Not started | - |
| 7. Infra — Users, Admin Panel & Analytics Migration | 0/TBD | Not started | - |
