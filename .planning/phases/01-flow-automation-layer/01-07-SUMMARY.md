---
phase: 01-flow-automation-layer
plan: 07
subsystem: scanner.cli + scanner.config
tags: [cli, click, areas, loader, readme, dual-backend]
requires:
  - scanner.capture.capture (Plan 03)
  - scanner.vision.judge + vision.slice + vision.disagreement + vision.factory (Plan 04)
  - scanner.report.contact_sheet (Plan 05)
  - scanner.flow.validate + flow.discover (Plan 06)
  - scanner.config.schema (Plan 02)
  - click >= 8.1, rich >= 13 (pyproject deps)
provides:
  - scanner.cli.cli — Click group dispatching all six Phase-1 subcommands
  - scanner.config.loader.load_area / load_areas — areas.json parser
  - scanner.config.loader.REPO_ROOT — repo-root resolver honouring SCANNER_REPO_ROOT
  - scanner/config/areas.json — Phase-1 empty-hospitality seed
  - scanner/README.md — dual-backend + env-var + scope documentation
affects:
  - Plan 08 dry-run (consumes the full CLI surface end-to-end)
tech-stack:
  added:
    - click group + nested subgroup pattern (flow validate / flow discover)
    - rich.logging.RichHandler (standard logging)
  patterns:
    - Deferred imports inside subcommand bodies for fast --help response
    - Click `show_default=True` surfaces --api-mode=subscription in help text
    - Env override (SCANNER_REPO_ROOT) for test-time repo-root swap
    - Area-agnostic dispatch via areas.json — no analysis/ coupling
key-files:
  created:
    - scanner/cli.py (276 lines — Click group)
    - scanner/config/loader.py (60 lines)
  modified:
    - scanner/__main__.py (7-line placeholder → 18-line delegator to cli.cli)
    - scanner/config/areas.json (flow_maps_dir: null → "scanner/flow-maps/hospitality/")
    - scanner/README.md (40 lines → 164 lines)
    - scanner/tests/test_cli.py (6-line scaffold → 78 lines, 7 tests)
    - scanner/tests/test_no_area_coupling.py (6-line scaffold → 87 lines, 2 tests)
decisions:
  - "Heavy imports (Playwright, anthropic SDK, claude-agent-sdk, PIL, Jinja2) deferred into subcommand bodies so --help is instant and optional backends do not break unrelated subcommands."
  - "--api-mode defaults to `subscription` per D-28; Click renders the default in --help text so the documented behaviour is discoverable without reading source."
  - "--headless defaults to False per user decision 2 (developer runs headed; CI passes --headless)."
  - "scanner/config/areas.json ships hospitality with null rubric_path / features_ts per D-25 + user decision 1; evidence lives at scanner/output/evidence/hospitality/ — NOT under analysis/."
  - "FLOW-02 area-coupling guard scans scanner/**.py (excluding tests/, __pycache__/, .venv/) for forbidden substrings; caught an `analysis/hospitality/` docstring in loader.py and was resolved pre-commit."
metrics:
  duration: 27m
  tasks: 2
  files: 6
  tests: 9
  completed: 2026-04-24
requirements: [FLOW-01, FLOW-02]
---

# Phase 01 Plan 07: CLI + areas.json + README Summary

Single Click entry point wires every Phase-1 module (`capture` / `vision` / `slice` / `report` / `score` / `flow validate` / `flow discover`) behind `python -m scanner`, with `--api-mode subscription` as the documented default (D-28) and `--headless` as opt-in (user decision 2). `scanner/config/areas.json` seeds the hospitality area with evidence under `scanner/output/evidence/` (user decision 1, D-25); the new FLOW-02 area-coupling guard enforces no `analysis.hospitality` leakage in `scanner/`.

## What shipped

### Commits

| Task | Hash | Description |
|------|------|-------------|
| 1 | `fad4acb` | Click CLI + areas loader + hospitality areas.json seed |
| 2 | `9b46429` | Dual-backend README + CLI smoke tests + area-coupling guard |

### Files touched

**Created:**

- `scanner/cli.py` (276 lines) — Click group with six subcommands + nested `flow` subgroup. Every subcommand defers its heavy imports (Playwright, anthropic SDK, claude-agent-sdk, PIL, Jinja2) into its function body. `--api-mode` option on `vision` uses `click.Choice(["subscription", "api-key"])` with `default="subscription"` and `show_default=True` — so the `[default: subscription]` tag renders in `--help`. `--headless/--no-headless` on `capture` defaults to `no-headless` per user decision 2.
- `scanner/config/loader.py` (60 lines) — `load_areas()` parses `scanner/config/areas.json` via `AreasConfig.model_validate_json`; `load_area(name)` returns the typed `AreaEntry` or raises a `KeyError` that points users at the config file. `REPO_ROOT` honours the `SCANNER_REPO_ROOT` env override — used by the test suite to isolate against a synthetic tmp-path repo.

**Modified:**

- `scanner/__main__.py` — replaced the Plan-01 `raise SystemExit("scanner CLI not yet wired")` placeholder with `from scanner.cli import cli; def _main(): cli()`. The `pyproject.toml`'s `[project.scripts] scanner = "scanner.__main__:_main"` entry now dispatches to the real CLI after `pip install -e .` / `uv sync`.
- `scanner/config/areas.json` — flipped `flow_maps_dir` from `null` to `"scanner/flow-maps/hospitality/"` to match the interfaces target. `rubric_path` and `features_ts` remain `null` per D-25 (Phase 2 fills them).
- `scanner/README.md` (164 lines) — Quickstart, Dual-backend vision table, Areas section with example end-to-end run, Credentials (env-var convention `{CLUB}_{AREA}_{FIELD}` → `MANCITY_HOSPITALITY_USER`), Phase 1 vs Phase 2 scope table, Tests, Traps (including `Liverpool: DO NOT TOUCH` from the repo `CLAUDE.md`).
- `scanner/tests/test_cli.py` (78 lines, 7 tests) — `CliRunner`-based smoke tests cover: `--help` lists all 6 subcommands; `vision --help` contains `--api-mode` with `[default: subscription]`; `capture --help` contains `--headless` / `no-headless` default; `flow validate --help`, `flow discover --help`, `score --help` all exit 0; unknown subcommand exits non-zero.
- `scanner/tests/test_no_area_coupling.py` (87 lines, 2 tests) — `test_no_area_coupling_in_scanner_package` rglob-scans `scanner/**/*.py` (excluding tests/, `__pycache__/`, `.venv/`) and fails on any of `analysis.hospitality`, `analysis/hospitality`, `from analysis.hospitality`, `import analysis.hospitality`. `test_phase1_areas_json_seed_matches_user_decision_1` asserts the `evidence_dir` routes under `scanner/output/` and that `rubric_path` / `features_ts` are `null`.

## `python -m scanner --help` output

```
Usage: python -m scanner [OPTIONS] COMMAND [ARGS]...

  FC Benchmark scanner — area-agnostic flow capture tooling.

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  capture  Capture a full-page screenshot with Playwright.
  flow     Flow-map operations: validate, discover.
  report   Render the HTML contact sheet for an area.
  score    Re-compute scores via scanner/scoring/recalculate.js (Node).
  slice    PIL-crop each present feature from the Opus judgement into...
  vision   Run two-judge (Opus + Sonnet) feature mapping on captured...
```

All six subcommands surface; `--version` resolves via `@click.version_option("0.1.0")`.

## Verification gates (all pass)

| Gate | Command | Result |
|------|---------|--------|
| CLI help lists 6 subcommands | `python -m scanner --help` | capture / flow / report / score / slice / vision |
| `--api-mode` default | `python -m scanner vision --help \| grep default` | `[default: subscription]` |
| `--headless` default | `python -m scanner capture --help \| grep default` | `[default: no-headless]` |
| Flow validate surface | `python -m scanner flow validate --help` | exit 0 |
| Flow discover surface | `python -m scanner flow discover --help` | exit 0 |
| Plan 07 tests | `pytest scanner/tests/test_cli.py scanner/tests/test_no_area_coupling.py` | 9 passed |
| Full scanner suite | `pytest scanner/tests/` | 128 passed |
| analysis/ invariant | `git diff --quiet analysis/` | exit 0 |
| README doc gates | `grep -c 'api-mode\|ANTHROPIC_API_KEY\|MANCITY_HOSPITALITY_USER\|Liverpool: DO NOT TOUCH'` | all present |

Test count by file: `test_cli.py` = 7, `test_no_area_coupling.py` = 2 — **9 tests total** added in Plan 07, all green; no regressions across the 128-test scanner suite.

## areas.json (final Phase-1 seed)

```json
{
  "hospitality": {
    "evidence_dir": "scanner/output/evidence/hospitality/",
    "results_dir": "scanner/output/results/hospitality/",
    "rubric_path": null,
    "features_ts": null,
    "flow_maps_dir": "scanner/flow-maps/hospitality/",
    "status": "pending"
  }
}
```

No deviation from the schema: all 6 keys from `AreaEntry` are present; `rubric_path` / `features_ts` remain `null` for the Phase-1 empty seed (D-25 + user decision 1).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] FLOW-02 guard triggered on loader.py docstring**

- **Found during:** Task 2, first test run.
- **Issue:** `test_no_area_coupling_in_scanner_package` failed because `scanner/config/loader.py`'s module docstring contained the string `analysis/hospitality/` as part of the explanation "…instead of hard-coding `analysis/hospitality/` anywhere in the package…". The scan tool matches substrings, not imports, so the documentation itself triggered the guard.
- **Fix:** Rephrased the docstring to use "per-area analysis subdirectories" — documents the same boundary without naming the forbidden string.
- **Files modified:** `scanner/config/loader.py` (docstring only; no code change).
- **Commit:** Folded into `9b46429` (Task 2). This is the correct behaviour — the guard is a grep-based backstop, not an AST-aware linter; catching documentation references proves the guard works.

### Authentication gates

None. Plan 07 is fully local CLI plumbing — no API calls, no login flows.

## Key decisions carried forward

- **Subscription backend is the documented default.** Click's `show_default=True` renders `[default: subscription]` in `vision --help`, so users do not need to read source to discover the D-28 choice.
- **Deferred imports are load-bearing for UX.** `python -m scanner --help` must respond in tens of ms; Playwright's import cost alone would blow that budget. Every subcommand body starts with its own `from scanner... import ...`.
- **`SCANNER_REPO_ROOT` env override is the contract for test isolation.** `conftest.py`'s `repo_root` fixture sets it to a tmp-path; downstream fixtures can populate that synthetic tree without ever touching the real repo. The loader reads the env on every call (not at import time) so monkeypatching works per-test.

## Self-Check: PASSED

- `scanner/cli.py` — FOUND
- `scanner/config/loader.py` — FOUND
- `scanner/__main__.py` — FOUND (modified)
- `scanner/config/areas.json` — FOUND (modified)
- `scanner/README.md` — FOUND (modified)
- `scanner/tests/test_cli.py` — FOUND (7 tests)
- `scanner/tests/test_no_area_coupling.py` — FOUND (2 tests)
- Commit `fad4acb` — FOUND (Task 1)
- Commit `9b46429` — FOUND (Task 2)
- `python -m scanner --help` exits 0 and lists 6 subcommands — PASS
- `python -m pytest scanner/tests/test_cli.py scanner/tests/test_no_area_coupling.py` 9 passed — PASS
- `git diff --quiet analysis/` exits 0 — PASS
