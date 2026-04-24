---
phase: 02-hospitality-pilot
plan: 06
subsystem: scanner/flow-maps
tags:
  - live-network
  - crawl
  - flow-maps
  - pilot-5-clubs
  - front-half-halt

requires:
  - scanner.flow.discover.discover_flow (Phase 2, Plan 02-05)
  - scanner.flow.validate.validate_flow_map (Phase 1, Plan 01-03)
  - scanner.capture.cookies.STRATEGIES (Phase 2, Plan 02-04)
  - scanner.config.areas.json hospitality entry (Phase 2, Plan 02-03)
  - playwright chromium installed

provides:
  - scanner/flow-maps/hospitality/mancity.json (entry-only stub — Cloudflare 403)
  - scanner/flow-maps/hospitality/tottenham.json (12 steps, cleanest crawl)
  - scanner/flow-maps/hospitality/realmadrid.json (entry-only stub — CAPTCHA halt per D-15)
  - scanner/flow-maps/hospitality/psg.json (12 steps via www.psg.fr fallback; billetterie primary was Cloudflare-blocked)
  - scanner/flow-maps/hospitality/chelsea.json (6 steps via hospitality.chelseafc.com fallback; primary redirected cross-origin)
  - .planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md (per-club results + registration-requirements + known crawler issues + halt checklist)

affects:
  - scanner/flow/discover.py (landing-goto wait condition fixed per Rule 1)

tech-stack:
  added: []
  patterns:
    - "Bounded-timeout landing goto: wait_until='domcontentloaded' + best-effort wait_for_load_state('networkidle', timeout=10000) in try/except — mirrors existing _descend pattern"

key-files:
  created:
    - scanner/flow-maps/hospitality/mancity.json
    - scanner/flow-maps/hospitality/tottenham.json
    - scanner/flow-maps/hospitality/realmadrid.json
    - scanner/flow-maps/hospitality/psg.json
    - scanner/flow-maps/hospitality/chelsea.json
    - .planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md
  modified:
    - scanner/flow/discover.py  (+9 LOC — Rule 1 fix for 30 s networkidle timeout on MCFC landing)

decisions:
  - "MCFC + PSG-billetterie Cloudflare 403 responses accepted as 3-step entry-only stubs per plan fallback protocol; flagged in crawl log for Chrome-MCP back-half handling (Phase 2.5 territory). User registration cannot unblock bot challenges."
  - "RMA CAPTCHA halt accepted per D-15 (no bypass); 3-step stub emitted. Back-half will need Chrome-MCP fallback."
  - "PSG fallback to www.psg.fr/en/hospitality succeeded (12 steps) — billetterie subdomain deferred to back-half Chrome-MCP."
  - "Chelsea crawled via fallback https://hospitality.chelseafc.com/ start (6 steps). Same-org subdomain treated as entry_origin to bypass cross-origin guard; no manual JSON surgery required."
  - "Rule 1 bug fix committed separately (5b976a1) from per-club flow-map commits to preserve clean diff-per-artifact history."

metrics:
  duration: ~12 minutes
  completed: 2026-04-24
  tasks: 3/3
  commits: 7  # 1 bug-fix + 5 flow-maps + 1 crawl-log
  tests_before: 167
  tests_after: 167  # no test changes; pytest re-ran green post-fix
  subscription_tokens: 0
---

# Phase 2 Plan 02-06: Execute Flow-Discovery Crawl × 5 Pilot Clubs Summary

Live Playwright crawl of 5 pilot-club hospitality landing pages using `discover_flow` (02-05). Emitted 5 schema-valid FlowMap JSONs + a per-club crawl log with registration-requirements and back-half handoff notes. Zero subscription tokens consumed. One Rule 1 crawler bug surfaced and fixed (30 s networkidle timeout on landing).

## What Was Built

| File | Steps | Login gates | Broker | External redirects | Dead-ends | CAPTCHA | Cookie-dismiss |
|------|-------|-------------|--------|--------------------|-----------|---------|----------------|
| `mancity.json`     | 3  | 0 | none | 0 | 1 (entry-URL; Cloudflare 403) | N | FAILED |
| `tottenham.json`   | 12 | 0 | none | 0 | 0 | N | OK |
| `realmadrid.json`  | 3  | 0 | none | 0 | 0 | **Y** (halt per D-15) | OK |
| `psg.json`         | 12 | 0 | none | 0 | 2 | N | FAILED (on fallback www domain) |
| `chelsea.json`     | 6  | 0 | none | 0 | 4 (self-referencing path anchor) | N | FAILED (on fallback subdomain) |

All 5 flow-maps validate against `scanner.flow.schema.FlowMap` (tested via `scanner flow validate`). Steps-per-file within 3-15 range (schema D-15). Zero `submit` actions, zero Liverpool references.

## Fallback URLs Used

| Club | Primary | Fallback used | Primary HTTP status |
|------|---------|---------------|---------------------|
| mancity | `www.mancity.com/hospitality` | — (entry-only stub accepted) | 403 Cloudflare |
| tottenham | `www.tottenhamhotspur.com/tickets/premium-experiences/` | — (primary OK) | 200 |
| realmadrid | `www.realmadrid.com/en-US/vip-area/home` | — (CAPTCHA halt; fallback wouldn't help) | 200 |
| psg | `billetterie.psg.fr/en/home-vip` | `www.psg.fr/en/hospitality` | 403 Cloudflare |
| chelsea | `www.chelseafc.com/en/hospitality` | `hospitality.chelseafc.com/match-by-match-hospitality-packages` | 302 → cross-origin |

## Manual JSON Corrections

**None.** All 5 flow-maps are pure crawler output. The Chelsea subdomain case (which plan 02-06 anticipated as a manual-edit candidate) resolved cleanly by re-running the crawl from the subdomain itself — starting FROM `hospitality.chelseafc.com` makes it `entry_origin`, so descent proceeds as same-origin and `external_redirects` stays empty on the final artifact.

## Commits

| Hash | Message |
|------|---------|
| `5b976a1` | `fix(02-06): bounded-timeout landing goto in discover_flow` |
| `b82bc5c` | `feat(02-06): crawl mancity hospitality flow-map` |
| `ad65206` | `feat(02-06): crawl tottenham hospitality flow-map` |
| `6d62a5a` | `feat(02-06): crawl realmadrid hospitality flow-map` |
| `462cabc` | `feat(02-06): crawl psg hospitality flow-map` |
| `c51ae1d` | `feat(02-06): crawl chelsea hospitality flow-map` |
| `9322f63` | `docs(02-06): write 5-club hospitality crawl log` |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Bounded-timeout landing goto in `discover_flow`**

- **Found during:** Task 1 (Man City crawl)
- **Issue:** `page.goto(entry_url, wait_until="networkidle")` in `discover_flow` at line 319 had no `timeout=` override, so Playwright's default 30 s ceiling fired a hard `TimeoutError` on MCFC. Reproducible on retry — not a flake. Modern club sites run long-poll analytics (Adobe Audience Manager, Segment, Snowplow) that never reach `networkidle` within 30 s. Meanwhile, the `_descend` function at lines 428-430 already uses the correct pattern: `wait_for_load_state("networkidle", timeout=10000)` inside a `try/except`. Inconsistent wait handling between landing and descent phases was a blocking bug for ALL 5 pilot clubs, not just MCFC.
- **Fix:** Switched landing `goto` to `wait_until="domcontentloaded"` + best-effort `wait_for_load_state("networkidle", timeout=10000)` in a `try/except`. Mirrors the existing `_descend` pattern. 9 LOC added to `scanner/flow/discover.py`.
- **Files modified:** `scanner/flow/discover.py` (lines 318-327)
- **Commit:** `5b976a1` (separate commit from per-club flow-maps per plan commit-hygiene rule).
- **Test coverage:** no new test added — the fix mirrors an already-tested pattern elsewhere in the module and full pytest suite re-ran green (167/167). A proper integration test requires the capture path which is back-half territory.

### Expected Branch Halts (NOT deviations — plan-anticipated)

- **Manchester City / PSG-billetterie Cloudflare 403:** handled by existing `_detect_dead_end` branch (HTTP >= 400 → dead_end append + entry-only flow-map). Acceptable per plan fallback protocol.
- **Real Madrid CAPTCHA:** handled by existing `captcha_encountered=True` path per D-15 (no bypass). Acceptable per user decision 7.
- **Chelsea cross-origin redirect on primary:** handled by existing external-redirect branch. Fallback to subdomain primary bypasses the guard cleanly.

## Authentication Gates

None. The front-half crawl surfaced zero login walls (`login_gated_steps` empty for all 5). Conservative recommendation in crawl log is to register dummy accounts for all 5 clubs ahead of back-half capture anyway, because shallow crawl depth means the purchase-path credentials likely sit one or two clicks deeper than current coverage.

## Known Stubs

None. All 5 flow-maps are the correct shape for downstream consumption by back-half capture. Three clubs (MCFC, RMA, PSG-billetterie) have 3-step entry-only stubs that represent genuine crawler branch-halts — these are the correct output for the observed bot-challenge / CAPTCHA state, NOT placeholders.

## Threat Flags

None. No new network endpoints, auth paths, file-access patterns, or schema changes introduced. The one code change (discover.py) is a wait-primitive fix with no trust-boundary implication.

## Performance

- **Total wall-clock:** ~12 min 23 s (19:48:52Z → 20:01:15Z)
- **Crawler invocations:** 7 (5 clubs + 2 fallback retries for PSG and Chelsea)
- **Per-crawl range:** 6 s (RMA CAPTCHA early-halt) → 57 s (CHE-subdomain full descent)
- **Playwright chromium launches:** 7 fresh contexts (no cookie leakage across clubs per T-02-06-07 mitigation)
- **Subscription tokens consumed:** 0 (no vision / SDK calls)
- **Test suite:** 167 passed / 0 failed (unchanged pre/post bug-fix; 40 s run)

## Pointers

- **User-facing:** `.planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md` — registration-requirements section, known crawler issues for v2, halt-confirmation checklist.
- **Back-half input:** `scanner/flow-maps/hospitality/*.json` — 5 schema-valid FlowMap files ready for capture consumption.
- **Known v2 work (deferred):** Cloudflare Turnstile detector, trusted-subdomains allowlist, dedupe on `meta.dead_ends`, per-domain cookie priorities, discover integration smoke test.

## Self-Check: PASSED

- [x] `scanner/flow-maps/hospitality/{mancity,tottenham,realmadrid,psg,chelsea}.json` — 5 files exist.
- [x] All 5 validate via `scanner flow validate`.
- [x] Each has 3-15 steps + populated metadata block.
- [x] `grep -c '"submit"' scanner/flow-maps/hospitality/*.json` → all 0.
- [x] `grep -c 'liverpool' scanner/flow-maps/hospitality/*.json` → all 0.
- [x] `.planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md` — 181 lines ≥ 60 min.
- [x] CRAWL-LOG contains `^## Registration Requirements` and `^## Front-Half Halt Confirmation`.
- [x] CRAWL-LOG contains all 5 per-club sections (Manchester City, Tottenham Hotspur, Real Madrid, PSG, Chelsea).
- [x] Halt checklist has all 7 back-half items UNCHECKED.
- [x] `git diff --quiet analysis/` exit 0.
- [x] Full pytest suite: 167 passed.
- [x] All 7 commits referenced in SUMMARY exist in `git log --oneline`.
- [x] Zero subscription tokens consumed (no vision / SDK invocations in this plan).
