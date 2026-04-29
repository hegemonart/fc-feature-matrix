# Roadmap: FC Benchmark — Flow Expansion (v2–v11)

## Overview

v1 shipped a validated homepage benchmark (61 features × 33 clubs). This roadmap expands the tool to 9 additional fan touchpoints. Each milestone follows the same delivery pattern: build capture automation → define feature rubric → run club captures → unlock UI tab. Phases are grouped by shared infrastructure and flow complexity, not by milestone number. The reusable flow automation layer is built once in Phase 1 (as part of the first real flow — Ticket Purchase), then adapted for each subsequent flow type. Matchday stands alone in Phase 7 because it requires scheduling infrastructure that no other phase needs.

## Phases

- [ ] **Phase 1: Flow Automation Layer** - Build reusable area-agnostic flow capture scanner at `/scanner/` — no area-specific benchmark ships (infra-tier; dry-run validated against one club only)
- [ ] **Phase 2: Hospitality Pilot** - 5-club hospitality benchmark using the Phase 1 scanner (Man City, Tottenham, Real Madrid, PSG, Chelsea) — first real benchmark area (v7)
- [ ] **Phase 2.5: Hospitality Full Rollout** - Remaining 28 clubs captured + scored; Hospitality Packages tab fully populated (v7.1)
- [ ] **Phase 3: App Home** - Manual capture process + rubric + UI tab for club mobile app home screens (v3)
- [ ] **Phase 4: Merch + Subscriptions** - Two e-commerce flows using the established scanner (v5 + v6)
- [ ] **Phase 5: Ticket Purchase** - Ticket flow benchmark using the established scanner (v2)
- [ ] **Phase 6: Sponsorship** - Brand-visibility and sponsor placement analysis via the scanner's screenshot-only path (v8)
- [ ] **Phase 7: Past Seasons + Between Season** - Content and archive flows (v9 + v11)
- [ ] **Phase 8: Matchday** - Match schedule API, cron-triggered capture system, and matchday benchmark (v10)

## Out-of-Band Infrastructure

These phases are **parallel to and independent of** the numbered flow-expansion phases above. They do not gate any numbered phase and can ship in any order. Mirrors the pattern set by `infra-ci-cd` which shipped before any numbered phase.

- [x] **`infra-ci-cd`** — GitHub Actions CI pipeline (lint / typecheck / test / build). Shipped. See `.planning/phases/infra-ci-cd/`.
- [ ] **`infra-users-admin`** — Users → Postgres, `/admin` panel (users / analytics / access-request triage), analytics → Postgres with 90-day retention, three load-bearing auth security fixes. See `.planning/phases/infra-users-admin/CONTEXT.md`.
- [x] **`infra-redesign-v2`** — Visual redesign of the matrix homepage and system-wide rollout: new neutral-dark palette + brand-orange accent, Inter Tight + Roboto Mono type system, atomic `DataCell` / `SortHeader` / sidebar / hover-tooltip components, extrapolation to `/club`, `/admin`, and modals. Shipped 2026-04-17 (5/5 plans, Lighthouse a11y 91, single-orange-CTA invariant codified). See `.planning/phases/infra-redesign-v2/`.

## Phase Details

### Phase 1: Flow Automation Layer
**Goal**: Build a reusable, area-agnostic flow-capture scanner at `/scanner/`. No area-specific benchmark ships in this phase — Phase 1 is pure infra. Validated by a single-page dry run against one club as smoke test only.
**Depends on**: Nothing (builds on v1 Python capture scripts in `analysis/homepage/crosscheck/`)
**Requirements**: FLOW-01, FLOW-02, FLOW-03, FLOW-04, FLOW-05, FLOW-06
**Success Criteria** (what must be TRUE):
  1. `/scanner/` package exists at repo root with `capture/`, `flow/`, `vision/`, `report/`, `scoring/`, `config/`, `output/` modules and is invoked as `python -m scanner <subcommand> --area <area> --club <slug>`
  2. Scanner is area-agnostic: `/scanner/config/areas.json` parameterizes paths, rubric location, features.ts location; no area-specific code inside any scanner module
  3. Capture module handles cookie consent dialogs (per-club strategies in `/scanner/capture/cookie_strategies.py`), post-capture vision check for banner residue, dummy-form-fill without submit, dynamic-content hide selectors, third-party platform redirects (generic — not broker-specific)
  4. Vision module implements two-judge protocol (Opus + Sonnet) with checklist-first verification (never open-ended discovery); strict JSON output; disagreement flagging to `/scanner/output/disagreements-{area}.json`
  5. Slicing module PIL-crops evidence from `evidence_bbox` output into `analysis/{area}/evidence/features/{club}_{feature_key}.png`
  6. Report module auto-generates HTML contact sheet per area (one grid per feature, N thumbnails per club, red border on absent)
  7. Scoring module (`recalculate.js` parameterized by area) reads area's `features.ts` and results JSONs, writes scores
  8. Dry-run passes: scanner invoked against Man City hospitality landing page (landing only, not full flow) with a 3-feature dummy rubric; zero errors; contact sheet renders
  9. Score-data invariant honored: Phase 1 must NOT modify `analysis/homepage/results/*.json`, `lib/scoring.ts`, `analysis/homepage/features.ts`, or create any new `analysis/{area}/` tree (those belong to Phase 2+). Verification gate: `git diff --quiet analysis/`
**Plans**: 8 plans
  - [x] 01-01-PLAN.md - Foundation: package skeleton + dual-backend deps + test scaffold + dummy rubric fixture
  - [x] 01-02-PLAN.md - Pydantic schemas: FlowMap / FeatureResult / AreasConfig
  - [x] 01-03-PLAN.md - Capture module: Playwright wrapper, MANCITY_STRATEGY cookies, banner verify via Haiku
  - [x] 01-04-PLAN.md - Vision module with DUAL BACKEND: VisionClient Protocol + SubscriptionVisionClient (claude-agent-sdk) + APIKeyVisionClient (anthropic SDK) + factory + two-judge + disagreement + slice
  - [x] 01-05-PLAN.md - Report (Jinja2 contact sheet) + Scoring (Node recalculate.js port with --area)
  - [x] 01-06-PLAN.md - Flow subpackage: validate.py (load + humanize errors) + discover.py stub
  - [x] 01-07-PLAN.md - CLI (Click group with --api-mode default subscription) + areas.json empty-hospitality seed + README
  - [x] 01-08-PLAN.md - Dry-run acceptance gate: mocked integration test + LIVE checkpoint through subscription backend against Man City hospitality

### Phase 2: Hospitality Pilot (5 clubs)
**Goal**: First real benchmark area using the Phase 1 scanner. 5-club hospitality pilot (Manchester City, Tottenham, Real Madrid, PSG, Chelsea) with full click-through capture, two-judge feature mapping, and user-approved coverage before Phase 2.5 rollout begins.
**Depends on**: Phase 1 (scanner infra)
**Requirements**: HOSP-01, HOSP-02, HOSP-03
**Success Criteria** (what must be TRUE):
  1. Review-source research produces `analysis/hospitality/FEATURES-CANDIDATES.md` with candidates tagged `{observed-on-site | complained-about | wished-for}` + `{source_type, url, quote}` — user approves and freezes list before rubric is written (hard gate)
  2. `analysis/hospitality/HOSPITALITY-FLOW.md` rubric defines every scoreable element of the hospitality UX, derived from frozen candidate list
  3. `analysis/hospitality/features.ts` mirrors homepage pattern (tier-weighted feature defs consumed by Next.js app at runtime)
  4. `/scanner/config/areas.json` hospitality entry populated; `/scanner/flow-maps/hospitality/{club}.json` exists for all 5 pilot clubs with click-path `landing → category → package-detail → match-selector → enquiry-form (filled, pre-submit)`
  5. Per-club hospitality-specific cookie/overlay strategies added to `/scanner/capture/cookie_strategies.py`; third-party broker redirects (Seat Unique / Keith Prowse / Eventmasters / P1 Travel / Pitch International) captured with vendor noted in flow-map metadata
  6. Credentials for login-gated clubs managed via `.planning/phases/02-hospitality-pilot/credentials.local.md` (gitignored) + env vars in `.env.local`
  7. Full capture → vision mapping → slicing → coverage report completes for all 5 pilot clubs; user reviews contact sheet and approves coverage
  8. `analysis/hospitality/results/{club}.json` exists for all 5 pilot clubs
  9. Hospitality Packages tab unlocked in app with pilot-subset data, visibly marked "Pilot: 5 clubs" until Phase 2.5 completes
**Plans**: 14 plans (front-half 7 shipped, back-half 7 planned 2026-04-27)
  - [x] 02-01-PLAN.md — Credentials helper (Phase 1 gap fill)
  - [x] 02-02-PLAN.md — Review sources + feature-candidates (user-approval gate)
  - [x] 02-03-PLAN.md — Rubric + features.ts + areas.json populate
  - [x] 02-04-PLAN.md — Per-club cookie strategies (TOT/RMA/PSG/CHE)
  - [x] 02-05-PLAN.md — Flow-discovery crawler implementation + schema metadata
  - [x] 02-06-PLAN.md — Live crawl × 5 pilot clubs + crawl log
  - [x] 02-07-PLAN.md — Front-half closure + back-half handoff
  - [x] 02-08-PLAN.md — Crawler v2 (turnstile + trusted_subdomains + dedupe + per-domain cookies) + Opus bbox calibration + credentials.py CWD fix
  - [x] 02-09-PLAN.md — Per-club flow-map override drafts (extend to full purchase path; mark Chrome MCP / requires_credentials / skipped)
  - [x] 02-10-PLAN.md — Multi-step capture orchestrator (capture_flow + login_to_club) + 5-club live capture wave
  - [x] 02-11-PLAN.md — Two-judge vision wave × 5 clubs (rubric extractor + per-club result JSONs + aggregated disagreements)
  - [x] 02-12-PLAN.md — Slice + contact sheet + derive results JSONs + recompute scores
  - [x] 02-13-PLAN.md — Hospitality Packages UI tab unlock (/hospitality route, Pilot: 5 clubs label, visual + a11y baseline)
  - [ ] 02-14-PLAN.md — Coverage report user review → pilot-gate confirmation (D-17, autonomous: false)

### Phase 2.5: Hospitality Full Rollout (remaining 28 clubs)
**Goal**: Complete hospitality coverage — remaining 28 clubs captured + scored using the already-validated Phase 2 tooling. Hospitality Packages tab loses "Pilot" tag.
**Depends on**: Phase 2 (pilot gate — user-approved coverage)
**Requirements**: HOSP-04
**Success Criteria** (what must be TRUE):
  1. Flow-maps authored for remaining 28 clubs (27 if Barcelona deferred; +5 headless-blocked via Chrome MCP fallback)
  2. 6th stress-test club decision resolved (Newcastle / Aston Villa — either added or explicitly skipped with rationale)
  3. All capture → vision → slice → score runs complete; evidence committed to `analysis/hospitality/evidence/`
  4. `analysis/hospitality/results/{club}.json` exists for all 33 clubs (or documented skips with reason)
  5. Hospitality Packages tab shows full-rollout data; pilot-only label removed
  6. Coverage report confirms parity with pilot quality bar
**Plans**: TBD

### Phase 3: App Home
**Goal**: Analysts can view scored app home benchmarks for all clubs in a new App Home tab, backed by standardized manual screenshots
**Depends on**: Phase 1
**Requirements**: APP-01, APP-02, APP-03, APP-04, APP-05, APP-06
**Success Criteria** (what must be TRUE):
  1. A documented manual capture process specifies which clubs, which apps, viewport size, and file format — any analyst can follow it without guesswork
  2. All captured screenshots are stored consistently in `analysis/app-home/crosscheck/img/` at a standard format and resolution
  3. A feature rubric (APP-HOME.md) covers hero, navigation, content blocks, and personalization dimensions
  4. The App Home tab is unlocked in the UI with per-club scores derived from the manual captures
**Plans**: TBD

### Phase 4: Merch + Subscriptions
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

### Phase 5: Ticket Purchase
**Goal**: The Ticket Purchase tab is unlocked with complete per-club benchmarks, using the scanner delivered in Phase 1
**Depends on**: Phase 1 (scanner + rubric-authoring conventions)
**Requirements**: TKT-01, TKT-02, TKT-03, TKT-04, TKT-05, TKT-06, TKT-07, TKT-08
**Success Criteria** (what must be TRUE):
  1. Scanner is invoked as `python -m scanner capture --area ticket --club <slug>` and navigates ticketing flows (5–15 steps) for all 33 clubs, saving cropped evidence to `analysis/ticket/evidence/features/`
  2. Scanner handles cookie consent, login walls, and third-party ticket platform redirects (Ticketmaster / See Tickets / Eventim / Tixbase) without manual intervention
  3. Per-club override configs in `/scanner/flow-maps/` allow non-standard ticketing flows to complete without crashing
  4. `analysis/ticket/TICKET-FLOW.md` rubric defines every scoreable element of the ticket purchase UX
  5. `analysis/ticket/features.ts` mirrors homepage/hospitality pattern
  6. The Ticket Purchase tab is unlocked in the app with per-club scores and screenshot evidence
**Plans**: TBD

### Phase 6: Sponsorship
**Goal**: The Sponsorship Visibility tab is unlocked with complete per-club benchmarks, leveraging the Phase 1 scanner's screenshot-only path
**Depends on**: Phase 1 (scanner capture + slice modules)
**Requirements**: SPON-01, SPON-02, SPON-03
**Success Criteria** (what must be TRUE):
  1. The sponsorship capture uses the scanner's screenshot-only path (no click-through) to screenshot homepage, matchday, and key pages focused on sponsor placements (logo positions, kit sponsors, digital ad units)
  2. Scanner configured with `--area sponsorship` reuses the Phase 1 cookie strategies, vision-judge mapping, and contact-sheet generation — no new scanner code required
  3. `analysis/sponsorship/SPONSORSHIP.md` rubric scores brand integration quality, placement prominence, and sponsor variety
  4. `analysis/sponsorship/features.ts` mirrors homepage/hospitality pattern
  5. The Sponsorship Visibility tab is unlocked in the app with per-club scores and evidence
**Plans**: TBD

### Phase 7: Past Seasons + Between Season
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

### Phase 8: Matchday
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

## Progress

**Execution Order:**
Numbered phases execute in order: 1 → 2 → 2.5 → 3 → 4 → 5 → 6 → 7 → 8. Phase 2.5 is a decimal sub-phase (hospitality full rollout) gated on Phase 2 pilot approval. Out-of-band infra phases run independently in any order and do not block the numbered track.

**Numbered (flow expansion v2–v11):**

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Flow Automation Layer | 0/8 | Planned | - |
| 2. Hospitality Pilot (5 clubs) | 7/14 | Back-half planned 2026-04-27; ready to execute | - |
| 2.5. Hospitality Full Rollout (28 clubs) | 0/TBD | Not started | - |
| 3. App Home | 0/TBD | Not started | - |
| 4. Merch + Subscriptions | 0/TBD | Not started | - |
| 5. Ticket Purchase | 0/TBD | Not started | - |
| 6. Sponsorship | 0/TBD | Not started | - |
| 7. Past Seasons + Between Season | 0/TBD | Not started | - |
| 8. Matchday | 0/TBD | Not started | - |

**Out-of-band (infrastructure):**

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| `infra-ci-cd` | 1/1 | Complete | 2026-04-16 |
| `infra-users-admin` | 0/TBD | Not started | - |
| `infra-redesign-v2` | 5/5 | Complete — system-wide visual rollout shipped | 2026-04-17 |
