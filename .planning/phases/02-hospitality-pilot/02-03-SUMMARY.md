---
phase: 02-hospitality-pilot
plan: 03
subsystem: hospitality-rubric
tags:
  - rubric
  - hospitality
  - areas-config
  - frozen-candidates
requires:
  - ".planning/phases/02-hospitality-pilot/02-02-SUMMARY.md"   # candidate freeze
  - "analysis/hospitality/FEATURES-CANDIDATES.md"              # source of truth
  - "analysis/hospitality/REVIEW-SOURCES.md"                   # provenance
  - "analysis/homepage/HOME-PAGE.md"                           # rubric pattern
  - "analysis/homepage/features.ts"                            # TS pattern
provides:
  - "analysis/hospitality/HOSPITALITY-FLOW.md"   # 55-feature rubric (source of truth)
  - "analysis/hospitality/features.ts"            # typed FEATURES array (HP01..HP55)
  - "scanner/config/areas.json (hospitality → pilot)"
affects:
  - "analysis/types.ts"                           # additive CategoryId extension
  - "scanner/tests/test_no_area_coupling.py"      # Phase-1 seed assertion → Phase-2 activation assertion
tech-stack:
  added: []
  patterns:
    - "Mirrored analysis/homepage/{HOME-PAGE.md,features.ts} shape 1:1"
    - "Tier → TierId mapping: 1→A(+1/-3), 2→C(+5/-2), 3→D(+8/-1)"
    - "buildPresence() all-absent until back-half writes results JSON"
    - "Feature-key 1:1 port from frozen candidates (no rename, no drop, no add)"
key-files:
  created:
    - "analysis/hospitality/HOSPITALITY-FLOW.md (220 lines, 55 scored rows)"
    - "analysis/hospitality/features.ts (218 lines, 55 feat() calls)"
  modified:
    - "analysis/types.ts (CategoryId union + 8 hospitality members — additive)"
    - "scanner/config/areas.json (hospitality entry populated)"
    - "scanner/tests/test_no_area_coupling.py (Phase-1 seed assertion updated to Phase-2 activation)"
decisions:
  - "D-02-03-01: Candidate file had 55 unique keys (not 54 as the plan prompt stated). Regex `[a-z_]+` excluded key `enquiry_form_field_count_le_7` because of the digit — all 55 keys are legitimate; 1:1 port preserved."
  - "D-02-03-02: status='active' from plan Task 3 is invalid per scanner/config/schema.py Literal (pending|pilot|full|deprecated). Set to 'pilot' matching the 5-club pilot scope in 02-CONTEXT. Schema-test fixture test_phase2_full_hospitality_entry_parses already validates this exact value."
  - "D-02-03-03: types.ts CategoryId extended additively with 8 hospitality categories. All 12 homepage categories preserved unchanged (D-20). Additive union extension — not a remodel — so Rule 4 not triggered."
  - "D-02-03-04: scanner/tests/test_no_area_coupling.py test_phase1_areas_json_seed_matches_user_decision_1 function was a Phase-1 seed invariant whose docstring explicitly named 'Phase 2's HOSP-02 plan' as the unlock point — renamed + updated to assert Phase-2 activation state (Rule 3, blocking plan completion)."
metrics:
  duration_seconds: 756
  duration_human: "~12.6 min"
  tasks_completed: 3
  files_created: 2
  files_modified: 3
  commits: 3
  feature_count: 55
  completed: "2026-04-24"
---

# Phase 02 Plan 03: Hospitality Rubric + features.ts + areas.json Populate Summary

Converted the user-frozen 55-candidate list into the three artifacts the scanner pipeline needs — the HUMAN-readable rubric (`HOSPITALITY-FLOW.md`), the MACHINE-readable typed feature array (`features.ts`), and the populated scanner config (`areas.json` hospitality entry advanced from `pending`-null-seed to `pilot` with both paths wired). No homepage files touched (D-20 intact); no scanner internals touched (D-21 intact) — only `scanner/config/areas.json` (explicit configuration, not internals) and `scanner/tests/test_no_area_coupling.py` (test update required by the activation itself).

## What Shipped

### Task 1 — `analysis/hospitality/HOSPITALITY-FLOW.md` (220 lines, 55 rows)

Mirrored the shape of `analysis/homepage/HOME-PAGE.md`:
- Header with source, scope, 8 categories enumerated.
- Scoring-convention section documenting the binary `absent | full` presence scale and the tier → weight mapping (Tier 1 → TierId A with +1/−3; Tier 2 → C with +5/−2; Tier 3 → D with +8/−1).
- 8 category sections (`## 1. Package Discovery` through `## 8. Booking Confirmation`), each a table with columns: Feature Key, Name, Description, Tier, Origin, Evidence/Notes.
- Rows ordered Tier 1 → 2 → 3 within each category; inside each tier, stable in candidate-file order.
- Feature-count summary table and provenance cross-check command.
- Out-of-scope mirror of FEATURES-CANDIDATES.md (FCB deferred, Bayern/NBA/West Ham headless-blocked, Arsenal catalog-only).
- **No mention of the CLAUDE.md DO-NOT-TOUCH club anywhere in the rubric body** (only implicitly by omission).

Commit: `d091354`

### Task 2 — `analysis/hospitality/features.ts` (218 lines, 55 feat() calls) + `analysis/types.ts` extension

`features.ts` uses the exact `feat()` helper signature from `analysis/homepage/features.ts`. Every HOSPITALITY-FLOW.md row has a matching `feat(...)` call. IDs `HP01..HP55` in rubric order. `HP` prefix distinguishes from homepage IDs (H/R/M/C/T/…).

`types.ts` `CategoryId` union extended additively with 8 hospitality members:
- `package_discovery`, `pricing_transparency`, `food_beverage`, `match_selector_ux`, `enquiry_friction`, `premium_amenities`, `post_booking_comms`, `booking_confirmation`.

All 12 pre-existing homepage `CategoryId` members preserved unchanged.

`buildPresence(_key)` returns `'absent'` for every product ID — Phase 2 back-half will swap this for a JSON-backed implementation mirroring `analysis/homepage/features.ts`.

Commit: `8d40d73`

### Task 3 — `scanner/config/areas.json` populated + Phase-1 test updated

`scanner/config/areas.json` hospitality entry:
- `rubric_path`: `null` → `"analysis/hospitality/HOSPITALITY-FLOW.md"`
- `features_ts`: `null` → `"analysis/hospitality/features.ts"`
- `status`: `"pending"` → `"pilot"` (Phase 2 is a 5-club pilot per 02-CONTEXT; `"active"` from plan Task 3 is not a valid Status literal per `scanner/config/schema.py`).
- `evidence_dir` / `results_dir` / `flow_maps_dir` unchanged (user decision 1).

`scanner/tests/test_no_area_coupling.py`: renamed `test_phase1_areas_json_seed_matches_user_decision_1` → `test_areas_json_hospitality_entry_matches_user_decision_1` and updated its assertions to reflect the Phase-2 activation (the function's own docstring previously named "Phase 2's HOSP-02 plan" as the unlock point, so this change was explicitly anticipated by the Phase-1 author).

Commit: `5dacb13`

## Feature Count (by category)

Authoritative per the rubric body rows (verified via
`grep -c "^| \`[a-z_0-9]" analysis/hospitality/HOSPITALITY-FLOW.md` = 55).

| Category | Tier 1 | Tier 2 | Tier 3 | Total |
|----------|-------:|-------:|-------:|------:|
| 1. Package Discovery | 3 | 3 | 1 | 7 |
| 2. Pricing Transparency | 3 | 4 | 1 | 8 |
| 3. Food & Beverage | 4 | 4 | 0 | 8 |
| 4. Match Selector UX | 3 | 1 | 2 | 6 |
| 5. Enquiry Friction | 3 | 4 | 0 | 7 |
| 6. Premium Amenities | 2 | 3 | 5 | 10 |
| 7. Post-Booking Comms | 5 | 1 | 0 | 6 |
| 8. Booking Confirmation | 1 | 2 | 0 | 3 |
| **Total** | **24** | **22** | **9** | **55** |

**Candidate-file reconciliation:** `FEATURES-CANDIDATES.md` contains 55 unique feature keys (50-seed + 5-extensions = 55). User's plan prompt said "54 APPROVED candidates" — the off-by-one is a regex artefact: counting `^| \`[a-z_]+\`` excludes `enquiry_form_field_count_le_7` because it contains a digit `7`. Correct unique-key count from `[a-z_0-9]` pattern is 55. All 55 are preserved 1:1 in HOSPITALITY-FLOW.md and features.ts.

## Verification Results

| Check | Result |
|-------|--------|
| `test -f analysis/hospitality/HOSPITALITY-FLOW.md` | PASS |
| `test -f analysis/hospitality/features.ts` | PASS |
| `wc -l HOSPITALITY-FLOW.md` | 220 (≥ 120 required) |
| `wc -l features.ts` | 218 (≥ 80 required) |
| Rubric row count | 55 |
| feat() call count | 55 |
| Candidate unique-key count | 55 |
| 1:1 key mapping rubric ↔ candidate file (`comm -23`) | 0 lines (ZERO drift) |
| 1:1 key mapping features.ts ↔ rubric | 0 lines (ZERO drift) |
| `npx tsc --noEmit` | PASS |
| `npx next build` | PASS (all 33 /club/[id] static pages generated) |
| areas.json hospitality.rubric_path | `analysis/hospitality/HOSPITALITY-FLOW.md` |
| areas.json hospitality.features_ts | `analysis/hospitality/features.ts` |
| areas.json hospitality.status | `pilot` |
| `scanner/tests/test_areas_schema.py` | 10/10 PASS |
| `scanner/tests/` full suite | 167/167 PASS |
| D-20 `git diff master..HEAD -- analysis/homepage/` | empty (PASS) |
| D-21 `git diff` of my 3 commits — scanner internals | only `scanner/config/areas.json` + `scanner/tests/test_no_area_coupling.py` touched; zero `scanner/{vision,scoring,report,capture}/` files modified by me |

## types.ts Extension

`CategoryId` union extended additively with 8 new members:

```
+ 'package_discovery'
+ 'pricing_transparency'
+ 'food_beverage'
+ 'match_selector_ux'
+ 'enquiry_friction'
+ 'premium_amenities'
+ 'post_booking_comms'
+ 'booking_confirmation'
```

All 12 homepage members unchanged (`header_nav`, `hero`, `match_fixtures`, `content`, `tickets_hospitality`, `commerce`, `community`, `heritage`, `players_teams`, `partners_sponsors`, `personalization`, `footer_nav`).

## Discrepancies Between Candidate File and Rubric

Zero. All 55 unique candidate keys appear as exactly one rubric row each; no rename, no drop, no addition.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Plan Task 3 prescribed `status="active"` but schema forbids it**
- **Found during:** Task 3.
- **Issue:** `scanner/config/schema.py` defines `Status = Literal["pending", "pilot", "full", "deprecated"]`. Setting `"active"` would fail schema validation, fail all 10 `test_areas_schema.py` tests, and break `AreasConfig.model_validate_json()` at scanner startup.
- **Fix:** Set `status="pilot"` — matches Phase 2 scope ("5-club pilot" in 02-CONTEXT) and matches the existing `test_phase2_full_hospitality_entry_parses` fixture which already validated exactly this shape in anticipation.
- **Files modified:** `scanner/config/areas.json`.
- **Commit:** `5dacb13`.

**2. [Rule 3 — Blocking] Phase-1 seed assertion in test_no_area_coupling.py blocked activation**
- **Found during:** Task 3 full-suite run.
- **Issue:** `test_phase1_areas_json_seed_matches_user_decision_1` asserted `rubric_path is None`, `features_ts is None`, `status == "pending"`. Task 3's explicit purpose is to populate those fields — the test was the Phase-1 invariant waiting to be updated at Phase-2 activation (its docstring explicitly named "Phase 2's HOSP-02 plan" as the unlock point).
- **Fix:** Renamed the test to `test_areas_json_hospitality_entry_matches_user_decision_1` and rewired the assertions to lock in the Phase-2 populated form. Stable invariants (evidence_dir, results_dir user-decision-1 routing) preserved as assertions; Phase-1 null/pending assertions replaced with Phase-2 populated/pilot assertions. Added cross-check of `features_ts` against the rubric-path value for drift detection.
- **Files modified:** `scanner/tests/test_no_area_coupling.py`.
- **Commit:** `5dacb13`.
- **Result:** Full scanner pytest suite: 167 passed (was 166 passed + 1 obsolete; now 167 passed).

**3. [Rule 3 — Blocking] Candidate key count is 55, not 54 as plan prompt stated**
- **Found during:** Task 1 verification.
- **Issue:** User prompt said "54 APPROVED candidates"; running `grep -c "^| \`[a-z_]+\`" FEATURES-CANDIDATES.md` returns 54 because the `[a-z_]+` regex excludes keys containing digits (namely `enquiry_form_field_count_le_7`). Actual unique-key count using `[a-z_0-9]+` is 55.
- **Fix:** Authored rubric with 55 rows (1:1 port of all 55 candidate keys, including `enquiry_form_field_count_le_7`). Documented the reconciliation in rubric and in this summary.
- **Files affected:** rubric row count + feat() count.
- **Not a user-visible deviation** — no keys dropped or added; just a clarification that the regex in the plan's acceptance criteria undercounts by one.

## Known Stubs

`buildPresence(_featureKey)` in `analysis/hospitality/features.ts` returns `'absent'` for every product ID. This is intentional and explicitly tracked:

- **File:** `analysis/hospitality/features.ts` (lines 26–31)
- **Why:** Phase 2 front-half does not write results JSON. Back-half (plans 02-06+) will produce `analysis/hospitality/results/*.json` and the function will be swapped for a JSON-backed version mirroring `analysis/homepage/features.ts`.
- **Scoped to plan:** Yes (explicit in plan Task 2 Action + `<interfaces>` block).
- **Downstream impact:** none observed. `npx next build` passes. No Hospitality UI tab exists yet (back-half territory).

## Auth Gates

None triggered during this plan.

## Threat-Model Compliance

| Threat ID | Mitigation Status |
|-----------|-------------------|
| T-02-03-01 (rubric adds features not in candidates) | PASS — `comm -23 rubric-keys candidate-keys` emits ZERO lines |
| T-02-03-02 (features.ts renames key during port) | PASS — `comm -23 feat-keys rubric-keys` emits ZERO lines (55=55=55) |
| T-02-03-03 (areas.json populated before rubric exists) | PASS — Task ordering enforced; commits are T1=rubric → T2=features.ts → T3=areas.json; same plan |
| T-02-03-04 (features.ts exposes homepage key accidentally) | PASS — `HP` prefix on all IDs; candidate feature keys (e.g. `menu_preview`, `fixture_list_visible`) are hospitality-specific and do not collide with homepage IDs (H/R/M/C/T/…) |
| T-02-03-05 (types.ts extension reorders homepage categories) | PASS — `git show 8d40d73 -- analysis/types.ts` shows additive-only extension; all 12 homepage members preserved in order |

## Commits

| Task | Hash | Message |
|------|------|---------|
| 1 | `d091354` | `docs(02-03): author HOSPITALITY-FLOW.md rubric from frozen candidates` |
| 2 | `8d40d73` | `feat(02-03): port hospitality rubric to features.ts (55 features)` |
| 3 | `5dacb13` | `feat(02-03): activate hospitality entry in scanner/config/areas.json` |

## Self-Check: PASSED

- HOSPITALITY-FLOW.md exists (220 lines) — FOUND
- features.ts exists (218 lines) — FOUND
- types.ts extension present — FOUND (8 additive union members)
- areas.json populated + status=pilot — FOUND
- test_no_area_coupling.py Phase-2 assertion — FOUND
- Commit d091354 — FOUND
- Commit 8d40d73 — FOUND
- Commit 5dacb13 — FOUND
- All 167 scanner tests pass — CONFIRMED
- `npx tsc --noEmit` clean — CONFIRMED
- `npx next build` passes — CONFIRMED
- D-20 (analysis/homepage/ untouched by this plan's 3 commits) — CONFIRMED
- D-21 (scanner internals untouched by this plan's 3 commits) — CONFIRMED
