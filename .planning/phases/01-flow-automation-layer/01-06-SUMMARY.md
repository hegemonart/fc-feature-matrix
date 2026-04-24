---
phase: 01-flow-automation-layer
plan: 06
subsystem: scanner.flow
tags: [flow, validate, discover, stub, pydantic, tdd]
requires:
  - scanner.flow.schema (Plan 02 — FlowMap, FlowStep, FormField)
  - pydantic v2 (ValidationError.errors())
provides:
  - scanner.flow.validate.validate_flow_map — load + validate flow-map JSON
  - scanner.flow.validate.FlowMapValidationError — humanized error wrapper
  - scanner.flow.discover.discover_flow — Phase-2 stub with migration pointer
affects:
  - Plan 07 CLI `flow validate <path>` subcommand (consumes validate_flow_map)
  - Plan 07 CLI `flow discover <url>` subcommand (wired to stub)
tech-stack:
  added: []
  patterns:
    - Humanized Pydantic errors via `ValidationError.errors()` → loc+msg+type
    - Closed-literal rejection surfaced as caller-friendly FlowMapValidationError
    - Phase-scope stub pattern (NotImplementedError with migration pointer)
key-files:
  created:
    - scanner/flow/validate.py (88 lines)
    - scanner/flow/discover.py (44 lines)
  modified:
    - scanner/tests/test_flow_validate.py (6-line scaffold → 133 lines, 6 tests)
    - scanner/tests/test_flow_discover.py (6-line scaffold → 27 lines, 2 tests)
decisions:
  - "Emit loc+msg+type from Pydantic errors — never the raw JSON body (T-06-03 mitigation)."
  - "Include Pydantic error type tag (e.g. `[literal_error]`, `[too_long]`) for stable test assertions."
  - "JSONDecodeError surfaces as `JSON parse error: {msg} (line N col M)` — positional info only, not file body."
  - "Phase-2 stub raises NotImplementedError with both the Phase-2 marker and the Phase-1 alternative (`scanner flow validate`) so users can self-serve."
metrics:
  duration: 12m
  tasks: 1
  files: 4
  tests: 8
  completed: 2026-04-24
requirements: [FLOW-03]
---

# Phase 01 Plan 06: Flow subpackage — validate + discover stub Summary

One-liner: Wave 5 completes the `scanner.flow` subpackage — a humanized-error flow-map loader (`validate_flow_map`) backed by Pydantic + an honest Phase-2 discovery stub that points users at the Phase-1 hand-authoring path.

## What was built

### `scanner/flow/validate.py` (88 lines)

- `FlowMapValidationError(ValueError)` — single exception type raised for missing file, malformed JSON, and schema violations. Message format: `{path}: {kind}: {detail}`.
- `validate_flow_map(path: Path) -> FlowMap` — reads UTF-8, parses JSON via stdlib, validates via `FlowMap.model_validate(data)`. Catches `json.JSONDecodeError` and `pydantic.ValidationError` and re-raises as `FlowMapValidationError` with the original chained via `raise ... from e`.
- `_humanize(errors)` — renders `ValidationError.errors()` as `  - {loc}: {msg} [{type}]` lines. The Pydantic error type tag (`literal_error`, `too_long`, etc.) is included for stable downstream assertions.

### `scanner/flow/discover.py` (44 lines)

- `discover_flow(entry_url: str, out_path: Path) -> None` — always raises `NotImplementedError` with a message that (a) states the Phase 2 scope boundary and (b) directs users to `scanner flow validate <path>` for Phase 1.
- Docstring + module-level `TODO(phase-2)` comment outline the planned Phase-2 approach (Playwright crawl + keyword heuristics) so the next implementer has a pointer.

## Sample humanized error output (for reviewers)

A flow-map with `"action": "submit"` at step 0 produces:

```
/tmp/tmpXYZ.json: schema validation failed:
  - steps.0.action: Input should be 'navigate', 'click', 'fill', 'wait' or 'screenshot' [literal_error]
```

The closed `FlowStep.action` Literal (D-16) is surfaced as a clean, one-line reason; the raw JSON body never appears in the exception string (T-06-03 mitigation).

## Stub message confirmation

The Phase-2 stub raises:

```
scanner.flow.discover — click-path discovery is Phase 2 scope (D-06). For Phase 1,
author flow-maps by hand and validate with `scanner flow validate <path>`.
```

The test `test_discover_flow_error_points_to_phase_1_alternative` asserts the literal `scanner flow validate` appears in the message so the CLI help stays honest if the wording drifts.

## Tests (8 total, all passing)

**`test_flow_validate.py` (6):**
1. `test_valid_flow_map_round_trips` — happy-path load, attributes match
2. `test_missing_file_raises_with_file_not_found` — "file not found" + path in message
3. `test_malformed_json_raises_with_parse_marker` — `{ "area": }` raises with "json" or "parse"
4. `test_schema_violation_too_many_steps_humanized` — 16 steps → mentions `steps` + `too_long`/`max_length`
5. `test_schema_violation_submit_action_humanized` — `action: submit` → mentions `action` + `submit`
6. `test_error_message_does_not_echo_full_raw_json` — T-06-03 regression guard

**`test_flow_discover.py` (2):**
1. `test_discover_flow_raises_not_implemented` — `NotImplementedError` + "Phase 2" marker
2. `test_discover_flow_error_points_to_phase_1_alternative` — literal "scanner flow validate" in message

## Verification

```
$ ./scanner/.venv/Scripts/python.exe -m pytest scanner/tests/test_flow_validate.py scanner/tests/test_flow_discover.py -v
...
8 passed in 0.23s

$ ./scanner/.venv/Scripts/python.exe -m pytest scanner/tests/ -q
119 passed in 17.96s
```

No regressions in the 111 pre-existing scanner tests.

**D-24 invariant gate:** `git diff --quiet analysis/` → exit 0. No touch to data layer.

## TDD Gate Compliance

- **RED:** `9df9735 test(01-06): add failing tests for flow validate + discover stub` — tests fail with `ModuleNotFoundError` (modules don't exist yet). Verified before GREEN.
- **GREEN:** `aa0763f feat(01-06): implement flow validate + discover stub` — all 8 tests pass.
- **REFACTOR:** None needed; code was clean at GREEN.

## Threat Mitigations (per plan's `<threat_model>`)

| Threat ID | Mitigation in this plan |
|-----------|-------------------------|
| T-06-01 (T: submit bypass) | `validate_flow_map` re-raises Pydantic's Literal rejection as `FlowMapValidationError`; test_schema_violation_submit_action_humanized regression-guards this path. |
| T-06-02 (D: huge file) | Accepted per plan. Phase-1 is hand-authored; no untrusted input. Phase 2 may add a size guard. |
| T-06-03 (I: secret leak via error) | `_humanize` emits only `loc + msg + type` — never `input`. Regression test `test_error_message_does_not_echo_full_raw_json` embeds a fake secret in a field value and asserts it never appears in the raised exception. |

## Deviations from Plan

**None — plan executed exactly as written.** No Rule 1-3 auto-fixes were needed.

One minor addition: the humanizer includes the Pydantic error type tag (`[literal_error]`, `[too_long]`) in addition to `loc + msg`. This is still inside the safety envelope of T-06-03 (no input echo) and gives tests a stable code to assert on, but it wasn't spelled out in the plan's `<action>` block. Documented here rather than tracked as a deviation because it's an information-only addition.

## Commits

| Hash | Type | Message |
|------|------|---------|
| 9df9735 | test | test(01-06): add failing tests for flow validate + discover stub |
| aa0763f | feat | feat(01-06): implement flow validate + discover stub |

## Follow-ups / Open items

- **Phase 2:** implement `discover_flow` per the `TODO(phase-2)` comment in `scanner/flow/discover.py`. Keyword heuristics list lives in `.planning/phases/02-hospitality-pilot/` (future).
- **Plan 07 (CLI):** wire `flow validate <path>` to `validate_flow_map` and `flow discover <url>` to the stub. The discover CLI should surface the `NotImplementedError` message verbatim so users see the Phase-1 alternative.

## Self-Check: PASSED

- scanner/flow/validate.py FOUND
- scanner/flow/discover.py FOUND
- scanner/tests/test_flow_validate.py FOUND (6 test functions)
- scanner/tests/test_flow_discover.py FOUND (2 test functions)
- commit 9df9735 FOUND in git log
- commit aa0763f FOUND in git log
- 8/8 tests pass; 119/119 full scanner suite passes
- D-24 `git diff --quiet analysis/` → exit 0
