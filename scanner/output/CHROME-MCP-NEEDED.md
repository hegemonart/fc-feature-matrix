# Chrome MCP Escalation List — Plan 02-16 Recapture Wave

Generated: 2026-04-28T13:15Z
Source run-logs (latest per club):

- `scanner/output/capture-run-log-hospitality-chelsea-20260428T125622Z.json`
- `scanner/output/capture-run-log-hospitality-mancity-20260428T125820Z.json`
- `scanner/output/capture-run-log-hospitality-realmadrid-20260428T130017Z.json`
- `scanner/output/capture-run-log-hospitality-psg-20260428T130253Z.json`
- `scanner/output/capture-run-log-hospitality-tottenham-20260428T124641Z.json`

## Headline (corrected after pixel + DOM verification)

The run-logs claim 0 chrome-mcp deferrals. **Pixel + DOM-title verification reveals 8 of those "captured" steps are actually Cloudflare Turnstile interstitials, not real content.** The stealth layer got past HTTP 403 (so the run-log labels them captured) but the Turnstile widget still renders client-side and never resolves under headless automation.

| Failure mode | Steps | Resolution |
|---|---:|---|
| Real Cloudflare Turnstile (still bot-blocked, just at a different layer) | 8 | Chrome MCP — interactive solve required |
| Selector-tuning failures (post-stealth, page loads but flow-map clicks miss) | 8 | Plan 02-17 flow-map iteration |
| Login selector misses | 2 | Plan 02-17 — `scanner/capture/login.py` per-club tuning |

Total escalation: **18 steps**, of which **8 are genuine Cloudflare blocks** (need Chrome MCP) and **10 are flow-map / login selector issues** (plan-02-17 territory).

## Section A — Genuine Cloudflare Turnstile blocks (Chrome MCP required)

These pages return HTTP 200 with stealth fingerprinting, but the response body is a Turnstile challenge page (title=`Just a moment...`, content=`Vérification de sécurité requise` / `Verify you are human`). DOM intel captures this honestly so Plan 02-17 hybrid routing will route correctly. To get real content, a human-presenced Chrome MCP session is required.

| Club | Step | Run-log status | Pixel-verified content |
|------|------|----------------|------------------------|
| mancity | landing | captured (stealth-override-unblocked) | Cloudflare interstitial — `REDIRECTING…` widget |
| mancity | landing-shot | captured (stealth-override-unblocked) | Cloudflare interstitial |
| mancity | tier-tunnel-club-premier-shot | captured (stealth-override-unblocked) | Cloudflare interstitial (same image as landing) |
| mancity | tier-tunnel-club-shot | captured (stealth-override-unblocked) | Cloudflare interstitial (same image as landing) |
| mancity | tier-backstage-shot | captured (stealth-override-unblocked) | Cloudflare interstitial (same image as landing) |
| mancity | enquiry-form-prefill-shot | captured (stealth-override-unblocked) | Cloudflare interstitial |
| psg | billetterie-home-vip-shot | captured (stealth-override-unblocked) | Turnstile FR — `VÉRIFICATION DE SÉCURITÉ REQUISE` |
| psg | billetterie-match-selector-shot | captured (stealth-override-unblocked) | Turnstile FR (same image) |
| psg | enquiry-form-prefill-shot (billetterie path) | captured (stealth-override-unblocked) | Turnstile FR (same image) |

The 6 MCFC and 3 PSG-billetterie PNGs were intentionally NOT staged for commit — they're not real evidence.

## Section B — Selector-tuning failures (Plan 02-17 flow-map iteration)

These pages load successfully (real hospitality content visible). The flow-map's click / fill selectors miss because the page DOM has shifted. Resolution is to update the selector list, not to escalate to Chrome MCP.

| Club | Step | Failure |
|------|------|---------|
| mancity | landing-wait | `stealth-override-failed: Timeout 5000ms` (waiter selector miss; page is Turnstile, this is a side-effect of A above) |
| mancity | match-selector | Page.click timeout waiting for `a[href*='enquire'], a.fixture-card, button.…` |
| mancity | enquiry-form-prefill | Page.fill timeout waiting for `input[name='name']` |
| realmadrid | matchday-tier-card-click | Page.click timeout waiting for `a[href*='matchday-hospitali…']` |
| psg | first-tier-click | Page.click timeout waiting for `a[href*='hospitality'] .card, a.tier-card, …` |
| psg | billetterie-match-selector | Page.click timeout (would be irrelevant: page is Turnstile per A above) |
| psg | enquiry-form-prefill (billetterie) | Page.fill timeout (Turnstile blocks form rendering) |
| tottenham | enquiry-form-prefill | Page.fill timeout waiting for `input[name='firstName'], input[name='first_name']…` |

3 of these (mancity landing-wait, psg billetterie-match-selector, psg enquiry-form-prefill billetterie) are downstream of the Turnstile blocks in section A and resolve once those clear.

## Section C — Login selector misses

| Club | Step | Failure |
|------|------|---------|
| realmadrid | enquiry-form-prefill | `login_to_club returned False (selector miss or marker timeout)` |
| psg | billetterie-login | `login_to_club returned False (selector miss or marker timeout)` |

Credentials are present in `.env.local`. The failure is the login flow not finding the email/password input fields with the current selector list.

## Stealth efficacy summary (corrected)

| Club | v1 chrome-mcp steps | v2 chrome-mcp (run-log) | v2 chrome-mcp (pixel-verified) |
|------|---:|---:|---:|
| chelsea | 0 | 0 | 0 |
| mancity | 13 | 0 | 6 (Turnstile under HTTP 200) |
| realmadrid | 10 | 0 | 0 |
| psg | 7 | 0 | 3 (billetterie Turnstile under HTTP 200) |
| tottenham | 0 | 0 | 0 |
| **Total** | **30** | **0** | **9** |

**Stealth genuinely eliminated 21 of 30 (70%) Cloudflare blocks** — primarily on Real Madrid and PSG main domain. The remaining 9 (MCFC entirely + PSG-billetterie subset) need Chrome MCP because the Turnstile interactive widget cannot be solved by stealth fingerprinting alone.

This is the realistic Phase 2.5 cost picture: budget ~30% of clubs to need Chrome MCP escalation for hospitality even after the Plan 02-15 v2 architecture, and ~70% to capture cleanly under stealth.
