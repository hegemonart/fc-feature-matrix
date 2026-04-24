---
phase: 01-flow-automation-layer
plan: 02
subsystem: scanner.schemas
tags: [pydantic, schema, contracts, dual-backend, vision, flow-map, areas-config]

dependency_graph:
  requires:
    - "Plan 01 (Wave 0): scanner package skeleton, pyproject with pydantic>=2.5, empty test scaffolds"
  provides:
    - "scanner.flow.schema: FlowMap, FlowStep, FormField"
    - "scanner.vision.schema: FeatureDef, FeatureVerdict, FeatureResult, JudgeResponse"
    - "scanner.config.schema: AreaEntry, AreasConfig (RootModel[dict[str, AreaEntry]])"
  affects:
    - "Plan 03 (capture) imports FlowStep for Playwright orchestration"
    - "Plan 04 (vision client Protocol) returns JudgeResponse from both backends"
    - "Plan 07 (CLI) loads areas.json via AreasConfig.model_validate"

tech_stack:
  added: []  # pydantic 2.13.3 was already in Plan 01 lockfile
  patterns:
    - "RootModel[dict[str, T]] for open-ended top-level JSON dicts (zero-migration forward compat)"
    - "Field(default_factory=list) over `= []` for list defaults (mutable-default trap)"
    - "Closed Literal unions encode business invariants at type level (D-16)"
    - "Field(ge, le) bounds reject out-of-range LLM output at parse time"
    - "tuple[float, float, float, float] | None for bbox (Pydantic v2 coerces list -> tuple)"

key_files:
  created:
    - path: scanner/flow/schema.py
      role: "Flow-map input contract; enforces D-15 (1-15 steps) and D-16 (closed action Literal)"
    - path: scanner/vision/schema.py
      role: "Two-judge vision output contract; identical shape for both backends (D-27..D-29)"
    - path: scanner/config/schema.py
      role: "areas.json contract; RootModel keyed by area name for Phase 3-8 extensibility"
  modified:
    - path: scanner/tests/test_flow_schema.py
      change: "10 tests covering D-15, D-16, form-fields, default-factory, round-trip"
    - path: scanner/tests/test_vision_schema.py
      change: "12 tests covering confidence bounds, notes cap, bbox coercion, FeatureDef permissive key, round-trip"
    - path: scanner/tests/test_areas_schema.py
      change: "10 tests covering Phase-1 seed, Phase-2 variant, multi-area dict shape, KeyError messaging"

decisions:
  - id: D-02-1
    text: "AreasConfig = RootModel[dict[str, AreaEntry]] (not named-field model). Adding an area in Phase 3-8 is a new JSON key — no schema migration. Honoring planner autonomous-decision #5."
  - id: D-02-2
    text: "`FeatureDef.key` has NO regex constraint at schema level (D-18). Non-snake_case keys parse successfully so runtime warnings handle casing, not load-time errors."
  - id: D-02-3
    text: "`confidence` bounds are strict (ge=0.0, le=1.0). Any clamping of LLM output happens in the Plan 04 client layer BEFORE model construction, not inside the schema via a validator."
  - id: D-02-4
    text: "`evidence_bbox` is tuple[float, float, float, float] | None. Pydantic v2 coerces JSON lists to tuples, so downstream code reliably gets tuples even though authors write lists."

metrics:
  duration: "~70 minutes"
  completed_date: "2026-04-24"
  tasks_planned: 3
  tasks_completed: 3
  tests_added: 32
  tests_passing: 32
  loc_added: 607  # 3 schema files + 3 test files
---

# Phase 01 Plan 02: Pydantic Schemas Summary

JSON contracts defined at every scanner boundary — flow-map input, dual-backend vision output, and areas.json config — with invariants (D-15 step bounds, D-16 closed action Literal) enforced at parse-time so malformed inputs fail fast with clear errors.

## What Landed

**Three schema modules, zero runtime dependencies beyond Pydantic v2:**

1. **`scanner/flow/schema.py`** (62 LOC) — `FlowMap`, `FlowStep`, `FormField`. `FlowStep.action` is `Literal["navigate", "click", "fill", "wait", "screenshot"]`; the closed union makes D-16 a type-level guarantee (no runtime check needed). `FlowMap.steps` uses `Field(min_length=1, max_length=15)` for D-15. `hide_selectors` uses `default_factory=list` to avoid the mutable-default trap.

2. **`scanner/vision/schema.py`** (78 LOC) — `FeatureDef`, `FeatureVerdict`, `FeatureResult`, `JudgeResponse`. `confidence` bounded [0.0, 1.0]; `notes` capped at 500 chars (mitigates threat T-02-04). `evidence_bbox: tuple[float, float, float, float] | None` — list→tuple coercion is automatic in Pydantic v2. `JudgeResponse.results: dict[str, FeatureVerdict]` is the exact shape BOTH vision backends will produce per D-27..D-29.

3. **`scanner/config/schema.py`** (47 LOC) — `AreaEntry`, `AreasConfig`. Top-level config is `RootModel[dict[str, AreaEntry]]` so Phase 3-8 areas drop in without schema migration. `.get(name)` raises `KeyError` with a sorted `known` list on miss. Status is the closed Literal `"pending" | "pilot" | "full" | "deprecated"` defaulting to `"pending"` for the Phase-1 empty-hospitality seed (D-25).

## Test Coverage

**32 tests total, 32 green, 0 skipped, 0 flaky.**

| File | Tests | Key coverage |
|------|-------|--------------|
| `test_flow_schema.py` | 10 | D-15 zero/16/exact-15 step boundaries, D-16 submit rejection, form-fields happy path + missing-selector error, `hide_selectors` default-factory isolation, round-trip `model_dump()` |
| `test_vision_schema.py` | 12 | Confidence above 1.0 / below 0.0 rejection, notes > 500 chars rejection, bbox list→tuple coercion, `present=False` with null bbox, empty `results` dict, FeatureDef permissive key (D-18), full round-trip |
| `test_areas_schema.py` | 10 | Phase-1 empty-hospitality seed (D-25), Phase-2 full variant, multi-area RootModel dict shape, missing `evidence_dir` / `results_dir` errors, bogus status rejection, `status` default-to-pending, optional paths default to None, `.get(unknown)` KeyError carries known-list, all four status literals accepted |

Running time: 0.25s for the combined suite. Coverage percentages not measured — `pytest-cov` is not in `scanner/pyproject.toml` optional-dependencies. Qualitative inspection: every line in each schema module is exercised by at least one test.

## Pydantic v2 Notes

- **`Field(min_length=1)` on list works.** Early draft of `test_flow_schema.py` had a helper bug (`steps or [default]` replaced empty lists) that masked the validator; fixed by switching to `if steps is None`. Important lesson for future test helpers: truthiness checks silently eat empty-but-valid inputs.
- **`RootModel[dict[str, T]]` is the idiomatic v2 replacement for `__root__: dict[...]`.** Access via `.root`. Subclasses can add methods (`.get(area)` here) without touching the `RootModel` generic.
- **List→tuple coercion is automatic for typed tuple fields.** `evidence_bbox: tuple[float, float, float, float]` parses a 4-element JSON array into a Python tuple, not a list — so consumers can rely on immutability without extra validators.
- **`notes: str = Field(max_length=500)` rejects at parse time.** Cleaner than a `@field_validator` for the same length check; sufficient for threat T-02-04.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `_valid_map(steps=[])` helper silently substituted a default valid step**

- **Found during:** Task 1, first GREEN-phase test run
- **Issue:** Helper used `steps or [_valid_step()]`; Python falsy-semantics on `[]` caused the empty list to be replaced, so `test_rejects_zero_steps` got a 1-step map and found no validation error.
- **Fix:** Switched to `if steps is None: steps = [_valid_step()]` in the helper; explicit empty lists now flow through to Pydantic.
- **Files modified:** `scanner/tests/test_flow_schema.py`
- **Commit:** bundled into Task 1 commit `35584f5`

**2. [Rule 3 - Blocking] Word "submit" in schema docstrings tripped the `grep -q 'submit' scanner/flow/schema.py` acceptance criterion**

- **Found during:** Task 1 acceptance-criteria verification
- **Issue:** The plan's criterion requires the literal word "submit" to have zero matches anywhere in `scanner/flow/schema.py` (not just outside the Literal union). The initial draft used "submit" in the module docstring and an inline comment to explain the D-16 invariant.
- **Fix:** Rephrased docstrings and comments to describe the closed-Literal invariant without naming the forbidden action — still documents D-16 clearly.
- **Files modified:** `scanner/flow/schema.py`
- **Commit:** bundled into Task 1 commit `35584f5`

No Rule 4 (architectural) escalations.

## Invariant Gate (D-24)

`git diff --quiet analysis/` exit 0 — no touch to `analysis/` (no scoring data, no rubric, no results modified). The scanner package is isolated per-D-24.

## Commits

| Hash      | Message                                                                 |
|-----------|-------------------------------------------------------------------------|
| `35584f5` | `feat(01-02): add FlowMap/FlowStep/FormField Pydantic schemas (Task 1)` |
| `dbdfe4b` | `feat(01-02): add FeatureDef/FeatureVerdict/JudgeResponse schemas (Task 2)` |
| `a015ec5` | `feat(01-02): add AreaEntry/AreasConfig Pydantic schemas (Task 3)`      |

## Self-Check: PASSED

- `scanner/flow/schema.py` exists — FOUND
- `scanner/vision/schema.py` exists — FOUND
- `scanner/config/schema.py` exists — FOUND
- `scanner/tests/test_flow_schema.py` populated (138 LOC, 10 tests) — FOUND
- `scanner/tests/test_vision_schema.py` populated (143 LOC, 12 tests) — FOUND
- `scanner/tests/test_areas_schema.py` populated (139 LOC, 10 tests) — FOUND
- Commits `35584f5`, `dbdfe4b`, `a015ec5` present in `git log` — FOUND
- `uv run pytest tests/test_flow_schema.py tests/test_vision_schema.py tests/test_areas_schema.py` → 32 passed, 0 failed, 0 skipped — PASS
- `grep -q 'submit' scanner/flow/schema.py` — returns 1 (no matches) — PASS
- `git diff --quiet analysis/` — exit 0 — PASS
