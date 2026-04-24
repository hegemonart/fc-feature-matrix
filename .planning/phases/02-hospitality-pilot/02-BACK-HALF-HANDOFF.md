# Phase 2 Back-Half — Handoff

**Source:** Phase 2 front-half closed 2026-04-24. Resume when user has registered dummy accounts (see "User Action Required" below) AND Chrome-MCP fallback strategy is confirmed for the three Cloudflare/CAPTCHA-gated clubs.

## What the back-half must deliver

Per ROADMAP.md Phase 2 success criteria (items 4–9):

- [ ] `/scanner/flow-maps/hospitality/{club}.json` — already shipped in front-half; back-half ONLY modifies these if a flow-map needs manual extension after user registration unlocks login-gated branches, OR if per-club override paths are authored for the deeper purchase flow (crawl depth 3 was insufficient).
- [ ] Full capture per pilot club via `scanner capture --area hospitality --club <slug>` — produces `scanner/output/evidence/hospitality/fullpage/{club}_{step}.png`.
- [ ] Two-judge vision mapping via `scanner vision --area hospitality --club <slug>` — Opus + Sonnet judgments with disagreement flagging to `scanner/output/disagreements-hospitality.json`.
- [ ] Evidence slicing — PIL bbox crops into `analysis/hospitality/evidence/features/{club}_{feature_key}.png` for each of 55 features × 5 clubs.
- [ ] Coverage report via `scanner report --area hospitality` — HTML contact sheet (grid per feature, thumbnail per club, red-border on absent).
- [ ] `analysis/hospitality/results/{club}.json` — scored feature presence per pilot club (unblocks `buildPresence()` swap in `analysis/hospitality/features.ts`, currently stubbed to always-absent).
- [ ] `scanner score --area hospitality` — recompute scores from results + features.ts tier weights.
- [ ] Hospitality Packages UI tab unlocked in the Next.js app with "Pilot: 5 clubs" label (until Phase 2.5). Single-orange-CTA invariant preserved. Visual regression baseline update.
- [ ] User review of coverage report → approval → pilot gate to Phase 2.5 (D-17).

## User Action Required (before back-half planning)

**Per `.planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md` §Registration Requirements:** the front-half crawl surfaced NO explicit login walls (`login_gated_steps` empty for all 5). **However,** crawl depth was shallow (3-12 steps) — the "Buy now" / "Select match" / enquiry-form CTAs sit 1-2 clicks deeper than the current flow-maps cover. Back-half will hit credential gates when descending into the purchase path for TOT / PSG / CHE at minimum.

**Conservative recommendation:** register dummy accounts for all 5 pilot clubs before back-half starts. If a club ends up not requiring an account, the credential is simply unused.

### Per-club registration table (verbatim from 02-06-CRAWL-LOG.md)

| Club | Register at | Env vars (in `.env.local`) | Notes |
|------|-------------|-----------------------------|-------|
| Manchester City | `https://www.mancity.com/account` | `MANCITY_HOSPITALITY_USER` / `MANCITY_HOSPITALITY_PASS` | Cloudflare Turnstile on hospitality landing — needs Chrome MCP to clear manually before a logged-in session can be used. |
| Tottenham Hotspur | `https://www.tottenhamhotspur.com/account/signup` | `TOTTENHAM_HOSPITALITY_USER` / `TOTTENHAM_HOSPITALITY_PASS` | Cleanest flow; standard email verification expected. |
| Real Madrid | `https://www.realmadrid.com/en-US/register` | `REALMADRID_HOSPITALITY_USER` / `REALMADRID_HOSPITALITY_PASS` | CAPTCHA on the VIP-area landing will block automated auth; Chrome MCP session needed to reach logged-in state. |
| PSG | `https://www.psg.fr/en/register` (www) AND/OR `https://billetterie.psg.fr/en/register` (billetterie) | `PSG_HOSPITALITY_USER` / `PSG_HOSPITALITY_PASS` | billetterie subdomain is Cloudflare-gated — register on www first, then log in once on billetterie via Chrome MCP to mint the session cookie. |
| Chelsea | `https://www.chelseafc.com/en/account/register` AND possibly Keith Prowse via `https://hospitality.chelseafc.com/` | `CHELSEA_HOSPITALITY_USER` / `CHELSEA_HOSPITALITY_PASS` | Hospitality subdomain is likely Keith Prowse whitelabel — expect a separate sign-up on that host if chelseafc.com SSO doesn't bridge. Confirm at back-half time. |

### Steps for the user

1. For each club listed above: register a dummy account. Recommended email convention: `your+{club}hosp@<yourdomain>.com` with a catchall OR Gmail `+alias` tag (5 isolated inboxes via one real account).
2. Store credentials verbatim in `.planning/phases/02-hospitality-pilot/credentials.local.md` — gitignored per D-13 (rule added in plan 02-01).
3. Copy the same credentials into `.env.local` at repo root — gitignored per D-14. Env-var convention (locked in plan 02-01): `{CLUB_UPPER}_HOSPITALITY_{USER|PASS}`. Example:

   ```
   TOTTENHAM_HOSPITALITY_USER=your+tothosp@example.com
   TOTTENHAM_HOSPITALITY_PASS=<strong-random-password>
   ```

4. Verify `.env.local` and `credentials.local.md` never get committed:
   ```bash
   git check-ignore .env.local .planning/phases/02-hospitality-pilot/credentials.local.md
   # both must exit 0
   ```
5. Sanity-check each credential loads via the Plan 02-01 helper:
   ```bash
   python -c "from scanner.capture import get_credential; print(get_credential('tottenham', 'user'))"
   # should print the email (not None)
   ```
6. When ready, run `/gsd:plan-phase 2` to plan the back-half (or prompt Claude directly).

## Back-half plan count: TBD

Preliminary back-half plan shape (to be refined at next planning session):

1. **Back-half Plan 1 — Crawler v2 fixes + Opus bbox empirical calibration.** Four small fixes filed in 02-06-CRAWL-LOG.md §Known Crawler Issues (Cloudflare Turnstile detector, trusted-subdomain allowlist, dedupe on `meta.dead_ends`, domain-specific cookie priorities) + a bbox calibration harness per 02-RESEARCH.md §8 option (ii). Ships BEFORE full capture.
2. **Back-half Plan 2 — Per-club flow-map override drafts.** Current max_depth=3 / MAX_STEPS=15 does not cover the full `landing → category → package → match → enquiry` sequence. Authors explicit click-paths (not crawler-discovered) into the 5 flow-maps, unlocking deeper purchase-flow capture. Likely needs Chrome MCP fallback flow-maps for MCFC / RMA / PSG-billetterie (the 3 Cloudflare / CAPTCHA clubs).
3. **Back-half Plan 3 — Full-page capture × 5 clubs.** Consumes front-half flow-maps (possibly extended by Plan 2). Writes to `scanner/output/evidence/hospitality/fullpage/`. Subscription cost: ~0 tokens (captures are Playwright-only, no vision calls yet).
4. **Back-half Plan 4 — Two-judge vision mapping × 5 clubs.** Subscription backend (D-28). Opus + Sonnet judgments against the 55-feature rubric. Disagreement artifact written to `scanner/output/disagreements-hospitality.json`.
5. **Back-half Plan 5 — Evidence slicing + contact sheet + `analysis/hospitality/results/{club}.json` generation.** PIL bbox crops, Jinja2 contact sheet (mirror of Phase 1 Plan 01-05), 5 results JSONs.
6. **Back-half Plan 6 — Hospitality Packages UI tab unlock in `app/page.tsx`.** "Pilot: 5 clubs" label. Single-orange-CTA invariant preserved (project CLAUDE.md rule). Visual regression baseline update via `npx playwright test --update-snapshots` where intentional.
7. **Back-half Plan 7 — Coverage report user review → pilot-gate confirmation (D-17).** Unblocks Phase 2.5 (remaining 28 clubs).

This list is a sketch. The next `/gsd:plan-phase 2` session refines it using the crawl-log metadata + the registration state the user will have in place by then.

## Budget estimates for back-half

- **Crawler v2 + calibration (Plan 1):** ~30 min coding + ~5 min bbox calibration run. ~0 subscription tokens.
- **Flow-map override drafting (Plan 2):** ~45 min per club × 5 = ~3.75 hrs manual click-path authoring (includes Chrome MCP sessions for MCFC/RMA/PSG-billetterie).
- **Capture wave (Plan 3):** ~5 min per club × 5 = ~25 min Playwright wall-clock; ~0 subscription tokens.
- **Vision wave (Plan 4):** ~3 min per club × 5 × 2 judges = ~30 min. **Subscription budget:** ~5–10 minutes of Max-20x quota assuming 3-min Opus + 1-min Sonnet per club.
- **Slicing + report + scoring (Plan 5):** < 2 min total (PIL + Jinja2 + Node recalculate).
- **UI tab unlock (Plan 6):** Next.js + React work, no network. Visual regression snapshot regen included.
- **User review + pilot gate (Plan 7):** Depends on user availability. D-17 gate.

**Estimated total:** ~6 hours of executor wall-clock across plans, plus human approval cycles.

## Pre-resumption checklist

Before invoking `/gsd:plan-phase 2` to plan the back-half:

- [ ] User has registered dummy accounts for all 5 pilot clubs (or explicitly waived for clubs where depth-first crawl confirms no login wall).
- [ ] `.env.local` contains all required `{CLUB}_HOSPITALITY_{USER|PASS}` env vars.
- [ ] `git check-ignore .env.local .planning/phases/02-hospitality-pilot/credentials.local.md` → both exit 0.
- [ ] `scanner/flow-maps/hospitality/*.json` still validate (`scanner flow validate` for each — no schema bit-rot).
- [ ] `scanner/` pytest suite still green on current HEAD (`cd scanner && uv run pytest tests/` → 167 passed).
- [ ] Phase 1 invariants still hold: `git diff --quiet analysis/homepage/` (D-20); D-21 module internals untouched.
- [ ] Chrome MCP extension confirmed installed + connected (required for MCFC / RMA / PSG-billetterie bot-challenge fallback).

## Risks carried into back-half

- **Opus bbox coord-space** (02-RESEARCH.md §8, assumption A5) — if the empirical calibration reveals native-pixel coords (as Plan 01-08 flagged for Opus 4.7), `scanner/vision/slice.py` gets a config-level override (research §8 option ii): add `bbox_mode: Literal["css", "native"] = "native"` per-model config, skip DPR=2 scaling when mode is native. If resized-space confirmed, no change. Front-half left this undecided intentionally.
- **Chelsea subdomain classification** (02-RESEARCH.md §10 Q3) — `hospitality.chelseafc.com` suspected Keith Prowse whitelabel. Revisit after full-crawl headers land. If confirmed, add `keithprowse.com` (or the underlying vendor domain) to `BROKER_DOMAINS` allowlist in `scanner/flow/discover.py`.
- **PSG CAPTCHA / Cloudflare** — if back-half re-crawls billetterie, it will re-hit the 403 bot-challenge. Chrome MCP fallback required, or scope-reduction (www-only coverage with a rubric-level note that billetterie was inaccessible to automated tooling).
- **Real Madrid CAPTCHA** — same story as PSG-billetterie. Chrome MCP fallback is the only path to logged-in state.
- **Manchester City Cloudflare Turnstile** — distinct from the above two in that it triggers on the hospitality landing itself (not a deeper page). Chrome MCP for MCFC hospitality captures (matches existing homepage-phase convention: 5 other clubs already use Chrome MCP).
- **Cookie strategy drift** — TOT/RMA/PSG/CHE wording was assumed from research; first capture wave will verify. If any club's banner wording shifted, add new entries to the per-club strategy's `priority` list (NOT to `GLOBAL_COOKIE_PRIORITIES` per user decision 2).
- **Self-referencing anchor spam (Chelsea)** — the crawler re-detects the same dead-end URL across descent rounds instead of deduplicating. Cosmetic but inflates `dead_ends` count. `set()` wrapper on `meta.dead_ends` write path filed for v2.

## References

- `.planning/phases/02-hospitality-pilot/02-CONTEXT.md` — 21 locked decisions (D-01 through D-28 range).
- `.planning/phases/02-hospitality-pilot/02-RESEARCH.md` — 10 research sections, still current for back-half. §8 (Opus bbox), §9 (Halt point), §10 (Open questions).
- `.planning/phases/02-hospitality-pilot/02-FRONT-HALF-SUMMARY.md` — what shipped in plans 02-01 through 02-06.
- `.planning/phases/02-hospitality-pilot/02-06-CRAWL-LOG.md` — authoritative registration-requirements source; per-club crawl outcomes.
- `scanner/flow-maps/hospitality/*.json` — 5 schema-valid FlowMap files ready for capture consumption.
- `analysis/hospitality/HOSPITALITY-FLOW.md` — 55-feature rubric (source of truth).
- `analysis/hospitality/features.ts` — typed feature array (HP01–HP55).

## Summary

- **Blocked on user:** dummy account registrations for 5 clubs (or explicit waiver per-club).
- **Blocked on work items:** 4 crawler v2 fixes + Opus bbox calibration + Chrome MCP fallback strategy for 3 bot-challenged clubs (all addressable by the next planner/executor in Back-half Plan 1).
- **Ready artifacts:** rubric, features.ts, areas.json (pilot), 5 flow-map stubs, 5 per-club cookie strategies, credentials helper.
- **Infrastructure:** Phase 1 scanner unchanged; ready to consume Phase 2 config.
- **Next step:** user registers accounts → `/gsd:plan-phase 2` → plan back-half.
