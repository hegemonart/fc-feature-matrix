---
phase: 01-flow-automation-layer
plan: 05
subsystem: scanner.report + scanner.scoring
tags: [jinja2, html, contact-sheet, nodejs, scoring, area-parameterized]

dependency_graph:
  requires:
    - "Plan 02 (Wave 1): scanner.vision.schema — FeatureDef, FeatureVerdict, JudgeResponse"
    - "Plan 02 (Wave 1): scanner.config.schema (AreaEntry, AreasConfig) — shape for areas.json"
    - "Plan 04 (Wave 3): dual-backend vision produces JudgeResponse that feeds the contact sheet"
  provides:
    - "scanner.report.contact_sheet.render_contact_sheet(area, rubric, judge_responses, evidence_dir, output_path) -> Path"
    - "scanner/report/templates/contact_sheet.html.j2 — dark-theme HTML with :target lightbox, grid layout, red-border absent cells"
    - "scanner/scoring/recalculate.js — Node port of analysis/homepage/crosscheck/recalculate-scores.js with --area flag"
    - "scanner/config/areas.json — Phase-1 empty-hospitality seed (D-25)"
  affects:
    - "Plan 07 (CLI) invokes render_contact_sheet after a run; passes evidence_dir + output path"
    - "Plan 08 (dry-run) renders the contact sheet for the single-club 3-feature Phase-1 flow"
    - "Phase 2 (hospitality rollout) populates areas.hospitality.features_ts + rubric_path; recalculate.js then runs the real rescore path"

tech_stack:
  added:
    - "commander>=12.1 (package.json dep; unused in Phase 1 tests — built-in arg parsing covers all 6 cases)"
  patterns:
    - "Pure-function renderer: no network, no shared state, no touching of analysis/ — just (inputs) -> HTML string -> disk"
    - "Jinja2 select_autoescape(['html','htm','xml','j2']) for XSS safety at the template boundary (T-05-01)"
    - "CSS-only :target lightbox — zero JS, zero external assets (research §5.3)"
    - "Phase-1 empty-seed guard: recalculate.js reads cfg.features_ts === null and early-exits 0 with informative message before touching any file (D-25 gate, D-24 invariant)"
    - "Verbatim port with thin wrapper: rescoreArea(resultsDir, weights) keeps the homepage crosscheck body intact, only path-resolution moves to main()"
    - "node:test (built-in) for zero-dep JS test suite — no npm install required to run the 6-case suite"

key_files:
  created:
    - path: scanner/report/templates/contact_sheet.html.j2
      role: "Jinja2 template — 53 lines, inline CSS, grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)), red-border absent, :target lightbox"
    - path: scanner/report/contact_sheet.py
      role: "render_contact_sheet public API; _build_feature_rows() helper turns dict[str, dict[str, JudgeResponse]] into per-feature rows for the template"
    - path: scanner/scoring/recalculate.js
      role: "Area-parameterized score recalc; empty-seed guard; exports main/parseWeights/rescoreArea for importability"
    - path: scanner/scoring/recalculate.test.js
      role: "6 node:test cases: empty-seed, unknown-area, missing-arg, importable, populated-path (os.tmpdir fixtures), D-24 invariant"
    - path: scanner/scoring/package.json
      role: "commander dep declared; `npm test` -> node --test recalculate.test.js"
    - path: scanner/config/areas.json
      role: "Phase-1 empty-hospitality seed per D-25 (evidence_dir + results_dir set, rubric_path/features_ts null, status pending)"
  modified:
    - path: scanner/tests/test_contact_sheet.py
      change: "Replaced Plan-01 docstring stub with 8 pytest cases covering all 6 plan behaviors + :target anchor + XSS autoescape"

decisions:
  - id: D-05-1
    text: "Template class switch rewritten as `{% if %}<div class='thumb'>{% else %}<div class='thumb absent'>` instead of `<div class='thumb{% if not %} absent{% endif %}'>`. Plan acceptance requires the literal string `thumb absent` be greppable in the *.j2 file. The if/else spelling satisfies the grep while rendering identical HTML. No behavioural change."
  - id: D-05-2
    text: "Hand-rolled --area argv parser instead of requiring commander. The test suite uses only node:test/built-ins so tests run without `npm install`. commander stays in package.json for Phase 2+ CLI polish (subcommands, --dry-run, etc.)."
  - id: D-05-3
    text: "Phase 1 contact sheet uses the OPUS verdict for thumb display (D-27..29: Opus 4.7 returns 1:1 bbox coords; Sonnet 4.6 needs DPR denormalisation). Disagreements between judges are surfaced separately in disagreements-{area}.json, not inline in the contact sheet."

metrics:
  duration: "~40 min"
  completed: "2026-04-24"
  tasks_completed: 2
  files_created: 7
  files_modified: 1
  commits:
    - "7ac8555 test(01-05): Task 1 RED — failing tests for contact_sheet render"
    - "3aae534 feat(01-05): Task 1 GREEN — Jinja2 contact sheet renderer"
    - "543ed96 test(01-05): Task 2 RED — failing tests for recalculate.js port"
    - "debd21c feat(01-05): Task 2 GREEN — recalculate.js --area port + package.json"
---

# Phase 01 Plan 05: Report and Scoring Summary

Two-module delivery: a pure-function Jinja2 contact-sheet renderer that visualises dual-judge verdicts with a dark-theme grid and CSS-only `:target` lightbox, and an area-parameterized Node port of the homepage scoring script that early-exits on the Phase-1 empty-seed and never mutates `analysis/` (D-24 invariant verified by a dedicated test).

## What Shipped

### Report module (`scanner/report/`)

**`contact_sheet.html.j2` — 53 lines.** Dark-theme self-contained HTML. One `<div class="feature">` block per rubric entry, a CSS grid (`grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))`) of thumbnails per feature, `thumb absent` red-border cells for `present: false` verdicts, pure-CSS `:target` lightbox for click-to-zoom. No external assets; no JavaScript.

**`contact_sheet.py` — 123 lines.** Single public function:

```python
render_contact_sheet(area, rubric, judge_responses, evidence_dir, output_path) -> Path
```

- Uses `jinja2.Environment(loader=FileSystemLoader(...), autoescape=select_autoescape(['html','htm','xml','j2']))` — XSS mitigation T-05-01.
- Consumes opus verdicts for thumb display (D-27..29 1:1 coords); sonnet data is present in the input shape for Phase 2 but ignored by the renderer.
- Pure function; writes atomically via `Path.write_text` after `mkdir(parents=True, exist_ok=True)`.

### Scoring module (`scanner/scoring/`)

**`recalculate.js` — 220 lines.** Port of `analysis/homepage/crosscheck/recalculate-scores.js`:

| Source constant | Ported to |
|-----------------|-----------|
| `ROOT = path.resolve(__dirname, '..')` (hard-coded to `analysis/homepage/`) | Resolved from `areas.json[area]` in `main()` |
| `RESULTS_DIR = path.join(ROOT, 'results')` | `path.join(repoRoot, cfg.results_dir)` |
| `FEATURES_TS = path.join(ROOT, 'features.ts')` | `path.join(repoRoot, cfg.features_ts)` |
| Weight-parsing regex | **Copied verbatim** |
| Rescore loop / `_scores.json` / `_aggregate.json` regeneration | **Copied verbatim**, refactored into `rescoreArea(resultsDir, weights)` |

Phase-1 empty-seed guard: when `cfg.features_ts === null || cfg.rubric_path === null`, the script logs `Area '...' not yet populated (features_ts/rubric_path=null) — skipping score computation (Phase 2 gate).` and exits 0. Because this path short-circuits before any write, running on the Phase-1 areas.json cannot mutate `analysis/` (test-verified — `phase-1 run does not mutate analysis/ (D-24)`).

**Exit codes:** `0` success/empty-seed-skip, `1` unknown area, `2` missing `--area`, `3` areas.json missing, `4` features.ts missing, `5` results_dir missing.

**`package.json` — 13 lines.** Declares `commander ^12.1.0` for future CLI polish; current tests use built-ins only so `npm install` is not required.

**`recalculate.test.js` — 189 lines, 6 cases.** Uses `node:test` + `node:child_process`:
1. Phase-1 empty-seed exits 0 with "not yet populated".
2. Unknown area exits 1, stderr mentions the area.
3. Missing `--area` exits non-zero with usage message.
4. Script importable without side-effects (`main` is a function).
5. Populated path: builds a throwaway repo under `os.tmpdir()` with `scanner/config/areas.json`, `analysis/demo/features.ts`, `analysis/demo/results/{alpha,beta}.json`; copies the script into the tmp tree; asserts the output includes `scores computed for 2 clubs` and that `alpha.total_score === 5`, `beta.total_score === 2`.
6. D-24 invariant: snapshots `git status --porcelain analysis/` before + after the Phase-1 run; the two must be identical.

### Config

**`scanner/config/areas.json` — 10 lines.** Phase-1 empty-hospitality seed (per D-25):

```json
{
  "hospitality": {
    "evidence_dir": "scanner/output/evidence/hospitality/",
    "results_dir": "scanner/output/results/hospitality/",
    "rubric_path": null,
    "features_ts": null,
    "flow_maps_dir": null,
    "status": "pending"
  }
}
```

Validates cleanly against the Plan-02 `AreasConfig` schema (the `test_phase1_empty_hospitality_seed_parses` test in `scanner/tests/test_areas_schema.py` covers this exact shape).

## Tests

| Suite | Cases | Result |
|-------|-------|--------|
| `scanner/tests/test_contact_sheet.py` | 8 | 8 pass |
| `scanner/scoring/recalculate.test.js` (node --test) | 6 | 6 pass |
| Full scanner pytest (`scanner/tests/`) | 111 | 111 pass (no regressions) |

## Plan-level Verification

| Check | Command | Result |
|-------|---------|--------|
| pytest renderer | `pytest scanner/tests/test_contact_sheet.py -v` | exit 0, 8 passed |
| node scoring | `node --test scanner/scoring/recalculate.test.js` | exit 0, 6 passed |
| D-24 invariant | `git diff --quiet analysis/` | exit 0 (analysis/ untouched) |
| autoescape in renderer | `grep -q autoescape scanner/report/contact_sheet.py` | match |
| "not yet populated" guard | `grep -q 'not yet populated' scanner/scoring/recalculate.js` | match |

## Deviations from Plan

**None.** No Rule 1/2/3/4 auto-fixes were needed inside the Task 1 or Task 2 scopes.

One note on the plan's acceptance-criterion wording:

- **`grep -c "thumb absent" scanner/report/templates/contact_sheet.html.j2` ≥ 1.**  My first template draft wrote the absent class inline as `{% if not club.present %} absent{% endif %}` which rendered correctly but did not contain the literal substring `thumb absent`. Rewrote as an `{% if %}<div class="thumb">{% else %}<div class="thumb absent">` branch (D-05-1). The rendered HTML is identical. This is a purely mechanical adjustment to meet the literal acceptance criterion — not a behavioural change.

## Deferred Items (out of scope for Plan 01-05)

Logged in `.planning/phases/01-flow-automation-layer/deferred-items.md`:

- **CLAUDE.md contains stray merge-conflict markers** (`<<<<<<< Updated upstream` / `=======` / `>>>>>>> Stashed changes` at lines ~100 and ~121). Pre-existing — present before this plan began. Not touched.

## Notes for Downstream Plans

- **Plan 07 (CLI):** Load `scanner/config/areas.json` via `AreasConfig.model_validate(json.loads(p.read_text()))`. After a run, call `render_contact_sheet(area, rubric, judge_responses, evidence_dir, output_path=scanner/output/contact-report-{area}.html)`.
- **Plan 08 (dry-run):** Import `render_contact_sheet` directly. The 3-feature dummy rubric in `scanner/tests/fixtures/dummy-hospitality-rubric.json` maps directly to `list[FeatureDef]`.
- **Phase 2 (hospitality rollout):** Flip `areas.hospitality.features_ts` and `rubric_path` from `null` to real paths; `recalculate.js --area hospitality` will then exercise the populated path instead of the empty-seed skip. No other change needed on the scanner side.

## Self-Check: PASSED

Files verified to exist and commits verified in git log:

- FOUND: `scanner/report/templates/contact_sheet.html.j2`
- FOUND: `scanner/report/contact_sheet.py`
- FOUND: `scanner/scoring/recalculate.js`
- FOUND: `scanner/scoring/recalculate.test.js`
- FOUND: `scanner/scoring/package.json`
- FOUND: `scanner/config/areas.json`
- FOUND: `scanner/tests/test_contact_sheet.py` (256 lines, 8 test defs)
- FOUND: commit 7ac8555 (RED Task 1)
- FOUND: commit 3aae534 (GREEN Task 1)
- FOUND: commit 543ed96 (RED Task 2)
- FOUND: commit debd21c (GREEN Task 2)
- FOUND: `git diff --quiet analysis/` exits 0 (D-24 OK)
