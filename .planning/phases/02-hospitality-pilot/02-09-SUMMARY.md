---
phase: 02-hospitality-pilot
plan: 09
subsystem: scanner.flow + flow-maps/hospitality
tags: [flow-maps, hospitality, schema-additive, chrome-mcp-handoff, option-b-partial]
dependency-graph:
  requires: [02-08]
  provides: [02-10]
  affects: [scanner.flow.schema, scanner.flow.validate, scanner/flow-maps/hospitality/*.json]
tech-stack:
  added: []
  patterns: [pydantic-additive-defaults, chrome-mcp-handoff-marker, requires-credentials-marker, skipped-step-marker]
key-files:
  created: []
  modified:
    - scanner/flow/schema.py
    - scanner/flow-maps/hospitality/mancity.json
    - scanner/flow-maps/hospitality/tottenham.json
    - scanner/flow-maps/hospitality/realmadrid.json
    - scanner/flow-maps/hospitality/psg.json
    - scanner/flow-maps/hospitality/chelsea.json
    - scanner/tests/test_flow_schema_overrides.py
    - scanner/tests/test_flow_discover.py
decisions:
  - "Chrome MCP handoff is per-step, not per-flow: a single flow-map can mix Playwright steps and Chrome-MCP steps (PSG www vs billetterie split)"
  - "skipped reason strings are free-form, not enum: lets the orchestrator surface human-readable rationale (Chelsea Option B 'requires-paid-account' is the inaugural value)"
  - "Plan 02-08 regression test loosened from strict-default to typing contract: Plan 02-09 deliberately populates trusted_subdomains_used / bot_challenge_encountered, so the additive-defaults test now verifies type, not zero-value"
metrics:
  completed_date: 2026-04-27T15:16:35Z
  duration: 2.5h
  tasks_completed: 3
  files_modified: 8
  commits: 9
---

# Phase 02 Plan 09: Per-Club Flow-Map Override Drafts Summary

**One-liner:** Extended 5 hospitality flow-maps from shallow crawler-discovered seeds (3-12 steps stopping at depth 3) to full D-08 purchase-path drafts (12-15 steps each, ending at enquiry-form-prefill) with per-step Chrome-MCP / requires-credentials / skipped markers so Plan 02-10 capture orchestration can route each step correctly.

---

## What was delivered

### Schema additions (additive, default-Falsy)

`scanner/flow/schema.py` — three new optional `FlowStep` fields:

| Field                  | Type           | Default | Purpose                                                                  |
| ---------------------- | -------------- | ------- | ------------------------------------------------------------------------ |
| `requires_credentials` | `bool`         | `False` | Capture orchestrator authenticates BEFORE this step (Plan 02-01 helper). |
| `manual_chrome_mcp`    | `bool`         | `False` | Orchestrator pauses Playwright; user drives Chrome MCP for this step.    |
| `skipped`              | `str \| None`  | `None`  | Free-form skip reason; orchestrator records skip in coverage output.     |

**D-15 / D-16 invariants unchanged:** 1-15 step cap, closed-Literal `action` field still bans `submit`. New fields are pure metadata.

### Per-club flow-map step counts (post-extension)

| Club        | Steps | manual_chrome_mcp | requires_credentials | skipped | fixture_id        | Notes                                                        |
| ----------- | ----- | ----------------- | -------------------- | ------- | ----------------- | ------------------------------------------------------------ |
| mancity     | 13    | 13                | 0                    | 0       | `FIRST_AVAILABLE` | Cloudflare Turnstile blocks every page → all steps Chrome MCP |
| tottenham   | 12    | 0                 | 0                    | 0       | `FIRST_AVAILABLE` | Cleanest crawl; full Playwright path to enquiry-form-prefill  |
| realmadrid  | 13    | 10                | 1                    | 0       | `FIRST_AVAILABLE` | Landing on Playwright; CAPTCHA halts → 10 descent steps Chrome MCP |
| psg         | 14    | 7                 | 1                    | 0       | `FIRST_AVAILABLE` | Dual-domain: 7 www.psg.fr Playwright + 7 billetterie Chrome MCP |
| chelsea     | 15    | 0                 | 0                    | 2       | `FIRST_AVAILABLE` | Option B partial: 5 package landings reachable; 2 deep steps `skipped='requires-paid-account'` |

Total: 67 steps across 5 flow-maps (avg 13.4/club, all within D-15 cap of 15).

### Per-club click-path coverage

**mancity** (13 steps, all `manual_chrome_mcp`):
- Landing → 4 hospitality tier landings (Tunnel Club Premier, Tunnel Club, Backstage, Your Matchday Experience) → match-selector → enquiry-form-prefill (D-10 dummy values).
- `metadata.bot_challenge_encountered=true`, `bot_challenge_reason='turnstile'`.

**tottenham** (12 steps, no Chrome MCP):
- Landing → /tickets/premium-experiences/matchday-options/ → /seasonal-options/premium-seats/ → match-selector → enquiry-form-prefill.
- `hide_selectors` include OKX sponsor overlay (research §5).

**realmadrid** (13 steps, 10 Chrome MCP):
- Steps 1-3 landing on Playwright (CAPTCHA not yet triggered).
- Steps 4-7 → /vip-area/matchday-hospitality + tier-card click (Chrome MCP).
- Steps 8-10 → /vip-area/seasonal-vip/palcos-vip alternate branch (Chrome MCP).
- Steps 11-13 → enquiry-form-prefill with `requires_credentials=true` (RMA gates seasonal-VIP enquiries per research §5) + Chrome MCP.

**psg** (14 steps, dual-domain):
- Steps 1-7 on www.psg.fr (Playwright): landing → first-tier-click → /en/hospitality/all-executive-club detail.
- Steps 8-14 on billetterie.psg.fr (Chrome MCP, `bot_challenge_reason='turnstile'`):
  - billetterie-home-vip + screenshot.
  - billetterie-login (`requires_credentials=true; manual_chrome_mcp=true`).
  - match-selector → enquiry-form-prefill.
- `metadata.trusted_subdomains_used=['billetterie.psg.fr']`.

**chelsea** (15 steps, Option B partial):
- Steps 1-3: landing on hospitality.chelseafc.com (Playwright reaches this).
- Steps 4-13: 5 package landings × (navigate + screenshot) — Centenary Club, Platinum, Home Dugout Club, Museum Suite, Tambling Suite.
- Steps 14-15: match-selector + enquiry-form-prefill — both `skipped='requires-paid-account'`. Capture orchestrator records the skip and does NOT execute.
- `metadata.broker_vendor='keith_prowse'` (suspected per research §5; Plan 02-12 confirms).
- `metadata.dead_ends` deduplicated (Plan 02-08 contract honored).

### D-08 click-through compliance

All 5 maps describe the canonical D-08 purchase path:
`landing → experience-category → package-detail → match-selector → enquiry-form (pre-submit, NEVER submit per D-16)`

### D-10 dummy form values

Every `fill` step uses the D-10 family:
- `Test Test`
- `test@example.com`
- `+44 0000 000000`

No real PII committed (T-09-02 disposition: accept).

### D-09 fixture placeholder

All 5 `metadata.fixture_id == "FIRST_AVAILABLE"`. Capture orchestrator (Plan 02-10) will overwrite with the actual ID at run-time.

### D-16 invariant verified

`pytest tests/test_flow_schema_overrides.py::test_no_submit_action_in_committed_flow_maps` parametrized over all 5 clubs — pre-validate JSON scan + schema-level closed-Literal both passed.

---

## Tests added

`scanner/tests/test_flow_schema_overrides.py` — 36 tests (all green):

| Group                          | Count | Coverage                                                                  |
| ------------------------------ | ----- | ------------------------------------------------------------------------- |
| Schema-level (additive defaults, round-trip, D-16 belt-and-braces) | 6     | Plan 02-09 schema invariants                                              |
| Disk-level (parametrized over 5 clubs)                              | 5     | All hospitality maps validate                                             |
| mancity                        | 3     | Step count + Chrome-MCP markers + fixture_id                              |
| tottenham                      | 3     | Step count + enquiry-form-prefill + fixture_id                            |
| realmadrid                     | 4     | Step count + dual VIP-branch + post-CAPTCHA Chrome MCP + fixture_id       |
| psg                            | 3     | Step count + dual-domain coverage + requires_credentials + fixture_id     |
| chelsea                        | 5     | Step count + skipped marker + dead_ends dedupe + broker_vendor + fixture_id |
| D-16 belt-and-braces (parametrized over 5 clubs) | 5     | Pre-validate scan for `submit` in JSON                                    |
| End-of-plan smoke              | 1     | Loop validate_flow_map() over all 5 maps                                  |
| **Total**                      | **36**| **All pass**                                                              |

Full scanner test suite: **235 passed** (199 baseline pre-Plan-02-09 + 36 schema-override tests).

---

## Commits

| Hash    | Type    | Description                                                                        |
| ------- | ------- | ---------------------------------------------------------------------------------- |
| 8726249 | test    | Failing tests for FlowStep override fields + per-club flow-maps (RED gate)         |
| 4c7c2ee | feat    | Extend FlowStep schema with override fields (GREEN gate Task 1 schema)             |
| e89e64d | feat    | mancity flow-map extended to full purchase path (Chrome MCP marked)                |
| d73a3d6 | feat    | tottenham flow-map extended to enquiry form prefill                                |
| 93516c5 | test    | RED gate for realmadrid + psg + chelsea extended flow-map shape                    |
| 5b56aa2 | feat    | realmadrid flow-map covers matchday + palcos-vip (CAPTCHA → Chrome MCP)            |
| ec531fc | feat    | psg flow-map covers www + billetterie (Cloudflare → Chrome MCP, requires_credentials) |
| 98444b1 | feat    | chelsea flow-map (Option B partial, paid-customer steps marked skipped) + test fix |
| (this)  | docs    | Complete plan summary + STATE/ROADMAP updates                                      |

9 commits total (matches per-task commit hygiene).

---

## TDD Gate Compliance

Plan 02-09 follows the per-task TDD pattern (Task 1, 2, 3 each with `tdd="true"`):

- **Task 1 RED gate:** `8726249 test(02-09): failing tests for FlowStep override fields + per-club extended flow-maps`
- **Task 1 GREEN gate (schema):** `4c7c2ee feat(02-09): extend FlowStep schema with override fields`
- **Task 1 GREEN gate (mancity):** `e89e64d feat(02-09): mancity flow-map extended to full purchase path`
- **Task 1 GREEN gate (tottenham):** `d73a3d6 feat(02-09): tottenham flow-map extended to enquiry form prefill`
- **Task 2 RED gate:** `93516c5 test(02-09): RED gate for realmadrid + psg + chelsea extended flow-map shape`
- **Task 2 GREEN gate (realmadrid):** `5b56aa2 feat(02-09): realmadrid flow-map covers matchday + palcos-vip`
- **Task 2 GREEN gate (psg):** `ec531fc feat(02-09): psg flow-map covers www + billetterie`
- **Task 3 GREEN gate (chelsea):** `98444b1 feat(02-09): chelsea flow-map (Option B partial)`

The Task 3 RED gate was authored together with Task 2 RED (commit 93516c5) for efficiency since both drew from the same test infrastructure. Both gate sequences (RED → GREEN) preserved.

---

## Acceptance criteria

- [x] All 5 hospitality flow-maps validate via `validate_flow_map()` (5/5 green).
- [x] FlowStep schema accepts 3 new optional fields with correct defaults.
- [x] D-16 closed Literal unchanged: `action: "submit"` still rejected.
- [x] No real PII in any form_fields (D-10 dummy values only).
- [x] At least one Chelsea step marked `skipped: "requires-paid-account"` (2 steps actually).
- [x] All 5 maps have `fixture_id: "FIRST_AVAILABLE"` placeholder per D-09.
- [x] `git diff --quiet analysis/` exits 0.
- [x] `git diff --quiet scanner/{vision,scoring,report,capture}/` exits 0.
- [x] All scanner tests still green (235 / 235).

**Acceptance: PASS.**

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Plan 02-08 regression test made wrong assumptions about Plan 02-09 outcomes**

- **Found during:** Task 3 final test sweep.
- **Issue:** `tests/test_flow_discover.py::test_existing_flow_maps_still_validate_after_schema_extension` asserted strict zero-defaults for the Plan 02-08 schema fields (`bot_challenge_encountered is False`, `trusted_subdomains_used == []`). Plan 02-09 deliberately populates these on individual maps (PSG bot_challenge for billetterie, Chelsea trusted_subdomains for hospitality.chelseafc.com).
- **Fix:** Loosened the assertions from strict zero-value to typing contract (`isinstance(..., bool)`, `isinstance(..., list)` with str elements). The original intent of the Plan 02-08 test was the additive-defaults contract — i.e. "the schema fields exist with the right type when not set" — which the typing assertions correctly verify without conflicting with deliberate value-population by Plan 02-09.
- **Files modified:** `scanner/tests/test_flow_discover.py`
- **Commit:** 98444b1

### Authentication gates

None encountered. All work was JSON authoring + Python schema editing.

---

## Threat surface scan

No new security-relevant surface introduced beyond the threat register. The three new metadata flags (`requires_credentials`, `manual_chrome_mcp`, `skipped`) are read-only markers consumed by Plan 02-10's capture orchestrator. They do not change any trust boundaries.

T-09-02 (Information Disclosure on enquiry-form-prefill values) was the highest-risk surface and is mitigated by hard-coding D-10 dummy values across all 5 maps (verified in `test_tottenham_extended_flow_includes_enquiry_form_prefill` and by manual inspection of all `form_fields` in the JSONs).

---

## Self-Check

- All 5 flow-maps exist on disk: `mancity.json` (13 steps), `tottenham.json` (12 steps), `realmadrid.json` (13 steps), `psg.json` (14 steps), `chelsea.json` (15 steps).
- All 9 commits in git log: 8726249, 4c7c2ee, e89e64d, d73a3d6, 93516c5, 5b56aa2, ec531fc, 98444b1 (the 9th is the metadata commit that follows this SUMMARY).
- All 235 scanner tests pass.
- Subscription cost: $0 (manual JSON authoring + zero new vision/SDK calls — within plan budget).

## Self-Check: PASSED

---

## Hand-off to Plan 02-10

Plan 02-10 (capture orchestrator for hospitality area) consumes these 5 flow-maps with the following execution contract:

1. For each step, check `skipped` first. If non-None, log skip reason and continue.
2. Else check `manual_chrome_mcp`. If true, pause Playwright and prompt the user with the URL + step name; resume on user signal.
3. Else check `requires_credentials`. If true, call `credentials.get_credential(club, area)` (Plan 02-01) and authenticate BEFORE running the step.
4. Else execute via Playwright as today.
5. The orchestrator records actual `fixture_id` in metadata at run time (overwriting the `"FIRST_AVAILABLE"` placeholder).
6. Coverage report (Plan 02-13) lists skip reasons + manual-MCP step counts per club.

The 5 flow-maps in `scanner/flow-maps/hospitality/` are now production-ready inputs for that orchestrator.
