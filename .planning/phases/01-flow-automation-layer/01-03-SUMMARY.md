---
phase: 01-flow-automation-layer
plan: 03
subsystem: scanner.capture
tags: [playwright, capture, cookies, banner-verify, form-fill, d-12, d-13, d-14, d-16]

dependency_graph:
  requires:
    - "Plan 01 (Wave 0): scanner package skeleton, pyproject with playwright, jinja2, anthropic, claude-agent-sdk"
    - "Plan 02 (Wave 1): scanner.flow.schema.FormField (typed as forward-reference for TYPE_CHECKING-only import)"
  provides:
    - "scanner.capture.browser: create_browser(club, area, *, headless), scroll_lazy, USER_DATA_ROOT"
    - "scanner.capture.cookies: dismiss_cookies(page, club, max_attempts), GLOBAL_COOKIE_PRIORITIES (20), STRATEGIES, MANCITY_STRATEGY"
    - "scanner.capture.banner_verify: verify_banner_gone(path, *, api_mode) -> bool (Haiku-pinned, lazy factory import)"
    - "scanner.capture.capture: capture_page(url, club, area, step_name, output_dir, *, headless, hide_selectors) -> Path"
    - "scanner.capture.form_dummy: DUMMY_VALUES, fill_form (page.fill only — D-16)"
  affects:
    - "Plan 04 (vision factory) — banner_verify will consume scanner.vision.factory.get_client via lazy import; Plan 04's VisionClient protocol must add `.ask_yes_no(screenshot_path, prompt) -> str` alongside `.analyze_screenshot`"
    - "Plan 07 (CLI) — `python -m scanner capture` wraps capture_page()"
    - "Plan 08 (dry-run) — one-club Man City smoke test consumes MANCITY_STRATEGY"

tech_stack:
  added: []  # playwright, claude-agent-sdk, anthropic were already in Plan 01 lockfile
  patterns:
    - "Persistent Playwright context per (area, club) — session survives across invocations, never leaks cross-area (D-13)"
    - "Try/finally teardown: ctx.close() + pw.stop() in finally-block so DoS from a hung navigation (T-03-04) can't leak processes"
    - "Lazy import of scanner.vision.factory inside verify_banner_gone — breaks circular-import constraint with Plan 04 while allowing isolated test runs (ImportError → permissive True + WARNING)"
    - "TYPE_CHECKING-only imports in form_dummy.py so FormField reference doesn't require playwright at module load"
    - "Grep-test as D-16 runtime invariant — test_no_submit_clicks_in_capture_module scans whole capture/ tree on every pytest run"
    - "TypedDict for CookieStrategy — total=False, optional priority + post_click_selectors"

key_files:
  created:
    - path: scanner/capture/browser.py
      role: "Playwright persistent-context factory + bounded scroll_lazy — D-12 viewport/DPR, D-13 user-data isolation"
    - path: scanner/capture/cookies.py
      role: "Per-club cookie dismissal dispatcher — 20-entry GLOBAL_COOKIE_PRIORITIES + MANCITY_STRATEGY populated"
    - path: scanner/capture/banner_verify.py
      role: "Post-capture Haiku yes/no banner check (D-14) — lazy vision-factory import with permissive fallback"
    - path: scanner/capture/capture.py
      role: "capture_page orchestrator — cookies-first, hide-selectors, scroll, full-page PNG"
    - path: scanner/capture/form_dummy.py
      role: "DUMMY_VALUES + fill_form — D-16 invariant (page.fill only, zero dispatch clicks)"
  modified:
    - path: scanner/tests/test_browser.py
      change: "Populated: 12 tests (6 create_browser, 2 scroll_lazy, 3 capture_page, 1 D-16 grep-test)"
    - path: scanner/tests/test_cookies.py
      change: "Populated: 10 tests (GLOBAL count, MANCITY priority, STRATEGIES dict, dispatch/fallback paths, max-attempts, exception swallow, post-click-selectors)"
    - path: scanner/tests/test_banner_verify.py
      change: "Populated: 5 tests (yes/no normalisation, Haiku model pin, permissive ImportError fallback)"

decisions:
  - id: D-03-1
    text: "CookieStrategy is a TypedDict (total=False) not a dataclass/pydantic model — keeps MANCITY_STRATEGY a plain dict that tests can monkeypatch onto STRATEGIES without model-construction overhead, and keeps the contract structural-typing-friendly for future per-club additions."
  - id: D-03-2
    text: "banner_verify catches ImportError (not general Exception) on the lazy `from scanner.vision.factory import get_client` — narrowly scoped so a real bug inside Plan 04 code isn't silently swallowed, only the absence of the module itself."
  - id: D-03-3
    text: "`time` is imported at module top of capture.py and inside scroll_lazy of browser.py — capture.py needs monkeypatch support for the settle sleep (tests patch `capture_mod.time.sleep`); browser.py's scroll_lazy uses local `import time` so the tight scroll loop's sleep isn't globally monkeypatched (would break test_scroll_lazy_is_bounded if shared)."
  - id: D-03-4
    text: "Cookies dismissed BEFORE scroll_lazy in capture_page, reversing the order from capture_elements.py which scrolled first. Rationale: on Man City, cookie banner overlays the full viewport — scrolling while it's present just scrolls the page underneath it. Dismiss-first yields a consistent pre-scroll screenshot."
  - id: D-03-5
    text: "Docstrings in capture.py and form_dummy.py rephrased away from the exact pattern `.click(...submit...)` — the D-16 grep-test tripped on prose mentioning the pattern. This is a Rule 1 bug-fix: the grep pattern is the canonical check, and prose that matches it is a false positive that also means the invariant is weakly worded. Rewording strengthens both docs and test."

metrics:
  duration: "~90 minutes"
  completed_date: "2026-04-24"
  tasks_planned: 2
  tasks_completed: 2
  tests_added: 27
  tests_passing: 27
  loc_added: 1025  # 5 capture modules + 3 test files (tests re-count from empty scaffold)
---

# Phase 01 Plan 03: Capture Module Summary

Area-agnostic capture pipeline landed — `capture_page(url, club, area, step_name, output_dir)` returns a Path to a full-page PNG via Playwright persistent context (1440×900 @ DPR 2), with dispatch-to-Haiku banner verification and the D-16 never-dispatch invariant enforced by a grep-test baked into the suite.

## What Landed

**Five capture modules, 438 source LOC, 1025 LOC total including tests:**

1. **`scanner/capture/browser.py`** (109 LOC) — `create_browser(club, area, *, headless=False)` launches a persistent Chromium context with locked viewport 1440×900, `device_scale_factor=2`, and a per-(area, club) user-data dir under `~/.scanner/user-data/{area}/{club}`. The per-area layer of that tree is the D-13 invariant: Phase 2 hospitality sessions for Man City cannot leak into Phase 5 ticket captures for the same club. `scroll_lazy(page)` is a verbatim port of `recapture_round5.py::scroll_lazy` — bounded at 15 steps to mitigate T-03-04 (infinite-scroll DoS).

2. **`scanner/capture/cookies.py`** (120 LOC) — `dismiss_cookies(page, club, max_attempts=3)` dispatcher. `GLOBAL_COOKIE_PRIORITIES` holds the 20-entry priority list ported verbatim from research §2.2 (English + Spanish + German + Portuguese + Italian variants). `MANCITY_STRATEGY` is the single populated entry in `STRATEGIES` — two-item priority `["accept all cookies", "accept all"]`, ready for Plan 08's dry-run. `CookieStrategy` is a TypedDict (total=False) so Phase-2+ additions are drop-in dicts. Liverpool is intentionally absent per CLAUDE.md trap.

3. **`scanner/capture/banner_verify.py`** (70 LOC) — `verify_banner_gone(path, *, api_mode="subscription") -> bool`. Sends the screenshot to Claude Haiku with a one-word yes/no prompt; returns True when clean. The `from scanner.vision.factory import get_client` is inside the function to break the circular-import constraint with Plan 04 (which ships the factory). On `ImportError`, the function logs a WARNING and returns True permissively — isolated plan-03 test runs don't have Plan 04 yet, and CI gets both.

4. **`scanner/capture/capture.py`** (96 LOC) — `capture_page(url, club, area, step_name, output_dir, *, headless=False, hide_selectors=None) -> Path`. Orchestrates: `create_browser` → `goto(wait_until="domcontentloaded")` → `wait_for_load_state("networkidle")` → 2s settle → **cookies FIRST** (CLAUDE.md trap) → `add_style_tag` for hide_selectors (D-17) → `scroll_lazy` → `page.screenshot(full_page=True)` → write to `output_dir/fullpage/{club}_{step_name}.png`. Teardown is in a `try/finally` so a hung nav or screenshot doesn't leak a Playwright process.

5. **`scanner/capture/form_dummy.py`** (43 LOC) — `DUMMY_VALUES` (name/email/phone/postal/default) + `fill_form(page, form_fields)`. Pure `page.fill(...)` loop, zero dispatch clicks. The D-16 grep-test in `test_browser.py` enforces the invariant across the entire `scanner/capture/` tree on every pytest run.

## Test Coverage

**27 tests across 3 files, 27 green, 0 skipped, 0 flaky.** Runtime 15.5s (most of it is module-load overhead inside uv's resolver — the actual test execution is sub-second).

| File | Tests | Key coverage |
|------|-------|--------------|
| `test_browser.py` | 12 | 6 create_browser (return shape, viewport 1440×900, DPR=2, user-data dir path, headless default+opt-in, UA+sandbox), 2 scroll_lazy (scrollTo call + bounded ≤20 evaluate calls on 10M-px page), 3 capture_page (output path + non-empty PNG, teardown on exception, hide_selectors CSS), 1 D-16 grep-test |
| `test_cookies.py` | 10 | GLOBAL list length=20, MANCITY priority asserts "accept all cookies" first, STRATEGIES["mancity"] dispatch, success-on-first-attempt, per-club priority passed (not global), global fallback for None/unknown club, max-attempts exhaustion, exception-swallow during races, post_click_selectors invocation order |
| `test_banner_verify.py` | 5 | Yes→False, No→True, Haiku model pin asserted via factory kwargs, case/punctuation normalisation ("  NO.  " → True), ImportError fallback returns True + WARNING log |

## Port Surprises

- **`capture_elements.py::process_club()`** is 90 lines of tightly coupled per-feature capture logic. Per research §8 (only ~30 lines survive the generalisation), the actual surviving patterns were just three: viewport/UA kwargs for `new_context`, the cookie-dismissal JS `evaluate` call, and the lazy-scroll loop. The rest (FEATURE_LOCATORS dispatch, per-feature cropping, fallback regions) all belongs to Plan 05's slice module, not capture.
- **`recapture_round5.py::scroll_lazy`** was essentially copy-portable — only change was making `step_px` and `settle_ms` parameters instead of hardcoded constants, and tightening exception handling so a failed first `evaluate` (document.body.scrollHeight) returns early cleanly instead of entering the loop with `h=None`.
- **Research §2.2's `CLUB_STRATEGIES`** was a commented-out dict literal. Plan 03's version populates Man City (the dry-run target) with the verified wording "accept all cookies" — that exact string is the first entry, so the generic `btn.textContent.includes("accept all cookies")` match wins before the shorter "accept all" prefix matches any other button on the page.

## MANCITY_STRATEGY size

Priority list length: **2** (`["accept all cookies", "accept all"]`). No `post_click_selectors` yet — Man City's hospitality landing page has no known post-consent promo popup as of 2026-04-24. If Plan 08's dry-run surfaces a newsletter modal that the Haiku check flags, it goes into `MANCITY_STRATEGY["post_click_selectors"]` as a follow-up commit within this plan's scope.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] D-16 grep-test tripped on docstring prose**

- **Found during:** Task 2, first GREEN-phase test run
- **Issue:** `scanner/capture/capture.py` and `scanner/capture/form_dummy.py` both had docstrings that included the literal pattern `.click("[type=submit]")` or `.click(*, submit*)` as *examples of what NOT to do*. The D-16 grep-test uses regex `\.click\([^)]*submit` which matched those docstrings, failing the invariant check even though no runtime code violated it.
- **Fix:** Rephrased both docstrings to describe the invariant without naming the forbidden pattern (swapped "submit" → "dispatch"). The invariant is now stated positively ("page.fill only") and the grep-test remains the canonical check.
- **Files modified:** `scanner/capture/capture.py`, `scanner/capture/form_dummy.py`
- **Commit:** bundled into Task 2 commit `c698393`

No Rule 2 (missing critical), Rule 3 (blocking), or Rule 4 (architectural) escalations.

## Invariant Gates

| Gate | Check | Result |
|------|-------|--------|
| D-16 (never dispatch) | `grep -rE '\.click\([^)]*submit' scanner/capture/` | no matches — PASS |
| D-24 (analysis/ untouched) | `git diff --quiet analysis/` | exit 0 — PASS |
| CLAUDE.md Liverpool trap | `grep -ri 'liverpool' scanner/capture/*.py` | no matches — PASS |
| D-12 viewport+DPR | `grep` for `"width": 1440, "height": 900` + `device_scale_factor=2` in browser.py | 1+2 matches — PASS |
| Haiku pin (D-14) | `grep claude-haiku-4-5 scanner/capture/banner_verify.py` | 1 match — PASS |

## Commits

| Hash      | Message                                                                           |
|-----------|-----------------------------------------------------------------------------------|
| `e30c8e0` | `feat(01-03): add browser factory + cookie dismissal dispatcher (Task 1)`         |
| `c698393` | `feat(01-03): add capture orchestrator + banner verify + form_dummy (Task 2)`     |

## Self-Check: PASSED

- `scanner/capture/browser.py` exists (109 LOC) — FOUND
- `scanner/capture/cookies.py` exists (120 LOC) — FOUND
- `scanner/capture/banner_verify.py` exists (70 LOC) — FOUND
- `scanner/capture/capture.py` exists (96 LOC) — FOUND
- `scanner/capture/form_dummy.py` exists (43 LOC) — FOUND
- `scanner/tests/test_browser.py` populated (12 tests, 295 LOC) — FOUND
- `scanner/tests/test_cookies.py` populated (10 tests, 160 LOC) — FOUND
- `scanner/tests/test_banner_verify.py` populated (5 tests, 132 LOC) — FOUND
- Commits `e30c8e0` and `c698393` present in `git log` — FOUND
- `uv run pytest tests/test_browser.py tests/test_cookies.py tests/test_banner_verify.py` → 27 passed, 0 failed — PASS
- `grep -rE '\.click\([^)]*submit' scanner/capture/` → no matches — PASS
- `git diff --quiet analysis/` → exit 0 — PASS
- Haiku model pin `claude-haiku-4-5` present in `scanner/capture/banner_verify.py` — FOUND
- Lazy `from scanner.vision.factory import get_client` inside `verify_banner_gone` (not at module top) — FOUND
