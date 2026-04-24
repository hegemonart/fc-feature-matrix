# Phase 2 Front-Half — Summary

**Closed:** 2026-04-24
**Scope:** Plans 02-01 through 02-06 (execution) + 02-07 (front-half closure). Halt point per 02-RESEARCH.md §9 reached.
**Status:** Front-half COMPLETE. Back-half pending user registrations and a subsequent planning session.

## What shipped

| Plan | Output | Notes |
|------|--------|-------|
| 02-01 | `scanner/capture/credentials.py` + tests + `.gitignore` entry | Phase 1 shipping gap closed. `get_credential()` + `MissingCredentialError`. 7 new tests (145 total). |
| 02-02 | `analysis/hospitality/REVIEW-SOURCES.md` + `FEATURES-CANDIDATES.md` | User-approval gate PASSED on 2026-04-24 (`approved — freeze candidates`). Candidate count: 55 unique keys (54 as plan prompt stated — regex undercount — true count 55). |
| 02-03 | `analysis/hospitality/HOSPITALITY-FLOW.md` + `features.ts` + areas.json populate | Rubric 1:1 port of candidate list (55 rows / 55 feat() calls / HP01–HP55). features.ts + types.ts extension compile clean. areas.json hospitality entry `status: "pilot"` (plan said "active" but schema forbids it; used schema-valid `pilot`). |
| 02-04 | 4 new cookie strategies (TOT/RMA/PSG/CHE) in `scanner/capture/cookies.py` | +10 tests. MANCITY_STRATEGY + GLOBAL_COOKIE_PRIORITIES unchanged (user decision 2 preserved). No Liverpool strategy. 155 total tests. |
| 02-05 | `scanner/flow/discover.py` full implementation + `FlowMapMetadata` in schema | +12 net tests (5 schema + 9 discover − 2 deleted stubs). 6 detection hooks. NotImplementedError stub gone. CLI flags `--area/--club/--headless` wired. 167 total tests. |
| 02-06 | 5 flow-map JSONs under `scanner/flow-maps/hospitality/` + `02-06-CRAWL-LOG.md` | All 5 validated. No submit. No Liverpool. Zero subscription tokens. 1 Rule-1 fix: bounded landing goto timeout in discover.py. |

## Halt-point gates (per 02-RESEARCH.md §9)

- [x] 5 flow-map JSON files exist at `scanner/flow-maps/hospitality/{mancity,tottenham,realmadrid,psg,chelsea}.json`
- [x] Each file validates against FlowMap schema (`scanner flow validate` exits 0 for all 5)
- [x] Each file has 3-15 steps (schema D-15 range; observed range 3-12)
- [x] Each file has a populated metadata block (FlowMapMetadata default-factory from plan 02-05)
- [x] User-facing summary written per club (`02-06-CRAWL-LOG.md` §Registration Requirements; 5 per-club sections)
- [x] `FEATURES-CANDIDATES.md` user-approved with ≥ 40 tagged candidates (actual: 55 unique keys across 8 categories; approval phrase received)
- [x] `REVIEW-SOURCES.md` written with source shortlist + rationale (10 gold-standard + 22 review-source URLs in Tier A/B/C)

All 7 gates MET.

## Per-Club Crawl Outcomes (from 02-06-CRAWL-LOG.md)

| Club | Steps | Login-gated | Broker | External | Dead-ends | CAPTCHA | Cookie-dismiss | Needs account? |
|------|-------|-------------|--------|----------|-----------|---------|----------------|----------------|
| mancity | 3 | 0 | none | 0 | 1 (Cloudflare 403 entry) | N | FAILED (no banner on challenge) | N/A — bot challenge, not credential gate |
| tottenham | 12 | 0 | none | 0 | 0 | N | OK (TOT_STRATEGY) | N for current depth |
| realmadrid | 3 | 0 | none | 0 | 0 | **Y** (halt per D-15) | OK | N/A — CAPTCHA not credential-gated |
| psg | 12 | 0 | none | 0 | 2 | N | FAILED (www fallback; strategy tuned for billetterie) | N for current depth |
| chelsea | 6 | 0 | none | 0 | 4 (self-referencing anchor spam) | N | FAILED (subdomain banner wording drift) | likely Y for deeper purchase flow |

**Totals:** 36 steps across 5 flow-maps; zero submit actions emitted; zero Liverpool references; zero login gates surfaced at current crawl depth.

## What did NOT ship (deferred to back-half)

- Full-page capture per club (`scanner capture`)
- Two-judge vision mapping (`scanner vision`) — Opus + Sonnet
- Evidence slicing (PIL bbox crops → `analysis/hospitality/evidence/features/{club}_{feature_key}.png`)
- Coverage report generation (`scanner report`)
- `analysis/hospitality/results/{club}.json` per pilot club (does not exist yet; D-25 upheld for front-half)
- Scoring (`scanner score`) — presence verdicts → tier-weighted scores
- Hospitality Packages UI tab unlock in `app/page.tsx` (with "Pilot: 5 clubs" label)
- Opus bbox empirical calibration (assumption A5 carry-over from Phase 1)
- Pilot-gate user approval of coverage contact sheet (D-17)
- HOSP-01, HOSP-02, HOSP-03 completion — all still "Pending" in REQUIREMENTS.md traceability table (partial progress logged in STATE.md only)

## Phase Invariants Verified

- `git diff --quiet analysis/homepage/` → exit 0 across all 7 front-half plans (D-20 — no homepage changes)
- Scanner module internals (`scanner/capture/{browser,banner_verify}.py`, `scanner/vision/`, `scanner/scoring/`, `scanner/report/`) untouched (D-21) — only `scanner/capture/cookies.py` (additive), `scanner/capture/credentials.py` (new sibling), `scanner/flow/{schema,discover}.py` (additive), `scanner/config/areas.json` (explicit config, not internals), `scanner/cli.py` (CLI layer) modified
- `FlowStep.action` Literal still forbids `submit` (D-16) — regression test in `test_flow_discover.py` guards this
- No Liverpool references in any produced artifact (CLAUDE.md trap) — 0 matches in flow-maps, cookies.py, strategies dict, candidates file body, rubric body
- `scanner/` pytest suite green: 167 tests pass (138 Phase-1 baseline + 29 Phase-2 additions: 7 creds + 10 cookies + 5 schema + 9 discover − 2 deleted stubs = +29 net)
- `npx tsc --noEmit` passes post-types.ts extension
- `npx next build` passes (all 33 /club/[id] static pages generated)

## Tech stack / patterns added

- **Pattern:** FlowMap additive extension via `default_factory` (schema evolution without breaking prior Phase-1 artifacts).
- **Pattern:** Sync Playwright crawler with depth + step caps, matching Phase 1 capture posture (`sync_playwright()` context manager — same idiom as `scanner.capture.browser`).
- **Pattern:** Two-doc user-review gate (REVIEW-SOURCES.md + FEATURES-CANDIDATES.md → frozen → rubric). Blocking `checkpoint:human-verify` with explicit approval phrase.
- **Pattern:** Credential lookup — env-backed, file-loaded (python-dotenv), `None`-on-absent, NAME-only error messaging (value-leak-proof `MissingCredentialError`).
- **Pattern:** Per-club `CookieStrategy` dispatch extending Phase-1 shape (5 strategies: MCFC/TOT/RMA/PSG/CHE; locale-aware FR/ES priorities inside the per-club dict, not in the global list).
- **Pattern:** Broker allowlist (5 vendors: seat_unique, keith_prowse, eventmasters, p1_travel, pitch_international) — cross-origin gate halts non-broker redirects.
- **Pattern:** Detect-then-halt per-branch (no recursion explosion on JS-heavy pages). 6 detection hooks: CAPTCHA, origin check, login gate, form pre-submit, rank+click, and HTTP>=400 / h1-404 dead-ends.

## Assumptions that still need verification (carry to back-half)

- **Opus bbox calibration** (02-RESEARCH.md §8, assumption A5) — empirical test before full capture wave. Phase 1 Plan 01-08 flagged Opus 4.7 returns bboxes in native pixel coords, not the resized coord space `denormalise_bbox` assumes. Recommended back-half action: small calibration experiment + per-model `bbox_mode: Literal["css", "native"]` config in areas.json.
- **Chelsea `hospitality.chelseafc.com` own-vs-broker classification** (02-RESEARCH.md §10 Q3) — strongly suspected Keith Prowse whitelabel per research §5. Revisit after a full crawl populates real headers; if confirmed, add to `BROKER_DOMAINS` allowlist.
- **Per-club cookie strategy priorities** — verified for MCFC (Phase-1), assumed-from-research for TOT/RMA/PSG/CHE until first full capture. Fallback flows landed on `www.psg.fr` / `hospitality.chelseafc.com` (distinct from primary domains the strategies targeted); back-half may need domain-specific priority extensions.
- **Cloudflare Turnstile detection gap** — the crawler's CAPTCHA detector looks for reCAPTCHA/hCaptcha selectors. MCFC + PSG-billetterie are Cloudflare-gated (distinct path: "Just a moment..." interstitial); currently flagged as HTTP 403 dead-ends. Back-half may want a `bot_challenge_encountered` flag in `FlowMapMetadata` v2.
- **Deep-crawl depth** — current max_depth=3 / MAX_STEPS=15 stops before purchase flows. Back-half may need per-club flow-map overrides with explicit click-paths (not crawler-discovered) for the full `landing → category → package → match → enquiry` sequence.

## Commits from the Front-Half (high-level)

Plan 02-01: `4d6999a`, `706d90b`, `ec04bd1` + metadata
Plan 02-02: `410b927`, `ef63648` + metadata
Plan 02-03: `d091354`, `8d40d73`, `5dacb13` + metadata `9d5d89a`
Plan 02-04: `2b48f40`, `12e6575` + metadata
Plan 02-05: `f762eae`, `82059c1`, `c59ec3f`, `cfa0975`, `e6b3607` + metadata `d19c51d`
Plan 02-06: `5b976a1`, `b82bc5c`, `ad65206`, `6d62a5a`, `462cabc`, `c51ae1d`, `9322f63` + metadata `e06f46a`

Approximately 30 commits total across the 6 execution plans + this closure plan (02-07).

## Pointers

- **Back-half resume:** `.planning/phases/02-hospitality-pilot/02-BACK-HALF-HANDOFF.md`
- **Authoritative crawl metadata:** `.planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md`
- **Locked decisions:** `.planning/phases/02-hospitality-pilot/02-CONTEXT.md` (21 D-codes)
- **Research (all 10 sections still current for back-half):** `.planning/phases/02-hospitality-pilot/02-RESEARCH.md`
- **Rubric (source of truth):** `analysis/hospitality/HOSPITALITY-FLOW.md` (55 rows)
- **Typed features:** `analysis/hospitality/features.ts` (HP01–HP55)
- **Flow-maps:** `scanner/flow-maps/hospitality/{mancity,tottenham,realmadrid,psg,chelsea}.json`

---
*Phase: 02-hospitality-pilot — front-half closure via plan 02-07*
*Completed: 2026-04-24*
