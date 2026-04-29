---
phase: 02-hospitality-pilot
plan: 02-17
title: Hospitality re-vision wave with Scanner v2 hybrid pipeline
type: out-of-band tactical
subsystem: scanner
status: complete
date_started: 2026-04-28
date_completed: 2026-04-28
tags: [scanner, vision, hybrid-routing, dom-detect, hospitality-pilot, plan-02-15-validation, plan-02-16-validation, cost-reduction]
dependency_graph:
  requires:
    - 02-15 (Scanner v2 architecture: DOM intel + hybrid routing)
    - 02-16 (recaptured PNG + DOM-intel set across 5 pilot clubs)
    - 02-11 (vision wave orchestrator — extended here for dom_intel_dir)
    - 02-12 (results derivation pipeline — re-run unchanged)
  provides:
    - Hybrid-routed per-club result JSONs (5 clubs)
    - Re-derived analysis/hospitality/results/{club}.json (5 files)
    - Regenerated sliced feature crops (24 PNGs touched)
    - Regenerated contact-report-hospitality.html
    - Re-computed scores (analysis/hospitality/results/_scores.json)
    - V2 coverage report side-by-side with V1 baseline
  affects:
    - 02-14 (pilot acceptance gate — now has v2 numbers to evaluate)
    - Phase 2.5 expansion plan (clearer Turnstile vs selector-tuning split)
tech_stack:
  added: []
  patterns:
    - "Hybrid DOM+vision wave orchestrator with per-step intel discovery"
    - "Two-pass results layering: scanner/output/results -> analysis/hospitality/results"
key_files:
  created:
    - .planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT-V2.md
    - .planning/phases/02-hospitality-pilot/02-17-REVISION-SUMMARY.md
    - .planning/phases/02-hospitality-pilot/v1-results-backup/ (snapshot of v1 analysis/hospitality/results/)
    - scanner/output/results-v1-backup/ (snapshot of v1 scanner/output/results/hospitality/)
    - scanner/output/disagreements-hospitality-v1-backup.json
    - 11 net-new evidence/features/{club}_{key}.png crops (RMA 7, TOT 2, CHE 2)
  modified:
    - scanner/scripts/extract_rubric.py (capture optional `detection` arg)
    - scanner/scripts/run_vision_wave.py (--dom-intel-dir + dom_intel_dir kwarg)
    - scanner/scoring/recalculate.js (regex tolerates 9-arg feat() calls)
    - scanner/tests/test_run_vision_wave.py (spy fixture accepts dom_intel_path)
    - analysis/hospitality/results/{chelsea,mancity,psg,realmadrid,tottenham}.json
    - analysis/hospitality/results/_aggregate.json + _scores.json
    - 13 evidence/features/{club}_{key}.png crops (re-sliced)
    - scanner/output/contact-report-hospitality.html (regenerated)
    - scanner/output/disagreements-hospitality.json (74 records vs v1's 112)
decisions:
  - "Used the Plan 02-16 latest run-logs (T12-13Z) per club for the wave — these capture the genuine hospitality content; the bot-blocked Turnstile steps return absent verdicts honestly through the hybrid pipeline."
  - "Ran 3 waves in parallel (chelsea + realmadrid + tottenham) and 2 waves sequentially (psg + mancity) to balance wall-clock budget with the disagreements file's last-writer-wins write semantics. Per-(club,step) uniqueness in the dedup logic prevented data loss."
  - "Backed up v1 results JSONs + v1 disagreements before overwriting — the V1 coverage report points to v1-results-backup/ for forensic comparison."
  - "Did NOT delete the 8 Turnstile-blocked PNGs — the hybrid pipeline correctly returns absent on those because DOM intel says title='Just a moment...'. Plan 02-16 already excluded them from commits as misleading evidence."
  - "Did NOT change features.ts itself — the detection tags Plan 02-15 added are sufficient. extract_rubric.py was extended to read those tags into features.json."
metrics:
  duration_minutes: ~50 (wave) + ~10 (derivation/scoring/report) = ~60
  vision_calls_total: 56 (28 PNGs × 2 judges)
  vision_calls_saved_from_v1_baseline: ~553 feature-cell verdicts answered by DOM (35.9% routing efficiency)
  subscription_cost_usd: 0
  cells_in_pilot: 275 (5 clubs × 55 features)
  v1_to_v2_present_delta: +6 (31 -> 37)
  v1_to_v2_disputed_delta: -6 (19 -> 13)
  v1_to_v2_disagreement_records_delta: -34 (112 -> 74)
  v1_to_v2_score_delta_aggregate: +33 (-452 -> -419)
  files_changed: 5 (modified scripts) + 7 (results JSONs) + 24 (evidence crops) + 2 (docs) + 1 (contact-report)
  commits: 3 feature + 1 docs commit (this commit)
---

# Phase 2 Plan 02-17: Hospitality Re-Vision Wave Summary

Re-ran the Plan 02-11 vision wave for all 5 hospitality pilot clubs against the Plan 02-16 stealth-recaptured PNG + DOM-intel set, using Plan 02-15's hybrid DOM+vision routing for the first time end-to-end on real captures. Re-derived all per-club results, regenerated the sliced feature crops + contact sheet, and recomputed scores. Updated coverage report v2 sits side-by-side with v1 for direct comparison.

## TL;DR — what changed v1 → v2

| Metric | v1 (vision-only) | v2 (hybrid) | Delta |
|--------|---:|---:|---:|
| Cells present (5×55=275) | 31 (11.3%) | **37 (13.5%)** | +6 |
| Cells disputed | 19 (6.9%) | **13 (4.7%)** | -6 |
| Disagreement records | 112 | **74** | -34 |
| Presence-kind disagreements | 39 | **21** | -18 |
| Features showing signal in ≥1 club | 14 | **20** | +6 |
| Features absent in all 5 | 41 | **35** | -6 |
| Aggregate score (sum) | -452 | **-419** | +33 |
| Cost (subscription) | $0 | **$0** | $0 |
| Vision API calls (Opus + Sonnet) | 32 | **56** | +24 (more PNGs in v2) |
| Feature-cell verdicts answered by DOM | 0 | **553** | +553 |
| DOM-routing efficiency | n/a | **35.9%** | — |

## Per-club deltas

| Club | v1 P | v2 P | dP | v1 D | v2 D | dD | v1 Agreement | v2 Agreement | v1 Score | v2 Score |
|------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tottenham | 12 | 12 | 0 | 7 | 6 | -1 | 96.73% | 97.45% | -57 | **-54** |
| Real Madrid | 6 | **9** | +3 | 3 | 1 | -2 | 94.55% | **99.64%** | -92 | **-74** |
| Chelsea | 8 | 7 | -1 | 9 | 6 | -3 | 92.12% | 96.06% | -79 | -86 |
| Manchester City | 5 | 5 | 0 | 0 | 0 | 0 | 100% | 100% | -99 | -99 |
| PSG | 0 | **4** | +4 | 0 | 0 | 0 | 100% | 100% | -125 | **-106** |
| **TOTAL** | **31** | **37** | **+6** | **19** | **13** | **-6** | 96.48% | **98.6%** | -452 | **-419** |

**Notable changes:**
- **Real Madrid jumped rank 3 → rank 2.** Stealth + DOM detection elevated 3 features that v1 mis-rated absent. Agreement rate +5% (94.55% → 99.64%).
- **PSG moved from 0 features present to 4.** Three main-domain pages contributed real content this time. The 3 billetterie-Turnstile pages still return absent (correctly, via hybrid routing reading `title="Just a moment..."`).
- **Chelsea slipped 1 cell.** Plan 02-16 flow-map duplication finding now manifests: 4 of 6 PNGs are the same package-list page; v1 saw a feature once but v2 sees consistent absence across the duplicates.
- **Tottenham unchanged on present-count, agreement +0.7%.** v1 already had high agreement; DOM routing reduced minor bbox/confidence quibbling.
- **MCFC unchanged.** All 5 v2 PNGs are Turnstile interstitials (per Plan 02-16); 5 features still come from a pre-orchestrator landing capture that survived. Honest result for Cloudflare-blocked content.

## Hybrid pipeline efficiency

| Club | DOM-resolved cells | Vision-resolved cells | Total | DOM % |
|------|---:|---:|---:|---:|
| Tottenham | 112 | 163 | 275 | 40.7% |
| Chelsea | 126 | 204 | 330 | 38.2% |
| Real Madrid | 100 | 175 | 275 | 36.4% |
| PSG | 120 | 210 | 330 | 36.4% |
| Manchester City | 95 | 235 | 330 | 28.8% |
| **AGGREGATE** | **553** | **987** | **1,540** | **35.9%** |

Plan 02-15 projected ~60% vision-call reduction on retail-equivalent cost; actual feature-cell-level routing was 35.9%. The discrepancy is because:
- v1's 32 PNG × 2 judges × 55 features = 3,520 cells (theoretical retail max).
- v2's 28 PNG × 2 judges × 55 features = 3,080 cells with 35.9% DOM-resolved → 1,975 vision cells (retail-equivalent ~$0.50–1.00 less).
- The 60% projection in Plan 02-15 included the dom-tagged features (38 of 55) PLUS the hybrid features (14 of 55) when DOM positively confirmed them — combined that's ~52 features, ~95% of the rubric. But hybrid features only short-circuit when DOM says present at high confidence; for absences they still go to vision. So the *actual* savings track the rubric × club content density, not the rubric tag distribution alone.

## Subscription cost (actual)

**$0** in subscription mode. The retail-equivalent estimate would be ~$1.50–2.50 per Plan 02-15 projection; we did not pay that because Claude Max plan covers vision calls. Hard cap of $5 not exceeded.

## Wall-clock duration

- Tottenham wave: 11.2 min
- Chelsea wave: 13.3 min
- Real Madrid wave: 10.4 min
- PSG wave: 7.4 min
- Manchester City wave: 7.8 min
- **Total wall-clock with parallelism (3 then 2): ~50 min**
- **Derivation + slice + report + score: ~10 min**
- **Total: ~60 min** — overran the 30-45 min budget. The parallelism cap was 3 (to avoid disagreements file races); a higher cap would have brought wall-clock under budget.

## Test count

348 tests pass (was 348 pre-edit). The new `dom_intel_path` kwarg on `two_judge` broke `test_rubric_passed_verbatim_to_two_judge` because the spy fixture didn't accept it; fixed inline (Rule 3). 0 net regressions.

## Open issues

- **5 v1→v2 absences flagged for spot-check:** price_per_person_visible (3→0), buy_now_without_enquiry (4→2), phone_booking_option (2→0). The DOM rules may be stricter than vision's interpretation. If user spot-checks confirm the v1 hits were correct, the rules need refinement (looser regex, broader keyword list, or downgrade the feature back to `hybrid` so vision can override DOM-absent).
- **8 genuine Cloudflare Turnstile blocks** documented in `scanner/output/CHROME-MCP-NEEDED.md` Section A. Phase 2.5 prerequisite, not a Phase 2 blocker. Hybrid pipeline correctly identifies these pages as absent for all features.
- **10 selector-tuning issues** in `CHROME-MCP-NEEDED.md` Section B + 2 login-selector misses in Section C. Plan 02-18 (flow-map iteration) territory.
- **Chelsea click-to-package-detail flow-map duplication** (Plan 02-16 deferred-items finding) still unresolved. 4 of 6 Chelsea PNGs are the same package-list page. Plan 02-18 territory.
- **Opus bbox out-of-bounds** (Plan 02-08 calibration finding) unchanged in v2. ~16 sliced PNGs may have clamped bboxes. Visible in contact sheet as slightly-off framing. Phase 2.5 carryover.

## Invariants verified

- `git diff --quiet analysis/homepage/` → exit 0 (D-20 holds; rubric, results, features.ts, scoring all untouched on homepage area)
- `analysis/hospitality/results/*.json` MAY change (this is the point of re-vision — and they did, with backups in `.planning/phases/02-hospitality-pilot/v1-results-backup/`)
- `analysis/hospitality/evidence/features/*.png` MAY change (re-sliced from new bboxes; 13 modified + 11 net-new)
- `scanner/tests` → 348 passed (1 fixed regression on `test_rubric_passed_verbatim_to_two_judge`)
- ANTHROPIC_API_KEY untouched; subscription mode used throughout
- Cumulative subscription cost = $0 ≤ $5 hard cap
- V1 coverage report PRESERVED at `.planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT.md`

## Deviations from plan

### Auto-fixed (Rule 1 — Bug)

1. **`extract_rubric.py` did not capture detection tags.** The Plan 02-15 features.ts had `detection` as the 9th positional arg in feat() calls, but the existing 6-arg-only regex never reads it. Without that tag flowing into features.json, `two_judge`'s routing falls back to vision-only for every feature — the entire hybrid pipeline is silently disabled. Fix: extended the regex to scan from each feat() match's end to the next match's start for the `, '<dom|visual|hybrid>')` trailing arg. Validated: 38 dom + 14 hybrid + 3 visual = 55 tags extracted to features.json.

2. **`scanner/scoring/recalculate.js` weight regex anchored on `\)` after the no-weight integer.** The Plan 02-15 detection-tagged features.ts now has `, 'detection')` between the no-weight and the closing paren, so the regex matched 0 features and `score` errored with "No features parsed". Fix: extended the regex to allow an optional `(?:,\s*'<mode>'\s*)?` group before the closing paren. 55 features now parse and score.

### Auto-fixed (Rule 3 — Blocking)

1. **`run_vision_wave.py` did not expose --dom-intel-dir or pass dom_intel_path to two_judge.** Without this, the orchestrator could not consume Plan 02-15's hybrid routing — every feature would have routed to vision regardless of detection tag. Fix: added optional `dom_intel_dir` arg + auto-discovers `{club}_{step}_intel.json` per PNG.

2. **`test_rubric_passed_verbatim_to_two_judge` test broke.** The spy fixture's signature didn't accept the new `dom_intel_path=None` kwarg that the orchestrator now forwards. Fix: added `dom_intel_path=None` to the spy. Pre-15 contract preserved (spy still asserts api_mode and rubric forwarded by identity when no DOM intel is available).

### Documented but not fixed

1. **5 v1→v2 absence regressions** (price_per_person_visible 3→0, buy_now_without_enquiry 4→2, phone_booking_option 2→0). These come from DOM rules being stricter than vision interpretation. Not fixing in this plan — the user spot-check is the gate that decides whether to refine the rules. If 5 of 5 v1 hits were genuine, the rules need broadening; if they were vision over-calls, v2 is the more accurate baseline.

2. **8 genuine Turnstile blocks**. Documented in `CHROME-MCP-NEEDED.md`. Phase 2.5 work.

## Self-Check

Files claimed and existence:

- `.planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT-V2.md` → FOUND
- `.planning/phases/02-hospitality-pilot/02-17-REVISION-SUMMARY.md` → FOUND (this file)
- `.planning/phases/02-hospitality-pilot/v1-results-backup/{tottenham,chelsea,realmadrid,psg,mancity}.json` → FOUND (5 files + _aggregate + _scores = 7 files)
- `scanner/output/results/hospitality/{tottenham,chelsea,realmadrid,psg,mancity}_features.json` → FOUND (5 files, all post-wave)
- `scanner/output/results-v1-backup/hospitality/*.json` → FOUND
- `scanner/output/disagreements-hospitality-v1-backup.json` → FOUND
- `scanner/output/disagreements-hospitality.json` → FOUND (74 records)
- `analysis/hospitality/results/{tottenham,chelsea,realmadrid,psg,mancity}.json` → FOUND (modified, v2 verdicts)
- `analysis/hospitality/results/_aggregate.json` + `_scores.json` → FOUND
- `analysis/hospitality/evidence/features/*.png` → 11 net-new + 13 modified (24 touched)
- `scanner/output/contact-report-hospitality.html` → FOUND (regenerated)

Commits made:

- `feat(02-17): wire dom_intel_path through run_vision_wave + extract_rubric detection` → script extensions
- `feat(02-17): re-derive hospitality results JSONs from hybrid verdicts` → results JSONs
- `feat(02-17): regenerate sliced feature crops + recompute scores` → evidence crops + scores
- `docs(02-17): write coverage report v2 + revision summary` → this summary + V2 coverage report (forthcoming)

Test count: 348 pass.

D-20 invariant: `git diff --quiet analysis/homepage/` → exit 0.

## Self-Check: PASSED

## Threat Flags

None — all writes confined to scanner/output/, analysis/hospitality/, and .planning/phases/02-hospitality-pilot/. No new endpoints, no auth surface changes, no schema changes at trust boundaries.
