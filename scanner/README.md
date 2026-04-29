# fc-benchmark-scanner

Area-agnostic flow-capture scanner for FC Benchmark. Phase 1 ships the
**infrastructure only** — capture + two-judge vision + HTML contact sheet +
flow-map schema + Click CLI. Phase 2 wires in the real hospitality rubric.

## Quickstart

```bash
# with uv (recommended)
uv sync --dev
uv run playwright install chromium
uv run python -m scanner --help

# or with pip
python -m pip install -e .
python -m playwright install chromium
python -m scanner --help
```

You should see six subcommands: `capture`, `vision`, `slice`, `report`,
`score`, and `flow` (with nested `validate` / `discover`).

## Dual-backend vision (D-26..D-29)

The vision judges run through one of two backends, selected per-invocation
via `--api-mode`:

| Flag                       | Client                  | Auth                            | Default? |
|----------------------------|-------------------------|---------------------------------|----------|
| `--api-mode subscription`  | `claude-agent-sdk`      | `claude` CLI logged in (Max 20x quota) | **yes** (D-28) |
| `--api-mode api-key`       | `anthropic` SDK         | `ANTHROPIC_API_KEY` env var     | no       |

Both modes produce **identical** strict-JSON output — the same
`FeatureVerdict` schema, the same `{feature_key: verdict}` dict shape.
Downstream (`slice`, `report`, `score`) is backend-agnostic.

If `--api-mode api-key` is chosen without `ANTHROPIC_API_KEY` in env, the
factory raises `RuntimeError` up front with an actionable message — the
key is never printed, logged, or accepted as a CLI flag (T-07-01).

Troubleshooting:

- `claude CLI not found`: install Claude Code or pass `--api-mode api-key`.
- `ANTHROPIC_API_KEY not set`: either `export ANTHROPIC_API_KEY=...` or
  use the default `subscription` mode.

## Areas

Every subcommand is parameterized by `--area` (D-04 / FLOW-02). Paths
are resolved through `scanner/config/areas.json`:

```json
{
  "hospitality": {
    "evidence_dir": "scanner/output/evidence/hospitality/",
    "results_dir":  "scanner/output/results/hospitality/",
    "rubric_path":  null,
    "features_ts":  null,
    "flow_maps_dir": "scanner/flow-maps/hospitality/",
    "status": "pending"
  }
}
```

Phase 1 ships an **empty** hospitality entry — `rubric_path` and
`features_ts` are `null`. Phase 2's HOSP-02 plan fills those in with the
real `HOSPITALITY-FLOW.md` + `features.ts`. Per D-25, scanner does **not**
create or touch `analysis/hospitality/` in Phase 1.

### Example end-to-end run (Phase 1 dry-run)

```bash
# 1. Capture Man City hospitality landing
python -m scanner capture \
  --area hospitality \
  --club mancity \
  --url https://www.mancity.com/tickets/hospitality

# 2. Run two-judge vision on the screenshot
python -m scanner vision \
  --area hospitality \
  --club mancity \
  --rubric scanner/tests/fixtures/dummy-hospitality-rubric.json

# 3. PIL-crop each present feature bbox
python -m scanner slice --area hospitality --club mancity

# 4. Build the HTML contact sheet
python -m scanner report --area hospitality

# 5. Re-score via Node
python -m scanner score --area hospitality
```

Headed browser by default — pass `--headless` in CI.

## Credentials

Phase 1 ships no credentials. Phase 2 introduces login-gated sites and
uses the following convention:

- `.env.local` at repo root (already `.gitignored` — project convention).
- Env-var keys: `{CLUB}_{AREA}_{FIELD}` — e.g.
  `MANCITY_HOSPITALITY_USER`, `MANCITY_HOSPITALITY_PASS`.
- Reader stub: `scanner.capture.credentials.get_credential(club, area, field)`
  (loaded via `python-dotenv`, returns `None` when unset).

The vision backends use their own env vars (`ANTHROPIC_API_KEY` for
api-key mode) — these are **separate** from per-club credentials.

## Phase 1 vs Phase 2 scope

| Concern                                | Phase 1 (this release) | Phase 2 (`hospitality-pilot`) |
|----------------------------------------|------------------------|-------------------------------|
| Scanner modules + CLI                  | shipped                | reused as-is                  |
| `scanner/output/evidence/hospitality/` | runtime dir            | populated per-run             |
| `analysis/hospitality/`                | **does not exist** (D-25) | created with real rubric   |
| `scanner/config/areas.json` hospitality| empty seed             | `rubric_path` / `features_ts` filled |
| Club credentials                       | none                   | `.env.local`                  |
| Automated flow discovery               | stub (`NotImplementedError`) | implemented (Phase 2)    |

## Tests

```bash
# Python (pytest)
source scanner/.venv/Scripts/activate  # Windows; or source .venv/bin/activate on *nix
python -m pytest scanner/tests/

# Node (scoring)
node --test scanner/scoring/recalculate.test.js
```

The pytest suite mocks both vision SDKs; no network is required. The
`test_no_area_coupling.py` test enforces the FLOW-02 invariant — scanner
package files must not import from `analysis.hospitality` or reference
that namespace by string.

## Layout

```
scanner/
  capture/   # Playwright capture + cookies + banner verify (Plan 03)
  vision/    # two-judge mapping + dual-backend clients + PIL slice (Plan 04)
  report/    # Jinja2 HTML contact sheet (Plan 05)
  flow/      # flow-map schema + validate + discover (Plan 06)
  scoring/   # tier-weighted scoring (Node)
  config/    # areas.json + loader + schema
  output/    # runtime artifacts (gitignored)
  tests/     # pytest suite with mocks for both SDKs
```

## Traps

- **Liverpool: DO NOT TOUCH.** Per repo `CLAUDE.md`, Liverpool's homepage
  capture is locked; do not rerun scanner against it.
- **Form-fill is `page.fill(...)` only.** Never dispatch via a submit
  button click (D-16). The grep guard in `tests/test_browser.py`
  enforces this across the whole `scanner/capture/` tree.
- **`analysis/` is invariant under scanner changes.** A scanner commit
  must never touch `analysis/homepage/results/*.json`. Invariant gate:
  `git diff --quiet analysis/` exits 0 after any scanner run.
- **`claude` CLI not on PATH** -> subscription mode unavailable. Install
  Claude Code CLI or pass `--api-mode api-key` with `ANTHROPIC_API_KEY`.
