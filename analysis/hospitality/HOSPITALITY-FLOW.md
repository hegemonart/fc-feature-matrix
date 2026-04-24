# Hospitality Flow — Scoring Rubric

**Version:** v1.0
**Date:** 24 April 2026
**Source:** `analysis/hospitality/FEATURES-CANDIDATES.md` (user-approved on 2026-04-24 — frozen per D-05 / D-06).
**Provenance log:** `analysis/hospitality/REVIEW-SOURCES.md`.
**Scope:** 5-club pilot (Manchester City, Tottenham Hotspur, Real Madrid, PSG, Chelsea); full rollout deferred to Phase 2.5.
**Categories:** 8 — Package Discovery, Pricing Transparency, Food & Beverage, Match Selector UX, Enquiry Friction, Premium Amenities, Post-Booking Comms, Booking Confirmation.

This rubric is the human-readable **source of truth** for hospitality scoring.
`analysis/hospitality/features.ts` is the machine-readable port — feature keys
map 1:1. Every row here traces to an approved candidate in
`FEATURES-CANDIDATES.md`; no row is introduced here that wasn't frozen by the
user. If a feature needs to be added, edit `FEATURES-CANDIDATES.md` first and
re-run plan 02-03.

---

## Scoring Convention

Each feature is scored on a closed presence scale: `absent | full`.

- `full` → the feature is clearly present and functional on the observed surface.
- `absent` → no evidence on any captured page.

(Rubric forward-compatibility: a `partial` state may be introduced in Phase 2.5
for features that are evidenced but under-specified, e.g. menu shown but no
allergen info. Front-half scoring stays binary.)

Tier weights mirror `analysis/homepage/features.ts` — asymmetric penalties
reflect the reality that missing a table-stakes feature hurts more than missing
a delight:

| Candidate Tier | TierId | weightYes | weightNo | Meaning |
|----------------|--------|-----------|----------|---------|
| 1 (table-stakes) | `A` | +1 | −3 | Every premium buyer expects this; absence is a penalty. |
| 2 (differentiator) | `C` | +5 | −2 | Presence lifts above peers; absence acceptable. |
| 3 (delight) | `D` | +8 | −1 | Rare; brand-forming. |

A club's hospitality score = sum of all feature weights (Yes weight when
present, No weight when absent). Scores can be negative if a club misses many
table-stakes features.

## Legend

- **Origin** — signal provenance (from FEATURES-CANDIDATES.md):
  - `O` = observed-on-site on one of the 10 gold-standard sites catalogued in `REVIEW-SOURCES.md §A`.
  - `C` = complained-about in user-review corpus (Trustpilot / TripAdvisor / Reddit).
  - `W` = wished-for in user-review corpus.
  - Multiple tags combine (`O, W` = observed AND wished-for).
- **Tier** — candidate-tier `1` / `2` / `3` (maps to TierId `A` / `C` / `D` per the table above).
- **Evidence/Notes** — condensed citation column linking back to the site or review row surfaced in `REVIEW-SOURCES.md`.

Ordering within each category: Tier 1 rows first, then Tier 2, then Tier 3;
inside each tier, stable in the input order from `FEATURES-CANDIDATES.md`.

---

## 1. Package Discovery

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `package_tier_list` | Package Tier List | Landing page lists all packages with distinguishing copy in one view. | 1 | O | All 10 gold sites; MCFC `/hospitality`; CHE `hospitality.chelseafc.com`. |
| `per_tier_landing_page` | Per-Tier Landing Page | Clicking a tier opens its own description landing page. | 1 | O | MCFC `/hospitality/the-tunnel-club-premier`. |
| `dress_code_info` | Dress-Code Info | Explicit per-tier dress code (smart, smart-casual, formal). | 1 | C | Seat Unique Trustpilot (Tier-A #1). |
| `tier_comparison_table` | Tier Comparison Table | Side-by-side feature matrix across tiers on a single page. | 2 | O | F1 Paddock Club (Tier-A #3). |
| `tier_capacity_indicator` | Tier Capacity Indicator | Min/max guests or per-box headcount visible. | 2 | O, W | F1 Legends Club; Seat Unique Trustpilot (Tier-A #1). |
| `upcoming_matches_pre_tier` | Upcoming Matches Pre-Tier | Package cards show which matches apply before tier-selection. | 2 | O | TOT `/matchday-options/`. |
| `multi_occasion_tagging` | Multi-Occasion Tagging | Booking captures occasion (birthday / anniversary / corporate / stag) for tailored service. | 3 | O, W | goseelearn family review (Tier-A #11); F1 Paddock Club analog. |

## 2. Pricing Transparency

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `price_per_person_visible` | Price Per Person Visible | Inc-VAT headline price on tier landing (not behind enquiry). | 1 | O, W | TOT £299/£449 visible; MCFC hides (Tier-A #5, r/coys). |
| `fixture_category_tiers` | Fixture Category Tiers | Match category pricing labels (Cat A/B/C) visible on selector. | 1 | O | EPL convention (MCFC, TOT, CHE). |
| `min_booking_unit` | Min Booking Unit | "Per seat" vs "per table of 10" vs "per box" plainly stated. | 1 | O, C | Seat Unique complaint pattern (Tier-A #1). |
| `price_range_by_match` | Price Range By Match | Low-high axis per tier (e.g. £269–£699 by opponent demand). | 2 | O | MCFC Tunnel Club listings. |
| `total_cost_preview_pre_submit` | Total Cost Preview Pre-Submit | Running total shown before enquiry submission. | 2 | W | Baymard-style wish; voiced across Tier-A blogs. |
| `deposit_vs_full_payment` | Deposit Vs Full Payment | Deposit vs full payment terms shown pre-enquiry. | 2 | C | Trustpilot surprise-terms complaints (Tier-A #1–3). |
| `corporate_invoice_billing` | Corporate Invoice Billing | VAT-invoice / PO / 30-day-term option for corporate buyers at enquiry stage. | 2 | W | P1 Travel Trustpilot (Tier-A #4); sportspro.com B2B (Tier-C #19). |
| `vat_inclusive_toggle` | VAT Inclusive Toggle | Switch between inc-VAT and ex-VAT for corporate buyers. | 3 | O | Some gold sites; F1 corporate flow. |

## 3. Food & Beverage

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `menu_preview` | Menu Preview | Representative menu shown on tier page (not "TBC"). | 1 | O, W | F1 3-course sample; MCFC Tunnel Club Premier "five-course". |
| `allergen_info` | Allergen Info | Allergen info available pre-booking (not only on the night). | 1 | C, W | Keith Prowse Trustpilot (Tier-A #2). |
| `vegetarian_options` | Vegetarian Options | Veggie / vegan option disclosure on menu preview. | 1 | C | Keith Prowse Trustpilot (Tier-A #2). |
| `bar_type_indicator` | Bar Type Indicator | Complimentary / cash / premium-only bar clearly indicated. | 1 | C | CHE Centenary cash-bar; TOT TripAdvisor "spirits at separate bar" (Tier-A #5, #7). |
| `chef_attribution` | Chef Attribution | Chef or restaurant partner explicitly credited. | 2 | O | F1 "renowned chefs"; MCFC "award-winning executive chefs". |
| `kids_menu` | Kids Menu | Explicit kids menu or child-friendly hospitality indicator. | 2 | W | goseelearn family review (Tier-A #11). |
| `meal_timing_visible` | Meal Timing Visible | Arrival / pre-match / post-match meal timing stated. | 2 | O | CHE Platinum "2.5h prior"; TOT "3h pre / 2h post". |
| `post_match_service` | Post-Match Service | What stays open after final whistle. | 2 | O | CHE Tambling "~1h after"; TOT "2h after final whistle". |

## 4. Match Selector UX

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `fixture_list_visible` | Fixture List Visible | Standard fixture list on match-selector step. | 1 | O | Standard across all 10 gold sites. |
| `competition_filter` | Competition Filter | PL / UCL / Cup filter on selector. | 1 | O | EPL + UCL clubs require this. |
| `sold_out_indicator` | Sold-Out Indicator | Explicit sold-out state on fixture rows. | 1 | O | Common; missed by some (surfaces during crawl). |
| `multi_match_bundle_selector` | Multi-Match Bundle Selector | Bundle several fixtures in one flow. | 2 | O | FIFA 2026; Real Madrid seasonal VIP. |
| `opponent_filter` | Opponent Filter | Search / filter by opponent. | 3 | O | F1 has via circuit; rare in football. |
| `availability_heatmap` | Availability Heatmap | Availability calendar view (vs list). | 3 | W | Reddit / blog wish-lists (Tier-B #17, #18); no football club has it. |

## 5. Enquiry Friction

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `enquiry_form_field_count_le_7` | Enquiry Form Field Count ≤ 7 | Form ≤ 7 fields (Baymard: 13→7 lifts completion ~15%). | 1 | C, W | Hospitality forms typically ~12+ (Tier-A blog reviews #8–10). |
| `immediate_confirmation_email` | Immediate Confirmation Email | Confirmation email on submit (not "we'll be in touch"). | 1 | C | Eventmasters Trustpilot (Tier-A #3). |
| `accessible_booking_option` | Accessible Booking Option | Wheelchair / accessible-seating hospitality booking path explicitly offered (not "contact us"). | 1 | C, W | TripAdvisor Tottenham & Bernabéu (Tier-A #5, #6); Reddit (Tier-B #12–18). |
| `buy_now_without_enquiry` | Buy Now Without Enquiry | Purchase without enquiry-first (self-serve checkout). | 2 | O, W | MCFC direct-buy on Tunnel Club; most clubs force enquiry. |
| `phone_booking_option` | Phone Booking Option | Phone alternative offered explicitly. | 2 | W | Age-skewed buyer preference, surfaces in Reddit threads. |
| `live_chat_availability` | Live Chat Availability | Live-chat widget present on hospitality page (hidden for capture per D-11). | 2 | O | Widgets present on MCFC, CHE, TOT. |
| `response_time_promise` | Response Time Promise | SLA visible ("within 1 hour", "same day"). | 2 | C, W | Industry: 5-min vs 1-hour → ~10× conversion; most clubs silent. |

## 6. Premium Amenities

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `parking_included_indicator` | Parking Included Indicator | Parking inclusion / exclusion visible. | 1 | C, W | Reddit threads (Tier-B #12–18) routinely ask about parking. |
| `match_program_included` | Match Program Included | Printed match program included. | 1 | O | Cheap inclusion, frequently missed. |
| `private_entrance_indicator` | Private Entrance Indicator | Dedicated entrance noted (queue-free ingress). | 2 | O | MCFC Tunnel Club; CHE Platinum. |
| `stadium_tour_inclusion` | Stadium Tour Inclusion | Tour bundled into hospitality package. | 2 | O | Some clubs bundle (TOT Stadium Tour add-on). |
| `concierge_service` | Concierge Service | Dedicated concierge / hostess on-package. | 2 | O | F1 "dedicated concierge"; MCFC + CHE hostess mentions. |
| `car_pickup_or_transfer` | Car Pickup Or Transfer | Car pickup / chauffeur / transfer included. | 3 | O | Real Madrid Emirates Skywards VIP package (Tier-A #6). |
| `pitchside_or_tunnel_access` | Pitchside Or Tunnel Access | Tunnel-walk or pitchside viewing element. | 3 | O | MCFC Tunnel Club; CHE Home Dugout Club. |
| `player_meet_and_greet` | Player Meet And Greet | Player interaction guaranteed or scheduled. | 3 | O | Tunnel Club legends; F1 House 44 (Hamilton). |
| `merchandise_voucher` | Merchandise Voucher | Merchandise voucher included. | 3 | O, W | Some clubs bundle (TOT, MCFC). |
| `transport_package_bundling` | Transport Package Bundling | Flights / hotels / train bundled into hospitality package (broker-adjacent). | 3 | O | Real Madrid Emirates Skywards (Tier-A #6); P1 Travel pattern (Tier-A #4). |

## 7. Post-Booking Comms

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `booking_change_policy_visible` | Booking Change Policy Visible | Change / cancellation policy visible pre-submit. | 1 | C | Seat Unique date-change-refund-refused complaint (Tier-A #1). |
| `seat_number_lead_time` | Seat Number Lead Time | When seat numbers are communicated (days before). | 1 | C | Seat Unique "4–5 days before" complaint (Tier-A #1). |
| `fixture_change_notification` | Fixture Change Notification | Schedule-change notification policy stated. | 1 | C | Eventmasters complaint (Tier-A #3). |
| `dietary_preferences_capture` | Dietary Preferences Capture | Dietary prefs captured at booking (not re-asked on the night). | 1 | C, W | Allergen complaints imply this (Tier-A #2). |
| `cancellation_refund_window` | Cancellation Refund Window | Cancellation-refund window disclosed (dates & amounts refundable vs policy-existence). | 1 | C | Seat Unique Trustpilot (Tier-A #1) — distinct from change-policy row. |
| `group_host_contact` | Group Host Contact | Host contact or allocation protocol for group bookings. | 2 | C | Eventmasters table-allocation complaint (Tier-A #3). |

## 8. Booking Confirmation

Per D-08, flow stops **pre-submit** — the confirmation page is never captured.
These rows are evaluated by enquiry-form-page copy only.

| Feature Key | Name | Description | Tier | Origin | Evidence/Notes |
|-------------|------|-------------|------|--------|----------------|
| `confirmation_page_clarity` | Confirmation Page Clarity | What the form PROMISES will happen post-submit (copy-only). | 1 | O | Varies widely across 10 gold sites. |
| `saved_booking_in_account` | Saved Booking In Account | Past bookings visible in account area (login-gated clubs). | 2 | O | Login-gated hospitality (D-12). |
| `receipt_download` | Receipt Download | Self-serve receipt / VAT invoice download. | 2 | O | Corporate buyer need. |

---

## Feature Count

| Category | Tier 1 | Tier 2 | Tier 3 | Total |
|----------|-------:|-------:|-------:|------:|
| 1. Package Discovery | 3 | 3 | 1 | 7 |
| 2. Pricing Transparency | 3 | 4 | 1 | 8 |
| 3. Food & Beverage | 4 | 4 | 0 | 8 |
| 4. Match Selector UX | 3 | 1 | 2 | 6 |
| 5. Enquiry Friction | 3 | 4 | 0 | 7 |
| 6. Premium Amenities | 2 | 3 | 5 | 10 |
| 7. Post-Booking Comms | 5 | 1 | 0 | 6 |
| 8. Booking Confirmation | 1 | 2 | 0 | 3 |
| **Total** | **24** | **22** | **9** | **55** |

Tier weights (cross-check against the scoring-convention table above):
- Tier 1 → TierId `A`, weightYes +1, weightNo −3
- Tier 2 → TierId `C`, weightYes +5, weightNo −2
- Tier 3 → TierId `D`, weightYes +8, weightNo −1

**Reconciliation with candidate file:** `FEATURES-CANDIDATES.md` contains 55
unique feature keys (50 seed candidates + 5 extensions from the review-source
dig). This rubric exposes exactly those 55 keys as scored rows. 1:1 port; no
key renamed, no key dropped, no key added. The candidate file's own header
text states "Total candidates: 50" (seed), then adds 5 extensions elsewhere —
combined, 55. The rubric source-of-truth is the table rows.

---

## Provenance

Every feature key in this rubric traces back to a row in
`analysis/hospitality/FEATURES-CANDIDATES.md` with a matching `Feature Key`.
Cross-check command:

```sh
comm -23 \
  <(grep -oE "\`[a-z_]+\`" analysis/hospitality/HOSPITALITY-FLOW.md | sort -u) \
  <(grep -oE "\`[a-z_]+\`" analysis/hospitality/FEATURES-CANDIDATES.md | sort -u)
```

Prints ZERO lines when every rubric key is anchored in the frozen candidate
list. If the command emits anything, the rubric has drifted and the offending
key must be removed or the candidate file must be re-opened for amendment
(re-run plan 02-03 after user approval).

---

## Out-of-Scope

Mirrors `FEATURES-CANDIDATES.md`:

- **Post-booking confirmation page content** — flow halts pre-submit (D-08). Confirmation-page copy IS evaluated on the enquiry form page only.
- **Non-match-day hospitality** (stadium events, corporate bookings outside matchday) — different rubric; not in Phase 2.
- **FC Barcelona** — Socios overlay; deferred to Phase 2.5.
- **Bayern, NBA, West Ham** — headless-blocked, deferred to Phase 2.5.
- **Arsenal** — catalog-only (read-only source inspection); NOT in the 5-club pilot crawl set.

---

*Authored by Plan 02-03 from the user-frozen candidate list. Paired with
`analysis/hospitality/features.ts` (machine-readable port) and registered in
`scanner/config/areas.json` for the scanner pipeline.*
