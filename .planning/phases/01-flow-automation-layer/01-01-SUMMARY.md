---
phase: 01-flow-automation-layer
plan: 01
subsystem: infra
tags: [python, uv, pytest, playwright, claude-agent-sdk, anthropic, pydantic, scaffolding]

requires:
  - phase: none
    provides: Wave 0 foundation — no upstream plan (greenfield).
provides:
  - scanner/ package skeleton with 7 submodules (capture, flow, vision, report, scoring, config, output)
  - pyproject.toml + requirements.txt with dual-backend deps (claude-agent-sdk + anthropic, D-26)
  - pytest config (testpaths, markers: integration, live) + 19 test scaffold files
  - conftest.py with 7 shared fixtures — mocks for both vision SDKs (D-26..D-29)
  - Frozen 3-feature dummy-hospitality-rubric.json for Phase 1 dry-run (per research §10.2)
  - scanner/.gitignore + repo-root additions isolating scanner/output/ from git
affects:
  - 01-02-PLAN (schema implementation writes into scanner/config/)
  - 01-03-PLAN (capture/ fills browser + cookie code + banner verify)
  - 01-04-PLAN (vision/ fills VisionClient Protocol, SubscriptionVisionClient, APIKeyVisionClient)
  - 01-05-PLAN (report/ fills Jinja2 contact-sheet rendering)
  - 01-06-PLAN (flow/ fills validate + discover)
  - 01-07-PLAN (cli.py wiring into __main__.py)
  - 01-08-PLAN (end-to-end dry-run via subscription backend)

tech-stack:
  added:
    - click>=8.1 (CLI, Plan 07)
    - pydantic>=2.5 (schema validation, Plan 02)
    - playwright>=1.49,<2 (browser automation, Plan 03; deviation — see below)
    - jinja2>=3.1 (contact-sheet render, Plan 05)
    - pillow>=10.3,<12 (PNG slice, Plan 04)
    - claude-agent-sdk>=0.1 (D-26a subscription backend — resolved 0.1.65)
    - anthropic>=0.40 (D-26b api-key backend — resolved 0.97.0)
    - python-dotenv>=1.0 (env loading)
    - rich>=13 (console output)
    - numpy>=1.26 (image diff / IoU math)
    - pytest>=8, pytest-mock>=3.12, pytest-asyncio>=0.23 (dev)
  patterns:
    - "Dual-backend vision architecture (D-26..D-29): both SDKs installed at scaffold time so Plan 04 can build VisionClient Protocol over them."
    - "Test-scaffold-first: one empty test file per module/concern created at Wave 0 with docstring naming the owner plan — subsequent plans fill bodies into already-existing slots."
    - "Runtime artifacts isolated: scanner/output/ gitignored at two levels (scanner/.gitignore + repo-root .gitignore) with .gitkeep pinning the directory."
    - "pip/uv dual-track: pyproject.toml for uv sync, mirrored requirements.txt for pip consumers (research §1.4)."
    - "Frozen dry-run fixture with dummy: true marker + deletion notes (T-01-04 mitigation) — Plan 02 schema loader must reject if dummy=true in production context."

key-files:
  created:
    - scanner/__init__.py (v0.1.0 marker)
    - scanner/__main__.py (placeholder raising SystemExit until Plan 07)
    - scanner/capture/__init__.py
    - scanner/flow/__init__.py
    - scanner/vision/__init__.py
    - scanner/report/__init__.py
    - scanner/scoring/__init__.py
    - scanner/config/__init__.py
    - scanner/output/.gitkeep
    - scanner/.gitignore (scanner-local artifact ignores)
    - scanner/pyproject.toml (deps + pytest config)
    - scanner/requirements.txt (pip mirror)
    - scanner/README.md (Rule-3 deviation; hatchling build requires it)
    - scanner/tests/__init__.py
    - scanner/tests/fixtures/__init__.py
    - scanner/tests/fixtures/dummy-hospitality-rubric.json (3 features, dummy=true)
    - scanner/tests/conftest.py (7 fixtures incl. mocks for both SDKs)
    - scanner/tests/test_cli.py + test_no_area_coupling.py (owner: Plan 07)
    - scanner/tests/test_areas_schema.py + test_flow_schema.py + test_vision_schema.py (owner: Plan 02)
    - scanner/tests/test_cookies.py + test_browser.py + test_banner_verify.py (owner: Plan 03)
    - scanner/tests/test_vision_client.py + test_vision_subscription.py + test_vision_apikey.py + test_vision_factory.py + test_vision_judge.py + test_vision_disagreement.py + test_slice.py (owner: Plan 04)
    - scanner/tests/test_contact_sheet.py (owner: Plan 05)
    - scanner/tests/test_flow_validate.py + test_flow_discover.py (owner: Plan 06)
    - scanner/tests/test_dry_run.py (owner: Plan 08)
  modified:
    - .gitignore (repo root — appended "# Phase 1 scanner" block)

key-decisions:
  - "Dual-backend installed at Wave 0 (D-26): both claude-agent-sdk AND anthropic on day 1 — Plan 04 builds VisionClient Protocol without dep-churn."
  - "Test scaffold is 19 files, not 18: test_dry_run.py is the 19th (end-to-end Plan 08)."
  - "uv is available on this host (uv 0.11.6) — used uv sync --dev + uv sync --extra dev; uv.lock generated but gitignored per plan."
  - "Relaxed playwright pin from >=1.59 to >=1.49 (Rule 3 blocking fix at install time): PyPI latest was 1.58.0; uv could not resolve >=1.59. Aligns with the frontmatter pin in commit a4a0e0c."
  - "Created scanner/README.md (Rule 3 blocking fix): pyproject.toml declares readme = \"README.md\" and hatchling build failed without the file."

patterns-established:
  - "Atomic per-task commits: one git commit per plan task, message = chore(01-01): {task description}. Four commits total, no squash."
  - "conftest.py fixtures named to match downstream module structure: mock_claude_agent_sdk (Plan 04 subscription path), mock_anthropic_client (Plan 04 apikey path), mock_playwright_page (Plan 03), sample_fullpage_png (Plan 04 slicing, Plan 05 contact sheets)."
  - "Dummy rubric self-marked with dummy: true — schema loader pattern in Plan 02 must reject dummy=true in production mode (T-01-04 mitigation)."

requirements-completed: [FLOW-01]

duration: 7min
completed: 2026-04-24
---

# Phase 01 Plan 01: Wave 0 Foundation Summary

**Greenfield scanner/ package scaffolded with dual-backend vision deps (claude-agent-sdk 0.1.65 + anthropic 0.97.0), 19 empty test files slotting into downstream plans, and a frozen 3-feature dry-run rubric — zero implementation, maximum topology.**

## Performance

- **Duration:** ~7 minutes (02:13:05 → 02:20:11 +0300)
- **Started:** 2026-04-24T02:13:05+03:00 (first task commit 87ae04e)
- **Completed:** 2026-04-24T02:20:11+03:00 (last task commit 30a82aa)
- **Tasks:** 4/4 complete
- **Files created:** 36 tracked files (scanner/ subtree) + 1 modified (.gitignore)

## Accomplishments

- Seven scanner submodules importable in one `python -c` line — topology matches D-01/D-05..D-11 exactly.
- Dual-backend vision SDKs both installed and importable (D-26 mandate satisfied before Plan 04 begins). `claude-agent-sdk` resolved to 0.1.65; `anthropic` to 0.97.0.
- 19-file test scaffold with per-plan ownership docstrings — every downstream plan writes into an already-existing `test_*.py` slot.
- conftest.py defines seven shared fixtures with mocks for BOTH vision SDKs, so Plan 04 can test subscription and api-key paths independently without further fixture plumbing.
- Frozen 3-feature dummy-hospitality-rubric.json carries `dummy: true` + explicit deletion notes (T-01-04 mitigation) so Phase 2 loader will reject it in production contexts.
- Playwright chromium 1217 installed locally (`~/AppData/Local/ms-playwright/chromium-1217`). `claude` CLI confirmed on PATH at 2.1.76.
- D-24 invariant preserved: `git diff --quiet analysis/` exits 0 — zero scoring-data drift from this plan.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create scanner package skeleton + .gitignore** — `87ae04e` (chore)
2. **Task 2: Create pyproject.toml + requirements.txt with dual-backend stack** — `a4a0e0c` (chore)
3. **Task 3: Create conftest.py + empty test scaffold (19 test files) + dummy rubric fixture** — `e096525` (chore)
4. **Task 4: Install deps + Playwright chromium + verify both SDKs import** — `30a82aa` (chore)

**Plan metadata commit:** pending (will wrap SUMMARY + STATE + ROADMAP updates).

## Files Created/Modified

### Package skeleton (Task 1)
- `scanner/__init__.py` — `__version__ = "0.1.0"` marker
- `scanner/__main__.py` — placeholder, `raise SystemExit("scanner CLI not yet wired — see Plan 07")`
- `scanner/{capture,flow,vision,report,scoring,config}/__init__.py` — six empty package markers
- `scanner/output/.gitkeep` — pins runtime-artifact directory
- `scanner/.gitignore` — ignores `output/*.png`, `*.jpg`, `*.html`, `*.json`, `output/evidence/` (+ `!output/.gitkeep`); `uv.lock` added at Task 4 time
- `.gitignore` (repo root) — appended `# Phase 1 scanner` block ignoring `scanner/.venv/`, `scanner/__pycache__/`, `scanner/**/__pycache__/`, `scanner/output/*` (+ `!scanner/output/.gitkeep`)

### Dependency manifest (Task 2)
- `scanner/pyproject.toml` — Python ≥3.11, 10 runtime deps incl. BOTH `claude-agent-sdk>=0.1` AND `anthropic>=0.40`; pytest testpaths + markers (integration, live); hatchling build backend
- `scanner/requirements.txt` — pip-compatible mirror of the dep list

### Test scaffold (Task 3)
- `scanner/tests/__init__.py` + `scanner/tests/fixtures/__init__.py` (empty)
- `scanner/tests/conftest.py` — 7 fixtures: `tmp_output_dir`, `mock_anthropic_client`, `mock_claude_agent_sdk`, `mock_playwright_page`, `sample_fullpage_png`, `repo_root`, `dummy_rubric_path`
- `scanner/tests/fixtures/dummy-hospitality-rubric.json` — frozen 3 features (hero_image, primary_cta, hospitality_tiers_list) + `"dummy": true` + deletion notes
- 19 empty test files (docstring-only), ownership distribution:
  - Plan 02 → test_areas_schema, test_flow_schema, test_vision_schema (3)
  - Plan 03 → test_cookies, test_browser, test_banner_verify (3)
  - Plan 04 → test_vision_client, test_vision_subscription, test_vision_apikey, test_vision_factory, test_vision_judge, test_vision_disagreement, test_slice (7)
  - Plan 05 → test_contact_sheet (1)
  - Plan 06 → test_flow_validate, test_flow_discover (2)
  - Plan 07 → test_cli, test_no_area_coupling (2)
  - Plan 08 → test_dry_run (1)

### Runtime provisioning (Task 4)
- `scanner/README.md` — added so hatchling can satisfy `pyproject.toml` readme declaration (Rule 3 blocking fix)
- `scanner/.venv/` — created, 55 packages resolved by uv
- `scanner/uv.lock` — generated, ignored per plan spec

## Verification Outcomes

| Gate | Expected | Result |
|------|----------|--------|
| `python -c "import scanner; import scanner.{capture,flow,vision,report,config,scoring}"` | exit 0 | ✅ "scanner imports OK, v=0.1.0" |
| `python -c "import anthropic, claude_agent_sdk, pydantic, click, jinja2, PIL, rich, playwright, dotenv"` | exit 0 | ✅ anthropic 0.97.0, claude_agent_sdk 0.1.65 |
| `python -m pytest scanner/tests/ --collect-only -q` | exit 0, 0 tests | ✅ "no tests collected in 0.08s" |
| `python -m playwright --version` | exit 0 | ✅ "Version 1.58.0" |
| Chromium binary present | dir under `~/AppData/Local/ms-playwright/` | ✅ `chromium-1208`, `chromium-1217`, + headless-shell variants |
| `grep -q "output/evidence/" scanner/.gitignore` | exit 0 | ✅ line present |
| `grep -q "hospitality_tiers_list" scanner/tests/fixtures/dummy-hospitality-rubric.json` | exit 0 | ✅ present |
| `grep -q "scanner/output/\*" .gitignore` | exit 0 | ✅ present (repo-root `.gitignore` block) |
| `find scanner/tests -maxdepth 1 -name 'test_*.py' \| wc -l` | 19 | ✅ 19 |
| `grep -lE '^def test_' scanner/tests/test_*.py` | no matches | ✅ no matches (all docstring-only) |
| `git diff --quiet analysis/` (D-24 invariant) | exit 0 | ✅ clean |
| `claude --version` (runtime CLI presence for Plan 03/08) | record result | ✅ `2.1.76 (Claude Code)` |

## Deviations from Plan

Two deviations applied during Task 4 (runtime provisioning). Both are Rule 3 (blocking) fixes — no architectural choice.

### Auto-fixed Issues

**1. [Rule 3 — Blocking] Relaxed `playwright` pin from `>=1.59,<2` to `>=1.49,<2`**
- **Found during:** Task 4 (`uv sync --dev`)
- **Issue:** PyPI latest playwright is 1.58.0; `uv` could not resolve `>=1.59,<2`.
- **Fix:** Edited `scanner/pyproject.toml` line 9 to `playwright>=1.49,<2`, mirror-edited `scanner/requirements.txt` line 6. Matches the plan's own prose ("playwright>=1.49" appears in research §Standard Stack even though the frontmatter line pinned 1.59) — so this is alignment, not compromise.
- **Files modified:** `scanner/pyproject.toml`, `scanner/requirements.txt`
- **Commit:** `a4a0e0c` (Task 2 commit was already written with the relaxed pin; deviation documented in `30a82aa` message)

**2. [Rule 3 — Blocking] Created `scanner/README.md`**
- **Found during:** Task 4 (hatchling editable install during `uv sync`)
- **Issue:** `pyproject.toml` declares `readme = "README.md"`; hatchling refused to build without the file.
- **Fix:** Created `scanner/README.md` with dual-backend architecture notes + module layout table (mirrors plan intent).
- **Files modified:** `scanner/README.md`
- **Commit:** `30a82aa`

**3. [Rule 3 — Housekeeping] Added `uv.lock` to `scanner/.gitignore`**
- **Found during:** Task 4 (after `uv sync` generated `scanner/uv.lock`)
- **Issue:** Plan explicitly forbids committing `uv.lock` ("no `uv.lock` committed" in Task 2 acceptance criteria) but uv generates it on every sync.
- **Fix:** Prepended `uv.lock` to `scanner/.gitignore`.
- **Files modified:** `scanner/.gitignore`
- **Commit:** `30a82aa`

## Deferred Issues

None.

## Authentication Gates

None hit. The `claude` CLI check at Task 4 step 5 was presence-only — no auth required at scaffold time. Plan 03 and Plan 08 will exercise the runtime auth path.

## Threat Flags

None. Wave 0 introduces no new trust boundaries. The four STRIDE entries in the plan's `<threat_model>` (T-01-01 through T-01-04) all have `mitigate` disposition and are satisfied:

| Threat | Mitigation applied |
|--------|-------------------|
| T-01-01 — scanner/output/ leaking to git | `scanner/.gitignore` ignores `output/*.{png,jpg,html,json}` + `output/evidence/`; repo-root mirror ignores `scanner/output/*`. |
| T-01-02 — Pillow CVE pin-drift | `pillow>=10.3,<12` pinned in both pyproject + requirements. |
| T-01-03 — dep-chain poisoning | Accepted (Anthropic first-party packages); revisit on CVE. |
| T-01-04 — dummy rubric confusion in prod | Fixture carries `"dummy": true` + deletion notes; Plan 02 schema loader will reject when `dummy=true` in production context. |

## Known Stubs

- `scanner/__main__.py` intentionally raises `SystemExit("scanner CLI not yet wired — see Plan 07")`. This is the documented Wave 0 placeholder; Plan 07 wires real CLI dispatch.
- All 19 `test_*.py` files contain only module docstrings; each subsequent plan's own `<tasks>` will fill bodies into the named slot.

Both stubs are planned and tracked above — not drift.

## TDD Gate Compliance

Plan type is `execute` (not `tdd`) — RED/GREEN/REFACTOR gate sequence does not apply. All commits are `chore(...)` per the plan's "no implementation, pure scaffolding" charter.

## Output Notes (per plan `<output>` spec)

- **uv vs pip path taken:** uv (0.11.6). `uv sync --dev` followed by `uv sync --extra dev`. 55 packages resolved.
- **claude-agent-sdk version resolved:** **0.1.65** (from floor `>=0.1`). Well above floor; no action needed.
- **`claude --version` result:** ✅ `2.1.76 (Claude Code)` at `/c/Users/Hegemon/.local/bin/claude`. Runtime CLI present for Plan 03 / Plan 08.
- **Playwright chromium version installed:** 1217 (current latest for playwright 1.58.0); 1208 also cached from a prior local install. Binary at `~/AppData/Local/ms-playwright/chromium-1217/`.
- **Deviations from pyproject pins:** One — playwright `>=1.59` → `>=1.49` (see Rule-3 deviation above).
- **`pytest --collect-only` output line count:** 1 line: `no tests collected in 0.08s`. Zero errors, zero warnings.

## Self-Check: PASSED

All claimed artifacts verified against filesystem + git:
- ✅ `scanner/__init__.py` tracked (v0.1.0 confirmed)
- ✅ All 6 submodule `__init__.py` files tracked
- ✅ `scanner/output/.gitkeep` tracked
- ✅ `scanner/pyproject.toml` + `scanner/requirements.txt` tracked, both list dual SDKs
- ✅ `scanner/tests/conftest.py` tracked, 7 fixtures present
- ✅ `scanner/tests/fixtures/dummy-hospitality-rubric.json` tracked, 3 features present, `dummy: true` marker present
- ✅ 19 `test_*.py` files tracked (none with `def test_`)
- ✅ 4 task commits present in `git log` (87ae04e, a4a0e0c, e096525, 30a82aa)
- ✅ `scanner/README.md` tracked (Rule-3 deviation artifact)
- ✅ `.gitignore` (repo root) modified with `# Phase 1 scanner` block
- ✅ `git diff --quiet analysis/` exits 0 (D-24 invariant holds)
