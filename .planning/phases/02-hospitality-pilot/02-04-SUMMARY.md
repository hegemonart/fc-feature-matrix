---
phase: 02-hospitality-pilot
plan: 04
subsystem: scanner/capture
tags:
  - scanner
  - cookies
  - per-club-strategies
  - additive-config
requires:
  - scanner/capture/cookies.py (Phase 1 — dismiss_cookies dispatcher + MANCITY_STRATEGY)
  - scanner/tests/test_cookies.py (Phase 1 — 10 baseline tests)
provides:
  - TOT_STRATEGY (scanner/capture/cookies.py)
  - RMA_STRATEGY (scanner/capture/cookies.py)
  - PSG_STRATEGY (scanner/capture/cookies.py)
  - CHE_STRATEGY (scanner/capture/cookies.py)
  - STRATEGIES dict with all 5 pilot club slugs
affects:
  - scanner back-half capture wave (Phase 2 Wave 3+) — can now call dismiss_cookies(page, club=<pilot-slug>) for any pilot club
tech-stack:
  added: []
  patterns:
    - per-club CookieStrategy dispatch (extends Phase-1 pattern additively)
key-files:
  created: []
  modified:
    - scanner/capture/cookies.py (+42 lines; 4 constants, 4 dispatch entries, 4 __all__ exports)
    - scanner/tests/test_cookies.py (+102 lines; 10 new tests)
decisions:
  - TOT_STRATEGY leads with "accept all cookies" (OneTrust EPL convention)
  - RMA_STRATEGY: ES-first priority ("aceptar todo") with EN fallback
  - PSG_STRATEGY: FR-first priority ("tout accepter") with EN fallback
  - CHE_STRATEGY: matches TOT shape (OneTrust convention on hospitality subdomain)
  - No French phrases added to GLOBAL_COOKIE_PRIORITIES (user decision 2 preserved)
  - No Liverpool strategy (CLAUDE.md trap enforced)
metrics:
  duration: ~10 minutes
  completed: 2026-04-24T19:39Z
  tasks_completed: 2
  commits: 2
  tests_added: 10
  tests_before: 145
  tests_after: 155
requirements:
  - HOSP-01 (partial — per-club cookie banner handling unblocks back-half capture wave)
---

# Phase 02 Plan 04: Per-Club Cookie Strategies (TOT/RMA/PSG/CHE) Summary

Extended `scanner/capture/cookies.py` with four per-club `CookieStrategy` constants (TOT/RMA/PSG/CHE) so the back-half capture wave can dismiss hospitality-page cookie banners across EN/ES/FR locales uniformly via `dismiss_cookies(page, club=<slug>)`. Pure additive change — `dismiss_cookies()`, `GLOBAL_COOKIE_PRIORITIES`, `MANCITY_STRATEGY`, and `_DISMISS_JS` were all preserved byte-for-byte.

## What Shipped

### scanner/capture/cookies.py (+42 lines)

Four new `CookieStrategy` constants following the Phase-1 TypedDict shape:

| Strategy | Priority list (verbatim) | Rationale |
|----------|--------------------------|-----------|
| `TOT_STRATEGY` | `["accept all cookies", "accept all", "allow all"]` | OneTrust convention (EPL); EN only |
| `RMA_STRATEGY` | `["aceptar todo", "aceptar todas", "acepto todo", "accept all", "aceptar"]` | ES-first (custom ES banner), EN fallback for /en/ path |
| `PSG_STRATEGY` | `["tout accepter", "accepter tous", "accepter tout", "j'accepte", "accept all"]` | FR-first (Didomi/Axeptio), EN fallback for /en/ path |
| `CHE_STRATEGY` | `["accept all cookies", "accept all", "allow all cookies"]` | OneTrust convention (hospitality.chelseafc.com); EN only |

All four match 02-RESEARCH.md §6 verbatim — zero drift.

`STRATEGIES` dispatch dict updated from 1 key → 5 keys (mancity preserved, 4 new entries added).

`__all__` extended with 4 new symbol names.

### scanner/tests/test_cookies.py (+102 lines)

10 new tests appended after existing Man City tests:

| # | Test name | Assertion |
|---|-----------|-----------|
| 1 | `test_tot_strategy_priority_starts_with_accept_all_cookies` | Leads with `"accept all cookies"`, len 3, all lowercase |
| 2 | `test_rma_strategy_priority_starts_with_spanish` | Leads with `"aceptar todo"`, `"accept all"` present |
| 3 | `test_psg_strategy_priority_starts_with_french` | Leads with `"tout accepter"`, `"accept all"` present |
| 4 | `test_che_strategy_priority_starts_with_accept_all_cookies` | Leads with `"accept all cookies"` |
| 5 | `test_strategies_dispatch_includes_all_5_pilot_clubs` | `{mancity, tottenham, realmadrid, psg, chelsea}` subset of keys |
| 6 | `test_strategies_does_not_include_liverpool` | `"liverpool" not in STRATEGIES` (CLAUDE.md trap) |
| 7 | `test_dismiss_cookies_uses_psg_priority_for_psg_club` | dispatch routes to PSG_STRATEGY priority |
| 8 | `test_dismiss_cookies_uses_rma_priority_for_realmadrid_club` | dispatch routes to RMA_STRATEGY priority |
| 9 | `test_global_cookie_priorities_unchanged` | `len(GLOBAL_COOKIE_PRIORITIES) == 20` (user decision 2) |
| 10 | `test_mancity_strategy_unchanged` | `MANCITY_STRATEGY["priority"] == ["accept all cookies", "accept all"]` |

## Tests

**Before:** 145 tests in `scanner/tests/` (10 in `test_cookies.py`)
**After:** 155 tests in `scanner/tests/` (20 in `test_cookies.py`)
**Delta:** +10 tests, all passing.

**Full suite:** `cd scanner && PYTHONPATH=.. uv run pytest tests/` → 155 passed in 31.75s. No regressions.

**TDD Gate Compliance:**
- RED commit: `2b48f40` — `test(02-04): add failing per-club cookie strategy tests for TOT/RMA/PSG/CHE` (7 tests failed with ImportError/KeyError; 3 regression tests passed)
- GREEN commit: `12e6575` — `feat(02-04): add TOT/RMA/PSG/CHE cookie strategies` (all 20 tests pass)
- REFACTOR: not needed (additive change, no cleanup required)

## Verification

All acceptance criteria met:

| Check | Expected | Actual |
|-------|----------|--------|
| `^TOT_STRATEGY: CookieStrategy` in cookies.py | 1 | 1 |
| `^RMA_STRATEGY: CookieStrategy` in cookies.py | 1 | 1 |
| `^PSG_STRATEGY: CookieStrategy` in cookies.py | 1 | 1 |
| `^CHE_STRATEGY: CookieStrategy` in cookies.py | 1 | 1 |
| `"tottenham":` in cookies.py | 1 | 1 |
| `"chelsea":` in cookies.py | 1 | 1 |
| `"liverpool"` in cookies.py | 0 | 0 |
| `MANCITY_STRATEGY: CookieStrategy = {` in cookies.py | 1 | 1 |
| `len(GLOBAL_COOKIE_PRIORITIES) == 20` | True | True |
| `"tout accepter"` occurrences in cookies.py | 1 (PSG only) | 1 |
| Diff `scanner/capture/cookies.py` hunks | purely additive | purely additive (no `-` content lines) |
| Diff `analysis/` | empty | empty (`git diff --quiet analysis/` exit 0) |
| Full scanner pytest suite | all pass | 155/155 pass |

## Commits

1. `2b48f40` — `test(02-04): add failing per-club cookie strategy tests for TOT/RMA/PSG/CHE` (scanner/tests/test_cookies.py +102 lines)
2. `12e6575` — `feat(02-04): add TOT/RMA/PSG/CHE cookie strategies` (scanner/capture/cookies.py +42 lines)

## Deviations from Plan

None — plan executed exactly as written. All priority lists are verbatim from 02-RESEARCH.md §6. No deviation rules triggered.

## Decisions Made

No new architectural decisions. All implementation choices were pre-locked by the plan:
- Priority order per club — locked by 02-RESEARCH.md §6
- Additive-only constraint — locked by D-21
- No French in GLOBAL_COOKIE_PRIORITIES — locked by user decision 2
- No Liverpool strategy — locked by CLAUDE.md project rule

## Known Stubs

None. All four strategies are production-ready configurations sourced from research. They remain hypotheses until first-crawl verification (TOT/CHE are "likely OneTrust", PSG is "likely Didomi or Axeptio", RMA is "custom ES banner likely") — but this is documented in file comments and is the correct level of commitment for pre-crawl config. The back-half capture wave will exercise them and report mismatches.

## Threat Flags

None. No new trust boundaries introduced. The STRIDE register in the plan already tracks T-02-04-01 (banner-wording changes → DoS) with an accepted mitigation (fallback to `GLOBAL_COOKIE_PRIORITIES` sweep). All mitigations from the threat register held:

- **T-02-04-02** (Liverpool opportunistic add) — grep confirms 0 occurrences
- **T-02-04-03** (`dismiss_cookies` body edit) — git diff confirms no `-` lines in function body
- **T-02-04-04** (French added to GLOBAL list) — `len(GLOBAL_COOKIE_PRIORITIES) == 20` confirmed, French present only inside `PSG_STRATEGY.priority`

## Self-Check: PASSED

- `scanner/capture/cookies.py` exists with 4 new constants (verified via grep counts)
- `scanner/tests/test_cookies.py` extended with 10 new tests (verified via pytest run)
- RED commit `2b48f40` exists in git log
- GREEN commit `12e6575` exists in git log
- `dismiss_cookies()` body byte-for-byte unchanged (verified via `git diff` containing only additive hunks)
- No Liverpool strategy anywhere (verified via grep count 0)
- `GLOBAL_COOKIE_PRIORITIES` length still 20 (verified at Python runtime)
- Full scanner pytest suite green (155/155)
