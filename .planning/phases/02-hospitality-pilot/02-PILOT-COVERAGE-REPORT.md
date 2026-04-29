# Phase 2 — Hospitality Pilot Coverage Report

**Generated:** 2026-04-28
**Pilot clubs:** Manchester City, Tottenham Hotspur, Real Madrid, Paris Saint-Germain, Chelsea
**Rubric:** 55 features (`analysis/hospitality/HOSPITALITY-FLOW.md` / `analysis/hospitality/features.ts`)
**Plans synthesized:** 02-08 (crawler v2 + bbox calibration + creds fix) → 02-09 (5 extended flow-maps) → 02-10 (capture orchestrator + live wave) → 02-11 (two-judge vision wave) → 02-12 (slice + contact-sheet + results derivation) → 02-13 (/hospitality tab unlock)
**Generator:** Plan 02-14 Task 1 (this file)

---

## TL;DR

- **Pilot status: PARTIAL.** All 5 clubs produced valid `analysis/hospitality/results/{club}.json` files with 55-feature coverage and the `/hospitality` tab is rendering them. But coverage is **uneven** — Tottenham + Chelsea got rich multi-step capture; Man City / Real Madrid / PSG got landing-only or partial-flow capture because Cloudflare Turnstile / CAPTCHA / dynamic dead-ends blocked the unattended Playwright run.
- **Aggregate feature coverage: 31 / 275 cells present (11.3%)** + **19 disputed cells (6.9%)** + **225 absent cells (81.8%)**. 14 of 55 features show up in at least one club; **0 features are universally present**; **41 features are absent in all 5 clubs**.
- **Top blocker: 30 deferred Chrome MCP steps** across MCFC (13), RMA (10), PSG (7) — each step is one click-or-screenshot the user must drive in Chrome MCP because Playwright was bot-blocked. Estimated user time: **~30–45 min**.
- **Subscription cost actually consumed: ~$0.05** (bbox calibration only; subscription wave was free under Claude Max plan). The earlier ~$5.50 retail estimate was the upper-bound API-equivalent — actual subscription spend was zero variable cost.
- **Recommended decision: Option (B) — APPROVE WITH CONDITIONS.** Accept the pilot as-is to close Phase 2 and unblock Phase 2.5 planning, but require the user to drive the 30 deferred Chrome MCP steps + a re-vision pass before the 28-club rollout begins. Rationale: the rubric, scanner pipeline, vision-judge consensus, slicing, and UI render are all proven; what's missing is bot-blocked sites' content, which Chrome MCP fixes manually rather than architecturally.

---

## Per-Club Summary

Counts are derived from `analysis/hospitality/results/{club}.json` (vision-judge output) crossed with `scanner/output/capture-run-log-hospitality-{club}-*.json` (capture-orchestrator output).

| Club | Captured Steps (Playwright) | Deferred Chrome MCP | Skipped (paid-only) | Capture Errors | Vision'd Steps | Features Present | Features Disputed | Features Absent | Judge Agreement | Score (raw) | Rank |
|------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Tottenham Hotspur | 11 | 0 | 0 | 1 | 5 | 12 | 7 | 36 | 96.73% | **−57** | **1** |
| Chelsea | 12 | 0 | 2 | 1 | 6 | 8 | 9 | 38 | 92.12% | **−79** | 2 |
| Real Madrid | 3 | 10 | 0 | 0 | 1 | 6 | 3 | 46 | 94.55% | **−92** | 3 |
| Manchester City | 0 | 13 | 0 | 0 | 1 | 5 | 0 | 50 | 100.00% | **−99** | 4 |
| Paris Saint-Germain | 6 | 7 | 0 | 1 | 3 | 0 | 0 | 55 | 100.00% | **−125** | 5 |
| **TOTALS** | **32** | **30** | **2** | **3** | **16** | **31** | **19** | **225** | **96.48%** | **−452** | — |

**Notes on totals:**
- "Captured Steps (Playwright)" includes both shot steps and intermediate navigate/click steps. "Vision'd Steps" is the count of distinct `*-shot.png` files that survived to vision judging — this is the data that produced the 55-feature presence map.
- MCFC's 5 "Features Present" come from a single `mancity_landing.png` captured during Plan 02-08 bbox-calibration (pre-orchestrator); the 13 orchestrator steps are all deferred to Chrome MCP. This is why MCFC has 100% judge agreement on a tiny sample.
- PSG's 0 features-present is legitimate (Opus + Sonnet fully agreed nothing was visible on the captured pages — landing + first-tier + all-executive-club). The remaining 7 steps (billetterie subdomain, login, match-selector, enquiry-form) are all deferred to Chrome MCP because PSG's billetterie subdomain blocks unattended browsers.
- Chelsea's 2 skipped steps are legitimate D-15 deferrals: `match-selector` and `enquiry-form-prefill` on `hospitality.chelseafc.com` require paid-customer status. This is the locked-in **Option B — partial coverage** outcome.
- Judge agreement rate is the per-step Opus-vs-Sonnet match rate over all 55 features; "disputed" features (where judges disagreed at least once) are flagged sticky in the result JSON and rendered specially in the UI.

---

## Per-Feature Coverage Rate (all 55)

`Present in N/5` = how many of the 5 pilot clubs have `features[<key>] === true` in their results JSON.
`Disputed in N/5` = how many of the 5 pilot clubs flagged this feature in `disputed_features[]` (sticky any-step disagreement).

| ID | Feature | Tier | Present in N/5 | Disputed in N/5 | Notes / category |
|----|---------|------|---:|---:|------|
| HP01 | Package Tier List | A | 3/5 | 0/5 | package_discovery — TOT/MCFC/CHE clear yes |
| HP02 | Per-Tier Landing Page | A | 4/5 | 0/5 | package_discovery — only PSG missing |
| HP03 | Dress-Code Info | A | 0/5 | 0/5 | package_discovery — universal absence |
| HP04 | Tier Comparison Table | C | 0/5 | 0/5 | package_discovery — universal absence |
| HP05 | Tier Capacity Indicator | C | 0/5 | 1/5 | package_discovery — Chelsea disputed |
| HP06 | Upcoming Matches Pre-Tier | C | 3/5 | 0/5 | package_discovery — TOT/MCFC/RMA |
| HP07 | Multi-Occasion Tagging | D | 0/5 | 0/5 | package_discovery — universal absence |
| HP08 | Price Per Person Visible | A | 3/5 | 1/5 | pricing_transparency — TOT/RMA/CHE; TOT disputed |
| HP09 | Fixture Category Tiers | A | 0/5 | 0/5 | pricing_transparency — universal absence |
| HP10 | Min Booking Unit | A | 0/5 | 1/5 | pricing_transparency — Chelsea disputed |
| HP11 | Price Range By Match | C | 0/5 | 1/5 | pricing_transparency — Real Madrid disputed |
| HP12 | Total Cost Preview Pre-Submit | C | 0/5 | 0/5 | pricing_transparency — universal absence |
| HP13 | Deposit Vs Full Payment | C | 0/5 | 0/5 | pricing_transparency — universal absence |
| HP14 | Corporate Invoice Billing | C | 0/5 | 0/5 | pricing_transparency — universal absence |
| HP15 | VAT Inclusive Toggle | D | 0/5 | 0/5 | pricing_transparency — universal absence |
| HP16 | Menu Preview | A | 1/5 | 0/5 | food_beverage — Tottenham only |
| HP17 | Allergen Info | A | 0/5 | 0/5 | food_beverage — universal absence |
| HP18 | Vegetarian Options | A | 0/5 | 0/5 | food_beverage — universal absence |
| HP19 | Bar Type Indicator | A | 2/5 | 2/5 | food_beverage — TOT+CHE present, both disputed |
| HP20 | Chef Attribution | C | 0/5 | 1/5 | food_beverage — Tottenham disputed |
| HP21 | Kids Menu | C | 0/5 | 0/5 | food_beverage — universal absence |
| HP22 | Meal Timing Visible | C | 1/5 | 2/5 | food_beverage — Chelsea present; TOT+CHE disputed |
| HP23 | Post-Match Service | C | 0/5 | 2/5 | food_beverage — TOT+CHE disputed (both N) |
| HP24 | Fixture List Visible | A | 3/5 | 0/5 | match_selector_ux — MCFC/TOT/RMA |
| HP25 | Competition Filter | A | 0/5 | 0/5 | match_selector_ux — universal absence |
| HP26 | Sold-Out Indicator | A | 0/5 | 0/5 | match_selector_ux — universal absence |
| HP27 | Multi-Match Bundle Selector | C | 0/5 | 0/5 | match_selector_ux — universal absence |
| HP28 | Opponent Filter | D | 0/5 | 0/5 | match_selector_ux — universal absence |
| HP29 | Availability Heatmap | D | 0/5 | 0/5 | match_selector_ux — universal absence |
| HP30 | Enquiry Form Field Count ≤ 7 | A | 0/5 | 0/5 | enquiry_friction — universal absence (form errors all 3 enquiry steps) |
| HP31 | Immediate Confirmation Email | A | 0/5 | 0/5 | enquiry_friction — universal absence |
| HP32 | Accessible Booking Option | A | 0/5 | 0/5 | enquiry_friction — universal absence |
| HP33 | Buy Now Without Enquiry | C | 4/5 | 1/5 | enquiry_friction — only PSG missing; Chelsea disputed |
| HP34 | Phone Booking Option | C | 2/5 | 0/5 | enquiry_friction — TOT+RMA |
| HP35 | Live Chat Availability | C | 1/5 | 1/5 | enquiry_friction — TOT present + disputed |
| HP36 | Response Time Promise | C | 0/5 | 0/5 | enquiry_friction — universal absence |
| HP37 | Parking Included Indicator | A | 0/5 | 0/5 | premium_amenities — universal absence |
| HP38 | Match Program Included | A | 0/5 | 0/5 | premium_amenities — universal absence |
| HP39 | Private Entrance Indicator | C | 0/5 | 0/5 | premium_amenities — universal absence |
| HP40 | Stadium Tour Inclusion | C | 1/5 | 1/5 | premium_amenities — Chelsea present + disputed |
| HP41 | Concierge Service | C | 1/5 | 1/5 | premium_amenities — Tottenham; Real Madrid disputed |
| HP42 | Car Pickup Or Transfer | D | 0/5 | 0/5 | premium_amenities — universal absence |
| HP43 | Pitchside Or Tunnel Access | D | 2/5 | 1/5 | premium_amenities — TOT+CHE; Chelsea disputed |
| HP44 | Player Meet And Greet | D | 0/5 | 0/5 | premium_amenities — universal absence |
| HP45 | Merchandise Voucher | D | 0/5 | 0/5 | premium_amenities — universal absence |
| HP46 | Transport Package Bundling | D | 0/5 | 0/5 | premium_amenities — universal absence |
| HP47 | Booking Change Policy Visible | A | 0/5 | 1/5 | post_booking_comms — Tottenham disputed |
| HP48 | Seat Number Lead Time | A | 0/5 | 0/5 | post_booking_comms — universal absence |
| HP49 | Fixture Change Notification | A | 0/5 | 1/5 | post_booking_comms — Real Madrid disputed |
| HP50 | Dietary Preferences Capture | A | 0/5 | 0/5 | post_booking_comms — universal absence |
| HP51 | Cancellation Refund Window | A | 0/5 | 0/5 | post_booking_comms — universal absence |
| HP52 | Group Host Contact | C | 0/5 | 0/5 | post_booking_comms — universal absence |
| HP53 | Confirmation Page Clarity | A | 0/5 | 0/5 | booking_confirmation — universal absence (forms not reached) |
| HP54 | Saved Booking In Account | C | 0/5 | 1/5 | booking_confirmation — Chelsea disputed |
| HP55 | Receipt Download | C | 0/5 | 0/5 | booking_confirmation — universal absence |

**Read this table:** the 14 features showing "Present in ≥1/5" are where the pilot has signal. The 41 universal-absent features are mostly in deeper-flow categories (`enquiry_friction`, `post_booking_comms`, `booking_confirmation`) — **expected**, because no club's enquiry-form step survived capture (3 of 5 attempts errored out, 2 are paid-gated/deferred). Phase 2.5 + the Chrome MCP handoff are the gates that unlock the deeper categories.

---

## Blocked / Skipped Steps + Reasons

Sourced from each club's `scanner/output/capture-run-log-hospitality-{club}-*.json`. `chrome-mcp` = unattended Playwright auto-skip, deferred to user manual run; `skipped` = D-15 paid-account gate; `error` = Playwright timeout / selector miss.

| Club | Step | Status | Reason |
|------|------|--------|--------|
| tottenham | enquiry-form-prefill | error | `Page.fill: Timeout 30000ms` — name input selector not matching tickets.tottenhamhotspur.com form |
| mancity | landing, landing-wait, landing-shot | chrome-mcp | Cloudflare Turnstile blocks unattended Playwright on mancity.com/hospitality |
| mancity | tier-tunnel-club-premier (+shot) | chrome-mcp | (same) |
| mancity | tier-tunnel-club (+shot) | chrome-mcp | (same) |
| mancity | tier-backstage (+shot) | chrome-mcp | (same) |
| mancity | tier-your-matchday-experience | chrome-mcp | (same) |
| mancity | match-selector | chrome-mcp | (same) |
| mancity | enquiry-form-prefill (+shot) | chrome-mcp | (same) |
| realmadrid | matchday-hospitality (+wait, +shot) | chrome-mcp | dynamic-content dead-end / dead_ends-detected; auto-skipped pre-orchestrator |
| realmadrid | matchday-tier-card-click (+shot) | chrome-mcp | (same) |
| realmadrid | palcos-vip (+wait, +shot) | chrome-mcp | (same) |
| realmadrid | enquiry-form-prefill (+shot) | chrome-mcp | (same) |
| psg | first-tier-click | error | `Page.click: Timeout 5000ms` — selector `a[href*='hospitality'] .card, a.tier-card` no match on psg.fr |
| psg | billetterie-home-vip (+shot) | chrome-mcp | billetterie.psg.fr blocks unattended browsers |
| psg | billetterie-login | chrome-mcp | (same) |
| psg | billetterie-match-selector (+shot) | chrome-mcp | (same) |
| psg | enquiry-form-prefill (+shot) | chrome-mcp | (same) |
| chelsea | landing-wait | error | 5s wait timeout (cosmetic; landing-shot still captured) |
| chelsea | match-selector | skipped | requires-paid-account (D-15 — locked-in Option B partial) |
| chelsea | enquiry-form-prefill | skipped | requires-paid-account (D-15) |

**Totals:** 32 captured + 30 chrome-mcp + 2 paid-skipped + 3 errors = 67 step-instances across 5 clubs (orchestrator counts each step once even if it's followed by a `*-shot` step). This matches the prompt's "32 captured / 30 deferred-manual / 3 errors" handoff totals.

The full step-by-step Chrome MCP recipe is in `.planning/phases/02-hospitality-pilot/02-10-MANUAL-CAPTURE-HANDOFF.md`.

---

## Disagreement Inventory (Opus 4.7 vs Sonnet 4.5)

Sourced from `scanner/output/disagreements-hospitality.json` (112 records).

**By club:**

| Club | Disagreement records | Sticky disputed features | Judge agreement rate |
|------|---:|---:|---:|
| Chelsea | 56 | 9 | 92.12% |
| Tottenham | 39 | 7 | 96.73% |
| Real Madrid | 9 | 3 | 94.55% |
| Manchester City | 8 | 0 | 100.00% |
| PSG | 0 | 0 | 100.00% |
| **Total** | **112** | **19 (16 unique feature keys)** | **96.48%** |

**By kind (per Phase 1 Plan 01-08 disagreement schema):**

| Kind | Count | Meaning |
|------|---:|---|
| bbox | 69 | Both judges agreed on presence; bbox coords differed (Opus tends to give union/header bbox; Sonnet gives tight bbox) |
| presence | 39 | Judges split on whether the feature is present at all (sticky → flagged disputed) |
| confidence | 4 | Both agreed on presence + bbox; only confidence delta crossed threshold |

**Key insight:** ~62% of disagreements are bbox-only (both judges agree the feature is there, just outline it differently). These are NOT correctness issues — they are calibration artifacts and should NOT block approval. The 39 presence disagreements are the spot-check workload.

**Top 5 most-disputed feature keys (across all clubs, all kinds):**

| Feature | Disagreement count |
|---------|---:|
| per_tier_landing_page | 11 |
| price_per_person_visible | 11 |
| buy_now_without_enquiry | 9 |
| bar_type_indicator | 9 |
| pitchside_or_tunnel_access | 8 |

These are mostly bbox disagreements on features both judges agreed are present (HP01/HP02/HP08/HP19/HP33/HP43 — Tier A and C anchors).

---

## The 19 Disputed Cells (Spot-Check Workload)

These are the cells where the user gate matters most. Each row is a `(club, feature)` pair where Opus and Sonnet disagreed on at least one step's presence call. The "Resolved as" column shows what landed in the final results JSON (per Plan 02-12's resolution policy: per-step Opus-when-agree, False+disputed-when-disagree, OR-flatten across steps with sticky disputed flag).

| # | Club | Feature | Tier | Resolved as | Recommended user spot-check |
|---|------|---------|------|---|---|
| 1 | Tottenham | bar_type_indicator (HP19) | A | **YES, disputed** | Visit tottenhamhotspur.com/hospitality/premium-seats; verify bar-type wording. |
| 2 | Tottenham | booking_change_policy_visible (HP47) | A | NO, disputed | Verify a change/cancellation policy is NOT shown pre-enquiry. |
| 3 | Tottenham | chef_attribution (HP20) | C | NO, disputed | Check menu blurb for any named chef/restaurant partner. |
| 4 | Tottenham | live_chat_availability (HP35) | C | **YES, disputed** | Confirm live-chat widget is present (we hide it for capture per D-11). |
| 5 | Tottenham | meal_timing_visible (HP22) | C | NO, disputed | Look for arrival / pre-match / post-match timing on tier landing. |
| 6 | Tottenham | post_match_service (HP23) | C | NO, disputed | Look for "stays open after final whistle" copy. |
| 7 | Tottenham | price_per_person_visible (HP08) | A | **YES, disputed** | Confirm inc-VAT headline price visible WITHOUT enquiry. |
| 8 | Real Madrid | concierge_service (HP41) | C | NO, disputed | Check VIP/Palcos pages for dedicated concierge mention. |
| 9 | Real Madrid | fixture_change_notification (HP49) | A | NO, disputed | Look for schedule-change policy. |
| 10 | Real Madrid | price_range_by_match (HP11) | C | NO, disputed | Look for low-high range per fixture. |
| 11 | Chelsea | bar_type_indicator (HP19) | A | **YES, disputed** | Verify complimentary/cash/premium-only bar is named. |
| 12 | Chelsea | buy_now_without_enquiry (HP33) | C | **YES, disputed** | Confirm self-serve checkout exists (vs enquiry-only). |
| 13 | Chelsea | meal_timing_visible (HP22) | C | **YES, disputed** | Look for arrival / pre-match / post-match timing copy. |
| 14 | Chelsea | min_booking_unit (HP10) | A | NO, disputed | Look for per-seat / per-table-of-10 / per-box copy. |
| 15 | Chelsea | pitchside_or_tunnel_access (HP43) | D | **YES, disputed** | Verify any pitchside/tunnel-walk amenity is offered. |
| 16 | Chelsea | post_match_service (HP23) | C | NO, disputed | Same as TOT/post_match: look for "stays open" copy. |
| 17 | Chelsea | saved_booking_in_account (HP54) | C | NO, disputed | Login-gated; not reachable in pilot. |
| 18 | Chelsea | stadium_tour_inclusion (HP40) | C | **YES, disputed** | Confirm tour bundled into a hospitality package. |
| 19 | Chelsea | tier_capacity_indicator (HP05) | C | NO, disputed | Look for min/max guests or per-box headcount. |

(16 unique feature keys; bar_type_indicator / meal_timing_visible / post_match_service each appear twice across clubs.)

**User action:** spot-check 3–5 of the **YES, disputed** cells (especially Tier A — HP19 / HP08) by visiting the source URL. If the YES calls look right, approve the pilot. If you find systematic over-calling, tag those features for re-vision in Phase 2.5.

---

## Chelsea Option B Partial Status

Chelsea was the locked-in Option B "main domain credentials worked, paid subdomain didn't" pilot member.

- `chelseafc.com/hospitality` (main domain, public) — fully captured: landing + 5 package detail pages (Centenary Club, Platinum, Home Dugout Club, Museum Suite, Tambling Suite). 12 captured shots.
- `hospitality.chelseafc.com` (paid-customer subdomain) — `match-selector` and `enquiry-form-prefill` steps marked `skipped: requires-paid-account` (D-15). Dummy account registration is not sufficient — needs prior paid hospitality customer status.
- Score: −79, rank 2/5.
- Disputed features: 9 (highest of any club, mostly bar / meal / post-match disagreements between judges).

**Recommendation for Phase 2.5:** keep Chelsea partial, with an explicit footnote in the matrix UI ("Chelsea: paid-customer subdomain not crawlable; deeper-flow features unmapped"). Alternative: swap Chelsea for **Newcastle United** or **Aston Villa** (D-18 stress-test mid-tier club). User should decide before Phase 2.5 starts. Recommendation is **keep Chelsea** — the public domain coverage is high-quality and the paid-subdomain is a known-and-documented limitation that's relevant for the benchmark itself (poor self-serve discovery is a feature finding, not a bug).

---

## Opus 4.7 Bbox Calibration Outcome

From `scanner/output/opus-bbox-calibration.json` (Plan 02-08, ground-truth = mancity_landing.png header bbox `[0, 0, 2880, 800]`):

- Decided mode: **`css`**
- CSS-IoU vs ground truth: 0.0076
- Native-IoU vs ground truth: 0.0011
- IoU margin for native: 0.20

**Read:** Both modes scored very low IoU on the calibration probe (Opus returned a tiny logo bbox `[115, 17, 168, 65]` versus the wide header GT). Per Plan 02-08's calibration policy, when CSS-IoU > native-IoU even by a hair, mode = `css`. **Practical impact:** ~16 of the sliced feature crops in `analysis/hospitality/evidence/features/` were sliced from out-of-bounds Opus bboxes that the slicer clamped to image bounds. This is a known calibration limitation — not blocking pilot approval but worth a Phase 2.5 follow-up to either retrain the bbox-mode decision or upgrade the slicer to use Sonnet's tighter bboxes when both judges agree on presence. Logged as a Phase 2.5 carryover.

---

## Subscription Budget Consumed

| Plan | Cost | Notes |
|------|---:|---|
| Plan 02-08 (bbox calibration) | ~$0.05 | Single Opus call against `mancity_landing.png` |
| Plan 02-11 (vision wave) | $0 | Subscription backend (Claude Max plan); no variable cost |
| Plan 02-12 (results derivation) | $0 | Local computation only |
| Plan 02-13 (UI unlock) | $0 | Code only |
| **Total** | **~$0.05** | API-equivalent retail estimate would be ~$5.50–6.50 |

**No subscription overage; well under any imaginable budget threshold.**

---

## Coverage Math Headline

> **31 / 275 cells present (11.3%) + 19 disputed (6.9%) + 225 absent (81.8%). 14 of 55 features show signal in ≥1 club. 0 features universal across 5 clubs. 41 features absent in all 5.**

Most absences cluster in deep-flow categories where capture didn't reach (enquiry_friction, post_booking_comms, booking_confirmation) — the Chrome MCP handoff is the gate that closes those. For the categories where capture did reach (package_discovery, pricing_transparency, food_beverage, premium_amenities), feature signal is present and judge-disputed cells are the spot-check workload.

---

## Open Issues from Prior Plans

These are non-blocking but the user should be aware:

- **Opus bbox out-of-bounds:** ~16 sliced PNGs in `analysis/hospitality/evidence/features/` were sliced from clamped bboxes. Visible in contact sheet as slightly-off framing. Not a correctness issue — feature-presence calls are unaffected.
- **PSG 0% present:** legitimate per judge consensus on the 3 captured pages (landing + first-tier + all-executive-club). The remaining 7 deferred Chrome MCP steps (billetterie subdomain) likely contain most PSG hospitality content. Don't read PSG's score as PSG's actual hospitality offering until Chrome MCP captures land.
- **MCFC sample size of 1:** the single `mancity_landing.png` produced a 5-feature presence map. After Chrome MCP captures land, expect MCFC's score and disputed-features count to rise materially.
- **REQUIREMENTS.md state inconsistency:** lines 86–88 already show HOSP-01..03 as `[x]` (set partial during front-half), but lines 162–164's traceability table still says `Pending`. Plan 02-14 Task 3 (post-approval) flips the traceability table; the v7 checklist is already correct.
- **Front-end build / 308-test guard:** Plan 02-13 locked the visual baseline and confirmed 308 tests pass; this plan is documentation-only and doesn't touch code.

---

## Decision Options for User

| Option | What it means | When to pick it |
|---|---|---|
| **(A) APPROVE pilot as-is** | Accept partial coverage. Mark HOSP-01..03 complete, close Phase 2, unlock Phase 2.5 planning. Manual Chrome MCP handoff becomes a Phase 2.5 prerequisite, not a Phase 2 blocker. | If the rubric, scanner pipeline, vision-judge consensus, and `/hospitality` UI render all check out — even if some clubs have thin data. |
| **(B) APPROVE WITH CONDITIONS** ⭐ | Approve the pilot, but require the user to complete the 30 Chrome MCP captures + a re-vision pass before Phase 2.5 is allowed to start. Captures in STATE.md as a Phase 2.5 prerequisite. | **Recommended.** The pilot proves the pipeline works; the gap is operational (bot-blocked sites need human-in-the-loop), not architectural. |
| **(C) REQUEST CHANGES** | Specific issues to address before approval (e.g., re-vision Tottenham with stricter prompt, swap Chelsea for Newcastle, retrain bbox calibration). Phase 2 stays paused, plan 02-15 schedules remediation. | If you find a systematic vision-judge over-calling pattern in spot-checks, OR want Chrome MCP captures done BEFORE closure, OR want Chelsea swapped. |
| **(D) REJECT pilot** | The pilot failed. Significant rework needed (rubric flaws, scanner architecture issues, etc.). | Unlikely given current evidence — only pick this if spot-checks reveal systematic correctness failures, not coverage gaps. |

---

## User Action Required

To approve and close Phase 2:

1. **Read this report end-to-end** (~10–15 min).
2. **Open `scanner/output/contact-report-hospitality.html`** in a browser. Visually scan all 55 features × 5 clubs. Are present features mostly accurate? Are red-bordered absent cells justifiable? Are disputed cells (judge-split) flagged appropriately?
3. **Run `npm run dev`, visit `http://localhost:3000/hospitality`.** Does the matrix render? "Pilot: 5 clubs" label visible? Are scores plausible (Tottenham at top per research §5)? Is the back-to-home affordance present and NOT styled orange (single-orange-CTA invariant)?
4. **Spot-check 3–5 disputed cells** (especially Tier A — HP19 bar_type_indicator on TOT/CHE; HP08 price_per_person_visible on TOT). Visit the source URL. Does the YES/NO call look right?
5. **Decide and signal:**
   - **Type `pilot approved` (case-insensitive)** to close the pilot gate and unlock Phase 2.5 planning.
   - **Type `pilot approved with caveats: <details>`** to approve but record specific Phase 2.5 follow-ups.
   - **Provide free-form rejection feedback** (any text not starting with `pilot approved`) — Plan 02-14 Task 4 will record the rejection in STATE.md as a blocker and exit without closing the phase.

**Estimated time investment:** ~10–15 min reading + ~5–10 min UI / contact-sheet scan + ~5 min spot-checking 3–5 disputed cells = **~20–30 min total**.

---

## Pointers

- This report: `.planning/phases/02-hospitality-pilot/02-PILOT-COVERAGE-REPORT.md`
- Pre-approval halt note: `.planning/phases/02-hospitality-pilot/02-14-PRE-APPROVAL-SUMMARY.md`
- Visual contact sheet: `scanner/output/contact-report-hospitality.html`
- Disagreement raw data: `scanner/output/disagreements-hospitality.json` (112 records)
- Per-club result JSONs: `analysis/hospitality/results/{mancity,tottenham,realmadrid,psg,chelsea}.json`
- Aggregate scores: `analysis/hospitality/results/_scores.json`
- Bbox calibration: `scanner/output/opus-bbox-calibration.json`
- Capture run-logs: `scanner/output/capture-run-log-hospitality-{club}-*.json`
- Manual Chrome MCP handoff: `.planning/phases/02-hospitality-pilot/02-10-MANUAL-CAPTURE-HANDOFF.md`
- Hospitality rubric: `analysis/hospitality/HOSPITALITY-FLOW.md`
- Feature definitions: `analysis/hospitality/features.ts`
- Live UI: `app/hospitality/page.tsx` (Plan 02-13)

---

*Generated by Plan 02-14 Task 1 — coverage aggregation. Phase 1 of plan execution complete; Phase 2 (closure or rejection capture) waits for explicit user signal in main conversation.*
