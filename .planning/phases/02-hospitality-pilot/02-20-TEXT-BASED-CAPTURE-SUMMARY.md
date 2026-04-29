---
phase: 02-hospitality-pilot
plan: 02-20
title: Text-based capture fallback for Cloudflare-blocked clubs (positive result)
type: out-of-band tactical
subsystem: scanner
status: complete
result: positive
date_started: 2026-04-29
date_completed: 2026-04-29
tags:
  - scanner
  - capture
  - cloudflare
  - text-fetch
  - synthetic-intel
  - hospitality-pilot
  - phase-2-closure
  - positive-result
dependency_graph:
  requires:
    - 02-15 (scanner v2 — hybrid DOM+vision pipeline)
    - 02-17 (DOM intel auto-discovery via {club}_{step}_intel.json convention)
    - 02-18 (DOM rule tuning — v2.5 baseline)
    - 02-19 (Patchright retry — established Cloudflare cannot be bypassed via stealth)
  provides:
    - DomIntel.text_extracts + DomIntel.source schema additions (back-compat)
    - dom_detect rules now consult text_extracts as fallback
    - scanner/capture/text_fetch.py — stdlib-only HTTP fetcher + HTML→text parser
    - scanner/config/reseller_urls.json — area→club→reseller-URL config
    - scanner/scripts/run_text_capture.py — Click CLI for synthetic capture
    - scanner/scripts/run_synthetic_wave.py — synthetic-source counterpart to run_vision_wave
    - 12 new regression tests in scanner/tests/test_text_fetch.py
    - Run-logs evidencing DOM-rule firing on reseller-text content
    - v3 pilot coverage report at .planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT-V3.md
  affects:
    - 02-14 (pilot acceptance gate — Phase 2 closes at v3 with 16 additional
      cells across MCFC + PSG; aggregate −362 → −290)
    - Phase 2.5 entry condition (Cloudflare bypass remains the bigger lever
      for Phase 3 scaling, but pilot is now substantively useful even
      without it)
tech_stack:
  added: []  # stdlib-only — no new third-party deps
  patterns:
    - "Synthetic DomIntel with source='synthetic' provenance marker"
    - "text_extracts as fallback text surface for DOM rules — keeps live and
      synthetic captures behind a single rule registry"
    - "Per-step intel-file fan-out so existing run_vision_wave auto-discovery
      finds synthetic intel without code changes"
    - "Stdlib HTML parser with depth-counter skip-tag tracking
      (script/style/noscript/svg/iframe stripping)"
key_files:
  created:
    - .planning/phases/02-hospitality-pilot/02-20-TEXT-BASED-CAPTURE-SUMMARY.md
    - .planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT-V3.md
    - scanner/capture/text_fetch.py (~365 lines)
    - scanner/config/reseller_urls.json
    - scanner/scripts/run_text_capture.py
    - scanner/scripts/run_synthetic_wave.py
    - scanner/tests/test_text_fetch.py (12 tests)
    - scanner/output/evidence/hospitality/dom/mancity_synthetic_intel.json
    - scanner/output/evidence/hospitality/dom/mancity_{landing,tier-tunnel-club,tier-tunnel-club-premier,tier-backstage,enquiry-form-prefill}-shot_intel.json
    - scanner/output/evidence/hospitality/dom/psg_synthetic_intel.json
    - scanner/output/evidence/hospitality/dom/psg_{billetterie-home-vip,billetterie-match-selector,enquiry-form-prefill}-shot_intel.json
    - scanner/output/text/hospitality/mancity_aggregated.md (audit trail)
    - scanner/output/text/hospitality/psg_aggregated.md (audit trail)
    - scanner/output/capture-run-log-hospitality-mancity-synthetic.json
    - scanner/output/capture-run-log-hospitality-psg-synthetic.json
    - scanner/output/results/hospitality/mancity_features.json (synthetic-source per-club result)
    - scanner/output/results/hospitality/psg_features.json (synthetic-source per-club result)
  modified:
    - scanner/capture/dom_intel.py (+text_extracts +source fields, additive)
    - scanner/vision/dom_detect.py (text_extracts surface in rules; new
      "book online" keyword in buy_now_without_enquiry)
    - analysis/hospitality/results/mancity.json (re-derived: 5→14 present, score −99→−49)
    - analysis/hospitality/results/psg.json (re-derived: 4→8 present, score −106→−84)
    - analysis/hospitality/results/_aggregate.json (recomputed)
    - analysis/hospitality/results/_scores.json (recomputed)
decisions:
  - "Use stdlib (urllib + html.parser) only. No new deps satisfies D-21
    (additive-only, no new dependencies in Phase 2). Reseller fetches succeed
    on a vanilla desktop UA — no need for stealth here, the resellers WANT
    the content public for SEO."
  - "Synthetic intel goes through the standard {club}_{step}_intel.json
    convention so run_vision_wave's existing auto-discovery finds it
    unchanged. Per-step intel files are byte-identical (same synthetic
    surface for all steps the reseller covers); this is intentional and
    documented in text_fetch.py's docstring."
  - "Visual-only features on synthetic-source clubs are marked no-data
    (Plan 02-20 Phase 5 Option A). Honest absence beats reseller-image
    scraping (Option B was rejected — different threat model, copyright
    concerns)."
  - "DOM_CONFIDENCE stays at 0.95 for synthetic verdicts. A confidence
    penalty for synthetic-source is logged as a Phase 2.5 polish item,
    not a v3 blocker."
  - "WebSearch / WebFetch substituted with curl-equivalent stdlib fetch
    (Rule 3 deviation — those Anthropic agent primitives aren't available
    inside the running scanner; functional equivalence achieved with
    urllib.request)."
metrics:
  duration_minutes: ~70 (10 min read mandatory files, 25 min code, 15 min
    capture + re-derive, 10 min report writing, 10 min self-check)
  vision_calls_total: 0 (no vision calls — synthetic captures have no PNG
    to send to a vision client)
  subscription_cost_usd: 0
  scanner_tests_baseline: 343 passing (was ~331 before; 5 unrelated tests
    skipped due to anthropic / claude_agent_sdk not installed in this
    sandbox — same skip rate as before this plan)
  new_tests: 12 (test_text_fetch.py)
  reseller_pages_fetched: 8 OK / 8 attempted across both clubs (1 dropped
    due to HTTP 403 from hospitalitycentre.co.uk)
  synthetic_intel_chars:
    mancity: 77837
    psg: 36769
  dom_rules_fired_true_synthetic:
    mancity: 14 (was 5 in v2.5)
    psg: 8 (was 4 in v2.5)
  pilot_score_delta_v25_to_v3:
    mancity: +50 (-99 -> -49)
    psg: +22 (-106 -> -84)
    aggregate: +72 (-362 -> -290)
    cells_present_aggregate: +13 (46 -> 59)
  files_changed: 11 created + 6 modified = 17
  commits: 5 feat + 1 chore + 1 docs (this commit) = 7
---

# Phase 2 Plan 02-20: Text-based capture fallback (positive result)

Out-of-band tactical fix that closes the 9 still-blocked steps Plan 02-19's
Patchright retry could not recover. We sidestep Cloudflare entirely by reading
the same hospitality content from third-party reseller pages (which are not
Turnstile-gated because the resellers sell the packages and want public SEO).
Synthesize text into DomIntel-shaped JSON, run hybrid pipeline, lift
mancity + PSG out of single-digit pilot coverage. **Pilot acceptance: v3.**

## TL;DR

| Result | Detail |
|--------|--------|
| Pilot coverage delta v2.5 → v3 | **+13 present cells (+72 aggregate score)** |
| New True features (mancity) | **+9** — chef_attribution, fixture_list_visible, parking, stadium_tour, concierge, tunnel/pitchside, fixture_change_notification, price_per_person, menu_preview, etc. |
| New True features (psg) | **+4** — competition_filter, phone_booking, price_per_person, stadium_tour |
| MCFC pilot rank | 5th → **3rd** (−99 → −49) |
| PSG pilot rank | 5th → **5th** (−106 → −84, gap closing) |
| Subscription cost | **$0** (no vision calls — synthetic source has no PNG) |
| TOT/CHE/RMA invariance | bit-stable identical to v2.5 |
| D-20 homepage invariant | intact (`git diff --quiet analysis/homepage/` exit 0) |
| Scanner test suite | **343 passing** (12 new + ~331 baseline; same 5 skipped as before) |
| New deps | **0** (stdlib-only) |

## What Was Built

### 1. Schema extension (back-compat)

`scanner/capture/dom_intel.py` gains two optional `DomIntel` fields:

```python
text_extracts: list[str] = []
source: Literal["live", "synthetic"] = "live"
```

Live captures (every existing intel JSON) validate unchanged: defaults are
empty/`"live"`. Synthetic captures populate both fields.

### 2. Rule extensions

`scanner/vision/dom_detect.py`:
- `_all_text_blobs()` folds `intel.text_extracts` into the searchable surface
- New keyword path on `package_tier_list` (count tier-name keyword hits across
  text_extracts: tunnel club, backstage, platinum, dugout, centenary, gold,
  premium seat, executive club, presidential, vip seat, corporate box, skybox,
  loge)
- Synthetic-source presence-only fallback on `enquiry_form_field_count_le_7`
  (cannot count fields from prose)
- New text-extract path on `buy_now_without_enquiry`, `phone_booking_option`,
  `tier_comparison_table`
- Live-capture behavior unchanged (text_extracts is empty for live=intel)

### 3. `text_fetch.py` — stdlib HTTP + HTML→text

365 lines, no new deps. Highlights:
- `_TextExtractor`: `html.parser.HTMLParser` subclass with depth-counter skip
  logic (handles malformed HTML where stack-pop logic would leave entire body
  marked-as-skipped — fixed during integration testing)
- `_fetch_url`: `urllib.request.urlopen` with desktop UA + 20s timeout + 2.5MB
  cap. Returns `FetchResult(url, status, text, headings, links, error)` —
  never raises
- `synthesize_dom_intel`: aggregates fetches into one DomIntel with
  `source="synthetic"`, dedupes, caps text per URL
- `write_synthetic_outputs`: per-step intel JSONs + aggregated `_synthetic_intel.json` + `{club}_aggregated.md` audit
- `write_synthetic_run_log`: Plan-02-10-shaped run-log w/ `status="synthetic"`

### 4. Config + CLI

- `scanner/config/reseller_urls.json` — area → club → reseller_urls map
- `scanner/scripts/run_text_capture.py` — Click CLI driver
- `scanner/scripts/run_synthetic_wave.py` — runs hybrid pipeline against
  synthetic intel, emits Plan-02-11-shaped per-club JSON. **Zero vision calls.**

### 5. Tests

12 new tests in `scanner/tests/test_text_fetch.py`:
- HTML extractor strips script/style
- Whitespace normalization
- DomIntel synthesis sets source=synthetic, dedups headings/buttons,
  skips failed fetches
- Top-level glue calls fetcher per URL
- Persisted outputs land in expected places
- 4 bridge tests confirming dom_detect rules fire on synthetic intel

All 343 dom-related + judge + schema tests still pass.

## Reseller fetch results

### mancity — 4/4 OK, 77,837 text chars

| Source | HTTP | Text chars |
|---|---:|---:|
| eventmasters.co.uk             | 200 | 47,596 |
| rockethospitality.com          | 200 | 17,175 |
| vipfootballhospitality.com     | 200 |  6,813 |
| sportlux.co.uk                 | 200 |  5,868 |

(`hospitalitycentre.co.uk` HTTP 403; dropped from config.)

### psg — 4/4 OK, 36,769 text chars

| Source | HTTP | Text chars |
|---|---:|---:|
| rockethospitality.com          | 200 | 12,120 |
| mitickets.com                  | 200 | 13,355 |
| vipmatchdays.com               | 200 |  7,540 |
| seesports.co.uk                | 200 |  3,443 |

## Coverage Comparison v2.5 → v3

Per-club deltas (from `analysis/hospitality/results/`):

| Club | v2.5 P | v3 P | Δ | v2.5 Score | v3 Score | Δ Score | Method |
|------|------:|----:|--:|----------:|--------:|--------:|--------|
| Tottenham | 14 | 14 | 0 | -40 | -40 | 0 | live |
| Real Madrid | 14 | 14 | 0 | -42 | -42 | 0 | live |
| Chelsea | 9 | 9 | 0 | -75 | -75 | 0 | live |
| Manchester City | 5 | **14** | **+9** | -99 | **-49** | **+50** | synthetic |
| Paris Saint-Germain | 4 | **8** | **+4** | -106 | **-84** | **+22** | synthetic |
| **TOTAL** | 46 | **59** | **+13** | -362 | **-290** | **+72** | mixed |

Pilot leaderboard v3: `tottenham=−40, realmadrid=−42, mancity=−49, chelsea=−75, psg=−84`.

## Audit (spot-checked)

Each new mancity claim has explicit reseller-text backing:

| Feature | Backing text |
|---------|--------------|
| `chef_attribution` | "...combined with an excellent premium chef's buffet..." (eventmasters) |
| `fixture_change_notification` | "...information on confirmed fixture changes is included in the publications section of the manchester city website..." (rockethospitality) |
| `pitchside_or_tunnel_access` | "Tunnel Club" tier name across all 4 sources |
| `parking_included_indicator` | explicit "parking included" / "complimentary parking" copy |
| `concierge_service` | "dedicated host" / "hospitality team" copy in tier descriptions |
| `stadium_tour_inclusion` | "stadium tour" mentioned in tier-add-on lists |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Substituted curl-equivalent stdlib fetch for WebSearch/WebFetch**
- **Found during:** Phase 1 implementation
- **Issue:** Plan calls for "WebSearch + WebFetch on reseller / search-cached pages." Those are Anthropic agent-side primitives not available inside the running scanner code path.
- **Fix:** `urllib.request.urlopen` with desktop UA + `html.parser.HTMLParser` for text extraction. Same network operation (HTTP GET against reseller sites) — these pages are not bot-protected, so a vanilla UA succeeds. Eliminates a hard dependency on agent-context tooling.
- **Files modified:** `scanner/capture/text_fetch.py` (uses stdlib instead of agent tools)
- **Commit:** `5fa066e`

**2. [Rule 1 - Bug] HTMLParser stack-pop logic left entire body skipped**
- **Found during:** First end-to-end run against `sportlux.co.uk` (returned 0 chars text despite HTTP 200 + 49,907 byte body)
- **Issue:** `_TextExtractor` used a tag stack to track skip-tags (script/style/noscript/svg/head/iframe). Real-world HTML often has unbalanced or void tags causing the stack to never pop properly — for example, `<head>` was left on the stack forever, marking everything inside `<body>` as "skipping."
- **Fix:** Switched to per-tag depth counter. Removed `head` from skip set entirely (head doesn't typically contain extractable body text we care about either way; if it did, `script`/`style` already strip the JS/CSS). Validated with end-to-end fetch on all 8 reseller URLs.
- **Files modified:** `scanner/capture/text_fetch.py` (`_TextExtractor`)
- **Commit:** (folded into the `chore(02-20)` synthetic-capture commit)

**3. [Rule 2 - Missing critical] Plan-mandated rubric default coupled scanner package to analysis.hospitality**
- **Found during:** `test_no_area_coupling` regression after writing `run_synthetic_wave.py`
- **Issue:** Initially used `default=Path("analysis/hospitality/features.json")` for `--rubric` Click option. That violates the FLOW-02 / D-04 invariant ("scanner/ must not import or reference analysis.hospitality").
- **Fix:** Made `--rubric` `required=True`. Caller passes the path explicitly; scanner stays area-agnostic.
- **Files modified:** `scanner/scripts/run_synthetic_wave.py`
- **Commit:** (folded into the re-vision commit `0e2e507`)

### Out-of-scope items (deferred to Phase 2.5)

- Confidence penalty for synthetic-source verdicts (drop DOM_CONFIDENCE 0.95 → 0.80)
- Hybrid Option B (send aggregated text content to vision client for hybrid features that DOM rule failed on)
- Browserbase / Bright Data POC for headless Cloudflare bypass

## Self-Check

Created files:
- `.planning/phases/02-hospitality-pilot/02-20-TEXT-BASED-CAPTURE-SUMMARY.md` — this file
- `.planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT-V3.md`
- `scanner/capture/text_fetch.py`
- `scanner/config/reseller_urls.json`
- `scanner/scripts/run_text_capture.py`
- `scanner/scripts/run_synthetic_wave.py`
- `scanner/tests/test_text_fetch.py`
- All synthetic intel JSONs + audit MDs + run-logs (force-added per existing scanner/output/ tracking precedent)

Modified files (Plan 02-20 commits):
- `scanner/capture/dom_intel.py` (+text_extracts +source fields)
- `scanner/vision/dom_detect.py` (text_extracts surface in rules)
- `analysis/hospitality/results/mancity.json` (re-derived from synthetic)
- `analysis/hospitality/results/psg.json` (re-derived from synthetic)
- `analysis/hospitality/results/_aggregate.json` (recomputed)
- `analysis/hospitality/results/_scores.json` (recomputed)

Commits (this branch):
- `f5e2775 feat(02-20): extend DomIntel schema with text_extracts + source fields`
- `44f54c1 feat(02-20): dom_detect rules now check text_extracts fallback`
- `5fa066e feat(02-20): add scanner/capture/text_fetch.py + reseller_urls.json`
- `(synth) chore(02-20): synthesize text-based intel for mancity + psg`
- `0e2e507 feat(02-20): re-vision + re-derive results with synthetic intel`
- `(this) docs(02-20): coverage report v3 + summary`

Invariants:
- `git diff --quiet analysis/homepage/` exit 0 ✓
- TOT/CHE/RMA results bit-stable identical to v2.5 ✓
- Subscription cost: $0 ✓
- 343 scanner tests passing (12 new + 331 baseline; 5 unrelated skipped due to env) ✓
- ANTHROPIC_API_KEY untouched (no vision calls made) ✓
- No new third-party dependencies (stdlib-only) ✓

## Self-Check: PASSED
