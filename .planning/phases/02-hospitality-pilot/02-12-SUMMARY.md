---
phase: 02-hospitality-pilot
plan: 12
subsystem: scanner.scripts + scanner.cli + scanner.report + analysis/hospitality
tags: [slice, contact-sheet, results-derivation, scoring, two-judge-resolution, hospitality]
dependency_graph:
  requires:
    - "Plan 02-11 (5 per-club two-judge result JSONs at scanner/output/results/hospitality/)"
    - "Plan 02-08 (areas.json bbox_mode + features_evidence_dir schema field)"
    - "Plan 01-08 (slice CLI + contact-sheet renderer + scoring pipeline)"
  provides:
    - "scanner/scripts/derive_results_json.py — Click CLI: judge-resolution + step OR-flattening + flat-presence-map emit"
    - "analysis/hospitality/evidence/features/{club}_{feature_key}.png — 25 PIL crops across 5 pilot clubs (canonical D-01 path)"
    - "analysis/hospitality/results/{club}.json — 5 per-club flat presence maps (55 features each) with disputed_features + skipped_features + total_score"
    - "analysis/hospitality/results/_scores.json + _aggregate.json — recalculate.js outputs"
    - "scanner/output/contact-report-hospitality.html — 67KB Jinja2 contact sheet (55 features × 5 clubs grid)"
  affects:
    - "Plan 02-13 (UI tab consumes analysis/hospitality/results/*.json — same shape as analysis/homepage/results/)"
    - "Plan 02-14 (user gate review reads contact-sheet HTML + disputed_features for spot-check)"
tech_stack:
  added:
    - "Areas.json schema fields: features_evidence_dir + scoring_results_dir (additive, default-fallback to legacy paths)"
    - "Click CLI --step '*' multi-step iterator (slice command)"
    - "Disagreement-resolution policy: agree→Opus value, disagree→False+disputed flag (sticky across step OR-flattening)"
  patterns:
    - "D-21 deviation: signature-additive config wiring in scanner/cli.py + scanner/report/contact_sheet.py + scanner/scoring/recalculate.js (mirrors Plan 02-08 + Plan 01-08 pattern; default-fallback preserves Phase-1 behavior)"
    - "Backslash-aware quoted-string regex for features.ts feat() parser (handles parens in description fields)"
    - "Plan-02-11 multi-step shape ↔ Phase-1 single-step shape tolerance in cli.py:report (OR-merge across steps)"
key_files:
  created:
    - scanner/scripts/derive_results_json.py
    - scanner/tests/test_derive_results_json.py
    - scanner/tests/test_slice_cli_features_evidence_dir.py
    - analysis/hospitality/evidence/features/* (25 PNGs)
    - analysis/hospitality/results/mancity.json
    - analysis/hospitality/results/tottenham.json
    - analysis/hospitality/results/realmadrid.json
    - analysis/hospitality/results/psg.json
    - analysis/hospitality/results/chelsea.json
    - analysis/hospitality/results/_scores.json
    - analysis/hospitality/results/_aggregate.json
    - scanner/output/contact-report-hospitality.html
  modified:
    - scanner/cli.py (slice_cmd + report_cmd extended; D-21 deviation, additive)
    - scanner/config/areas.json (features_evidence_dir + scoring_results_dir set for hospitality)
    - scanner/config/schema.py (AreaEntry.scoring_results_dir field — Plan 02-12 additive)
    - scanner/scoring/recalculate.js (regex fix for paren-descs + scoring_results_dir support — D-21 deviation)
    - scanner/report/contact_sheet.py (additive features_evidence_dir + crop_rel_template params — D-21 deviation, default preserves Phase-1)
    - scanner/tests/test_dry_run.py (assertion updated to canonical analysis/ path — Rule 1 fix)
    - .gitignore + scanner/.gitignore (whitelist contact-report-*.html)
decisions:
  - "Disagreement resolution policy is per-step deterministic: agree → Opus value, disagree → False + sticky disputed flag. Multi-step OR-flattening means an earlier-step agree-true wins over a later-step disagreement, but the disputed flag remains sticky for Plan 02-14 reviewer surfacing."
  - "Slice canonical path = analysis/<area>/evidence/features/ (D-01). The Phase-1 scanner/output/evidence/<area>/features/ remains the default fallback when features_evidence_dir is unset."
  - "scoring_results_dir is a new additive areas.json field; recalculate.js prefers it when set, falling back to results_dir. This separates vision-intermediate JSONs (steps/opus/sonnet shape) from canonical flat results (features/disputed/skipped shape)."
  - "report CLI tolerates BOTH per-club JSON shapes (Phase-1 single-step AND Plan-02-11 multi-step) so contact sheets render across the seam."
metrics:
  duration_minutes: ~50
  completed: "2026-04-28"
  tests_added: 16
  tests_total_passing: 288
  slice_count: 25
  contact_sheet_kb: 67
  result_jsons: 5
  scored_clubs: 5
---

# Phase 02 Plan 12: Slice + Contact Sheet + Results Derivation + Score Recompute Summary

**One-liner:** Sliced 25 per-feature PIL crops from Plan-02-11 two-judge verdicts to the canonical analysis/ tree, derived 5 per-club flat-presence-map results JSONs (with disputed-feature flagging), rendered a 55×5 contact-sheet HTML, and scored all 5 pilot clubs against the 55-feature hospitality rubric — all without modifying scanner/vision/, scanner/capture/, or homepage analysis (D-20 + D-21 honored except for the documented additive deviations).

## What Got Built

### Task 1 — Slice CLI canonical path + multi-step iteration

**`scanner/cli.py:slice_cmd`** extended (additive, signature-preserving):
- Reads optional `features_evidence_dir` from the area config; falls back to `evidence_dir/features/`.
- Accepts `--step '*'` to iterate every captured step in the Plan-02-11 result-JSON `steps` map. Backwards-compatible with the Phase-1 single-step shape.
- Multi-step deduplication: when a feature appears in multiple steps, slice from the first step where its bbox is non-null.

**`scanner/config/areas.json`** hospitality entry:
- `features_evidence_dir: "analysis/hospitality/evidence/features/"` (canonical D-01 path).

**`scanner/vision/slice.py`** is **NOT** modified — D-21 invariant honored at the math layer. Only call-site config wiring changed.

**Slicing run produced 25 PIL crops:**

| Club        | Slices | Captured steps |
| ----------- | -----: | -------------- |
| mancity     | 4 | landing |
| tottenham   | 10 | landing-shot, matchday-options-shot, premium-seats-detail-shot, match-selector-shot, enquiry-form-prefill-shot |
| realmadrid  | 3 | landing-shot |
| psg         | 0 | landing-shot, first-tier-shot, all-executive-club-shot (Opus reported 0 features present across all 3 steps) |
| chelsea     | 8 | landing-shot + 5 package-detail steps (paid-customer steps deferred per Plan 02-11) |
| **Total**   | **25** | |

On-disk size: 35 MB at `analysis/hospitality/evidence/features/`.

Out-of-bounds bboxes (15+ skips across all clubs) are recorded by `slice_feature` with a reason; the run continues. This matches the Phase-1 contract (T-12-04 mitigation).

### Task 2 — Derive results JSONs + render contact sheet + recompute scores

**`scanner/scripts/derive_results_json.py`** (197 lines, Click CLI):
- Reads Plan-02-11 `{steps: {step: {opus, sonnet}}}` JSON.
- Applies disagreement resolution per step (agree → Opus value; disagree → False + sticky disputed flag).
- OR-flattens across steps for the final per-feature presence boolean.
- Emits the canonical flat shape with `product_id` (recalculate.js compat) + `club_id` + `disputed_features` + `skipped_features` + `judge_agreement_rate` + `captured_steps` + `generated_at`.

**`scanner/cli.py:report`** extended:
- Tolerates both per-club JSON shapes (Phase-1 single-step + Plan-02-11 multi-step) via OR-merge across steps.
- Passes `features_evidence_dir` to `render_contact_sheet` so thumbnail hrefs point at the canonical analysis/ tree (computed via `os.path.relpath` — area-agnostic).

**`scanner/report/contact_sheet.py`** (signature-additive):
- `render_contact_sheet(features_evidence_dir=None)` — additive Path param.
- `_build_feature_rows(crop_rel_template=None)` — additive format-string param.
- Default `None` preserves Phase-1 path layout. No coupling to any specific area name (test_no_area_coupling green).

**`scanner/scoring/recalculate.js`** (D-21 deviation, additive):
- **Rule 1 fix:** the original `feat()` regex used `[^)]*` for the desc field, which truncated at the first `)` inside descriptions. 21 of 55 hospitality features have parens in their description (e.g. `dress_code_info: "Explicit per-tier dress code (smart, smart-casual, formal)"`). Replaced with a backslash-aware 6-quoted-string + 2-number pattern. Now parses 55/55.
- **Rule 3 additive config:** `cfg.scoring_results_dir || cfg.results_dir` — prefers the canonical analysis/ flat-results dir when set; falls back to `results_dir` for Phase-1 homepage compat.

### Per-club derived results (analysis/hospitality/results/{club}.json)

| Club        | Present | Disputed | Skipped | Captured steps | Judge agreement | Total score |
| ----------- | ------: | -------: | ------: | -------------: | --------------: | ----------: |
| tottenham   | 12 | 7 | 0 | 5 | 96.73% | **-57** (rank 1) |
| chelsea     | 8  | 9 | 0 | 6 | 92.12% | **-79** (rank 2) |
| realmadrid  | 6  | 3 | 0 | 1 | 94.55% | **-92** (rank 3) |
| mancity     | 5  | 0 | 0 | 1 | 100.00% | **-99** (rank 4) |
| psg         | 0  | 0 | 0 | 3 | 100.00% | **-125** (rank 5) |

Negative scores reflect minimal hospitality-feature presence in the pilot set — most Tier-1 features yield -3 when absent. Phase 2 surfaces presence; Plan 02-13 wires the UI tab; Plan 02-14 is the user gate.

`_skipped_features` is 0 across all clubs because the two-judge wave evaluated all 55 rubric features per captured step; even a single captured step yields verdicts for every feature.

### Contact sheet

`scanner/output/contact-report-hospitality.html` — 67 KB.
- 55 `<div class="feature">` blocks (one per rubric entry).
- 275 cells (55 × 5 clubs): 41 present + 234 absent.
- Thumbnail hrefs: `./../../analysis/hospitality/evidence/features/{club}_{feature_key}.png` (relative path computed via `os.path.relpath` — area-agnostic).
- Open command: `open scanner/output/contact-report-hospitality.html` or load in any browser.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] features.ts feat() regex truncated descriptions with parens (recalculate.js)**
- **Found during:** Task 2 — score recompute parsed only 34/55 hospitality features.
- **Issue:** The Phase-1 regex used `[^)]*` for the desc-field group, which stops at the first `)` inside the description text. 21 hospitality features have parens in their desc (e.g. `(smart, smart-casual, formal)`).
- **Fix:** Replaced the middle group with a 6-quoted-string + 2-number pattern using a backslash-aware string body `'(?:[^'\\]|\\.)*'`. Verified against `analysis/hospitality/features.ts` — 55/55 features now parsed.
- **Files modified:** `scanner/scoring/recalculate.js`
- **Commit:** 5415bdf

**2. [Rule 1 - Bug] cli.py:report failed on Plan-02-11 multi-step JSON shape**
- **Found during:** Task 2 — first invocation of `scanner report --area hospitality` raised `KeyError: 'opus'`.
- **Issue:** Phase-1 report code reads `data["opus"]`, but Plan-02-11 wave wrote `{steps: {step: {opus, sonnet}}}`.
- **Fix:** Added shape-detection branch + an OR-merge helper that flattens per-step verdicts before passing to the renderer. Phase-1 single-step shape still handled when `steps` key absent.
- **Files modified:** `scanner/cli.py`
- **Commit:** 7747807

**3. [Rule 1 - Bug] test_dry_run assertion expected legacy slice path**
- **Found during:** Full test run after committing `features_evidence_dir` config.
- **Issue:** The dry-run integration test copies the real `areas.json` into a tmp repo, so the new canonical path took effect — but the test assertion still pointed at `scanner/output/evidence/.../features/`.
- **Fix:** Updated the assertion to look at `analysis/hospitality/evidence/features/` AND added a guard that the legacy path is NOT populated.
- **Files modified:** `scanner/tests/test_dry_run.py`
- **Commit:** 8be03da

**4. [Rule 1 - Bug] Docstring example violated test_no_area_coupling**
- **Found during:** Full test run after committing contact_sheet.py changes.
- **Issue:** My initial docstring example referenced `analysis/hospitality/` literally — caught by the FLOW-02 invariant test that scans scanner/*.py for area-specific path strings.
- **Fix:** Genericized the docstring + comment to reference "the area's analysis evidence path" without naming any area.
- **Files modified:** `scanner/report/contact_sheet.py`
- **Commit:** 7747807 (folded with the report-CLI fix)

**5. [Rule 3 - Blocking] scoring required different path from vision intermediate JSONs**
- **Found during:** Task 2 — `scanner score --area hospitality` failed with `Cannot convert undefined or null to object` on `Object.entries(d.features)`.
- **Issue:** Vision intermediate JSONs (`scanner/output/results/<area>/<club>_features.json`) have shape `{steps: {step: {opus, sonnet}}}`; recalculate.js needs flat `{features: {key: bool}}`. Single `results_dir` field can't simultaneously serve both consumers.
- **Fix:** Added `scoring_results_dir` to AreaEntry + areas.json (hospitality → `analysis/hospitality/results/`). recalculate.js prefers it when set; falls back to `results_dir` for Phase-1 homepage compat. Default-additive — no behavior change for Phase-1 areas.
- **Files modified:** `scanner/config/schema.py`, `scanner/config/areas.json`, `scanner/scoring/recalculate.js`, `scanner/scripts/derive_results_json.py` (added `product_id` alias)
- **Commit:** 5415bdf

### D-21 deviation rationale (full audit)

The plan explicitly authorized "additive call-site config wiring" in `scanner/cli.py:slice_cmd`, mirroring the Plan 02-08 bbox_mode pattern. Plan 02-12 extends that pattern to:

1. **`scanner/cli.py:report`** — adds shape-tolerance + features_evidence_dir threading. Pure config-passing.
2. **`scanner/report/contact_sheet.py`** — adds `features_evidence_dir` + `crop_rel_template` params with default `None` preserving Phase-1 behavior. Signature-additive.
3. **`scanner/scoring/recalculate.js`** — adds `scoring_results_dir` preference with fallback. Plus Rule-1 regex correctness fix (the prior regex was straight-up broken on hospitality features).
4. **`scanner/config/schema.py`** — adds `scoring_results_dir: str | None = None` field. Pydantic-additive, default-None.

`scanner/vision/slice.py` (denormalise_bbox + slice_feature math), `scanner/capture/` (browser, banner_verify, cookie_strategies), and `scanner/scoring/recalculate.js`'s scoring/aggregation/output body are all **untouched** at the math/logic layer.

### Auth gates

None. Subscription wave (Plan 02-11) and local-only PIL/Jinja2/Node operations (Plan 02-12).

## Verification

- [x] 25 per-feature crops at `analysis/hospitality/evidence/features/`
- [x] 5 per-club result JSONs at `analysis/hospitality/results/{club}.json` (55 features each)
- [x] Contact sheet HTML renders without error (67 KB, 55 feature blocks, 41 thumbs + 234 absent placeholders)
- [x] `scanner score --area hospitality` exits 0 (55 features parsed, 5 clubs scored)
- [x] D-20: `git diff --quiet analysis/homepage/` exits 0
- [x] D-21: `scanner/vision/slice.py`, `scanner/capture/` untouched (other scanner module changes are documented additive deviations)
- [x] All 288 scanner tests pass (272 baseline + 8 slice + 8 derive)
- [x] Disputed-feature counts surfaced in result JSONs (mancity=0, tottenham=7, realmadrid=3, psg=0, chelsea=9 → total 19 disputed-feature flags for Plan 02-14 reviewer)

## Commits Landed

```
f13890f test(02-12): add failing tests for slice CLI features_evidence_dir + multi-step iteration (RED)
8be03da feat(02-12): slice CLI honors features_evidence_dir + iterates --step '*'
75b1aa5 chore(02-12): slice 5-club hospitality crops to analysis/hospitality/evidence/features/
26a699a test(02-12): add failing tests for derive_results_json (RED)
af88855 feat(02-12): scanner/scripts/derive_results_json.py — judge resolution + step flattening
7747807 feat(02-12): report CLI handles Plan-02-11 multi-step shape + features_evidence_dir
a2a995e chore(02-12): derive 5 pilot-club hospitality results JSONs at analysis/hospitality/results/
dcb43cc chore(02-12): render hospitality contact sheet (scanner report)
5415bdf feat(02-12): recalculate.js scores hospitality area + regex fix for paren-descs
afc1a08 chore(02-12): recompute hospitality scores (scanner score)
```

(Plan 02-12 metadata commit forthcoming — captures STATE.md + ROADMAP.md + this SUMMARY.)

## TDD Gate Compliance

Both Task 1 and Task 2 followed RED → GREEN cycle:
- Task 1: `f13890f test(02-12)` (RED, 6 failing) → `8be03da feat(02-12)` (GREEN, 8 passing)
- Task 2: `26a699a test(02-12)` (RED, 8 failing) → `af88855 feat(02-12)` (GREEN, 8 passing)

## Pointer to Plan 02-13 + 02-14

- **Plan 02-13 (UI tab unlock):** Reads `analysis/hospitality/results/{club}.json` — same shape as `analysis/homepage/results/*.json` (with `features` flat map + `total_score`). Add a `disputed_features` badge / banner in the UI for clubs with disputed flags.
- **Plan 02-14 (user gate):** Open `scanner/output/contact-report-hospitality.html` in browser. Spot-check the 41 present-thumb cells. Review the 19 disputed-feature flags across the 5 clubs (chelsea=9, tottenham=7, realmadrid=3) for any reviewer-overrides.

## Self-Check: PASSED

Verified via Read/Bash:
- `scanner/scripts/derive_results_json.py` FOUND
- `scanner/tests/test_derive_results_json.py` FOUND (8 tests pass)
- `scanner/tests/test_slice_cli_features_evidence_dir.py` FOUND (8 tests pass)
- `analysis/hospitality/evidence/features/` populated (25 PNGs)
- `analysis/hospitality/results/{mancity,tottenham,realmadrid,psg,chelsea}.json` × 5 FOUND with 55-feature `features` map + total_score
- `analysis/hospitality/results/_scores.json` + `_aggregate.json` FOUND
- `scanner/output/contact-report-hospitality.html` FOUND (67 KB, 55 feature blocks)
- All 10 commits FOUND in `git log`: f13890f, 8be03da, 75b1aa5, 26a699a, af88855, 7747807, a2a995e, dcb43cc, 5415bdf, afc1a08
- 288 scanner tests pass
- D-20 invariant clean: `git diff --quiet analysis/homepage/` exits 0
