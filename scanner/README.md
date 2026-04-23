# fc-benchmark-scanner

Area-agnostic flow-capture scanner for FC Benchmark.

Phase 1 (`flow-automation-layer`) scaffolds this package. See `../.planning/phases/01-flow-automation-layer/` for the plan set.

## Quick start (development)

```bash
# with uv (recommended)
uv sync --dev
uv run playwright install chromium
uv run pytest scanner/tests/

# or with pip
python -m pip install -r scanner/requirements.txt
python -m playwright install chromium
python -m pytest scanner/tests/
```

## Dual vision backend (D-26)

Both backends are installed by default:

- `claude-agent-sdk` — subscription-backed (default)
- `anthropic` — API-key backed (fallback)

Select at runtime via `python -m scanner vision --api-mode {subscription|api-key}` (wired in Plan 07).

## Layout

- `capture/` — Playwright capture loop + cookie strategies + banner verification (Plan 03)
- `flow/` — flow-map JSON schema + crawl tooling (Plans 02, 06)
- `vision/` — two-judge feature mapping, dual-backend clients, PIL slicing (Plan 04)
- `report/` — Jinja2 HTML contact sheet (Plan 05)
- `scoring/` — tier-weighted scoring (later plans)
- `config/` — `areas.json` path resolution (Plan 02)
- `output/` — runtime artifacts (regenerable, gitignored)
- `tests/` — pytest suite with mocks for both SDKs
