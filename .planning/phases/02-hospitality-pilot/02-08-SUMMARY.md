---
phase: 02-hospitality-pilot
plan: 08
subsystem: scanner-foundation
tags:
  - crawler-v2
  - turnstile
  - trusted-subdomains
  - dedupe
  - cookie-domain-override
  - opus-bbox-calibration
  - credentials-cwd-fix
  - foundation-fixes
requires:
  - ".planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md (§Known Crawler Issues 1–4)"
  - ".planning/phases/02-hospitality-pilot/02-RESEARCH.md (§8 calibration approach)"
  - ".planning/phases/02-hospitality-pilot/02-BACK-HALF-HANDOFF.md (credentials CWD escalation)"
  - ".planning/phases/01-flow-automation-layer/01-08-SUMMARY.md (Opus bbox issue)"
provides:
  - "scanner/flow/discover.py: Cloudflare Turnstile detector + trusted_subdomains allowlist + meta dedupe + per-domain cookie dispatch"
  - "scanner/flow/schema.py: FlowMapMetadata.bot_challenge_encountered + bot_challenge_reason + trusted_subdomains_used (additive defaults)"
  - "scanner/capture/cookies.py: dismiss_cookies(domain=...) forward-compat hook for broker-page strategies"
  - "scanner/capture/credentials.py: find_dotenv(usecwd=True) tree-walk so credentials resolve from any CWD"
  - "scanner/config/schema.py: AreaEntry.bbox_mode + trusted_subdomains + features_evidence_dir (additive)"
  - "scanner/config/areas.json: bbox_mode='css' + trusted_subdomains seed for chelsea/psg/tottenham"
  - "scanner/scripts/calibrate_opus_bbox.py: standalone Opus bbox calibration harness (~310 lines)"
  - "scanner/output/opus-bbox-calibration.json: empirical calibration artifact (decided_mode='css')"
  - "scanner/cli.py slice_cmd: bbox_mode config gate (D-21 narrow deviation, call-site only)"
affects:
  - ".planning/ROADMAP.md — Phase 2 row will advance to 8/TBD (back-half resumed)"
  - "scanner/.gitignore — one-line override admitting opus-bbox-calibration.json"
tech-stack:
  added:
    - "click (already present) — used for the new calibration harness CLI"
  patterns:
    - "Halt-and-record halt-class detection (mirror of _detect_captcha): _detect_bot_challenge returns a reason label, never raises, sets a sibling boolean+reason pair on FlowMapMetadata"
    - "Order-preserving list dedupe via list(dict.fromkeys(...)) (Python 3.7+ dict insertion-order guarantee)"
    - "Forward-compatible kwarg with empty-default lookup: dismiss_cookies(domain=) collapses to pre-08 behavior when STRATEGIES has no domain entry"
    - "Default-safe IoU margin: calibration falls back to existing-behavior mode unless empirical evidence beats it by 0.20 IoU"
    - "Config-driven gate at the call-site (D-21 narrow deviation): denormalise_bbox math untouched, only the slice CLI handler reads bbox_mode and chooses to invoke or skip"
  removed: []
key-files:
  created:
    - "scanner/scripts/__init__.py"
    - "scanner/scripts/calibrate_opus_bbox.py"
    - "scanner/output/opus-bbox-calibration.json"
    - "scanner/tests/test_calibrate_opus_bbox.py"
    - ".planning/phases/02-hospitality-pilot/02-08-SUMMARY.md"
  modified:
    - "scanner/flow/discover.py (+92 lines: bot challenge detector, trusted_subdomains, dedupe helper, descent rewiring)"
    - "scanner/flow/schema.py (+18 lines: 3 additive metadata fields)"
    - "scanner/capture/cookies.py (+34 lines: domain= kwarg dispatch)"
    - "scanner/capture/credentials.py (+12 lines: find_dotenv tree-walk)"
    - "scanner/config/schema.py (+22 lines: BboxMode + 3 additive AreaEntry fields)"
    - "scanner/config/areas.json (+7 lines: bbox_mode + trusted_subdomains seed)"
    - "scanner/cli.py (+10 lines: slice_cmd bbox_mode gate)"
    - "scanner/tests/test_flow_discover.py (+10 tests, +175 lines)"
    - "scanner/tests/test_cookies.py (+2 tests, +59 lines)"
    - "scanner/tests/test_areas_schema.py (+6 tests, +57 lines)"
    - "scanner/tests/test_credentials.py (+3 tests, +88 lines)"
    - "scanner/.gitignore (+3 lines: artifact override)"
decisions:
  - "Cloudflare Turnstile detection is a sibling class of CAPTCHA, not a sub-classification: separate boolean+reason fields preserve the existing captcha_encountered semantics and let downstream consumers triage Turnstile vs reCAPTCHA differently"
  - "trusted_subdomains is a per-club dict in areas.json, not a global allowlist: each club has its own legitimate sub-brand domains; centralized allowlist would have to be tagged per-club anyway and would risk cross-club leaks if the wrong key was queried"
  - "Per-domain cookie dispatch concatenates domain-then-club priority lists rather than replacing — the broker page may share consent vocabulary with the parent (e.g. 'tout accepter' on PSG broker pages too), so collapsing dupes via dict.fromkeys is cheaper than authoring exhaustive domain entries"
  - "Calibration harness uses subscription-mode by default (D-28) so no API key handling is in the call path; api-key mode is a future-stub raise"
  - "decided_mode defaults to 'css' (the pre-08 behavior) unless native_iou beats css_iou by 0.20 — calibration is an observation that may flip the gate, never a regression risk if it's noisy"
  - "find_dotenv tree-walk PREFERS the discovered .env.local over the legacy _REPO_ROOT path; falls back only when find_dotenv returns empty (e.g. site-packages installs)"
metrics:
  duration: "~25 minutes (auto-mode, single executor pass)"
  task_count: 3
  test_delta: "+32 (167 -> 199, all green)"
  commit_count: 7
  files_touched: 16
  subscription_cost_usd: "~0.05 (single Opus vision call for calibration)"
  d_20_invariant: "preserved (git diff --quiet analysis/ exits 0)"
  d_21_invariant: "preserved (scanner/vision/slice.py untouched; only call-site config gate added in scanner/cli.py)"
---

# Phase 02 Plan 08: Crawler v2 Foundation Fixes Summary

Six "fix-the-foundation" items shipped before back-half capture begins. Crawler v2 (Cloudflare Turnstile detection, trusted-subdomain allowlist, dead-ends dedupe, per-domain cookie dispatch) lands the cleanups deferred from front-half plus an empirical Opus bbox calibration and a credentials.py CWD bug fix. Plan 02-09 onwards now have a credible foundation.

## Six-Fix Changelog

1. **Cloudflare Turnstile detector** (`scanner/flow/discover.py`) — `_detect_bot_challenge(page, status)` returns `'turnstile'` when (HTTP 403 AND ('Just a moment' text OR cf-challenge selector)). Sibling to `_detect_captcha`; halts the branch and records `meta.bot_challenge_encountered=True`, `meta.bot_challenge_reason='turnstile'`. Never raises (try/except wrapped). Wired into `discover_flow` before the dead-end branch on landing.
2. **Trusted-subdomain allowlist** (`scanner/flow/discover.py` + `scanner/config/areas.json`) — `_inspect_origin` now accepts a `trusted_subdomains` kwarg; matches against both raw netloc and stripped netloc so entries can be authored either form (`hospitality.chelseafc.com` or `www.psg.fr`). Hospitality seed: chelsea → hospitality.chelseafc.com, psg → billetterie.psg.fr + www.psg.fr, tottenham → tottenhamhotspurstadium.com.
3. **Dedupe `meta.*` lists** (`scanner/flow/discover.py:_dedupe_meta`) — Called once before `_write_and_validate` JSON-serialises. Collapses duplicate URLs across `dead_ends`, `external_redirects`, `login_gated_steps`, and `trusted_subdomains_used` while preserving insertion order via `list(dict.fromkeys(...))`.
4. **Per-domain cookie priority override** (`scanner/capture/cookies.py`) — `dismiss_cookies(page, club=, *, domain=None)` extends the dispatcher with a forward-compat `domain` kwarg. When `STRATEGIES[domain]` exists its priority list is concatenated FIRST then the club's (deduped via dict.fromkeys); when absent, behavior collapses to the pre-08 club-only path. `discover_flow` now passes `domain=urlparse(page.url).netloc` on landing so the override is exercised end-to-end.
5. **Opus bbox empirical calibration** (`scanner/scripts/calibrate_opus_bbox.py` + `scanner/cli.py:slice_cmd`) — One-shot Click CLI sends a single Opus vision query asking for the bbox of a known feature, computes `css_iou` (denormalise applied) vs `native_iou` (raw), picks `'native'` only when the gap exceeds 0.20 IoU. Result for hospitality: **`decided_mode = 'css'`** (Opus returns model-resized coords; existing denormalise_bbox path is correct). The slice CLI handler reads `bbox_mode` from areas.json and skips `denormalise_bbox` only when set to `'native'` AND model is Opus — denormalise math itself is untouched (D-21 narrow deviation: call-site config gate only).
6. **`credentials.py` CWD bug fix** (`scanner/capture/credentials.py`) — Replaces `load_dotenv(_REPO_ROOT/'.env.local')` with `find_dotenv(filename='.env.local', usecwd=True)` tree-walk. Falls back to the legacy `_REPO_ROOT` path when find_dotenv returns empty. T-08-03 mitigation: find_dotenv only walks UP from CWD, never escapes the filesystem-root boundary.

## Bbox Calibration Outcome

Run against `scanner/output/evidence/hospitality/fullpage/mancity_landing.png` (2880×6778, MCFC site).

| Field | Value |
|---|---|
| Observed bbox (Opus reply) | `[115, 17, 168, 65]` (logo-sized 53×48) |
| Ground truth (header band) | `[0, 0, 2880, 800]` |
| `css_iou` (denormalise_bbox applied) | 0.0076 |
| `native_iou` (raw bbox) | 0.0011 |
| Margin | 0.20 |
| **Decided mode** | **`css`** (default-safe; native did not beat css by 0.20) |

Subscription cost: ~$0.05 (one Opus vision call, succeeded on first try, no retry needed).

Interpretation: Opus returned a tight bbox around the small logo glyph, not the full header band. Both IoUs are low because the prompt-and-ground-truth describe different scales, but the relative ordering still favors css-mode: when denormalised by ~2.63× (image long edge 6778 / model limit 2576), the bbox grows to ~140×126 which has greater overlap with the header band than the raw 53×48 box. Areas.json hospitality entry already carries `"bbox_mode": "css"` from the Task-1 commit, so no further config change is needed.

## Test Count Delta

| Suite | Pre-08 | Post-08 | Δ |
|---|---|---|---|
| `test_flow_discover.py` | 9 | 19 | +10 |
| `test_cookies.py` | 18 | 20 | +2 |
| `test_areas_schema.py` | 11 | 17 | +6 |
| `test_credentials.py` | 7 | 10 | +3 |
| `test_calibrate_opus_bbox.py` | — | 11 | +11 |
| **TOTAL** | **167** | **199** | **+32** |

All 199 green. Front-half flow-map JSONs (`chelsea.json`, `mancity.json`, `psg.json`, `realmadrid.json`, `tottenham.json`) still validate after the schema extension (verified by a regression test).

## D-21 Deviation Entry (Documented)

`scanner/vision/slice.py:denormalise_bbox` is in the protected D-21 list. The change here is **call-site only**: `scanner/cli.py:slice_cmd` reads `entry.bbox_mode` from areas.json and either invokes `denormalise_bbox` (when `bbox_mode == 'css'`, default) or passes the raw bbox through (when `bbox_mode == 'native'` AND model is Opus). The `denormalise_bbox` math itself is unchanged (verified: `git log scanner/vision/slice.py` shows last modification was Plan 01-04, not 02-08).

This deviation is reproduced verbatim in `scanner/output/opus-bbox-calibration.json:decision_notes`:

> D-21 deviation note: bbox_mode is read at the slice CLI call-site, not by modifying denormalise_bbox internals. Approved per Plan 02-08 deviation entry; denormalise_bbox math is untouched.

## Commits

| Commit | Type | Files | Why |
|---|---|---|---|
| `c666b81` | feat(02-08) | discover.py, schema.py, config/schema.py, areas.json | turnstile + trusted_subdomains + dedupe + AreaEntry extensions |
| `e8c21b2` | feat(02-08) | cookies.py | per-domain cookie priority override |
| `923c62b` | test(02-08) | test_flow_discover.py, test_cookies.py, test_areas_schema.py | 18 regression tests for crawler v2 fixes |
| `d4cabaf` | fix(02-08) | credentials.py, test_credentials.py | find_dotenv(usecwd=True) tree-walk |
| `446bc97` | feat(02-08) | scripts/__init__.py, scripts/calibrate_opus_bbox.py, cli.py | calibration harness + bbox_mode gate |
| `a65e1cb` | chore(02-08) | output/opus-bbox-calibration.json, .gitignore | calibration result for reproducibility |
| `51aa331` | test(02-08) | test_calibrate_opus_bbox.py | 11 tests for bbox_mode wiring + decision logic |

## Threat-Model Implementation Status

| Threat | Disposition | Implementation |
|---|---|---|
| T-08-01 (Info disclosure via vision call) | mitigate | Subscription mode default (D-28); only the on-disk hospitality landing PNG sent — no new exfiltration surface |
| T-08-02 (Tampering with calibration JSON) | accept | File generated; pytest parses it (`test_calibration_artifact_format_required_fields`) so a malformed commit fails CI |
| T-08-03 (find_dotenv tree-walk escape) | mitigate | find_dotenv only walks UP from CWD; filesystem-root bounded; new test exercises a sibling tmp dir |
| T-08-04 (DoS via _detect_bot_challenge) | accept | Function never raises (try/except around content() and query_selector); empty body falls through to `None` |
| T-08-05 (Spoofed trusted_subdomain) | mitigate | trusted_subdomains live in areas.json (committed, PR-reviewed); 4 explicit entries only |

## Pointers

- Front-half halt origin: `.planning/phases/02-hospitality-pilot/02-FRONT-HALF-SUMMARY.md`
- Back-half resumption checklist: `.planning/phases/02-hospitality-pilot/02-BACK-HALF-HANDOFF.md`
- Crawler issues catalogued: `.planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md` §Known Crawler Issues
- Opus bbox issue origin: `.planning/phases/01-flow-automation-layer/01-08-SUMMARY.md`
- Calibration approach reference: `.planning/phases/02-hospitality-pilot/02-RESEARCH.md` §8

## Self-Check: PASSED

- Files created: `scanner/scripts/__init__.py`, `scanner/scripts/calibrate_opus_bbox.py`, `scanner/output/opus-bbox-calibration.json`, `scanner/tests/test_calibrate_opus_bbox.py` — all present (verified: `ls scanner/scripts scanner/output/opus-bbox-calibration.json scanner/tests/test_calibrate_opus_bbox.py`).
- Commits exist: c666b81, e8c21b2, 923c62b, d4cabaf, 446bc97, a65e1cb, 51aa331 — all on `claude/charming-bhaskara-a8317c` (verified via `git log --oneline -7`).
- Test suite: 199 passed, 0 failed (latest `uv run pytest tests/ -q` after final commit).
- D-20: `git diff --quiet analysis/` exit 0.
- D-21: `git log scanner/vision/slice.py` last entry is Plan 01-04 commit `ce56ac4`, not Plan 02-08.
