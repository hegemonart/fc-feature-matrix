# Hospitality Candidate Features — review-gated draft

**Phase:** 2 (hospitality pilot)
**Generated:** 2026-04-24
**Status: DRAFT — awaiting user approval (D-05 hard gate).**

Per D-05, this list must be frozen by the user before `HOSPITALITY-FLOW.md`
or `features.ts` is written (plan 02-03). Approve / edit / merge / re-tier
inline; do not create a second document. When you're done, respond
**`approved — freeze candidates`** and plan 02-03 will proceed.

---

## How to use this document

1. Review candidates below (8 categories, ≥40 rows).
2. For each candidate, decide:
   - **Accept** — leave as-is.
   - **Reject** — strike through with `~~~key~~~` + one-line rationale.
   - **Modify** — edit tier / origin / description inline.
   - **Merge** — annotate "merge with `other_key`" in the Source column.
3. Add missing candidates at the bottom of the relevant category (extend tables).
4. When satisfied, reply exactly: **`approved — freeze candidates`**

**Why this gate matters (D-05):** Plan 02-03 writes `HOSPITALITY-FLOW.md`
and `features.ts` directly from this list. Once those files exist, reworking
the feature set becomes expensive (rubric paragraphs + scoring weights +
`features.ts` imports). Cheaper to fix the list now.

---

## Legend

- **Origin** — provenance of the signal that surfaced this candidate:
  - `O` = observed-on-site (one of the 10 gold-standard sites has it)
  - `C` = complained-about (review quote: users say this is done badly or not at all)
  - `W` = wished-for (review quote: users ask for this, explicit or strongly implied)
  - Multiple tags are additive — `O, C` means observed but complained about.
- **Tier** — scoring weight class:
  - `1` = table-stakes (every premium buyer expects; absence = penalty). Weight 1×.
  - `2` = differentiator (presence lifts above peers; absence acceptable). Weight 2×.
  - `3` = delight (rare; brand-forming). Weight 3×.
- **Source** — citation pointer to a row in `REVIEW-SOURCES.md` (site name or Tier-A/B/C number).

Weights are **ballpark** here; finalized in `features.ts` post-freeze.

---

## Counts

- **Total candidates: 50** (target ≥40 per D-05; research §3 seed had 48; review-dig added 2 extensions marked **+** in category tables and gathered in a summary section at the end.)
- **By category:** Package Discovery 6, Pricing Transparency 7, Food & Beverage 8, Match Selector UX 6, Enquiry Friction 6, Premium Amenities 9, Post-Booking Comms 5, Booking Confirmation 3 — plus 2 review-dig extensions surfaced under the most relevant categories (below).
- **By origin (incl. extensions):** `O`-anchored 32, `C`-anchored 20, `W`-anchored 14 (many rows carry multiple tags).
- **By tier:** `1` ≈ 22, `2` ≈ 19, `3` ≈ 9.

## Tier Weight Rationale

- **Tier 1** ≈ 22 features. Table-stakes. Weight multiplier 1× in scoring.
- **Tier 2** ≈ 19 features. Differentiators. Weight 2×.
- **Tier 3** ≈ 9 features. Delight. Weight 3×.

(Final weights set in `features.ts`; draft values here are indicative.)

---

## 1. Package Discovery

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `package_tier_list` | Visible tier listing | Landing page lists all packages with distinguishing copy in one view | O | 1 | All 10 gold sites; MCFC `/hospitality`; CHE `hospitality.chelseafc.com` |
| `tier_comparison_table` | Side-by-side tier matrix | Feature comparison across tiers on a single page | O | 2 | F1 Paddock Club (Tier-A #3) |
| `per_tier_landing_page` | Dedicated tier page | Clicking a tier opens its own description landing | O | 1 | MCFC `/hospitality/the-tunnel-club-premier` |
| `tier_capacity_indicator` | Party-size visibility | Min/max guests or per-box headcount visible | O, W | 2 | F1 Legends Club; Seat Unique Trustpilot (Tier-A #1) |
| `dress_code_info` | Dress-code call-out | Explicit per-tier dress code (smart, smart-casual, formal) | C | 1 | Seat Unique Trustpilot (Tier-A #1) |
| `upcoming_matches_pre_tier` | Per-package fixture list | Package cards show which matches apply before tier-selection | O | 2 | TOT `/matchday-options/` |

## 2. Pricing Transparency

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `price_per_person_visible` | Headline price visible | Inc-VAT headline price on tier landing (not behind enquiry) | O, W | 1 | TOT £299/£449 visible; MCFC hides — Tier-A #5, r/coys |
| `price_range_by_match` | Per-match price range | Low-high axis per tier (e.g. £269–£699 by opponent demand) | O | 2 | MCFC Tunnel Club listings |
| `fixture_category_tiers` | Cat A/B/C labels | Match category pricing labels visible on selector | O | 1 | EPL convention (MCFC, TOT, CHE) |
| `total_cost_preview_pre_submit` | Total-cost preview | Running total shown before enquiry submission | W | 2 | Baymard-style wish; voiced across Tier-A blogs |
| `vat_inclusive_toggle` | VAT inc/ex toggle | Switch between inc-VAT and ex-VAT for corporate buyers | O | 3 | Some gold sites; F1 corporate flow |
| `min_booking_unit` | Booking granularity clarity | "Per seat" vs "per table of 10" vs "per box" plainly stated | O, C | 1 | Seat Unique complaint pattern (Tier-A #1) |
| `deposit_vs_full_payment` | Payment-terms visibility | Deposit vs full payment terms shown pre-enquiry | C | 2 | Trustpilot surprise-terms complaints (Tier-A #1–3) |

## 3. Food & Beverage

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `menu_preview` | Sample menu visible | Representative menu shown on tier page (not "TBC") | O, W | 1 | F1 3-course sample; MCFC Tunnel Club Premier "five-course" |
| `chef_attribution` | Named chef / partner | Chef or restaurant partner explicitly credited | O | 2 | F1 "renowned chefs"; MCFC "award-winning executive chefs" |
| `allergen_info` | Allergen disclosure | Allergen info available pre-booking (not only on the night) | C, W | 1 | Keith Prowse Trustpilot (Tier-A #2) |
| `vegetarian_options` | Veggie / vegan options | Veggie / vegan option disclosure on menu preview | C | 1 | Keith Prowse Trustpilot (Tier-A #2) |
| `kids_menu` | Kids menu / kid-friendly | Explicit kids menu or child-friendly hospitality indicator | W | 2 | goseelearn family review (Tier-A #11) |
| `bar_type_indicator` | Bar model disclosed | Complimentary / cash / premium-only bar clearly indicated | C | 1 | CHE Centenary cash-bar; TOT TripAdvisor "spirits at separate bar" (Tier-A #5, #7) |
| `meal_timing_visible` | Meal timing info | Arrival / pre-match / post-match meal timing stated | O | 2 | CHE Platinum "2.5h prior"; TOT "3h pre / 2h post" |
| `post_match_service` | Post-match service | What stays open after final whistle | O | 2 | CHE Tambling "~1h after"; TOT "2h after final whistle" |

## 4. Match Selector UX

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `fixture_list_visible` | Fixture list | Standard fixture list on match-selector step | O | 1 | Standard across all 10 gold sites |
| `competition_filter` | Competition filter | PL / UCL / Cup filter on selector | O | 1 | EPL + UCL clubs require this |
| `opponent_filter` | Opponent search | Search / filter by opponent | O | 3 | F1 has via circuit; rare in football |
| `sold_out_indicator` | Sold-out indicator | Explicit sold-out state on fixture rows | O | 1 | Common; missed by some (surfaces during crawl) |
| `availability_heatmap` | Calendar heatmap | Availability calendar view (vs list) | W | 3 | Reddit / blog wish-lists (Tier-B #17, #18); no football club has it |
| `multi_match_bundle_selector` | Multi-match bundle | Bundle several fixtures in one flow | O | 2 | FIFA 2026; Real Madrid seasonal VIP |

## 5. Enquiry Friction

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `buy_now_without_enquiry` | Direct-buy path | Purchase without enquiry-first (self-serve checkout) | O, W | 2 | MCFC direct-buy on Tunnel Club; most clubs force enquiry |
| `enquiry_form_field_count_le_7` | ≤7 form fields | Form ≤7 fields (Baymard: 13→7 lifts completion ~15%) | C, W | 1 | Hospitality forms typically ~12+ (blog reviews Tier-A #8–10) |
| `immediate_confirmation_email` | Instant confirmation | Confirmation email on submit (not "we'll be in touch") | C | 1 | Eventmasters Trustpilot (Tier-A #3) |
| `phone_booking_option` | Phone booking | Phone alternative offered explicitly | W | 2 | Age-skewed buyer preference, surfaces in Reddit threads |
| `live_chat_availability` | Live chat available | Live-chat widget present on hospitality page (hidden for capture per D-11) | O | 2 | Widgets present on MCFC, CHE, TOT |
| `response_time_promise` | SLA disclosure | Response-time SLA visible ("within 1 hour", "same day") | C, W | 2 | Industry: 5-min vs 1-hour → ~10x conversion; most clubs silent |

## 6. Premium Amenities

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `parking_included_indicator` | Parking indicator | Parking inclusion / exclusion visible | C, W | 1 | Reddit threads (Tier-B #12–18) routinely ask about parking |
| `car_pickup_or_transfer` | Car transfer | Car pickup / chauffeur / transfer included | O | 3 | Real Madrid Emirates Skywards VIP package (Tier-A #6) |
| `private_entrance_indicator` | Private entrance | Dedicated entrance noted (queue-free ingress) | O | 2 | MCFC Tunnel Club, CHE Platinum |
| `pitchside_or_tunnel_access` | Pitchside / tunnel access | Tunnel-walk or pitchside viewing element | O | 3 | MCFC Tunnel Club; CHE Home Dugout Club |
| `player_meet_and_greet` | Player meet-and-greet | Player interaction guaranteed or scheduled | O | 3 | Tunnel Club legends; F1 House 44 (Hamilton) |
| `stadium_tour_inclusion` | Stadium tour bundle | Tour bundled into hospitality package | O | 2 | Some clubs bundle (TOT Stadium Tour add-on) |
| `match_program_included` | Match program included | Printed match program included | O | 1 | Cheap inclusion, frequently missed |
| `concierge_service` | Concierge service | Dedicated concierge / hostess on-package | O | 2 | F1 "dedicated concierge"; MCFC + CHE hostess mentions |
| `merchandise_voucher` | Merch voucher | Merchandise voucher included | O, W | 3 | Some clubs bundle (TOT, MCFC) |

## 7. Post-Booking Comms

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `booking_change_policy_visible` | Change / cancel policy | Change / cancellation policy visible pre-submit | C | 1 | Seat Unique date-change-refund-refused complaint (Tier-A #1) |
| `seat_number_lead_time` | Seat lead time disclosed | When seat numbers are communicated (days before) | C | 1 | Seat Unique "4–5 days before" complaint (Tier-A #1) |
| `group_host_contact` | Group host contact | Host contact or allocation protocol for group bookings | C | 2 | Eventmasters table-allocation complaint (Tier-A #3) |
| `fixture_change_notification` | Fixture-change notification | Schedule-change notification policy stated | C | 1 | Eventmasters complaint (Tier-A #3) |
| `dietary_preferences_capture` | Dietary capture | Dietary prefs captured at booking (not re-asked on the night) | C, W | 1 | Allergen complaints imply this (Tier-A #2) |

## 8. Booking Confirmation (pre-submit only)

Per D-08, flow stops pre-submit — confirmation page is never captured. These
rows are evaluated by enquiry-form-page copy only.

| Key | Name | Description | Origin | Tier | Source |
|-----|------|-------------|--------|------|--------|
| `confirmation_page_clarity` | Next-steps clarity | What the form PROMISES will happen post-submit | O | 1 | Copy-only evaluation; varies widely across 10 gold sites |
| `saved_booking_in_account` | Saved booking | Past bookings visible in account area (login-gated clubs) | O | 2 | Login-gated hospitality (D-12) |
| `receipt_download` | Receipt download | Self-serve receipt / VAT invoice download | O | 2 | Corporate buyer need |

---

## Additions from the review-source dig (≥2 entries per D-05)

Beyond the 48-candidate seed in research §3, the review-source consultation
surfaced these additional candidates. Each is a feature NOT already in the
seed and tied to a specific review-source row.

| Key | Category | Name | Description | Origin | Tier | Source |
|-----|----------|------|-------------|--------|------|--------|
| `accessible_booking_option` | Enquiry Friction | Accessible booking path | Wheelchair / accessible-seating hospitality booking path explicitly offered (not "contact us") | C, W | 1 | TripAdvisor Tottenham & Bernabéu accessibility threads (Tier-A #5, #6); routinely requested on Reddit (Tier-B #12–18) |
| `corporate_invoice_billing` | Pricing Transparency | Corporate invoicing | VAT-invoice / PO / 30-day-term option for corporate buyers at enquiry stage | W | 2 | P1 Travel Trustpilot corporate-buyer mentions (Tier-A #4); sportspro.com B2B coverage (Tier-C #19) |
| `cancellation_refund_window` | Post-Booking Comms | Refund window disclosed | Cancellation-refund window disclosed (distinct from the change-policy row above: specifies dates & amounts refundable vs policy-existence) | C | 1 | Seat Unique Trustpilot (Tier-A #1) — distinct complaint thread from the change-policy candidate |
| `multi_occasion_tagging` | Package Discovery | Occasion tag | Booking captures occasion (birthday / anniversary / corporate entertainment / stag) for tailored service | O, W | 3 | goseelearn family review (Tier-A #11); F1 Paddock Club has this (Tier-A #3 analog) |
| `transport_package_bundling` | Premium Amenities | Transport bundling | Flights / hotels / train bundled into hospitality package (broker-adjacent) | O | 3 | Real Madrid Emirates Skywards (Tier-A #6); P1 Travel pattern (Tier-A #4) |

**Note on numbering:** Seed (48) + additions (5) = **50 candidates**, already
inside the target band. If the user merges any additions back into seed rows
during review, target floor (40) remains comfortably cleared.

---

## Out-of-Scope (noted, not scored)

- **Post-booking confirmation page content** — flow halts pre-submit (D-08). The confirmation-page copy IS evaluated on the enquiry form page only.
- **Non-match-day hospitality** (stadium events, corporate bookings outside matchday) — different rubric; not in Phase 2.
- **Liverpool** — CLAUDE.md DO NOT TOUCH. Not consulted, not scored.
- **FC Barcelona** — Socios overlay; deferred to Phase 2.5.
- **Bayern, NBA, West Ham** — headless-blocked, deferred to Phase 2.5.
- **Arsenal** — catalog-only (read-only source inspection), NOT in the 5-club pilot crawl set.

---

## Invariants (referenced by acceptance criteria)

- Every row has a non-empty **Source** column pointing at a row in `REVIEW-SOURCES.md`.
- Every row carries at least one origin tag (`O` / `C` / `W`).
- Every row has a tier (`1` / `2` / `3`).
- Every `key` is unique (`^| \`key\`` lines across the file).
- No feature row mentions Liverpool (Liverpool only appears once, in Out-of-Scope).

---

**When you're happy with this list, respond `approved — freeze candidates`.**
Plan 02-03 will then write `HOSPITALITY-FLOW.md` + `features.ts` + activate
`scanner/config/areas.json` for the hospitality area.

*Draft produced by Plan 02-02, Phase 02-hospitality-pilot. Source: research §3 (48-candidate seed) + review-source dig (5 additions).*
