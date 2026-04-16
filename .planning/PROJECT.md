# FC Benchmark

## What This Is

UX benchmarking tool that scores digital experiences across 33 sports organizations (FC Barcelona, Bayern Munich, Liverpool, etc.). Currently covers homepage features (61 features, scored and visualized in a feature matrix). The next phase expands coverage to 9 additional fan touchpoints — ticket purchase, app home, merch, subscriptions, hospitality, sponsorship, past seasons, matchday, and between-season — each with dedicated screenshot evidence and feature rubrics.

## Core Value

Complete end-to-end digital experience benchmarking across every major fan touchpoint for 33 sports organizations — the most comprehensive sports UX dataset available.

## Requirements

### Validated

- ✓ Homepage feature matrix (61 features × 33 clubs) — v1
- ✓ Auth system (bcrypt, cookie sessions, users.json) — v1
- ✓ Feature matrix UI with filters, sorting, detail panels — v1
- ✓ Cross-check system with element-level screenshot evidence — v1
- ✓ Python screenshot capture scripts (capture_elements.py) — v1
- ✓ Locked tab navigation for future flows — v1
- ✓ Analytics via Upstash Redis — v1
- ✓ Access request flow (email via Resend) — v1

### Active

- [ ] Ticket purchase flow analysis (v2)
- [ ] Club mobile app home — 3000px scroll capture (v3)
- [ ] Merch purchase flow analysis (v5)
- [ ] Subscription/membership purchase flow analysis (v6)
- [ ] Hospitality packages flow analysis (v7)
- [ ] Sponsorship visibility analysis (v8)
- [ ] Past seasons experience analysis (v9)
- [ ] Matchday experience — scheduled auto-screenshots (v10)
- [ ] Between-season experience analysis (v11)

### Out of Scope

- Native iOS/Android app automation — can't simulate 33 apps; mobile screenshots taken manually
- Real-time live match data — matchday captures are scheduled snapshots, not live streams
- User-generated scoring — scores are analyst-defined, not crowdsourced
- Public access — tool remains gated behind auth

## Context

**Existing codebase:**
- Screenshot automation: `analysis/homepage/crosscheck/capture_elements.py` — opens Chrome, navigates pages, screenshots, crops to specific elements, analyzes. This is the foundation for all flow automation.
- Data layer: `analysis/homepage/results/*.json` per-club feature values; `analysis/homepage/features.ts` feature definitions
- Each new flow needs: feature rubric (FLOW-NAME.md), results JSONs per club, and screenshot evidence in `crosscheck/img/`
- Recalculate script: `analysis/homepage/crosscheck/recalculate-scores.js` — runs after any JSON changes

**Flow automation model:**
- Claude agent runs ~40 times (once per club) per flow type
- Agent navigates the club's flow, screenshots each step (5–15 pages), crops evidence per feature
- v10 matchday is unique: scheduled cron triggers captures at -10min, +30min, +90min relative to kickoff
- Match schedules sourced from public API (football-data.org or similar)

**Existing locked tabs in UI:** Ticket Purchase, Merch Store, Subscriptions, Matchday Experience, Hospitality Packages, Sponsorship Visibility, Between Season, Past Seasons — each milestone unlocks one tab with real data.

## Constraints

- **Tech stack**: Python (screenshot automation), TypeScript/Next.js (app), JSON (data storage) — no DB migration
- **Manual for v3**: Mobile app home screenshots taken manually — no iOS simulator automation
- **Match schedule API**: football-data.org free tier covers most clubs; fallback to manual for gaps
- **Per-club rubric**: Each flow type needs a feature rubric defined before automation can run

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Extend existing Python capture scripts | Already proven, handles cookies/popups, club-specific overrides exist | — Pending |
| New automation layer vs extend homepage scripts | Flow capture (multi-page navigation) is fundamentally different from element cropping | — Pending |
| football-data.org for matchday schedule | Free tier, good coverage of European clubs | — Pending |
| Mobile app home via manual capture | Cannot automate 33 club apps; manual is acceptable for v3 | ✓ Decided |

---
*Last updated: 2026-04-16 after initialization*
