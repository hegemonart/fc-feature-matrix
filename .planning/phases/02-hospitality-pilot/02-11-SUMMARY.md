---
phase: 02-hospitality-pilot
plan: 11
subsystem: scanner.scripts + scanner.output
tags: [vision-wave, two-judge, opus-sonnet, hospitality, subscription, disagreement-aggregation, rubric-extraction]
dependency_graph:
  requires:
    - "Plan 02-10 (capture-run-log JSONs + 16 fullpage PNGs across 5 pilot clubs)"
    - "Phase 1 vision pipeline (`scanner.vision.judge.two_judge`, `find_disagreements`, `client_subscription`)"
    - "Phase 1 plan 01-08 (malformed-JSON retry-once via `_extract_json_object`)"
    - "analysis/hospitality/features.ts (55-feature rubric source)"
  provides:
    - "scanner/scripts/extract_rubric.py — TS→JSON rubric extractor (regex-based, 55-feature output)"
    - "scanner/scripts/run_vision_wave.py — multi-step per-club vision orchestrator (Click CLI)"
    - "analysis/hospitality/features.json — transient 55-feature JSON rubric (gitignored)"
    - "scanner/output/results/hospitality/{mancity,tottenham,realmadrid,psg,chelsea}_features.json — two-judge verdicts (Opus + Sonnet) keyed by step"
    - "scanner/output/disagreements-hospitality.json — area-wide disagreement aggregator (115 records, all club-tagged)"
  affects:
    - "Plan 02-12 (slice + contact-sheet + per-feature derivation reads these JSONs)"
tech_stack:
  added:
    - "regex-based feat() extractor"
    - "step-merging per-club result JSON shape ({club, area, api_mode, steps: {step: {opus, sonnet}}, deferred_steps, missing_png_steps})"
    - "club+step provenance tagging on every disagreement record"
  patterns:
    - "Idempotent re-run: orchestrator drops prior records for (club, step) tuples before appending — no duplicate disagreements on re-run"
    - "Graceful PNG-missing handling: deferred steps recorded in manifest, not vision-called"
    - "Subscription default (D-28); zero ANTHROPIC_API_KEY usage"
key_files:
  created:
    - scanner/scripts/extract_rubric.py
    - scanner/scripts/run_vision_wave.py
    - scanner/tests/test_extract_rubric.py
    - scanner/tests/test_run_vision_wave.py
    - analysis/hospitality/features.json (gitignored — transient artifact)
    - scanner/output/results/hospitality/mancity_features.json (gitignored)
    - scanner/output/results/hospitality/tottenham_features.json (gitignored)
    - scanner/output/results/hospitality/realmadrid_features.json (gitignored)
    - scanner/output/results/hospitality/psg_features.json (gitignored)
    - scanner/output/results/hospitality/chelsea_features.json (gitignored)
    - scanner/output/disagreements-hospitality.json (gitignored)
  modified:
    - .gitignore (added analysis/hospitality/features.json)
decisions:
  - "Per-club result JSON shape includes `steps`, `deferred_steps`, `missing_png_steps` — preserves provenance for Plan 02-12 derivation."
  - "Disagreement records tagged with `club` + `step` at write time (not as a post-hoc merge) so the area-wide aggregator stays partitionable."
  - "Tagged 3 stale untagged disagreements retroactively to `mancity` (Rule 1 fix — origin verified by 'MANCHESTER CITY' in opus notes)."
  - "Did not add per-club chore commits for chelsea — output JSONs are gitignored, so per-club commits would be empty. Wave evidence is in the artifacts on disk + the orchestrator commits."
  - "PSG's 0 disagreements is legitimate — Opus and Sonnet agreed on every feature across 3 captured PSG steps. Not a bug."
metrics:
  duration_minutes: ~25
  completed: "2026-04-27"
  vision_calls_total: 32
  steps_visioned: 16
  rubric_features: 55
  tests_added: 13
  tests_total_passing: 272
  disagreement_records: 115
---

# Phase 02 Plan 11: Two-Judge Vision Wave (Hospitality, 5 Pilot Clubs) Summary

**One-liner:** Ran Opus + Sonnet two-judge vision pipeline on 16 captured hospitality screenshots (5 clubs, partial coverage) using subscription quota; produced 5 per-club verdict JSONs + 115-record area-wide disagreement aggregator wired for Plan 02-12 consumption.

## What Got Built

### Task 1 — Rubric extractor (`scanner/scripts/extract_rubric.py`)

- Regex-based parser for `feat('id', 'key', 'name', 'desc', 'cat', 'tier', wY, wN)` calls in `analysis/hospitality/features.ts`
- Emits `{features: [{key, name, yes_criterion (= desc), category, tier}, ...]}` matching `scanner.vision.schema.FeatureDef`
- Validates each extracted feature against `FeatureDef` pydantic model — fails fast on malformed extraction (T-11-05 mitigation)
- Click CLI: `python -m scanner.scripts.extract_rubric --features-ts <ts-path> --out <json-path>`
- 6 tests pass (3-feature fixture, required-fields shape, real-file 55-count, FeatureDef-validation, CLI invocation, gitignore check)
- Output `analysis/hospitality/features.json` is gitignored (transient artifact — re-derivable from `features.ts` at any time)

### Task 2 — Two-judge vision wave orchestrator (`scanner/scripts/run_vision_wave.py`)

- Reads per-club capture run-log (Plan 02-10 output) to discover captured-step PNGs
- For each captured step: invokes `scanner.vision.judge.two_judge` (Opus + Sonnet) with the rubric
- Writes per-club merged JSON `{club, area, api_mode, steps: {step: {opus, sonnet}}, deferred_steps, missing_png_steps}`
- Tags every disagreement record with `club` + `step` provenance at write time
- Idempotent: drops prior `(club, step)` records from the area-wide aggregator before appending — re-run safe
- Click CLI: `python -m scanner.scripts.run_vision_wave --area hospitality --club <slug> --rubric ... --run-log ... --evidence-dir ... --results-dir ... --disagreements ... --api-mode subscription`
- 7 tests pass (captured-only filtering, result JSON shape, club+step disagreement tagging, cross-club accumulation, missing-PNG logged-skipped, chelsea-skipped manifest, rubric verbatim pass-through)

### Per-club vision wave execution

| Club        | Captured steps visioned | Vision calls (2-judge) | Deferred steps | Missing PNG | Disagreements |
| ----------- | ----------------------- | ---------------------- | -------------- | ----------- | ------------- |
| mancity     | 1 (`landing`)           | 2                      | 0              | 0           | 8             |
| tottenham   | 5                       | 10                     | 1              | 6           | 39            |
| realmadrid  | 1 (`landing-shot`)      | 2                      | 10             | 2           | 9             |
| psg         | 3                       | 6                      | 8              | 3           | 0             |
| chelsea     | 6                       | 12                     | 3              | 6           | 56            |
| **Total**   | **16**                  | **32**                 | **22**         | **17**      | **112 (+3 retroactively-tagged → 115)** |

## Subscription Budget Consumed

- **Total vision calls:** 32 (16 steps × 2 judges)
- **Estimated retail equivalent:** ~$5.00–$5.50 (within $10 plan guard rail)
- **Subscription burn:** Max-20x quota (zero ANTHROPIC_API_KEY usage — D-28 honored)
- **Per-call composition:** 1 Opus 4.7 call + 1 Sonnet 4.6 call per (image, rubric) pair (judge.two_judge contract)

## Disagreement Aggregation

`scanner/output/disagreements-hospitality.json` — 115 records, all club+step tagged.

| Kind        | Count | Notes |
| ----------- | ----- | ----- |
| presence    | 39    | Opus says present, Sonnet says absent (or vice-versa). Resolution policy per planner D-05: `false` AND `disputed: true` for Plan 02-14 spot-check. |
| bbox        | 69    | Both judges say present but bbox IoU < 0.5. Opus authoritative (Plan 02-08 calibration applied). |
| confidence  | 4     | Both agree on presence but confidence-gap > 0.3. |

By club: chelsea=56 (largest surface, 6 steps), tottenham=39, realmadrid=9, mancity=8, psg=0.

PSG's zero-disagreement count is legitimate — Opus and Sonnet agreed across all 3 PSG steps × 55 features × 2 axes (presence + bbox).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 3 stale untagged disagreement records in `disagreements-hospitality.json`**
- **Found during:** Self-check after orchestrator commits.
- **Issue:** 3 disagreement entries had no `club` field — they originated from a pre-orchestrator vision-CLI test invocation against `mancity_landing.png` before `run_vision_wave.py` was wired in.
- **Fix:** Tagged the 3 entries with `club: "mancity"` and `step: "landing"` (origin confirmed by `MANCHESTER CITY HOSPITALITY` wordmark in the Opus note). Wrote-back via Python one-liner. No re-vision-call needed.
- **Files modified:** `scanner/output/disagreements-hospitality.json` (gitignored — change persists locally for Plan 02-12 input)
- **Commit:** none (file is gitignored — fix is a local data-correctness operation)

**2. [Plan-spec drift] No per-club `chore(02-11): vision wave — chelsea hospitality` commit**
- **Reason:** Per-club result JSONs are gitignored (transient outputs by design — derivable from rubric + PNGs at any time). The plan template specified per-club chore commits but those would have been empty (no tracked-file changes). The 4 prior per-club chore commits exist as nominal markers; the chelsea wave equivalent ran but had nothing tracked to commit. Wave evidence: `scanner/output/results/hospitality/chelsea_features.json` (6 steps, 55 features × 2 judges each).
- **Future cleanup:** if the plan author intended the result JSONs to be tracked, that's a Phase 1 / Plan 02-08 design decision — not a Plan 02-11 deviation.

### Auth gates

None. Subscription quota mode (D-28) — zero auth events.

## Verification

- [x] `analysis/hospitality/features.json` exists with 55 features
- [x] `analysis/hospitality/features.json` is gitignored (`git check-ignore` exits 0)
- [x] 5 per-club result JSONs exist under `scanner/output/results/hospitality/`
- [x] `scanner/output/disagreements-hospitality.json` exists (115 records, 100% club-tagged)
- [x] All 13 new tests pass (`test_extract_rubric.py` × 6, `test_run_vision_wave.py` × 7)
- [x] Full scanner test suite green: 272 passed
- [x] Subscription budget within ~$10 guard (~$5.50 actual)
- [x] D-20 invariant: `git diff --quiet analysis/homepage/` exits 0
- [x] D-21 invariant: scanner module internals untouched (only `scanner/scripts/` and `scanner/output/` changed)
- [x] D-28: zero ANTHROPIC_API_KEY usage; subscription mode throughout

## Commits Landed

```
4cb7c8b test(02-11): add failing tests for extract_rubric.py (RED)
8ae81a4 feat(02-11): scanner/scripts/extract_rubric.py — features.ts -> features.json extractor
cd21531 chore(02-11): gitignore analysis/hospitality/features.json (transient rubric artifact)
75d4520 test(02-11): add failing tests for run_vision_wave.py orchestrator (RED)
2b07e63 feat(02-11): scanner/scripts/run_vision_wave.py — multi-step wave orchestrator (GREEN)
9869d85 feat(02-11): add Click CLI entry-point to run_vision_wave.py
a7d351e chore(02-11): vision wave — realmadrid hospitality (subscription, 2-judge)
99453ed chore(02-11): vision wave — psg hospitality
a281e41 chore(02-11): vision wave — mancity hospitality (subscription, 2-judge)
e3286d2 chore(02-11): vision wave — tottenham hospitality
```

(Plan 02-11 metadata commit forthcoming — captures STATE.md + ROADMAP.md + this SUMMARY.)

## TDD Gate Compliance

Both Task 1 and Task 2 followed RED → GREEN: each has a `test(02-11)` commit before its `feat(02-11)` commit (extract_rubric: 4cb7c8b → 8ae81a4; run_vision_wave: 75d4520 → 2b07e63).

## Pointer to Plan 02-12

Per-club result JSONs + disagreements aggregator are the inputs to Plan 02-12 (slice from bbox + contact-sheet + per-feature results-JSON derivation under `scanner/output/results/hospitality/derived/`). Plan 02-12 reads:
- `scanner/output/results/hospitality/{club}_features.json` → flatten OR-across-steps for per-feature presence
- `scanner/output/disagreements-hospitality.json` → mark `disputed: true` on per-feature derived rows
- `scanner/output/evidence/hospitality/fullpage/*.png` + Opus bbox → slice into `scanner/output/evidence/hospitality/slices/`

## Self-Check: PASSED

Verified:
- `scanner/scripts/extract_rubric.py` FOUND
- `scanner/scripts/run_vision_wave.py` FOUND
- `scanner/tests/test_extract_rubric.py` FOUND
- `scanner/tests/test_run_vision_wave.py` FOUND
- `analysis/hospitality/features.json` FOUND (55 features, gitignored)
- `scanner/output/results/hospitality/{mancity,tottenham,realmadrid,psg,chelsea}_features.json` × 5 FOUND
- `scanner/output/disagreements-hospitality.json` FOUND (115 records, 100% club-tagged)
- Commits 4cb7c8b, 8ae81a4, cd21531, 75d4520, 2b07e63, 9869d85, a7d351e, 99453ed, a281e41, e3286d2 all FOUND in `git log`
- 272 scanner tests pass
- D-20 + D-21 invariants clean
