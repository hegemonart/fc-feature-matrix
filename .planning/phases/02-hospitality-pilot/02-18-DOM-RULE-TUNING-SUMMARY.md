---
phase: 02-hospitality-pilot
plan: 02-18
title: DOM Rule Tuning — fix v1→v2 regressions on hospitality pilot
type: out-of-band tactical
subsystem: scanner
status: complete
date_started: 2026-04-28
date_completed: 2026-04-28
tags:
  - scanner
  - vision
  - hybrid-routing
  - dom-detect
  - hospitality-pilot
  - rule-tuning
  - regression-fix
  - plan-02-17-followup
dependency_graph:
  requires:
    - 02-15 (Scanner v2 architecture: DOM intel + hybrid routing)
    - 02-16 (recaptured PNG + DOM-intel set across 5 pilot clubs)
    - 02-17 (v2 hybrid wave that surfaced the v1→v2 absence regressions)
  provides:
    - Refined dom_detect.py rules (price_per_person_visible, buy_now_without_enquiry)
    - Detection-tag downgrades on 4 features (dom → hybrid)
    - 7 new regression tests in scanner/tests/test_dom_detect.py
    - Re-derived analysis/hospitality/results/{club}.json (5 files)
    - Regenerated sliced feature crops
    - Regenerated contact-report-hospitality.html
    - Re-computed scores (v2.5 baseline)
  affects:
    - 02-14 (pilot acceptance gate — now has v2.5 numbers)
    - Phase 2.5 expansion plan (hybrid routing now empirically validated)
tech_stack:
  added: []
  patterns:
    - "DOM-rule + vision-fallback hybrid routing for body-text-only signals"
    - "i18n keyword expansion (ES/FR) in DOM rules for international clubs"
key_files:
  created:
    - .planning/phases/02-hospitality-pilot/02-18-DOM-RULE-TUNING-SUMMARY.md
    - .planning/phases/02-hospitality-pilot/v2-results-backup/ (snapshot of v2 results)
  modified:
    - scanner/vision/dom_detect.py (price_per_person + buy_now rules widened)
    - scanner/tests/test_dom_detect.py (+7 regression tests)
    - analysis/hospitality/features.ts (4 detection tags: dom → hybrid)
    - analysis/hospitality/HOSPITALITY-FLOW.md (matching tag updates)
    - analysis/hospitality/results/{tottenham,chelsea,realmadrid,psg,mancity}.json
    - analysis/hospitality/results/_aggregate.json + _scores.json
    - 25 evidence/features/*.png crops (re-sliced) + 3 net-new
    - scanner/output/contact-report-hospitality.html (regenerated)
    - scanner/output/disagreements-hospitality.json (cumulative; 4 club re-vision)
decisions:
  - "Two-pronged fix: (1) widen 2 DOM rules to capture cases vision saw correctly in v1, (2) downgrade 4 detection tags from dom to hybrid where DOM intel surface (headings/buttons/meta) cannot see the signal that lives in body text."
  - "Did NOT widen all 5 rules to dom-only because phone_booking_option, concierge_service, and stadium_tour_inclusion genuinely live in body text the dom_intel.py JS extractor doesn't capture (no <a href='tel:'>, no <h1> 'Concierge', etc.). Hybrid is the right routing — DOM rule still runs first and catches positives like RMA's 'Buy Hospitality tickets', but absences fall through to vision."
  - "Re-ran 4 of 5 clubs (skipped MCFC; all interstitials, no rule change can recover that). 1-club serial + 3-club parallel kept wall-clock under budget."
  - "Backed up v2 results before overwriting (v2-results-backup/) for forensic comparison alongside v1-results-backup from Plan 02-17."
metrics:
  duration_minutes: ~45 (3-club parallel + 1-club serial wave + ~10 min derivation/scoring/report + ~5 min rule-design)
  vision_calls_total: 44 (4 clubs × ~11 vision calls each)
  subscription_cost_usd: 0
  rules_modified: 2 (price_per_person_visible, buy_now_without_enquiry)
  tags_downgraded: 4 (price_per_person_visible, phone_booking_option, stadium_tour_inclusion, concierge_service)
  tests_added: 7
  v1_to_v25_present_delta: +15 (31 → 46)
  v2_to_v25_present_delta: +9 (37 → 46)
  v1_to_v25_disputed_delta: -12 (19 → 7)
  v2_to_v25_disputed_delta: -6 (13 → 7)
  v1_to_v25_score_delta_aggregate: +90 (-452 → -362)
  v2_to_v25_score_delta_aggregate: +57 (-419 → -362)
  files_changed: 30 (4 source + 25 binary + 1 doc)
  commits: 3 feature/chore + 1 docs (this commit)
  scanner_tests: 355 passing (was 348 before plan; +7 new regression tests)
---

# Phase 2 Plan 02-18: DOM Rule Tuning Summary

Out-of-band tactical fix targeting the 5 v1→v2 absence regressions surfaced
by Plan 02-17's coverage report v2. Refined 2 DOM detection rules in
`scanner/vision/dom_detect.py`, downgraded 4 features from `detection: dom`
to `detection: hybrid` so vision can override when the DOM intel surface
doesn't carry the signal, and re-ran the hybrid vision wave for the 4
affected clubs (skipping Manchester City — all v2 PNGs are Cloudflare
interstitials, no rule change can recover that data).

## TL;DR — what changed v2 → v2.5

| Metric | v1 (vision-only) | v2 (hybrid v1) | **v2.5 (this plan)** | Δ vs v2 |
|--------|---:|---:|---:|---:|
| Cells present (5 × 55 = 275) | 31 (11.3%) | 37 (13.5%) | **46 (16.7%)** | **+9** |
| Cells disputed | 19 (6.9%) | 13 (4.7%) | **7 (2.5%)** | **-6** |
| Aggregate score (sum) | -452 | -419 | **-362** | **+57** |
| Cost (subscription) | $0 | $0 | **$0** | $0 |

## Per-club deltas

| Club | v1 P | v2 P | v2.5 P | v1 D | v2 D | v2.5 D | v1 Score | v2 Score | v2.5 Score | ΔScore vs v2 | Rank v2.5 |
|------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tottenham | 12 | 12 | **14** | 7 | 6 | **1** | -57 | -54 | **-40** | **+14** | **1** |
| Real Madrid | 6 | 9 | **14** | 3 | 1 | **1** | -92 | -74 | **-42** | **+32** | **2** |
| Chelsea | 8 | 7 | **9** | 9 | 6 | **5** | -79 | -86 | **-75** | **+11** | 3 |
| Manchester City | 5 | 5 | 5 | 0 | 0 | 0 | -99 | -99 | -99 | 0 | 4 |
| Paris Saint-Germain | 0 | 4 | **4** | 0 | 0 | 0 | -125 | -106 | -106 | 0 | 5 |
| **TOTAL** | **31** | **37** | **46** | **19** | **13** | **7** | **-452** | **-419** | **-362** | **+57** | — |

## Per-Regression Diagnosis & Fix

5 regressions identified by comparing `analysis/hospitality/results/{club}.json` against
`.planning/phases/02-hospitality-pilot/v1-results-backup/{club}.json`:

### 1. `price_per_person_visible` — TOT, CHE, RMA all v1=True → v2=False

**Root cause (per-club):**
- **TOT**: matchday-options page has visible "TICKETS FROM £249" / "TICKETS FROM £299" /
  "Tickets from £25" buttons. The v2 rule `_PRICE_PER_PERSON_RE` required an explicit
  "per person|guest|head|pp" suffix, which TOT's tier-from copy doesn't carry.
- **CHE, RMA**: prices live in body-text descriptions on package pages. The DOM intel
  extractor (`scanner/capture/dom_intel.py`) only captures headings + buttons + meta +
  schema_jsonld — it doesn't see body paragraphs. v1 vision saw the prices; v2 DOM rule
  had no signal to fire on.

**Fix applied:**
- Added `_PRICE_TIER_RE` regex matching `(tickets|prices|packages)? from (£|€|$) NNN`
  for hospitality tier-landing copy.
- Downgraded `detection` tag from `dom` to `hybrid` so vision picks up CHE/RMA cases
  where the rule can't fire (body-text-only).
- Test: `test_price_per_person_visible_tickets_from_phrasing` (verifies `TICKETS FROM £249`
  matches), `test_price_per_person_visible_prices_from_phrasing`, `test_price_per_person_visible_bare_from_phrasing`,
  `test_price_per_person_visible_negative_no_currency_post_widen`.

**Result v2.5:** TOT=True (DOM rule), CHE=True (vision fallback), RMA=True (vision fallback). All v1 hits restored.

### 2. `buy_now_without_enquiry` — CHE, RMA both v1=True → v2=False

**Root cause:**
- **RMA**: Has `Buy Hospitality tickets` buttons (extracted by DOM intel as buttons).
  The v2 rule keyword list `["book now", "buy now", "buy ticket", "purchase"]` did NOT
  include the literal phrase "buy hospitality" — RMA's button reads "Buy Hospitality"
  not "Buy Now" or "Buy Ticket".
- **CHE**: Genuinely has no buy-now-without-enquiry button. Only `CONTACT US` /
  `Contact us`. v1 vision was incorrect here; v2 DOM is the more accurate reading.
  This regression is intentional — we accept it as a v1-correction, NOT a v2-fix.

**Fix applied:**
- Broadened keyword list to include `"buy hospitality"`, `"buy seat"`, `"checkout"`,
  plus i18n equivalents `"comprar"`, `"reservar"` (Spanish; RMA + ATM future), `"acheter"`,
  `"réserver"` (French; PSG). Kept `detection: dom`.
- Tests: `test_buy_now_without_enquiry_buy_hospitality_phrasing`,
  `test_buy_now_without_enquiry_spanish_comprar`,
  `test_buy_now_without_enquiry_french_acheter`.

**Result v2.5:** RMA=True (DOM rule fires on "Buy Hospitality tickets"). CHE=False
(intentional — v2 was correct, v1 was wrong; matches the underlying webpage). MCFC=True
(unchanged — interstitial-derived).

### 3. `phone_booking_option` — TOT, RMA both v1=True → v2=False

**Root cause:**
Comprehensive scan across all 27 captured DOM intel JSONs found **0 `<a href="tel:">` links
anywhere**. Every visible phone number on the captured pages is rendered as plain text in
body content, which the DOM intel extractor doesn't capture. The existing rule's
fallback (`call/phone/tel + digits` regex on text blob) also can't fire because that
text isn't in the headings/buttons/meta surfaces.

**Fix applied:**
- Downgraded `detection` from `dom` to `hybrid`. The existing rule still fires for
  any future page that does have a `<a href="tel:">` link — but absent that signal,
  vision now gets to look at the screenshot and see the phone number.
- No rule change. Existing tests `test_phone_booking_option_via_tel_link` and
  `test_phone_booking_option_via_text` still pass.

**Result v2.5:** TOT=True (vision), RMA=True (vision). All v1 hits restored.

### 4. `concierge_service` — TOT v1=True → v2=False

**Root cause:**
"Concierge" / "hostess" / "host service" copy not present in TOT's headings or button
text. The descriptions live in the body paragraphs of package pages where DOM intel
doesn't reach.

**Fix applied:**
- Downgraded `detection` from `dom` to `hybrid`. Existing rule (keyword scan over
  headings/buttons/title/image-alt/meta) still runs; if it fires we use it, otherwise
  vision gets the screenshot.
- No rule change.

**Result v2.5:** TOT=True (vision). Bonus: RMA also flips to True (vision saw concierge
copy on Real Madrid hospitality pages — a v1 false-negative now corrected upward).

### 5. `stadium_tour_inclusion` — CHE v1=True → v2=False

**Root cause:**
Same pattern as concierge: "stadium tour" / "behind-the-scenes tour" copy lives in
body paragraphs of CHE package pages, not in headings/buttons that DOM intel captures.

**Fix applied:**
- Downgraded `detection` from `dom` to `hybrid`. Existing keyword rule still runs.
- No rule change.

**Result v2.5:** CHE=True (vision). Bonuses: TOT=True (vision saw it on TOT premium
seats; v1 false-negative corrected) and PSG=True (vision saw "Stadium tour" copy that
DOM intel had also surfaced on PSG headings — DOM rule fires here so PSG short-circuits
without vision).

## Hybrid Pipeline Efficiency (v2.5 vs v2)

The 4 detection-tag downgrades shift more features through vision instead of DOM-only.
This is the intentional cost: ~10-15 more vision calls per club PNG, gaining the
ability to read body-text signals that DOM intel can't reach.

| Detection mode | v2 count | v2.5 count | Δ |
|---|---:|---:|---:|
| dom | 38 | 34 | -4 |
| hybrid | 14 | 18 | +4 |
| visual | 3 | 3 | 0 |
| **Total** | **55** | **55** | — |

DOM-resolved feature-cell rate (cells answered without vision): roughly **30%** in v2.5
(was 35.9% in v2). The 5-point efficiency drop is offset by the +9 cells now correctly
present, which is the intended outcome — the hybrid pipeline now does its job.

## Subscription cost (actual)

**$0** in subscription mode (Claude Max plan). Wave statistics:

| Club | Vision calls | New disagreements | Wall-clock |
|---|---:|---:|---:|
| Tottenham | 10 | 21 | 800s (13.3 min) |
| Chelsea | 12 | 40 | 966s (16.1 min) |
| Real Madrid | 10 | 32 | 640s (10.7 min) |
| Paris Saint-Germain | 12 | 0 | 657s (11.0 min) |
| **Total** | **44** | **93** | **~30 min wall-clock with parallelism** |

Plus ~10 min for derivation + slice + report + score. Total ~45 min, within the
30-45 min budget.

Hard cap of $2 not exceeded (cumulative subscription mode = $0).

## Test count

355 scanner tests pass (was 348 before plan; +7 new regression tests added in
`scanner/tests/test_dom_detect.py`):

- `test_price_per_person_visible_tickets_from_phrasing`
- `test_price_per_person_visible_prices_from_phrasing`
- `test_price_per_person_visible_bare_from_phrasing`
- `test_price_per_person_visible_negative_no_currency_post_widen`
- `test_buy_now_without_enquiry_buy_hospitality_phrasing`
- `test_buy_now_without_enquiry_spanish_comprar`
- `test_buy_now_without_enquiry_french_acheter`

Each one captures the exact button/heading text that produced the v1→v2 false-negative,
preventing the regression from sneaking back if the rule is later refactored.

## Open issues

- **CHE buy_now_without_enquiry stays False in v2.5.** v1 had it True, v2 has it False,
  v2.5 keeps False. This is intentional: a comprehensive scan of CHE's 6 captured DOM
  intel files found **only `CONTACT US` / `Contact us` buttons**, no buy/book/purchase
  copy anywhere. v1 vision was overcalling; v2 DOM is correct; widening the rule to
  "contact us" would create false positives across all 5 clubs. Marking as v1-correction.
- **MCFC unchanged.** All 6 v2 PNGs are Cloudflare interstitials; no rule change can
  recover hospitality data from a "Just a moment..." page. Phase 2.5 / Chrome MCP work.
- **PSG unchanged on cells-present (4 → 4).** The 3 billetterie Turnstile pages remain
  blocked. The rule changes did flip stadium_tour_inclusion to True for PSG (DOM rule
  fired on "Stadium tour" heading), but other features that v1 scored False stay False
  here.
- **DOM intel surface limitation surfaced.** Body-text content (paragraph descriptions
  of package perks, prices, and service offerings) is the primary detection surface
  for ~15-20% of hospitality features. Either extend `dom_intel.py` to capture body text
  or accept hybrid routing as the resolution. Plan 02-15 chose the latter; Plan 02-18
  reaffirms it.
- **Opus bbox out-of-bounds** (Plan 02-08 carryover): ~10 sliced features in v2.5 still
  show "bbox outside image bounds" warnings — TOT concierge_service in
  premium-seats-detail-shot, RMA fixture_list_visible in matchday-tier-card-shot, etc.
  Phase 2.5 calibration work.

## Invariants verified

- `git diff --quiet analysis/homepage/` → exit 0 (D-20 holds; rubric, results, features.ts,
  scoring all untouched on homepage area)
- `analysis/hospitality/results/*.json` MAY change — point of re-vision; backed up to
  `.planning/phases/02-hospitality-pilot/v2-results-backup/` for forensic comparison
- `analysis/hospitality/evidence/features/*.png` MAY change — re-sliced from new bboxes
- `scanner/tests` → 355 passed (no regressions; +7 new tests added)
- ANTHROPIC_API_KEY untouched; subscription mode used throughout
- Cumulative subscription cost = $0 ≤ $2 hard cap
- D-21 honored (changes confined to `dom_detect.py` rules, `features.ts` tags,
  `HOSPITALITY-FLOW.md` rubric tags, and result/evidence regeneration)

## Deviations from plan

### Auto-fixed (Rule 3 — Blocking)

1. **Click `--step '*'` argument glob-expansion on MSYS bash on Windows.** When invoking
   `scanner slice --step '*'` via `bash`, the shell expanded `*` to a directory listing
   despite quoting. Fix: invoked the slice via Click's CliRunner from a temporary
   `.tmp_slice_all.py` Python wrapper that bypasses argv shell tokenization. The wrapper
   was deleted after use; not committed. Pre-existing issue; not introduced by this plan.

### Documented but not fixed

1. **CHE buy_now_without_enquiry not restored.** Documented as v1-correction (v1 was
   incorrectly True; v2/v2.5 correctly False). Not a defect of v2.5.
2. **MCFC interstitials.** Pre-existing; Phase 2.5 / Chrome MCP work.

## Self-Check

Files claimed and existence:

- `.planning/phases/02-hospitality-pilot/02-18-DOM-RULE-TUNING-SUMMARY.md` → FOUND (this file)
- `.planning/phases/02-hospitality-pilot/v2-results-backup/{tottenham,chelsea,realmadrid,psg,mancity}.json` → FOUND (5 files + _aggregate + _scores + scanner-results-hospitality dir)
- `scanner/output/results/hospitality/{tottenham,chelsea,realmadrid,psg,mancity}_features.json` → FOUND (5 files, post-revision)
- `analysis/hospitality/results/{tottenham,chelsea,realmadrid,psg,mancity}.json` → FOUND (modified, v2.5 verdicts)
- `analysis/hospitality/results/_aggregate.json` + `_scores.json` → FOUND
- `scanner/output/contact-report-hospitality.html` → FOUND (regenerated)
- `scanner/vision/dom_detect.py` → MODIFIED (price_per_person + buy_now rules widened)
- `scanner/tests/test_dom_detect.py` → MODIFIED (+7 regression tests)
- `analysis/hospitality/features.ts` → MODIFIED (4 detection tags downgraded)
- `analysis/hospitality/HOSPITALITY-FLOW.md` → MODIFIED (matching tag updates)

Commits made (excluding this docs commit):

- `fix(02-18): refine price_per_person + buy_now dom rules + regression tests` (fadffc6)
- `fix(02-18): downgrade 4 dom-tagged features to hybrid for vision fallback` (69b97a8)
- `chore(02-18): re-vision affected clubs with refined rules + re-derive` (4236020)

Test count: 355 pass (was 348 + 7 new = 355).

D-20 invariant: `git diff --quiet analysis/homepage/` → exit 0.

## Self-Check: PASSED

## Threat Flags

None — all writes confined to `scanner/output/`, `analysis/hospitality/`,
`scanner/vision/dom_detect.py`, `scanner/tests/`, and
`.planning/phases/02-hospitality-pilot/`. No new endpoints, no auth surface changes,
no schema changes at trust boundaries.
