---
phase: 02-hospitality-pilot
plan: 02-19
title: Patchright stealth-fork retry against Cloudflare Turnstile (negative result)
type: out-of-band tactical
subsystem: scanner
status: complete
result: negative
date_started: 2026-04-28
date_completed: 2026-04-28
tags:
  - scanner
  - capture
  - cloudflare
  - turnstile
  - patchright
  - stealth
  - hospitality-pilot
  - negative-result
  - phase-2-closure
dependency_graph:
  requires:
    - 02-15 (scanner v2 — playwright-stealth integration)
    - 02-16 (recapture wave + stealth probe + Chrome MCP escalation list)
    - 02-18 (DOM rule tuning — v2.5 baseline)
  provides:
    - patchright>=1.49 dependency in scanner/pyproject.toml
    - browser.create_browser(engine="playwright"|"patchright") dispatch
    - capture.capture_flow(engine=...) passthrough
    - CLI --engine [playwright|patchright] flag (flow-map mode)
    - 4 new regression tests in scanner/tests/test_browser.py
    - Run-logs evidencing Patchright's behavior on mancity + psg
    - Negative-result documentation: Patchright does NOT bypass Cloudflare
      Turnstile interactive challenges under headless automation
  affects:
    - 02-14 (pilot acceptance gate — Patchright path now known to NOT close
      the 9 still-blocked steps; v2.5 16.7% coverage stands as final)
    - Phase 2.5 expansion plan (Cloudflare bypass formally escalated as
      Phase 2.5 prerequisite — Chrome MCP / browser-as-a-service / paid
      anti-bot vendor)
tech_stack:
  added:
    - patchright>=1.49 (stealth-patched Playwright fork, 35MiB Chromium)
  patterns:
    - "Engine dispatch with lazy import (patchright not loaded unless requested)"
    - "Stealth double-application avoidance (Patchright skips playwright-stealth path)"
key_files:
  created:
    - .planning/phases/02-hospitality-pilot/02-19-PATCHRIGHT-RETRY-SUMMARY.md
  modified:
    - scanner/pyproject.toml (+patchright dep)
    - scanner/capture/browser.py (engine dispatch + lazy import)
    - scanner/capture/capture.py (capture_flow engine kwarg passthrough)
    - scanner/cli.py (--engine flag wired into capture_flow call)
    - scanner/tests/test_browser.py (+4 regression tests)
decisions:
  - "Patchright integration kept additive — playwright-stealth code path is
    unchanged and remains the default. Ships as opt-in tool for future
    Cloudflare-edge-tier evaluation, not a default-on regression."
  - "Patchright skips playwright-stealth application by design (Patchright
    ships its own Chromium-level patches; double-applying triggers a
    UserWarning and is redundant)."
  - "Retry wave proves Patchright passes initial TLS fingerprinting (HTTP 200
    on PSG-billetterie vs HTTP 403 under playwright-stealth) but does NOT
    bypass Cloudflare's JavaScript Turnstile widget after the page reaches
    networkidle. The interactive 'Verify you are human' challenge remains
    unresolved under headless automation."
  - "Negative result accepted as final. Phase 2 pilot acceptance gate stands
    at v2.5 (16.7% coverage, 5/55 features, -362 aggregate score). Cloudflare
    bypass deferred to Phase 2.5 with three escalation paths: Chrome MCP,
    browser-as-a-service (Browserbase / Bright Data), or paid CAPTCHA-solver
    integration (CapMonster, 2Captcha)."
metrics:
  duration_minutes: ~50 (15 min integration, 5 min probe, 15 min capture wave,
    15 min triage + summary)
  vision_calls_total: 0 (no re-vision triggered — captures are still Turnstile pages)
  subscription_cost_usd: 0
  scanner_tests: 359 passing (was 355 + 4 new)
  patchright_probe_results:
    mancity: BLOCKED (HTTP 403, content_size=911686, all CF challenge tokens hit)
    psg-billetterie: UNBLOCKED-AT-PROBE (HTTP 200, no CF tokens at goto-time)
  patchright_capture_wave_results:
    mancity: 11 captures all 251_502 bytes (Cloudflare interstitial signature)
    psg: 10 captures, billetterie PNGs 885_895 bytes — pixel-verified to be
      "VÉRIFICATION DE SÉCURITÉ REQUISE" Turnstile widget despite
      stealth-override-unblocked tag
  files_changed: 5 source + 1 doc = 6
  commits: 2 feat + 1 docs (this commit)
---

# Phase 2 Plan 02-19: Patchright Retry — Negative Result Summary

Out-of-band tactical evaluation of Patchright (stealth-patched Playwright fork)
as a Cloudflare Turnstile bypass for the 9 still-blocked steps surfaced by
Plan 02-16's pixel-verified Chrome MCP escalation list. Retry wave proved
Patchright is **not** a viable replacement for human-presenced Chrome MCP
sessions on Cloudflare-Turnstile-protected pages. Phase 2 pilot acceptance
stands at v2.5 (Plan 02-18's 16.7% coverage baseline).

## TL;DR

| Result | Detail |
|--------|--------|
| Pilot coverage delta v2.5 → v3 | **0 cells** (no net change) |
| Patchright probe (HTTP layer) | 1/2 unblocked (PSG-billetterie HTTP 200; mancity still HTTP 403) |
| Patchright capture (full headless run) | **0/9** still-blocked steps recovered |
| New PNGs unlocked vs v2.5 | 0 |
| Re-vision triggered | No (no new captures to process) |
| Subscription cost | $0 (no vision calls) |
| v2.5 baseline preservation | Intact (analysis/hospitality/results/ unchanged) |
| D-20 invariant (homepage results) | Intact |
| Scanner test suite | 359 passing (355 baseline + 4 new) |

## What Was Built

### Code (Plan 02-19 commits)

1. **`feat(02-19): add patchright dependency + engine= dispatch in browser.py`**
   - `patchright>=1.49` added to `scanner/pyproject.toml` deps
   - `create_browser()` gains `engine: Literal["playwright", "patchright"] = "playwright"` kwarg
   - When `engine="patchright"`: lazy-imports `patchright.sync_api.sync_playwright`,
     skips applying `playwright-stealth` (Patchright already provides equivalent at
     Chromium-patch level)
   - 4 regression tests added: default-engine path, patchright dispatch,
     patchright-skips-stealth, invalid-engine raises ValueError

2. **`feat(02-19): wire engine= through capture_flow + CLI; retry wave (negative)`**
   - `capture_flow()` accepts `engine="playwright"` default kwarg, threads it into
     `create_browser()`
   - CLI `capture` command gains `--engine [playwright|patchright]` Click choice flag
     (flow-map mode only — single-page mode kept on default for parity)
   - Retry wave run-logs preserved (gitignored but on disk for forensic recall)

### Defaults preserved

- `create_browser()` defaults to `engine="playwright"` — Plan 02-15 Wave A behavior unchanged
- All 359 scanner tests pass; 0 regressions
- `git diff --quiet analysis/homepage/` exit 0 — D-20 invariant intact
- `git diff --quiet analysis/hospitality/` exit 0 — v2.5 baseline intact

## Patchright Probe — HTTP Layer

Side-effect-free `goto(domcontentloaded)` probe via the new `engine="patchright"`
path. Probe ran on the 2 known-Turnstile URLs from Plan 02-16's escalation list:

| Club | URL | HTTP | Title | CF tokens | Verdict |
|------|-----|-----:|-------|-----------|---------|
| mancity | `https://www.mancity.com/hospitality` | **403** | `Just a moment...` | 5 hits (`challenges.cloudflare.com`, `cf-turnstile`, `cf-chl-`, `_cf_chl_opt`, `just a moment`) | **BLOCKED** |
| psg-billetterie | `https://billetterie.psg.fr/en/home-vip` | **200** | `VIP & hospitality offers \| Paris Saint-Germain` | 0 hits at goto-time | **UNBLOCKED (HTTP)** |

**Read this:** PSG-billetterie's TLS fingerprint passed Cloudflare's edge under
Patchright (vs HTTP 403 / interstitial under playwright-stealth). MCFC's
edge-tier Cloudflare configuration rejects even Patchright's TLS fingerprint —
expected, since MCFC clearly runs a stricter ruleset (commercial site under
heavy bot-pressure).

## Patchright Capture Wave — Full Headless Run

Full `capture_flow` against the same 2 clubs with `--auto-skip-manual
--allow-stealth-override-manual --engine patchright`:

| Club | Captures | Errors | Missing-creds | Run-log |
|------|---------:|-------:|--------------:|---------|
| mancity | 11 | 2 | 0 | `scanner/output/capture-run-log-hospitality-mancity-20260428T201735Z.json` |
| psg | 10 | 3 | 1 | `scanner/output/capture-run-log-hospitality-psg-20260428T201538Z.json` |

### Pixel-verification of "captured" PNGs

The run-log status `captured` reflects HTTP success, not visual content. Manual
inspection of the resulting PNGs:

**Manchester City (all 11 captured):**
- All PNGs sized exactly **251,502 bytes** — file-size-identical signature of
  the Cloudflare `REDIRECTING…` interstitial with embedded Turnstile widget
  ("Verify you are human" + Cloudflare logo)
- 0 PNGs contain real hospitality content
- Net change vs v2.5: **0**

**PSG (10 captured):**
- 3 main-domain PNGs sized 19,305 bytes (blank/post-banner; same as v2.5 baseline)
- 3 billetterie PNGs sized **885,895 bytes** with `reason="stealth-override-unblocked"`
  in the run-log — pixel-verified to display "**VÉRIFICATION DE SÉCURITÉ REQUISE** /
  CAPTCHA BOX / Verify you are human" Turnstile widget overlaid on PSG branding
- 0 PNGs contain real billetterie hospitality content
- Net change vs v2.5: **0**

### Why probe succeeded but capture failed

The probe used `wait_until="domcontentloaded"` followed by 6s `time.sleep`. The
capture pipeline (`capture_page` / `_execute_action` for `navigate`) uses
`domcontentloaded` THEN `wait_for_load_state("networkidle", timeout=30_000)` THEN
`time.sleep(2)`. The longer `networkidle` wait gives Cloudflare's JS challenge
ample time to render the Turnstile widget DOM, which the probe's 6-second
quick-check missed.

The widget is interactive (mouse-click required) and cannot be solved by any
amount of fingerprint stealth. Patchright vs playwright-stealth is the same
class of evasion (network-level + runtime-property masks) — once the widget
renders client-side, headless automation is stuck without either:
1. A real human (Chrome MCP)
2. A vendor solver (CapMonster, 2Captcha — paid, ToS-grey, ~$0.001/solve)
3. A managed browser-as-a-service with built-in solver (Browserbase, Bright Data)

## Per-Step Outcome vs Plan 02-16 Escalation List

Cross-reference against `scanner/output/CHROME-MCP-NEEDED.md` Section A
(9 genuine Cloudflare blocks):

| Step | v2.5 status | v3 (Patchright) | Recovered? |
|------|-------------|-----------------|------------|
| mancity / landing | Turnstile interstitial | Turnstile interstitial (251KB) | No |
| mancity / landing-shot | Turnstile interstitial | Turnstile interstitial (251KB) | No |
| mancity / tier-tunnel-club-premier-shot | Turnstile interstitial | Turnstile interstitial (251KB) | No |
| mancity / tier-tunnel-club-shot | Turnstile interstitial | Turnstile interstitial (251KB) | No |
| mancity / tier-backstage-shot | Turnstile interstitial | Turnstile interstitial (251KB) | No |
| mancity / enquiry-form-prefill-shot | Turnstile interstitial | Turnstile interstitial (251KB) | No |
| psg / billetterie-home-vip-shot | Turnstile FR | Turnstile FR (886KB) | No |
| psg / billetterie-match-selector-shot | Turnstile FR | Turnstile FR (886KB) | No |
| psg / enquiry-form-prefill-shot (billetterie path) | Turnstile FR | Turnstile FR (886KB) | No |
| **TOTAL recovered** | — | — | **0/9** |

## Coverage Comparison v2.5 → v3

Per-club deltas:

| Club | v2.5 P | v3 P | Δ | v2.5 D | v3 D | Δ | v2.5 Score | v3 Score | Δ Score |
|------|------:|----:|--:|------:|----:|--:|----------:|--------:|--------:|
| Tottenham | 14 | 14 | 0 | 1 | 1 | 0 | -40 | -40 | 0 |
| Real Madrid | 14 | 14 | 0 | 1 | 1 | 0 | -42 | -42 | 0 |
| Chelsea | 9 | 9 | 0 | 5 | 5 | 0 | -75 | -75 | 0 |
| Manchester City | 5 | 5 | 0 | 0 | 0 | 0 | -99 | -99 | 0 |
| Paris Saint-Germain | 4 | 4 | 0 | 0 | 0 | 0 | -106 | -106 | 0 |
| **TOTAL** | **46** | **46** | **0** | **7** | **7** | **0** | **-362** | **-362** | **0** |

No vision wave triggered (no new content to score). v2.5 results stand as
final pilot baseline.

## Acceptance & Recommendation

### Patchright integration: ACCEPTED (additive tool)

The engine-dispatch code stays. It costs nothing on the default path
(playwright-stealth still applies, default behavior preserved) and gives Phase
2.5 / Phase 3 a tested escape hatch should Cloudflare's edge-tier defenses
shift in our favor — which they sometimes do (the arms race cuts both ways).

### Retry result: NEGATIVE (Cloudflare arms race)

Patchright is one rung up the stealth ladder from playwright-stealth, but
Cloudflare's enterprise customers (MCFC) and JS-challenge-protected vendor
sites (PSG-billetterie) are operating at a higher rung still. Recovering
those 9 steps requires interactive solving, not stealth.

### Phase 2 pilot acceptance: v2.5 STANDS

- 5 clubs pilot-verified at 16.7% coverage (46/275 cells present, 7/275 disputed)
- Aggregate score -362 (Tottenham leads at -40, PSG closes at -106)
- 0 universal-present features; 35 universal-absent
- Hybrid DOM+vision pipeline at 35.9% DOM-resolution rate (cost-leverage proven)
- All-the-while $0 subscription cost in both v1, v2, v2.5, and v3 retry waves

### Phase 2.5 prerequisite (formally escalated)

Cloudflare bypass for the 9 remaining steps becomes a Phase 2.5 entry condition.
Three viable escalation paths in priority order:

1. **Chrome MCP (manual)** — $0, ToS-clean, ~30 min user time per club for the
   9 outstanding steps. **Recommended for pilot closure.** User drives a
   real Chrome session, scanner records DOM intel + screenshot via the
   existing `manual_chrome_mcp` flow.
2. **Browser-as-a-service** (Browserbase / Bright Data) — ~$50/mo, includes
   built-in Turnstile solving, drop-in Playwright-API-compatible. Worth a
   1-club POC before Phase 3 (when the matrix expands to 33 clubs and manual
   Chrome MCP no longer scales).
3. **CAPTCHA-solver vendor** (CapMonster / 2Captcha) — ~$0.001/solve, ToS-grey
   on Cloudflare's side. Avoid until BaaS option is benched.

### What we would NOT do

- Continue retrying additional stealth forks (rebrowser-playwright, undetected-
  chromedriver) — same evasion class, same arms-race ceiling.
- Accept Turnstile interstitial PNGs as evidence — they would inflate
  coverage with bogus hits.
- Block Phase 3 on closing the 9 steps — pilot already validates the rubric +
  pipeline. Phase 3 can scale on the proven 5-club path while Phase 2.5 closes
  the Cloudflare gap independently.

## Self-Check

Created files:
- `.planning/phases/02-hospitality-pilot/02-19-PATCHRIGHT-RETRY-SUMMARY.md` ✓ FOUND

Modified files (Plan 02-19 commits):
- `scanner/pyproject.toml` (+patchright dep) ✓
- `scanner/capture/browser.py` (engine dispatch) ✓
- `scanner/tests/test_browser.py` (+4 tests, 359 total passing) ✓
- `scanner/capture/capture.py` (capture_flow engine kwarg) ✓
- `scanner/cli.py` (--engine flag) ✓

Commits (this branch):
- `341159e feat(02-19): add patchright dependency + engine= dispatch in browser.py` ✓
- `a6b661f feat(02-19): wire engine= through capture_flow + CLI; retry wave (negative)` ✓
- (this commit will record `docs(02-19): patchright retry summary (negative result)`)

Invariants:
- `git diff --quiet analysis/homepage/` exit 0 ✓
- `git diff --quiet analysis/hospitality/` exit 0 ✓ (v2.5 results untouched)
- Subscription cost: $0 ✓
- Scanner tests: 359 passing ✓ (was 355 baseline + 4 new patchright tests)
- ANTHROPIC_API_KEY untouched ✓ (no vision calls made)

## Self-Check: PASSED
