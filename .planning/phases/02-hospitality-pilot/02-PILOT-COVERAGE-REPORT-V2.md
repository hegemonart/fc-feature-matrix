# Phase 2 — Hospitality Pilot Coverage Report (V2 — Scanner v2 hybrid pipeline)

**Generated:** 2026-04-28
**Pilot clubs:** Manchester City, Tottenham Hotspur, Real Madrid, Paris Saint-Germain, Chelsea
**Rubric:** 55 features (38 dom / 14 hybrid / 3 visual)
**Generator:** Plan 02-17 — re-vision wave with hybrid DOM+vision routing

> **Methodology change banner.** This report is the SECOND pass over the same
> 5-club hospitality pilot. The v1 report (`02-PILOT-COVERAGE-REPORT.md`) was
> produced by a vision-only wave (Plan 02-11). The v2 report below was
> produced by Plan 02-15's hybrid DOM+vision pipeline operating on the
> Plan 02-16 stealth-recapture set. Both reports are kept side-by-side for
> direct comparison; v1 is the baseline, v2 is the post-architecture-upgrade
> snapshot.

---

## TL;DR

- **Pilot status: PARTIAL — improved.** 4 of 5 clubs (Tottenham, Chelsea, Real Madrid, PSG) produced richer coverage than v1. Manchester City remains genuinely bot-blocked (Cloudflare Turnstile passes the HTTP-200 stealth check but does not resolve the interactive widget); 5 of 6 MCFC PNGs are interstitials, vision correctly returns absent.
- **Aggregate cells (5 × 55 = 275):** **37 present (13.5%, +6) / 13 disputed (4.7%, -6) / 238 absent (86.5%)**. 20 of 55 features show signal in ≥1 club (vs 14 in v1). Still 0 universal-present features. 35 features are absent in all 5 clubs (was 41 in v1).
- **Hybrid pipeline efficiency: 35.9% of feature-verdict cells answered by DOM detection (553 of 1,540 cells) without invoking vision.** That's the cost-saving mechanism — DOM-resolved features get a $0 deterministic verdict.
- **Disagreement reduction: 19 → 13 disputed cells (-32%); 112 → 74 disagreement records (-34%); 39 → 21 presence disagreements (-46%).** DOM is objective so dom-tagged features can no longer have judge-vs-judge presence disputes.
- **Subscription cost actually consumed: $0** (subscription backend, Claude Max plan). Wall-clock budget: ~50 min of wave time + ~10 min of derivation/scoring/report. Under the $5 hard cap.
- **Recommended decision: Option (B) — APPROVE WITH CONDITIONS.** Same as v1, but the conditions list is shorter: stealth + DOM closed RMA's gap entirely. The remaining gap is 8 genuine Turnstile blocks (5 MCFC + 3 PSG-billetterie) + 10 selector-tuning items, all documented in `scanner/output/CHROME-MCP-NEEDED.md`. Closing those is a Phase 2.5 prerequisite, not a Phase 2 blocker.

---

## Per-Club V1 → V2 Comparison

Counts derived from `analysis/hospitality/results/{club}.json`.

| Club | v1 P | v2 P | ΔP | v1 D | v2 D | ΔD | v1 Agr% | v2 Agr% | v1 Score | v2 Score | ΔScore | Rank V2 |
|------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tottenham Hotspur | 12 | 12 | 0 | 7 | 6 | -1 | 96.73% | 97.45% | -57 | **-54** | +3 | 1 |
| Real Madrid | 6 | 9 | **+3** | 3 | 1 | **-2** | 94.55% | 99.64% | -92 | **-74** | **+18** | **2** ↑ |
| Chelsea | 8 | 7 | -1 | 9 | 6 | -3 | 92.12% | 96.06% | -79 | **-86** | -7 | 3 ↓ |
| Manchester City | 5 | 5 | 0 | 0 | 0 | 0 | 100% | 100% | -99 | **-99** | 0 | 4 |
| Paris Saint-Germain | 0 | 4 | **+4** | 0 | 0 | 0 | 100% | 100% | -125 | **-106** | **+19** | 5 |
| **TOTALS** | **31** | **37** | **+6** | **19** | **13** | **-6** | **96.48%** | **98.6%** | **-452** | **-419** | **+33** | — |

**Read this:**
- **Real Madrid jumped rank 3 → rank 2.** Stealth got past Cloudflare, DOM detection picked up the Spanish-language hospitality content programmatically, and 3 features that v1 mis-rated absent now correctly read present.
- **PSG moved from 0 features present to 4.** The 3 Cloudflare-Turnstile billetterie PNGs are still bot-blocked (and the hybrid pipeline correctly returns absent on those), but the 3 main-domain PSG pages contributed real content this time.
- **Chelsea slipped 1 present cell.** This is a known v2 effect: Chelsea's flow-map duplication (4 of 6 PNGs are the same package-list page; Plan 02-16 finding) means features that v1 saw present once are now seen consistently absent across the 4 duplicate captures. Net coverage is more honest, not worse.
- **Manchester City unchanged.** All 6 MCFC v2 PNGs are Cloudflare interstitials (per Plan 02-16 pixel-verification); the 5 features still showing present come from a single pre-orchestrator landing capture that survived. The 5 Turnstile-blocked steps will need Chrome MCP (per `CHROME-MCP-NEEDED.md`).

---

## Hybrid Pipeline Efficiency

| Club | DOM-resolved cells | Vision-resolved cells | Total | DOM % |
|------|---:|---:|---:|---:|
| Tottenham | 112 | 163 | 275 | 40.7% |
| Chelsea | 126 | 204 | 330 | 38.2% |
| Real Madrid | 100 | 175 | 275 | 36.4% |
| PSG | 120 | 210 | 330 | 36.4% |
| Manchester City | 95 | 235 | 330 | 28.8% |
| **TOTAL** | **553** | **987** | **1,540** | **35.9%** |

**Read this:**
- 553 of 1,540 verdict cells (35.9%) were resolved by DOM detection rules at $0 cost.
- Vision API calls per PNG remain 2 (Opus + Sonnet) regardless of which features filter to vision — but the per-feature cost savings show up as fewer features going through Opus 4.7's reasoning + Sonnet 4.5's check.
- MCFC's 28.8% DOM rate is the lowest because all its PNGs are Turnstile interstitials — the DOM intel honestly captures `title="Just a moment..."` and the rules see no hospitality content to match.
- Cost savings vs v1 retail estimate: Plan 02-15's projection was ~60% reduction (1.50–2.50 vs 5.50–6.50). Actual subscription cost: **$0** in both v1 and v2 because Claude Max plan covers vision calls. The retail-equivalent $-saving applies only when a future migration to api-key mode happens.

---

## Per-Feature Coverage Rate (all 55) — V2

`Present in N/5` = how many of the 5 pilot clubs have `features[<key>] === true` in v2 results.
`Disputed in N/5` = how many of the 5 pilot clubs flagged this feature in `disputed_features[]` in v2.

Only features whose v1→v2 status changed are listed below; the universal-absent and unchanged features are summarised in the count footer.

| Feature | v1 Present | v2 Present | v1 Disputed | v2 Disputed |
|---------|---:|---:|---:|---:|
| package_tier_list | 3/5 | **5/5** | 0/5 | 0/5 |
| per_tier_landing_page | 4/5 | 4/5 | 0/5 | **2/5** |
| tier_capacity_indicator | 0/5 | **1/5** | 1/5 | 1/5 |
| price_per_person_visible | 3/5 | **0/5** | 1/5 | 0/5 |
| min_booking_unit | 0/5 | **2/5** | 1/5 | 1/5 |
| price_range_by_match | 0/5 | 0/5 | 1/5 | **0/5** |
| menu_preview | 1/5 | **2/5** | 0/5 | 0/5 |
| chef_attribution | 0/5 | **1/5** | 1/5 | 0/5 |
| meal_timing_visible | 1/5 | **2/5** | 2/5 | **1/5** |
| post_match_service | 0/5 | **3/5** | 2/5 | 2/5 |
| competition_filter | 0/5 | **1/5** | 0/5 | 0/5 |
| buy_now_without_enquiry | 4/5 | **2/5** | 1/5 | **0/5** |
| phone_booking_option | 2/5 | **0/5** | 0/5 | 0/5 |
| stadium_tour_inclusion | 1/5 | **2/5** | 1/5 | **0/5** |
| concierge_service | 1/5 | **0/5** | 1/5 | 0/5 |
| pitchside_or_tunnel_access | 2/5 | 2/5 | 1/5 | **0/5** |
| booking_change_policy_visible | 0/5 | 0/5 | 1/5 | **0/5** |
| fixture_change_notification | 0/5 | 0/5 | 1/5 | **0/5** |
| group_host_contact | 0/5 | **1/5** | 0/5 | **1/5** |
| confirmation_page_clarity | 0/5 | 0/5 | 0/5 | **1/5** |

**Notable swings:**
- **package_tier_list: 3/5 → 5/5.** DOM rule on `<a>` tag count + tier-name keyword matches catches PSG and Real Madrid this time. v1 vision-only mis-rated PSG absent.
- **post_match_service: 0/5 → 3/5.** Both Chelsea and Real Madrid pages now resolve present. Plus tottenham. Hybrid routing: DOM rule scans body text for "post-match" / "after the final whistle" / "stays open"; clearer signal than vision-only.
- **price_per_person_visible: 3/5 → 0/5.** This one is concerning — v1 said TOT/RMA/CHE present, v2 says all absent. Investigation needed: the DOM rule looks for inc-VAT price patterns ("£XXX" or "from £XXX") in the visible text; v1 vision was matching softer "from £" copy. Possible v2 false-negative — flag for spot-check.
- **buy_now_without_enquiry: 4/5 → 2/5.** Similar concern: v1 had it 4/5, v2 has 2/5. DOM rule looks for explicit "Buy Now" / "Book Now" / `<button class="buy">` patterns vs vision's broader interpretation. Spot-check needed.
- **phone_booking_option: 2/5 → 0/5.** DOM rule looks for `<a href="tel:">` links; possibly the phone number is rendered as text rather than a tel: link on TOT and RMA. Spot-check needed.

---

## The 13 Disputed Cells in V2 (Spot-Check Workload)

Down from 19 in v1. These are the cells where Opus and Sonnet disagreed on at least one step's presence call. Resolution per Plan 02-12 policy: per-step Opus-when-agree, False+disputed-when-disagree, OR-flatten across steps with sticky disputed flag.

| # | Club | Feature | Tier | Resolved as | Spot-check |
|---|------|---------|------|---|---|
| 1 | Tottenham | bar_type_indicator (HP19) | A | **YES, disputed** | Verify on tottenhamhotspur.com/hospitality/premium-seats; check bar wording. |
| 2 | Tottenham | confirmation_page_clarity (HP53) | A | NO, disputed | Confirm post-enquiry confirmation copy. |
| 3 | Tottenham | group_host_contact (HP52) | C | NO, disputed | Look for group/host contact info. |
| 4 | Tottenham | live_chat_availability (HP35) | C | **YES, disputed** | Confirm live-chat widget present (we hide it for capture per D-11). |
| 5 | Tottenham | per_tier_landing_page (HP02) | A | **YES, disputed** | Verify each tier (Centenary / Platinum / etc.) opens its own dedicated landing page. |
| 6 | Tottenham | post_match_service (HP23) | C | **YES, disputed** | Look for "stays open after final whistle" copy. |
| 7 | Chelsea | bar_type_indicator (HP19) | A | **YES, disputed** | Verify complimentary/cash/premium-only bar is named. |
| 8 | Chelsea | meal_timing_visible (HP22) | C | **YES, disputed** | Look for arrival / pre-match / post-match timing copy. |
| 9 | Chelsea | min_booking_unit (HP10) | A | **YES, disputed** | Look for per-seat / per-table-of-10 / per-box copy. |
| 10 | Chelsea | post_match_service (HP23) | C | **YES, disputed** | Same as TOT #6. |
| 11 | Chelsea | saved_booking_in_account (HP54) | C | NO, disputed | Login-gated; not reachable in pilot. |
| 12 | Chelsea | tier_capacity_indicator (HP05) | C | NO, disputed | Look for min/max guests or per-box headcount. |
| 13 | Real Madrid | per_tier_landing_page (HP02) | A | **YES, disputed** | Verify each Palco / VIP page is its own dedicated landing. |

**Removed from v1 disputed list (now agreed):**
- TOT booking_change_policy_visible, chef_attribution, meal_timing_visible, price_per_person_visible
- RMA concierge_service, fixture_change_notification, price_range_by_match
- CHE buy_now_without_enquiry, pitchside_or_tunnel_access, stadium_tour_inclusion, post_match_service (still disputed but moved from NO-disputed to YES-disputed)

**Added to v2 disputed list:**
- TOT confirmation_page_clarity, group_host_contact, per_tier_landing_page, post_match_service
- CHE meal_timing_visible (newly disputed YES), min_booking_unit (changed from NO-disputed to YES-disputed)
- RMA per_tier_landing_page

**User action:** spot-check 3–5 of the **YES, disputed** cells (especially Tier A — HP19 / HP02 / HP10) by visiting the source URL. If the YES calls look right, approve the pilot.

---

## Manual Handoff Status (V2)

Sourced from `scanner/output/CHROME-MCP-NEEDED.md`. Down from 30 deferred steps in v1 to **8 genuine Cloudflare-Turnstile blocks + 10 selector-tuning issues = 18 escalation items**.

### Section A: Genuine Cloudflare Turnstile blocks (Chrome MCP required)

| Club | Step | Run-log status | Pixel-verified content |
|------|------|----------------|------------------------|
| mancity | landing-shot | captured (stealth-override-unblocked) | Cloudflare interstitial |
| mancity | tier-tunnel-club-premier-shot | captured | Cloudflare interstitial |
| mancity | tier-tunnel-club-shot | captured | Cloudflare interstitial |
| mancity | tier-backstage-shot | captured | Cloudflare interstitial |
| mancity | enquiry-form-prefill-shot | captured | Cloudflare interstitial |
| psg | billetterie-home-vip-shot | captured | Turnstile FR |
| psg | billetterie-match-selector-shot | captured | Turnstile FR |
| psg | enquiry-form-prefill-shot (billetterie) | captured | Turnstile FR |

**Eight steps total.** These 8 PNGs were intentionally NOT staged for commit in Plan 02-16 — they're not real evidence. The hybrid pipeline still routes correctly: DOM intel captures `title="Just a moment..."`, no rule matches, vision sees the interstitial → all features absent. Honest result.

### Section B: Selector-tuning failures (Plan 02-17 flow-map iteration)

| Club | Step | Failure |
|------|------|---------|
| mancity | landing-wait | stealth-override-failed: Timeout 5000ms (downstream of Section A) |
| mancity | match-selector | Page.click timeout |
| mancity | enquiry-form-prefill | Page.fill timeout (downstream of Section A) |
| realmadrid | matchday-tier-card-click | Page.click timeout |
| psg | first-tier-click | Page.click timeout |
| psg | billetterie-match-selector | Page.click timeout (downstream of Section A) |
| psg | enquiry-form-prefill (billetterie) | Page.fill timeout (downstream of Section A) |
| tottenham | enquiry-form-prefill | Page.fill timeout |

**Eight steps; 4 are downstream of Turnstile blocks** (resolve when Section A clears). Real selector-tuning items: 4.

### Section C: Login selector misses

| Club | Step | Failure |
|------|------|---------|
| realmadrid | enquiry-form-prefill | login_to_club returned False (selector miss or marker timeout) |
| psg | billetterie-login | login_to_club returned False (selector miss or marker timeout) |

Credentials are present in `.env.local`. The failure is the login flow not finding the email/password input fields.

### Stealth efficacy: corrected

| Club | v1 chrome-mcp steps | v2 chrome-mcp (run-log) | v2 chrome-mcp (pixel-verified) |
|------|---:|---:|---:|
| chelsea | 0 | 0 | 0 |
| mancity | 13 | 0 | 5 (Turnstile under HTTP 200) |
| realmadrid | 10 | 0 | 0 |
| psg | 7 | 0 | 3 (billetterie Turnstile under HTTP 200) |
| tottenham | 0 | 0 | 0 |
| **Total** | **30** | **0** | **8** |

**Stealth genuinely eliminated 22 of 30 (73%) Cloudflare blocks** — primarily on Real Madrid (full elimination) and PSG main domain (5 of 7 cleared). The remaining 8 (MCFC 5 + PSG-billetterie 3) need Chrome MCP because the Turnstile interactive widget cannot be solved by stealth fingerprinting alone.

This is the realistic Phase 2.5 cost picture: budget ~25-30% of clubs to need Chrome MCP escalation for hospitality even after the Plan 02-15 v2 architecture, and ~70% to capture cleanly under stealth.

---

## Subscription Budget Consumed

| Plan | Cost | Notes |
|------|---:|---|
| Plan 02-08 (bbox calibration) | ~$0.05 | Pre-existing, single Opus call (v1 + v2 share this) |
| Plan 02-11 (v1 vision wave) | $0 | Subscription backend, no variable cost |
| Plan 02-15 (scanner v2 architecture) | $0 | Code only |
| Plan 02-16 (recapture wave) | $0 | Capture only |
| **Plan 02-17 (this re-vision)** | **$0** | Subscription backend (Claude Max plan); 56 vision calls × 0 retail cost |
| **Total** | **~$0.05** | API-equivalent retail estimate would be ~$1.50–2.50 (per Plan 02-15 projection) |

**Hard cap of $5 not exceeded.** Wall-clock budget of 30-45 min was overrun (~50 min of wave time) — the parallelism was constrained by needing to keep the disagreements file consistent, so 3 waves ran in parallel and 2 waves ran sequentially.

---

## Coverage Math Headline (V2)

> **37 / 275 cells present (13.5%) + 13 disputed (4.7%) + 238 absent (86.5%). 20 of 55 features show signal in ≥1 club (was 14 in v1). 0 features universal across 5 clubs. 35 features absent in all 5 (was 41 in v1).**

Compared to v1: +6 cells now present, -6 disputed, +6 features now showing signal in ≥1 club. Most absences still cluster in deep-flow categories (enquiry_friction, post_booking_comms, booking_confirmation) where capture didn't reach.

---

## Open Issues (Carried from V1, Unchanged or Updated)

- **Opus bbox out-of-bounds:** ~16 sliced PNGs from v1 had clamped bboxes. v2 re-slicing did not address this — same limitation. Logged as Phase 2.5 carryover.
- **PSG 4/55 present:** improved from v1's 0/55. The remaining gap is the 3 Turnstile-blocked billetterie steps (Chrome MCP required).
- **MCFC 5/55 present:** unchanged from v1. The 5 features come from a pre-orchestrator landing capture that survived. The 5 Turnstile-blocked v2 steps need Chrome MCP.
- **Chelsea flow-map click-to-detail duplication** (Plan 02-16 finding): 4 of 6 Chelsea PNGs are the same package-list page. The flow-map's click navigation doesn't actually navigate. Pre-existing defect; deferred to Plan 02-18 (flow-map iteration).
- **Several v1-present features now absent in v2** (price_per_person_visible 3→0, buy_now_without_enquiry 4→2, phone_booking_option 2→0): the DOM rules are stricter than vision interpretation. Flagged for spot-check; if the DOM rules are too narrow, refine with examples from the v1 hits.
- **Front-end build / 308-test guard:** scanner/tests still 348/348. analysis/homepage/ untouched (D-20 holds). vitest tests not re-run in this plan.

---

## Decision Options for User (Updated)

| Option | What it means | When to pick it |
|---|---|---|
| **(A) APPROVE pilot v2 as-is** | Accept the v2 numbers. Mark HOSP-01..03 complete (already marked partial in v1; v2 confirms with cleaner data), close Phase 2, unlock Phase 2.5 planning. The 8 Turnstile blocks + 10 selector-tuning issues become a Phase 2.5 prerequisite, not a Phase 2 blocker. | If the rubric, hybrid pipeline, judge consensus, and `/hospitality` UI all check out — even with MCFC's known interstitial gap. Lowest friction path. |
| **(B) APPROVE WITH CONDITIONS** ⭐ | Approve v2, but require:  (i) Chrome MCP captures for the 8 Turnstile-blocked steps before Phase 2.5 starts, (ii) flow-map iteration plan (Plan 02-18) for the 4 selector-tuning + Chelsea duplication issues, (iii) spot-check the v1→v2 absences (price_per_person, buy_now, phone_booking) and refine DOM rules if v1 was correct. | **Recommended.** v2 proves the hybrid pipeline works; the gap is operational (bot-blocked sites need human-in-the-loop) plus a small false-negative DOM-rule list to refine. |
| **(C) REQUEST CHANGES** | Specific issues to address before approval (e.g., re-vision with relaxed DOM rules for the 5 v1→v2 absences, retrain bbox calibration, swap Chelsea for Newcastle). Phase 2 stays paused. | If you find systematic v2 false-negatives in spot-checks, OR want Chrome MCP captures done BEFORE closure. |
| **(D) REJECT pilot v2** | The v2 pipeline regressed — significant rework needed. Roll back to v1 numbers. | Unlikely. Only if spot-checks reveal v2 is systematically worse than v1, not just stricter. |

---

## User Action Required

To approve and close Phase 2 with v2:

1. **Read this report** (10–15 min).
2. **Re-open `scanner/output/contact-report-hospitality.html`** (regenerated from v2 verdicts). Visually scan all 55 features × 5 clubs. Note the v2 changes (post_match_service appearing 3/5; package_tier_list 5/5; price_per_person 0/5).
3. **Run `npm run dev`, visit `/hospitality`.** Verify the matrix re-renders with the new scores. Tottenham still top? RMA jumped to rank 2? PSG no longer dead-last on data-empty grounds (now has 4 present)?
4. **Spot-check 3–5 of the v1→v2 disagreements:**
   - **price_per_person_visible**: did v2 mis-rate TOT/RMA/CHE absent? Check tottenhamhotspur.com/hospitality/premium-seats — is there an explicit £XXX price on the tier landing?
   - **buy_now_without_enquiry**: did v2 mis-rate TOT/RMA absent? Check for a literal "Book Now" / "Buy Now" button.
   - **phone_booking_option**: did v2 miss `tel:` links? Check tottenhamhotspur.com/hospitality footer for a phone number — is it `<a href="tel:">` or text-only?
5. **Spot-check 3–5 of the 13 v2 disputed cells** (especially Tier A — HP19 / HP02 / HP10). Visit source. Does the resolved YES/NO call look right?
6. **Decide and signal:**
   - **Type `pilot v2 approved`** to close the pilot gate.
   - **Type `pilot v2 approved with caveats: <details>`** to approve but record specific Phase 2.5 follow-ups (recommended additions: refine DOM rules for the 5 v1→v2 absences, schedule Chrome MCP captures for the 8 Turnstile blocks).
   - **Provide free-form rejection feedback** (any text not starting with `pilot v2 approved`) to record blocker.

**Estimated time investment:** ~15 min reading + ~5–10 min UI / contact-sheet scan + ~10 min spot-checking = **~30–35 min total** (slightly more than v1 because of v1→v2 changes to verify).

---

## Pointers

- This report (V2): `.planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT-V2.md`
- V1 baseline (preserved): `.planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT.md`
- Scanner v2 architecture: `.planning/phases/02-hospitality-pilot/02-15-SCANNER-V2-SUMMARY.md`
- Recapture wave: `.planning/phases/02-hospitality-pilot/02-16-RECAPTURE-SUMMARY.md`
- Revision (this plan): `.planning/phases/02-hospitality-pilot/02-17-REVISION-SUMMARY.md`
- Visual contact sheet: `scanner/output/contact-report-hospitality.html` (regenerated from v2)
- Chrome MCP escalation list: `scanner/output/CHROME-MCP-NEEDED.md`
- Disagreement raw data: `scanner/output/disagreements-hospitality.json` (74 records, was 112)
- V1 disagreement archive: `scanner/output/disagreements-hospitality-v1-backup.json`
- Per-club v2 result JSONs: `analysis/hospitality/results/{club}.json`
- Per-club v1 result archive: `.planning/phases/02-hospitality-pilot/v1-results-backup/{club}.json`
- Aggregate scores: `analysis/hospitality/results/_scores.json`

---

*Generated by Plan 02-17 — re-vision wave with hybrid DOM+vision routing. Phase 2 awaits explicit user signal.*
