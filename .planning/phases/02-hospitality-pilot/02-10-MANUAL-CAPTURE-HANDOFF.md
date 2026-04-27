# Plan 02-10 — Manual Chrome MCP Capture Handoff

**Generated:** 2026-04-27
**Phase:** 02 — Hospitality Pilot
**Plan:** 02-10 (Wave 7 — capture orchestrator + 5-club live capture wave)
**Run mode:** `--headless --auto-skip-manual` (unattended)

---

## Why this doc exists

`capture_flow` cannot drive Chrome MCP browser sessions (which require live human
interaction in the user's actual Chrome). When a `FlowStep` is marked
`manual_chrome_mcp: true`, the orchestrator records `status="chrome-mcp"`
in the run-log and defers the step to this handoff doc.

Steps requiring manual Chrome MCP execution per club:

| Club | Total flow steps | Auto-captured (Playwright) | Deferred to Chrome MCP | Skipped (paid-only) | Errors |
| --- | --- | --- | --- | --- | --- |
| tottenham | 12 | 11 | 0 | 0 | 1 |
| mancity | 13 | 0 | 13 | 0 | 0 |
| realmadrid | 13 | 3 | 10 | 0 | 0 |
| psg | 14 | 6 | 7 | 0 | 1 |
| chelsea | 15 | 12 | 0 | 2 | 1 |

**Subscription cost so far:** $0 (no vision calls in this plan).

**Estimated user time to drive Chrome MCP for all deferrals:** ~30–45 min total,
biased toward MCFC (~15 min for 13 steps) + RMA (~10 min for 10 steps)
+ PSG (~7 min for 7 steps).

---

## How to drive a deferred step

For each deferred step below:

1. Open the URL in a Chrome window where Chrome MCP is connected.
2. Wait for Cloudflare Turnstile / CAPTCHA / page load to settle.
3. Dismiss any cookie banner.
4. If the step is a `screenshot` action (or follows a navigate/click that
   should be screenshotted), take a full-page screenshot in Chrome and save it as:
   `scanner/output/evidence/hospitality/fullpage/{club}_{step_name}.png`
5. If the step is a `click` action, perform the click in Chrome — the next
   `screenshot` step usually follows.
6. If the step is `fill`, populate dummy form fields per D-10 (`Test Test` /
   `test@example.com` / `+44 0000 000000`), DO NOT submit, then capture the
   pre-submit screenshot.
7. Update the run-log JSON to flip the step's `status` from `"chrome-mcp"`
   to `"captured"` once the PNG is on disk (manual edit; Plan 02-12's
   contact sheet will read the updated log).

---

## Per-club deferred steps

### Tottenham — 0 deferred

No manual Chrome MCP work needed. All 12 flow steps were attempted via Playwright
(11 captured + 1 form-fill error). Playwright fully exercised this club.

### MCFC — 13 deferred (Cloudflare Turnstile blocks all flow steps)

Reason for deferral: every step on `mancity.com/hospitality` hits Cloudflare's
"Just a moment..." interstitial, which blocks headless Chromium. Chrome MCP
(running in user's actual Chrome) passes Turnstile cleanly.

| # | step_name | URL | action | selector |
| --- | --- | --- | --- | --- |
| 1 | landing | `https://www.mancity.com/hospitality` | navigate | — |
| 2 | landing-wait | — | wait | — |
| 3 | landing-shot | — | screenshot | — |
| 4 | tier-tunnel-club-premier | `https://www.mancity.com/hospitality/the-tunnel-club-premier` | navigate | — |
| 5 | tier-tunnel-club-premier-shot | — | screenshot | — |
| 6 | tier-tunnel-club | `https://www.mancity.com/hospitality/the-tunnel-club` | navigate | — |
| 7 | tier-tunnel-club-shot | — | screenshot | — |
| 8 | tier-backstage | `https://www.mancity.com/hospitality/backstage` | navigate | — |
| 9 | tier-backstage-shot | — | screenshot | — |
| 10 | tier-your-matchday-experience | `https://www.mancity.com/hospitality/your-matchday-experience` | navigate | — |
| 11 | match-selector | — | click | `a[href*='enquire'], a.fixture-card, button.select-match` |
| 12 | enquiry-form-prefill | — | fill | (form_fields per flow-map) |
| 13 | enquiry-form-prefill-shot | — | screenshot | — |

Expected PNG outputs (5):
- `mancity_landing-shot.png`
- `mancity_tier-tunnel-club-premier-shot.png`
- `mancity_tier-tunnel-club-shot.png`
- `mancity_tier-backstage-shot.png`
- `mancity_enquiry-form-prefill-shot.png`

### Real Madrid — 10 deferred (CAPTCHA on areavip / palcos-vip subtree)

Reason for deferral: navigating beyond the public hospitality landing onto the
matchday hospitality / palcos-vip flow triggers a reCAPTCHA. 3 public-facing
steps (landing, landing-wait, landing-shot) captured cleanly via Playwright;
the rest deferred.

| # | step_name | URL | action | selector |
| --- | --- | --- | --- | --- |
| 1 | matchday-hospitality | (per flow-map) | navigate | — |
| 2 | matchday-hospitality-wait | — | wait | — |
| 3 | matchday-hospitality-shot | — | screenshot | — |
| 4 | matchday-tier-card-click | — | click | (per flow-map) |
| 5 | matchday-tier-card-shot | — | screenshot | — |
| 6 | palcos-vip | (per flow-map) | navigate | — |
| 7 | palcos-vip-wait | — | wait | — |
| 8 | palcos-vip-shot | — | screenshot | — |
| 9 | enquiry-form-prefill | — | fill | (form_fields per flow-map) |
| 10 | enquiry-form-prefill-shot | — | screenshot | — |

Expected PNG outputs (4):
- `realmadrid_matchday-hospitality-shot.png`
- `realmadrid_matchday-tier-card-shot.png`
- `realmadrid_palcos-vip-shot.png`
- `realmadrid_enquiry-form-prefill-shot.png`

### PSG — 7 deferred (`billetterie.psg.fr` Cloudflare + login)

Reason for deferral: the `billetterie.psg.fr` subdomain is Cloudflare-protected.
The `www.psg.fr` portion (3 steps) was captured cleanly. Login step requires
user-supplied PSG hospitality credentials when arriving via Chrome MCP.

| # | step_name | URL | action | selector |
| --- | --- | --- | --- | --- |
| 1 | billetterie-home-vip | (per flow-map) | navigate | — |
| 2 | billetterie-home-vip-shot | — | screenshot | — |
| 3 | billetterie-login | (per flow-map) | navigate | — (login REQUIRES credentials, see `.env.local`) |
| 4 | billetterie-match-selector | — | click | (per flow-map) |
| 5 | billetterie-match-selector-shot | — | screenshot | — |
| 6 | enquiry-form-prefill | — | fill | (form_fields per flow-map) |
| 7 | enquiry-form-prefill-shot | — | screenshot | — |

Expected PNG outputs (4):
- `psg_billetterie-home-vip-shot.png`
- `psg_billetterie-match-selector-shot.png`
- `psg_enquiry-form-prefill-shot.png`
- (login step itself is not screenshotted; it's a navigate+credentials gate)

### Chelsea — 0 deferred

No manual Chrome MCP work needed. The Cloudflare detector did not fire on
`hospitality.chelseafc.com` (the trusted-subdomain allowlist from Plan 02-08
made this work). All 13 flow steps attempted via Playwright:
- 12 captured
- 2 skipped intentionally (`requires-paid-account`: match-selector +
  enquiry-form-prefill — D-15 / Option B partial decision 2026-04-27)
- 1 error (networkidle timeout on landing-wait — non-fatal)

---

## Resume protocol when ready

After driving the deferred steps in Chrome MCP and saving the PNGs to
`scanner/output/evidence/hospitality/fullpage/`:

1. Update each affected run-log JSON's `steps[i].status` from `"chrome-mcp"`
   to `"captured"` and set `steps[i].output_path` to the saved PNG path.
2. Re-run the totals computation:
   ```python
   import json
   for f in glob.glob('scanner/output/capture-run-log-hospitality-*.json'):
       d = json.load(open(f))
       d['totals'] = {
           'captured': sum(1 for s in d['steps'] if s['status'] == 'captured'),
           'skipped': sum(1 for s in d['steps'] if s['status'] == 'skipped'),
           'chrome_mcp': sum(1 for s in d['steps'] if s['status'] == 'chrome-mcp'),
           'missing': sum(1 for s in d['steps'] if s['status'] == 'missing-credentials'),
           'error': sum(1 for s in d['steps'] if s['status'] == 'error'),
       }
       json.dump(d, open(f, 'w'), indent=2)
   ```
3. Commit the updated PNGs + run-logs as `chore(02-10): manual Chrome MCP
   capture wave for {club}` per club.
4. Plan 02-12 (contact sheet) will then render the full pilot.

---

## Coverage report (post-resolution target)

If the user drives all 30 deferred Chrome-MCP steps successfully:

| Club | Total | Captured | Deferred | Skipped | Coverage % |
| --- | --- | --- | --- | --- | --- |
| tottenham | 12 | 11 | 0 | 0 | 92% |
| mancity | 13 | 13 | 0 | 0 | 100% |
| realmadrid | 13 | 13 | 0 | 0 | 100% |
| psg | 14 | 13 | 0 | 0 | 93% |
| chelsea | 15 | 12 | 0 | 2 | 80% (intentional) |

If left unresolved, current pilot coverage:

| Club | Total | Captured | Deferred | Skipped | Coverage % |
| --- | --- | --- | --- | --- | --- |
| tottenham | 12 | 11 | 0 | 0 | 92% |
| mancity | 13 | 0 | 13 | 0 | 0% |
| realmadrid | 13 | 3 | 10 | 0 | 23% |
| psg | 14 | 6 | 7 | 0 | 43% |
| chelsea | 15 | 12 | 0 | 2 | 80% |

The 30 manual_chrome_mcp deferrals represent the back-half's known Cloudflare
gap (Plan 02-08 quantified this; Plan 02-09 marked the steps; Plan 02-10
demonstrates the orchestrator handles them gracefully).
