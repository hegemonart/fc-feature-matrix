---
phase: 02-hospitality-pilot
plan: 01
subsystem: infra
tags: [credentials, dotenv, python, scanner, phase-1-gap-fill]

# Dependency graph
requires:
  - phase: 01-flow-automation-layer
    provides: "scanner/ package scaffolding, capture/ module pattern (cookies.py style)"
provides:
  - "scanner.capture.get_credential(club, field, area='hospitality') — env-backed credential lookup returning None when unset (D-15-aware)"
  - "scanner.capture.MissingCredentialError — caller-raised exception referencing env var NAME only (no value leakage)"
  - "Env-var key convention implemented & tested: {CLUB_UPPER}_{AREA_UPPER}_{FIELD_UPPER}"
  - ".env.local auto-loaded on import via python-dotenv (override=False; shell env wins per T-02-01-05)"
  - ".planning/phases/*/credentials.local.md gitignored (D-13 storage location protected)"
affects: [02-04-flow-discover-crawler, 02-hospitality-capture, back-half-login-flows]

# Tech tracking
tech-stack:
  added: []  # python-dotenv was already in scanner/pyproject.toml (no new deps)
  patterns:
    - "Closed-enum Literal['user', 'pass'] + runtime ValueError guard (mirrors vision/factory.get_client)"
    - "Module-level load_dotenv at import; idempotent, override=False"
    - "Error classes refuse to accept value= kwargs by construction (no-value-leakage pattern)"

key-files:
  created:
    - "scanner/capture/credentials.py (~95 lines; get_credential + MissingCredentialError + _build_env_key)"
    - "scanner/tests/test_credentials.py (7 tests covering full contract)"
  modified:
    - "scanner/capture/__init__.py (re-export of get_credential + MissingCredentialError; was empty)"
    - ".gitignore (+2 lines: header comment + .planning/phases/*/credentials.local.md)"

key-decisions:
  - "override=False on load_dotenv: shell env wins over .env.local (T-02-01-05 accepted risk, intentional for CI secret-store injection)"
  - "get_credential returns None (not raises) on missing env: preserves caller's D-15 freedom to skip the step and record in flow-map metadata rather than failing the run"
  - "MissingCredentialError takes no value= kwarg: compile-time guarantee that the error surface can never carry a secret (T-02-01-02)"
  - "area parameter keyword-default 'hospitality': forward-compatible with ticket/membership/etc. areas without breaking callers that only pass (club, field)"

patterns-established:
  - "Credential lookup pattern: env-backed, file-loaded, None-on-absent, NAME-only error messaging"
  - "Package public surface via __init__ re-exports (mirrors scanner.vision style)"
  - "Security-first error classes: refuse value= kwargs at constructor level"

requirements-completed: [HOSP-01]  # partial — credentials infra unblocking later login-gated flows

# Metrics
duration: 8min
completed: 2026-04-24
---

# Phase 02 Plan 01: Credentials Helper (Phase 1 Gap Closure) Summary

**Shipped the `scanner.capture.credentials` module that the Phase 1 scanner README advertised but never delivered — a python-dotenv wrapper reading `{CLUB}_{AREA}_{FIELD}` env vars, returning `None` on absence, with a value-leak-proof `MissingCredentialError`.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-24T18:41:00Z
- **Completed:** 2026-04-24T18:49:26Z
- **Tasks:** 2 (Task 1 TDD split into RED + GREEN commits = 3 task commits total)
- **Files modified:** 4 (1 test file created, 1 module created, 1 __init__ re-export, 1 gitignore line)

## Accomplishments

- `scanner/capture/credentials.py` ships the interface Phase 1 README promised (research §7 gap closed)
- 7/7 new pytests green; 145/145 total scanner tests green (zero regression vs 138 baseline)
- `__init__.py` re-export makes `from scanner.capture import get_credential, MissingCredentialError` the canonical import path for downstream plans (02-04 crawler, back-half capture)
- Threat register T-02-01-01..-07 fully discharged: zero `print`/`logger.*credential` hits; error class refuses `value=` kwarg; `.planning/phases/*/credentials.local.md` now gitignored

## Task Commits

1. **Task 1 (RED): Failing credentials tests** — `4d6999a` (test)
2. **Task 1 (GREEN): credentials module + __init__ re-export** — `706d90b` (feat)
3. **Task 2: gitignore credentials.local.md** — `ec04bd1` (chore)

_Plan metadata commit (SUMMARY + STATE) to follow._

## Files Created/Modified

- `scanner/capture/credentials.py` — get_credential + MissingCredentialError + _build_env_key; load_dotenv(override=False) at import; `_ALLOWED_FIELDS = ("user", "pass")`; Literal guard raises ValueError on unknown field.
- `scanner/capture/__init__.py` — re-exports `get_credential` and `MissingCredentialError` (file was previously empty).
- `scanner/tests/test_credentials.py` — 7 tests: present, missing→None, case folding (club+field), invalid field→ValueError, custom area routing, error message references env var NAME + .env.local (and refuses value= kwarg), idempotent re-import safety.
- `.gitignore` — +2 lines (comment + `.planning/phases/*/credentials.local.md`); `.env*.local` and all other rules unchanged.

## Decisions Made

- **override=False:** Shell env always wins over `.env.local` — intended for CI secret-store injection (T-02-01-05 accepted). Documented in module docstring.
- **None instead of raise on missing:** Gives callers D-15 freedom. `MissingCredentialError` exists for callers that do want to hard-fail, but the default code path is soft.
- **No `value=` kwarg on `MissingCredentialError`:** Enforced by the constructor's fixed signature — tests verify `TypeError` when any code tries to pass one. This is a compile-time guarantee that the error surface cannot carry a secret.
- **area defaults to "hospitality":** Keeps Phase 2 callsites short `get_credential("mancity", "user")` while leaving room for `area="ticket"` / `area="membership"` in later phases (test 5 exercises this path).

## Deviations from Plan

None — plan executed exactly as written. The interface block in the plan was followed to the letter (signature, behavior, error message format, security invariants).

## Issues Encountered

None. `python-dotenv` was already pinned in `scanner/pyproject.toml` (research §7 confirmed this); no install step was needed. Baseline test count (138) matched expectations; post-change count (145) matched 138+7 exactly.

## Verification Results

**Acceptance greps (Task 1):**
- `test -f scanner/capture/credentials.py` → exists
- `grep -c "^def get_credential" scanner/capture/credentials.py` → 1
- `grep -c "class MissingCredentialError" scanner/capture/credentials.py` → 1
- `grep -q "load_dotenv" scanner/capture/credentials.py` → found
- `grep -q "from scanner.capture.credentials import" scanner/capture/__init__.py` → found
- `git grep -nE "print\(.*os\.environ|logger\..*credential" scanner/capture/credentials.py` → 0 hits (exit=1)
- `git grep -nE "HOSPITALITY_USER=|HOSPITALITY_PASS=" scanner/` → 0 hits (exit=1, no hardcoded sample values)

**Acceptance (Task 2):**
- `grep -c "credentials.local.md" .gitignore` → 1
- `grep -q ".env\*.local" .gitignore` → still present (unchanged)
- `git check-ignore .planning/phases/02-hospitality-pilot/credentials.local.md` → exit 0

**Tests:**
- `uv run pytest tests/test_credentials.py -v` → 7 passed in 0.05s
- `uv run pytest tests/ -q` → 145 passed in 31.90s (138 baseline + 7 new, zero regression)

**Phase invariants (D-20, D-21):**
- `git diff --quiet HEAD~3 HEAD -- analysis/` → exit 0 (analysis/ untouched)
- `git diff --quiet HEAD~3 HEAD -- scanner/vision/ scanner/scoring/ scanner/report/` → exit 0
- `git diff --quiet HEAD~3 HEAD -- scanner/capture/cookies.py browser.py banner_verify.py form_dummy.py capture.py` → exit 0 (existing capture modules untouched — credentials.py is a NEW sibling, not an internal modification)
- `git diff --diff-filter=D --name-only HEAD~3 HEAD` → empty (no deletions)

## User Setup Required

None — credentials are populated by the human out-of-band in `.env.local` (gitignored). A separate per-phase `.planning/phases/02-hospitality-pilot/credentials.local.md` note (now gitignored) is the recommended place to record which clubs have working dummy accounts (D-13).

## Next Phase Readiness

- **02-04 flow-discover crawler:** Can import `from scanner.capture import get_credential` immediately; form-auth step can branch on `get_credential(club, "user") is None` → skip per D-15 with metadata flag.
- **Back-half hospitality capture:** Same import path; caller is free to raise `MissingCredentialError(club, "user", "hospitality", env_var_name)` when a credential is truly mandatory.
- **Out-of-scope / deferred:** No actual credentials added to any `.env.local` yet — that's the human's responsibility at dummy-account registration time. No plan-02-01 follow-up needed.

## Self-Check: PASSED

- Created `scanner/capture/credentials.py` → exists
- Created `scanner/tests/test_credentials.py` → exists
- Modified `scanner/capture/__init__.py` → re-exports present
- Modified `.gitignore` → entry present
- Commit `4d6999a` (test RED) → in git log
- Commit `706d90b` (feat GREEN) → in git log
- Commit `ec04bd1` (chore gitignore) → in git log

---
*Phase: 02-hospitality-pilot*
*Completed: 2026-04-24*
