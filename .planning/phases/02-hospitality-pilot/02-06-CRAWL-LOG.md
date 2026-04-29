# 02-06 Crawl Log — 5-Club Hospitality Flow-Discovery

**Ran:** 2026-04-24
**Scope:** Phase 2 front-half. Crawler = `scanner.flow.discover.discover_flow` (plan 02-05). No capture / vision / slicing / report / results JSON executed.
**Network budget used:** ~3.5 minutes wall-clock across 6 crawls (5 clubs + 2 fallback retries).
**Subscription budget used:** zero (no vision / SDK calls).

## Per-Club Results

### Manchester City (`mancity`)

- **Entry URL:** `https://www.mancity.com/hospitality`
- **HTTP status:** 403 (Cloudflare anti-bot challenge — "Just a moment..." interstitial)
- **Fallback used:** no (the Phase-1 dry-run URL is the primary; no alternate was documented)
- **Steps emitted:** 3 (entry-only seed: navigate + wait + screenshot)
- **Cookie dismissal:** FAILED (`cookie_dismiss_failed=true`) — no consent banner on the challenge page
- **Login gates detected:** none
- **Broker vendor:** none
- **External redirects:** 0
- **Dead ends:** 1 — `https://www.mancity.com/hospitality` (challenge page flagged by status-403 branch of `_detect_dead_end`)
- **CAPTCHA:** N (Cloudflare Turnstile interstitial — distinct from the crawler's CAPTCHA detector, which looks for reCAPTCHA/hCaptcha selectors)
- **Registration needed:** N/A — the bot challenge is the block; user accounts cannot unlock it. Needs Chrome-MCP fallback in the back-half (Phase 2.5 territory).

### Tottenham Hotspur (`tottenham`)

- **Entry URL:** `https://www.tottenhamhotspur.com/tickets/premium-experiences/`
- **HTTP status:** 200
- **Fallback used:** no
- **Steps emitted:** 12 (cleanest crawl of the five — landing + depth-1 and depth-2 descents into tier pages)
- **Cookie dismissal:** OK (TOT_STRATEGY — `cookie_dismiss_failed=false`)
- **Login gates detected:** none
- **Broker vendor:** none
- **External redirects:** 0
- **Dead ends:** 0
- **CAPTCHA:** N
- **Registration needed:** N — back-half capture can proceed without credentials for the currently-crawled depth.

### Real Madrid (`realmadrid`)

- **Entry URL:** `https://www.realmadrid.com/en-US/vip-area/home`
- **HTTP status:** 200 (landing reached)
- **Fallback used:** no (the CAPTCHA halts descent regardless of URL — no point retrying the fallback)
- **Steps emitted:** 3 (entry-only seed; descent aborted after CAPTCHA detection per D-15)
- **Cookie dismissal:** OK (`cookie_dismiss_failed=false`)
- **Login gates detected:** none
- **Broker vendor:** none
- **External redirects:** 0
- **Dead ends:** 0
- **CAPTCHA:** **Y** — `captcha_encountered=true`. Crawler halted descent per D-15 (no bypass).
- **Registration needed:** N/A — CAPTCHA is not credential-gated; user registration will NOT unblock this. **CAPTCHA halted crawl — user registration won't unblock this; consider Chrome MCP fallback for back-half (Phase 2.5 territory).**

### PSG (`psg`)

- **Entry URL (final, after fallback):** `https://www.psg.fr/en/hospitality`
- **Primary URL attempted:** `https://billetterie.psg.fr/en/home-vip` → HTTP 403 (Cloudflare anti-bot); 3-step stub with entry URL in dead_ends.
- **HTTP status (fallback):** 200
- **Fallback used:** YES — primary `billetterie.psg.fr/en/home-vip` was Cloudflare-blocked; fallback `www.psg.fr/en/hospitality` crawled cleanly.
- **Steps emitted:** 12 (depth-1 and depth-2 descents)
- **Cookie dismissal:** FAILED on the `www.psg.fr` domain (`cookie_dismiss_failed=true`). PSG_STRATEGY priorities target the billetterie banner copy; the www-subdomain uses different wording. Non-fatal — descent continued because no overlay blocked clicks.
- **Login gates detected:** none
- **Broker vendor:** none
- **External redirects:** 0
- **Dead ends:** 2 — both `https://www.psg.fr/en/the-club` (non-hospitality branch that ranked surprisingly; crawler correctly marked as dead-end for this area).
- **CAPTCHA:** N
- **Registration needed:** N — no credential wall surfaced in the www-path crawl. Back-half capture of the billetterie subdomain will likely need Chrome-MCP fallback for the same 403 reason.

### Chelsea (`chelsea`)

- **Entry URL (final, after fallback):** `https://hospitality.chelseafc.com/match-by-match-hospitality-packages`
- **Primary URL attempted:** `https://www.chelseafc.com/en/hospitality` → 302-redirected to `hospitality.chelseafc.com/` → 3-step stub with the subdomain URL in external_redirects (cross-origin guard fired per D-15).
- **HTTP status (fallback):** 200
- **Fallback used:** YES — starting the crawl directly FROM the `hospitality.chelseafc.com` subdomain makes it the `entry_origin`, so descent proceeds as same-origin.
- **Steps emitted:** 6 (depth-1 descent into package pages)
- **Cookie dismissal:** FAILED (`cookie_dismiss_failed=true`) — subdomain uses a custom banner whose wording isn't in CHE_STRATEGY.priority yet.
- **Login gates detected:** none
- **Broker vendor:** none recognized (`hospitality.chelseafc.com` is not in `BROKER_DOMAINS`). Likely Keith Prowse whitelabel per 02-RESEARCH.md §5; confirmation needs a back-half inspection pass.
- **External redirects:** 0 (none on the subdomain-started crawl).
- **Dead ends:** 4 — the detector picked `https://hospitality.chelseafc.com/match-by-match-hospitality-packages/match-by-match-hospitality-packages` (recursive path appended by a self-referencing anchor on the page) four times; likely same link ranked and clicked across descent rounds. Known crawler limitation — filed below.
- **CAPTCHA:** N
- **Registration needed:** likely Y for deeper purchase flow (Keith Prowse checkout). The current 6-step crawl did not surface a login gate because depth was shallow; back-half capture at greater depth will almost certainly hit one.

## Fallback URL Usage

| Club      | Primary URL attempted                                    | Fallback URL used                                                                                         | Primary HTTP status |
|-----------|----------------------------------------------------------|-----------------------------------------------------------------------------------------------------------|---------------------|
| mancity   | `https://www.mancity.com/hospitality`                    | none (entry-only stub accepted; no alternate URL documented)                                              | 403 (Cloudflare)    |
| tottenham | `https://www.tottenhamhotspur.com/tickets/premium-experiences/` | — (primary succeeded)                                                                              | 200                 |
| realmadrid| `https://www.realmadrid.com/en-US/vip-area/home`          | — (CAPTCHA halt; fallback wouldn't help)                                                                  | 200                 |
| psg       | `https://billetterie.psg.fr/en/home-vip`                 | `https://www.psg.fr/en/hospitality`                                                                       | 403 (Cloudflare)    |
| chelsea   | `https://www.chelseafc.com/en/hospitality`               | `https://hospitality.chelseafc.com/match-by-match-hospitality-packages`                                   | 302 → subdomain     |

## Manual Corrections

No manual JSON edits were required. All 5 flow-maps were produced entirely by the crawler (no post-facto metadata surgery). The Chelsea subdomain case, which plan 02-06 anticipated as a manual-correction candidate, resolved cleanly by re-running the crawl from the subdomain itself — `external_redirects` is empty on the final artifact.

## Registration Requirements (User Action)

The front-half crawl surfaced NO explicit login walls in any of the 5 flow-maps (`login_gated_steps` is empty for all). Nevertheless, because crawl depth was shallow (3-12 steps) and the "Buy now" / "Select match" CTAs were not traversed beyond the first level, the back-half WILL likely surface credential gates when descending into the purchase path for TOT, PSG, CHE (and MCFC/RMA once Chrome-MCP unblocks them).

**Conservative recommendation for user off-session work:** register dummy accounts for all 5 pilot clubs BEFORE back-half runs, so we are not blocked mid-capture. If a club ends up not requiring an account, the credential is simply unused.

### Manchester City — register at `https://www.mancity.com/account`

- **Env vars to set:**
  ```bash
  MANCITY_HOSPITALITY_USER=your+mancityhosp@example.com
  MANCITY_HOSPITALITY_PASS={strong-random-password}
  ```
  Stored in `.env.local` (gitignored — D-14).
- **Credentials doc:** record the same values in `.planning/phases/02-hospitality-pilot/credentials.local.md` (gitignored — D-13).
- **Registration notes:** Cloudflare Turnstile on the hospitality landing will need to be cleared manually (Chrome MCP) before the logged-in session can be used.

### Tottenham Hotspur — register at `https://www.tottenhamhotspur.com/account/signup`

- **Env vars to set:**
  ```bash
  TOTTENHAM_HOSPITALITY_USER=your+tothosp@example.com
  TOTTENHAM_HOSPITALITY_PASS={strong-random-password}
  ```
- **Credentials doc:** `.planning/phases/02-hospitality-pilot/credentials.local.md`.
- **Registration notes:** cleanest flow; expect standard email verification.

### Real Madrid — register at `https://www.realmadrid.com/en-US/register`

- **Env vars to set:**
  ```bash
  REALMADRID_HOSPITALITY_USER=your+rmahosp@example.com
  REALMADRID_HOSPITALITY_PASS={strong-random-password}
  ```
- **Credentials doc:** `.planning/phases/02-hospitality-pilot/credentials.local.md`.
- **Registration notes:** CAPTCHA on the VIP-area landing will block automated auth; Chrome MCP session needed to reach logged-in state. User registration only unblocks the back-half if paired with the manual-browser fallback.

### PSG — register at `https://www.psg.fr/en/register` (www) AND/OR `https://billetterie.psg.fr/en/register` (billetterie)

- **Env vars to set:**
  ```bash
  PSG_HOSPITALITY_USER=your+psghosp@example.com
  PSG_HOSPITALITY_PASS={strong-random-password}
  ```
- **Credentials doc:** `.planning/phases/02-hospitality-pilot/credentials.local.md`.
- **Registration notes:** billetterie subdomain is Cloudflare-gated — register on www first, then log in once on billetterie via Chrome MCP to mint the session cookie. The www-domain crawl is already credentialed-enough for the shallow flow-map.

### Chelsea — register at `https://www.chelseafc.com/en/account/register` AND possibly Keith Prowse via `https://hospitality.chelseafc.com/`

- **Env vars to set:**
  ```bash
  CHELSEA_HOSPITALITY_USER=your+chehosp@example.com
  CHELSEA_HOSPITALITY_PASS={strong-random-password}
  ```
- **Credentials doc:** `.planning/phases/02-hospitality-pilot/credentials.local.md`.
- **Registration notes:** the hospitality subdomain is likely Keith Prowse whitelabel — expect a separate sign-up on that host if the chelseafc.com SSO doesn't bridge. Confirm at back-half time.

## Third-Party Broker Encounters

| Club    | broker_vendor      | URL observed                                                 |
|---------|--------------------|--------------------------------------------------------------|
| chelsea | (suspected, not detected by BROKER_DOMAINS) | `hospitality.chelseafc.com` subdomain — likely Keith Prowse whitelabel per 02-RESEARCH.md §5 |

No broker redirects were detected by the crawler's `BROKER_DOMAINS` allowlist (Seat Unique, Keith Prowse, DTI, etc.). The Chelsea case above is flagged for back-half human inspection — if confirmed Keith Prowse, the `BROKER_DOMAINS` dict should be extended for v2 of the crawler.

## Known Crawler Issues Filed for Back-Half

1. **MCFC / PSG-billetterie Cloudflare Turnstile:** the crawler has no "Just a moment..." detector (distinct from CAPTCHA selectors) — the landing gets flagged as a dead-end via HTTP 403 but the root cause (bot-challenge, not real 404) is opaque to downstream readers. Consider adding a `bot_challenge_encountered` flag to `FlowMapMetadata` in v2, and treating it with the same branch-halt semantics as `captcha_encountered`.
2. **Chelsea subdomain classification:** `hospitality.chelseafc.com` is Chelsea-operated same-org but the crawler's cross-origin guard classifies it as `external_redirects` on the www-start path. For v2 consider adding a per-club `trusted_subdomains` list in areas.json so legitimate subdomains aren't treated as external brokers.
3. **Chelsea self-referencing dead_end spam:** the CHE subdomain has anchor hrefs that append the current path onto itself (`/match-by-match-hospitality-packages/match-by-match-hospitality-packages`), and the crawler re-detects the same dead-end URL across descent rounds instead of deduplicating. Cosmetic but inflates `dead_ends` count. Consider `set()` wrapper on `meta.dead_ends` write path.
4. **PSG_STRATEGY / CHE_STRATEGY cookie-priority miss:** the strategies were tuned for the billetterie / chelseafc.com primary domains respectively, but the fallback flows landed on `www.psg.fr` / `hospitality.chelseafc.com` whose consent banners use different wording. Add domain-specific priority lists OR broaden the strategies during back-half.
5. **`discover_flow` landing-goto wait condition (fixed):** the crawler originally passed `wait_until="networkidle"` to `page.goto` with no timeout override, causing a hard 30 s `TimeoutError` on MCFC (and likely any site with long-poll analytics). Fixed in this plan via commit `fix(02-06): bounded-timeout landing goto in discover_flow` — switched to `domcontentloaded` + best-effort 10 s networkidle, mirroring the `_descend` pattern. Filed as Rule 1 bug per plan deviation rules; no test added (out of scope; deferred to back-half smoke test once capture path is live).

## Front-Half Halt Confirmation

The following is explicitly NOT done in this plan (deferred to back-half):

- [ ] Full-page capture (`scanner capture`)
- [ ] Two-judge vision mapping (`scanner vision`)
- [ ] Evidence slicing (`scanner slice`)
- [ ] Coverage report generation (`scanner report`)
- [ ] Scoring (`scanner score`)
- [ ] `analysis/hospitality/results/{club}.json` creation
- [ ] Hospitality Packages UI tab unlock

Back-half will plan these in a subsequent session once user registrations complete AND Chrome-MCP fallback is in place for MCFC / RMA / PSG-billetterie (the three Cloudflare / CAPTCHA clubs).
