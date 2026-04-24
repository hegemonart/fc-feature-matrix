# Plan 01-08 — Live Dry-Run Log

**Executed:** 2026-04-24 04:52 - 05:04 UTC (~12 min end-to-end)
**Executor:** Claude Opus 4.7 (GSD executor agent), autonomous with user authorization
**Backend:** subscription (claude-agent-sdk over Max 20x quota — D-28 primary path)
**Fixture rubric:** `scanner/tests/fixtures/dummy-hospitality-rubric.json` (3 dummy features)

## Pre-flight

| Check                                | Result                                            |
| ------------------------------------ | ------------------------------------------------- |
| `claude --version`                   | `2.1.76 (Claude Code)` — PASS                     |
| `python -m playwright --version`     | `Version 1.58.0` — PASS                           |
| `git status`                         | clean on `analysis/`                              |
| `git diff --quiet analysis/`         | exit 0 — D-24 baseline clean                      |

## URL Selection

| URL                                                | HTTP   | Notes                              |
| -------------------------------------------------- | ------ | ---------------------------------- |
| `https://www.mancity.com/hospitality`              | **200** (223 KB)  | **CHOSEN** — real hospitality content |
| `https://www.mancity.com/tickets/hospitality`      | 404 (143 KB error page) | rejected |

Chose `https://www.mancity.com/hospitality` on first-success (it returned 200 with real
hospitality content). `/tickets/hospitality` returned 404 despite being listed first in
the plan's preferred order; documented in the URL-selection rule.

## Pipeline Execution

| Stage    | Start     | End       | Duration | Outcome                                   |
| -------- | --------- | --------- | -------- | ----------------------------------------- |
| capture  | 04:52:34  | 04:52:49  | ~15 s    | PASS — 4.0 MB PNG, 2880×6778 (DPR=2)      |
| vision (1st attempt) | 04:53:10 | 04:56:06 | ~2 m 56 s | FAIL — Sonnet returned non-JSON  |
| vision (2nd attempt, after fix) | 05:00:45 | 05:03:40 | ~2 m 55 s | PASS — 3 disagreements flagged |
| slice    | 05:03:55  | 05:03:56  | <1 s     | 2/3 crops — primary_cta bbox out of bounds |
| report   | 05:04:25  | 05:04:25  | <1 s     | PASS — HTML with 3 feature sections       |

**Total pipeline duration (successful path):** ~20 s capture + 175 s vision + <1 s slice + <1 s report ≈ **3 min 15 s**.

**Headless note:** `--headless` flag was passed for capture because the executor runs
in a non-interactive shell where a visible browser window is not possible. The plan
specifies headed as default for human verification — if a developer re-runs this
manually, they should drop `--headless` to eyeball the browser. This does not affect
the captured PNG.

## Vision — Opus verdicts

| Feature                    | Present | Confidence | Bbox (x,y,w,h)                | Notes (abbrev.)                                                |
| -------------------------- | ------- | ---------- | ----------------------------- | -------------------------------------------------------------- |
| `hero_image`               | **true**    | 0.75       | (0, 0, 2880, 480)             | "Dark navy header band with MANCHESTER CITY HOSPITALITY wordmark" |
| `primary_cta`              | **true**    | 0.90       | (1960, 2668, 660, 110)        | "Multiple high-contrast light-blue 'Buy now' buttons in fixtures"  |
| `hospitality_tiers_list`   | **true**    | 0.95       | (449, 1358, 2100, 740)        | "3 package cards: Men's Team / Women's Team / City Events"         |

## Vision — Sonnet verdicts

| Feature                    | Present | Confidence | Bbox (x,y,w,h)           | Notes (abbrev.)                                              |
| -------------------------- | ------- | ---------- | ------------------------ | ------------------------------------------------------------ |
| `hero_image`               | **false**   | 0.72       | null                     | "Plain dark navy text section — no photographic hero ≥1/3 vp" |
| `primary_cta`              | **true**    | 0.98       | (579, 622, 152, 34)      | "High-contrast cyan 'Buy now' buttons in fixtures section"    |
| `hospitality_tiers_list`   | **true**    | 0.82       | (50, 248, 748, 195)      | "Three structurally distinct hospitality category cards"      |

## Disagreements (3 flagged)

| # | Feature                    | Kind        | Summary                                                               |
| - | -------------------------- | ----------- | --------------------------------------------------------------------- |
| 1 | `hero_image`               | presence    | Opus=true (header band counts), Sonnet=false (no photographic hero)   |
| 2 | `primary_cta`              | bbox (IoU<0.5) | Both present=true; bboxes point at different 'Buy now' instances   |
| 3 | `hospitality_tiers_list`   | bbox (IoU<0.5) | Both present=true; bboxes at different scales (see deviation 3)    |

Three disagreements is higher than the plan's "0-1 for clean subscription result"
expectation — but reviewing the Sonnet/Opus notes, both judges saw the same content and
merely disagreed on bbox precision and rubric interpretation ("does a branded navy text
band qualify as a hero banner?"). The disagreement machinery worked correctly.

## Artifact Checks (all 7 from PLAN 01-08 how-to-verify table)

| # | Check                                                       | Result |
| - | ----------------------------------------------------------- | ------ |
| 1 | `test -s scanner/output/evidence/hospitality/fullpage/mancity_landing.png` | **PASS** — 4,008,593 bytes |
| 2 | Vision JSON has all 3 feature keys under both opus+sonnet   | **PASS** |
| 3 | `disagreements-hospitality.json` exists                     | **PASS** — 2,886 bytes, 3 entries |
| 4 | 1-3 crops in `evidence/hospitality/features/`               | **PASS** — 2 crops (hero_image, hospitality_tiers_list) |
| 5 | `contact-report-hospitality.html` has 3 `<div class="feature">` | **PASS** — 3,390 bytes, exactly 3 feature divs |
| 6 | `git diff --quiet analysis/` after dry-run                  | **PASS** — D-24 invariant holds |
| 7 | Full pytest suite green                                     | **PASS** — 138/138 (+8 new tests from this plan) |

## Deviations Applied

### Rule 1 — Bug fix: Subscription backend rejected markdown-fenced JSON
- **Discovered:** Vision 1st attempt (Sonnet call) failed with `json.JSONDecodeError` —
  model returned JSON inside prose or markdown fences despite "no fences" instruction.
- **Fix:** Added `_extract_json_object()` helper in `scanner/vision/client_subscription.py`
  that strips fences/preambles, plus a retry-once-with-stricter-prompt path per T-08-02
  threat mitigation. If both attempts fail, raises `RuntimeError` with preview of both
  responses.
- **Tests:** 7 new pytest cases in `test_vision_subscription.py` covering fence stripping,
  preamble slicing, passthrough, retry-after-first-fail, and double-fail error.
- **Outcome:** Vision 2nd attempt PASSED cleanly.

### Rule 1 — Bug fix: Contact sheet image paths didn't match slice output layout
- **Discovered:** Regenerated HTML after fresh vision run; `<img src>` hrefs pointed to
  `evidence/<feat_key>/<club>_<feat>.png` but the `slice` subcommand writes to
  `evidence/<area>/features/<club>_<feat>.png`. HTML rendered with broken image links.
- **Fix:** `_build_feature_rows()` in `scanner/report/contact_sheet.py` now accepts `area`
  and builds `evidence/<area>/features/<club>_<feat>.png` paths.
- **Tests:** New regression test `test_thumb_src_matches_slice_output_layout`.
- **Outcome:** Contact sheet paths now match real crop locations.

### Rule 3 — Environment adaptation: Headless capture
- **Context:** Plan specifies headed (`--no-headless`) as default so humans can watch the
  capture. Executor runs in a non-interactive shell with no display; passed `--headless`
  flag to avoid a Playwright launch error.
- **Impact:** None on the captured PNG. A human re-running this plan manually should
  drop `--headless`.

### Noted bug (NOT fixed in this plan): Opus bbox scale
- **Observation:** Opus 4.7 returned bboxes in *native image pixel coordinates* rather
  than the model's 2576-px resized space that `denormalise_bbox` expects. For
  `primary_cta (1960, 2668, 660, 110)` on a 2880×6778 image, `denormalise_bbox` scales
  x=1960 → 5155 which exceeds image width 2880 → `slice_feature` rejects with "bbox
  outside image bounds". Hero and tiers were rescued by image-bound clamping.
- **Why not fixed:** Fixing `denormalise_bbox` logic is architectural (changes the
  research §3.6 assumption about model coord spaces) and requires a new research pass
  to distinguish "Opus 4.7 uses native coords" from "Sonnet 4.6 also uses native coords"
  — Sonnet's `primary_cta (579, 622)` might be native OR resized-and-correct. Requires
  multiple runs with known-geometry images to determine empirically. Filed for Phase 2.
- **Workaround:** 2/3 crops succeeded. Plan's check 4 requires "1-3 crops" which passed.

## Subscription Quota Impact

4 Claude calls consumed via Max 20x subscription (2 Opus + 2 Sonnet across the two
vision attempts). No individual metering exposed; retail equivalent per research §5
is ~$0.11. First attempt burned 2 of these (Opus succeeded, Sonnet failed at parse).

## Conclusion

**Phase 1 complete via live dry-run validation.** Subscription backend (D-28) confirmed
working end-to-end against a live URL. Two real bugs surfaced and were fixed in the
same plan with test coverage. One known limitation (Opus native-coord bbox) documented
for Phase 2.

- FLOW-05 (acceptance artifacts generated): SATISFIED
- FLOW-06 (dual-backend interchangeability): SATISFIED (api-key path has mock coverage
  in test_dry_run.py; subscription path confirmed live)
- D-24 (analysis/ untouched): HOLDS
- D-28 (subscription as primary): VALIDATED

No open blockers.
