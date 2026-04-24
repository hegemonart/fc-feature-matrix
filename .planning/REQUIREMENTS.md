# Requirements: FC Benchmark — Flow Expansion

**Defined:** 2026-04-16
**Core Value:** Complete end-to-end digital experience benchmarking across every major fan touchpoint for 33 sports organizations

## v1 Requirements (Validated — already shipped)

- ✓ Homepage feature matrix (61 features × 33 clubs)
- ✓ Auth system, feature matrix UI, screenshot evidence system
- ✓ Python capture scripts, analytics, access request flow

---

## Phase 1 Requirements — Flow Automation Layer (Scanner Infrastructure)

Infrastructure tier; no CHANGELOG v-number bump. Enables Phases 2+ to share capture/vision/scoring tooling.

- [x] **FLOW-01**: `/scanner/` Python package at repo root with `capture/`, `flow/`, `vision/`, `report/`, `scoring/`, `config/`, `output/` modules; CLI `python -m scanner <subcommand> --area <area> --club <slug>`
- [x] **FLOW-02**: Area-parameterized — `/scanner/config/areas.json` drives all path resolution; no area-specific code inside scanner modules
- [x] **FLOW-03**: Capture module with Playwright persistent context, 1440×900 @ 2x DPR full-page PNG, per-club cookie strategies in `cookie_strategies.py`, post-capture banner vision verification, dummy-form-fill without submit, flow-map JSON schema supporting 5-15 click-through steps with `hide_selectors`
- [x] **FLOW-04**: Vision module with two-judge (Opus + Sonnet) checklist-first protocol emitting strict JSON `{feature_key: {present, step, evidence_bbox, confidence, notes}}`; disagreement flagging; PIL-slice module crops evidence from bbox
- [ ] **FLOW-05**: Report module generates HTML contact sheet per area (grid per feature, N club thumbnails, red-border on absent); scoring module (`recalculate.js --area <area>`) reads area's `features.ts` and results JSONs; dry-run passes for Man City hospitality landing page with 3-feature dummy rubric
- [x] **FLOW-06**: `VisionClient` abstraction with dual backend — (a) Claude Agent SDK (subscription-backed, default) consuming user's Max 20x quota; (b) `anthropic` SDK (pay-per-token, fallback). Selected via `--api-mode subscription|api-key` CLI flag. Dry-run passes through subscription path. Both backends produce identical strict-JSON feature verdict output.

---

## v2 Requirements — Ticket Purchase Flow

### Automation

- [ ] **TKT-01**: Flow capture script navigates club ticketing site and screenshots each step (5–15 pages)
- [ ] **TKT-02**: Script handles cookie consent / login walls automatically
- [ ] **TKT-03**: Script runs per-club (~33 runs) and saves evidence to `analysis/ticket/crosscheck/img/`
- [ ] **TKT-04**: Per-club override config for sites with non-standard flows

### Analysis

- [ ] **TKT-05**: Feature rubric defined for ticket purchase flow (TICKET-FLOW.md)
- [ ] **TKT-06**: Results JSON produced per club after analysis
- [ ] **TKT-07**: Scores calculated and displayed in Ticket Purchase tab

### UI

- [ ] **TKT-08**: Ticket Purchase tab unlocked with real data in matrix UI

---

## v3 Requirements — Club App Home (3000px Scroll)

### Data Collection

- [ ] **APP-01**: Manual screenshot process documented (which clubs, which apps, how to capture)
- [ ] **APP-02**: Screenshots standardized to consistent viewport and format
- [ ] **APP-03**: Evidence stored in `analysis/app-home/crosscheck/img/`

### Analysis

- [ ] **APP-04**: Feature rubric defined for app home (APP-HOME.md) — hero, nav, content blocks, personalization
- [ ] **APP-05**: Results JSON per club
- [ ] **APP-06**: Scores calculated and displayed in App Home tab (new tab to add)

---

## v5 Requirements — Merch Purchase Flow

- [ ] **MERCH-01**: Flow capture script for club online store (browse → jersey → add to cart → checkout)
- [ ] **MERCH-02**: Cookie / geo-restriction handling (many club stores block non-local IPs)
- [ ] **MERCH-03**: Feature rubric for merch flow (MERCH-FLOW.md)
- [ ] **MERCH-04**: Results JSON per club + Merch Store tab unlocked

---

## v6 Requirements — Subscription / Membership Purchase

- [ ] **SUBS-01**: Flow capture for membership/streaming purchase flows
- [ ] **SUBS-02**: Handles paywalled preview pages (screenshot available content, note gating)
- [ ] **SUBS-03**: Feature rubric for subscription flow (SUBS-FLOW.md)
- [ ] **SUBS-04**: Results JSON per club + Subscriptions tab unlocked

---

## v7 Requirements — Hospitality Packages

### Phase 2 — 5-club pilot

- [ ] **HOSP-01**: Flow capture for VIP/premium hospitality purchase flows (5 pilot clubs: MCFC, TOT, RMA, PSG, CHE) via Phase 1 scanner with `--area hospitality`
- [ ] **HOSP-02**: Feature rubric (HOSPITALITY-FLOW.md) — package tiers, amenities, booking UX — derived from user-approved FEATURES-CANDIDATES.md (observed-on-site + user-review research)
- [ ] **HOSP-03**: Results JSON per pilot club + Hospitality Packages tab unlocked with 5-club pilot data (visibly labeled "Pilot")

### Phase 2.5 — full rollout

- [ ] **HOSP-04**: Remaining 28 clubs captured + scored (headless-blocked 5 via Chrome MCP, Barcelona via Socios-aware override, mid-tier stress-test decision resolved); Hospitality Packages tab loses "Pilot" label

---

## v8 Requirements — Sponsorship Visibility

- [ ] **SPON-01**: Automated homepage + key page captures focused on sponsor placements
- [ ] **SPON-02**: Feature rubric (SPONSORSHIP.md) — logo placement, brand integration, kit sponsors, digital ads
- [ ] **SPON-03**: Results JSON per club + Sponsorship Visibility tab unlocked

---

## v9 Requirements — Past Seasons Experience

- [ ] **PAST-01**: Flow capture for archive / history / stats sections
- [ ] **PAST-02**: Feature rubric (PAST-SEASONS.md) — match archives, season reviews, historical stats, legends
- [ ] **PAST-03**: Results JSON per club + Past Seasons tab unlocked

---

## v10 Requirements — Matchday Experience

### Schedule Automation

- [ ] **MDAY-01**: Match schedule fetched from football-data.org API for all 33 clubs
- [ ] **MDAY-02**: Cron job triggers screenshot capture at: T-10min, T+30min, T+90min per match
- [ ] **MDAY-03**: Captures homepage, app home (if accessible), and key fan-facing pages at each trigger
- [ ] **MDAY-04**: Manual fallback for clubs not covered by API

### Analysis

- [ ] **MDAY-05**: Feature rubric (MATCHDAY.md) — live score widgets, stadium info, transport, real-time updates
- [ ] **MDAY-06**: Results JSON per club (averaged across captured matches)
- [ ] **MDAY-07**: Matchday Experience tab unlocked with scheduled evidence

---

## v11 Requirements — Between Season Experience

- [ ] **BTWN-01**: Captures taken during known off-season periods for each club
- [ ] **BTWN-02**: Feature rubric (BETWEEN-SEASON.md) — transfer news, pre-season content, fan engagement, retention mechanics
- [ ] **BTWN-03**: Results JSON per club + Between Season tab unlocked

---

## v2 Requirements (Deferred)

- Real-time live match integration (stream data, not just snapshots)
- User-generated scoring / community annotations
- Public unauthenticated access to full matrix

## Out of Scope

| Feature | Reason |
|---------|--------|
| Native iOS/Android app automation | Cannot simulate 33 club apps; manual only for v3 |
| Real-time data | Snapshots are sufficient for benchmarking purposes |
| Crowdsourced scoring | Analyst-controlled quality bar required |
| Non-sports organizations | Scope is sports clubs only |

## Traceability

| Requirement | Phase | Milestone | Status |
|-------------|-------|-----------|--------|
| FLOW-01 | Phase 1 | infra | Pending |
| FLOW-02 | Phase 1 | infra | Pending |
| FLOW-03 | Phase 1 | infra | Pending |
| FLOW-04 | Phase 1 | infra | Pending |
| FLOW-05 | Phase 1 | infra | Pending |
| FLOW-06 | Phase 1 | infra | Pending |
| HOSP-01 | Phase 2 | v7 | Pending |
| HOSP-02 | Phase 2 | v7 | Pending |
| HOSP-03 | Phase 2 | v7 | Pending |
| HOSP-04 | Phase 2.5 | v7.1 | Pending |
| APP-01 | Phase 3 | v3 | Pending |
| APP-02 | Phase 3 | v3 | Pending |
| APP-03 | Phase 3 | v3 | Pending |
| APP-04 | Phase 3 | v3 | Pending |
| APP-05 | Phase 3 | v3 | Pending |
| APP-06 | Phase 3 | v3 | Pending |
| MERCH-01 | Phase 4 | v5 | Pending |
| MERCH-02 | Phase 4 | v5 | Pending |
| MERCH-03 | Phase 4 | v5 | Pending |
| MERCH-04 | Phase 4 | v5 | Pending |
| SUBS-01 | Phase 4 | v6 | Pending |
| SUBS-02 | Phase 4 | v6 | Pending |
| SUBS-03 | Phase 4 | v6 | Pending |
| SUBS-04 | Phase 4 | v6 | Pending |
| TKT-01 | Phase 5 | v2 | Pending |
| TKT-02 | Phase 5 | v2 | Pending |
| TKT-03 | Phase 5 | v2 | Pending |
| TKT-04 | Phase 5 | v2 | Pending |
| TKT-05 | Phase 5 | v2 | Pending |
| TKT-06 | Phase 5 | v2 | Pending |
| TKT-07 | Phase 5 | v2 | Pending |
| TKT-08 | Phase 5 | v2 | Pending |
| SPON-01 | Phase 6 | v8 | Pending |
| SPON-02 | Phase 6 | v8 | Pending |
| SPON-03 | Phase 6 | v8 | Pending |
| PAST-01 | Phase 7 | v9 | Pending |
| PAST-02 | Phase 7 | v9 | Pending |
| PAST-03 | Phase 7 | v9 | Pending |
| BTWN-01 | Phase 7 | v11 | Pending |
| BTWN-02 | Phase 7 | v11 | Pending |
| BTWN-03 | Phase 7 | v11 | Pending |
| MDAY-01 | Phase 8 | v10 | Pending |
| MDAY-02 | Phase 8 | v10 | Pending |
| MDAY-03 | Phase 8 | v10 | Pending |
| MDAY-04 | Phase 8 | v10 | Pending |
| MDAY-05 | Phase 8 | v10 | Pending |
| MDAY-06 | Phase 8 | v10 | Pending |
| MDAY-07 | Phase 8 | v10 | Pending |

**Coverage: 48/48 requirements mapped across 8 phases + Phase 2.5 decimal**

| Phase | Requirements | Count |
|-------|--------------|-------|
| Phase 1 - Flow Automation Layer (scanner infra) | FLOW-01 to FLOW-06 | 6 |
| Phase 2 - Hospitality Pilot (5 clubs) | HOSP-01 to HOSP-03 | 3 |
| Phase 2.5 - Hospitality Full Rollout (28 clubs) | HOSP-04 | 1 |
| Phase 3 - App Home | APP-01 to APP-06 | 6 |
| Phase 4 - Merch + Subscriptions | MERCH-01 to MERCH-04, SUBS-01 to SUBS-04 | 8 |
| Phase 5 - Ticket Purchase | TKT-01 to TKT-08 | 8 |
| Phase 6 - Sponsorship | SPON-01 to SPON-03 | 3 |
| Phase 7 - Past Seasons + Between Season | PAST-01 to PAST-03, BTWN-01 to BTWN-03 | 6 |
| Phase 8 - Matchday | MDAY-01 to MDAY-07 | 7 |
| **Total** | | **48** |

Unmapped: 0

---
*Requirements defined: 2026-04-16 | Phase traceability added: 2026-04-16*
