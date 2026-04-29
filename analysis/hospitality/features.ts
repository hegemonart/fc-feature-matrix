/* ================================================================
   analysis/hospitality/features.ts  --  Phase 2 front-half
   55 hospitality features sourced from analysis/hospitality/HOSPITALITY-FLOW.md.

   Presence maps are empty (all 'absent') until Phase 2 back-half writes
   results JSON files to analysis/hospitality/results/. The scanner
   pipeline registered in scanner/config/areas.json will populate those
   JSONs during capture + vision; this module picks them up thereafter.

   Tier → weight convention (mirrors analysis/homepage/features.ts):
     Tier 1 (table-stakes)   → TierId 'A', weightYes=+1, weightNo=-3
     Tier 2 (differentiator) → TierId 'C', weightYes=+5, weightNo=-2
     Tier 3 (delight)        → TierId 'D', weightYes=+8, weightNo=-1

   ID scheme: HP01..HP55 in rubric order (Package Discovery → Booking
   Confirmation; Tier 1 first then Tier 2 then Tier 3 inside each
   category). `HP` prefix distinguishes from homepage IDs (H/R/M/C/T/...).
   ================================================================ */

import type { Feature, CategoryId, TierId, PresenceStatus, DetectionMode } from '../types';
import { ALL_IDS } from '../products';

// ── Phase 2 back-half: pilot results JSON imports (Plan 02-12 outputs) ──
// JSON `product_id` slugs (mancity, realmadrid) differ from products.ts
// canonical IDs (man_city, real_madrid). The PILOT_RESULTS map below is
// keyed by the products.ts canonical ID so buildPresence can look up
// against ALL_IDS directly.
import mancity from './results/mancity.json';
import tottenham from './results/tottenham.json';
import realmadrid from './results/realmadrid.json';
import psg from './results/psg.json';
import chelsea from './results/chelsea.json';

const PILOT_RESULTS: Record<string, Record<string, boolean>> = {
  man_city: mancity.features,
  tottenham: tottenham.features,
  real_madrid: realmadrid.features,
  psg: psg.features,
  chelsea: chelsea.features,
};

/** Build a presence map for a given feature key.
 *
 * Phase 2 back-half (Plan 02-13): reads from analysis/hospitality/results/*.json
 * for the 5 pilot clubs (Man City, Tottenham, Real Madrid, PSG, Chelsea).
 * Non-pilot product IDs stay 'absent' until Phase 2.5 expands coverage.
 * Mirrors the analysis/homepage/features.ts buildPresence pattern.
 */
function buildPresence(featureKey: string): Record<string, PresenceStatus> {
  const m: Record<string, PresenceStatus> = {};
  ALL_IDS.forEach(id => {
    m[id] = PILOT_RESULTS[id]?.[featureKey] === true ? 'full' : 'absent';
  });
  return m;
}

/** Helper to define a feature concisely.
 *
 * Plan 02-15 Wave D: `detection` defaults to `'visual'` so legacy callers
 * keep producing the same Feature shape. Hospitality features always pass
 * an explicit detection tag (matches HOSPITALITY-FLOW.md Detection column).
 */
function feat(
  id: string,
  key: string,
  name: string,
  desc: string,
  cat: CategoryId,
  tier: TierId,
  weightYes: number,
  weightNo: number,
  detection: DetectionMode = 'visual',
): Feature {
  return {
    id,
    key,
    name,
    desc,
    cat,
    tier,
    weightYes,
    weightNo,
    weight: weightYes,   // backward compat with legacy consumers
    presence: buildPresence(key),
    detection,
  };
}

// ================================================================
//  55 FEATURES — organized by HOSPITALITY-FLOW.md sections
// ================================================================

export const FEATURES: Feature[] = [
  // ── 1. Package Discovery ──
  feat('HP01', 'package_tier_list', 'Package Tier List',
    'Landing page lists all packages with distinguishing copy in one view',
    'package_discovery', 'A', 1, -3, 'hybrid'),
  feat('HP02', 'per_tier_landing_page', 'Per-Tier Landing Page',
    'Clicking a tier opens its own description landing page',
    'package_discovery', 'A', 1, -3, 'visual'),
  feat('HP03', 'dress_code_info', 'Dress-Code Info',
    'Explicit per-tier dress code (smart, smart-casual, formal)',
    'package_discovery', 'A', 1, -3, 'dom'),
  feat('HP04', 'tier_comparison_table', 'Tier Comparison Table',
    'Side-by-side feature matrix across tiers on a single page',
    'package_discovery', 'C', 5, -2, 'dom'),
  feat('HP05', 'tier_capacity_indicator', 'Tier Capacity Indicator',
    'Min/max guests or per-box headcount visible',
    'package_discovery', 'C', 5, -2, 'hybrid'),
  feat('HP06', 'upcoming_matches_pre_tier', 'Upcoming Matches Pre-Tier',
    'Package cards show which matches apply before tier-selection',
    'package_discovery', 'C', 5, -2, 'hybrid'),
  feat('HP07', 'multi_occasion_tagging', 'Multi-Occasion Tagging',
    'Booking captures occasion (birthday / anniversary / corporate / stag) for tailored service',
    'package_discovery', 'D', 8, -1, 'dom'),

  // ── 2. Pricing Transparency ──
  feat('HP08', 'price_per_person_visible', 'Price Per Person Visible',
    'Inc-VAT headline price on tier landing (not behind enquiry)',
    'pricing_transparency', 'A', 1, -3, 'hybrid'),
  feat('HP09', 'fixture_category_tiers', 'Fixture Category Tiers',
    'Match category pricing labels (Cat A/B/C) visible on selector',
    'pricing_transparency', 'A', 1, -3, 'dom'),
  feat('HP10', 'min_booking_unit', 'Min Booking Unit',
    'Per-seat vs per-table-of-10 vs per-box plainly stated',
    'pricing_transparency', 'A', 1, -3, 'hybrid'),
  feat('HP11', 'price_range_by_match', 'Price Range By Match',
    'Low-high axis per tier by opponent demand (e.g. £269–£699)',
    'pricing_transparency', 'C', 5, -2, 'dom'),
  feat('HP12', 'total_cost_preview_pre_submit', 'Total Cost Preview Pre-Submit',
    'Running total shown before enquiry submission',
    'pricing_transparency', 'C', 5, -2, 'hybrid'),
  feat('HP13', 'deposit_vs_full_payment', 'Deposit Vs Full Payment',
    'Deposit vs full payment terms shown pre-enquiry',
    'pricing_transparency', 'C', 5, -2, 'dom'),
  feat('HP14', 'corporate_invoice_billing', 'Corporate Invoice Billing',
    'VAT-invoice / PO / 30-day-term option for corporate buyers at enquiry stage',
    'pricing_transparency', 'C', 5, -2, 'dom'),
  feat('HP15', 'vat_inclusive_toggle', 'VAT Inclusive Toggle',
    'Switch between inc-VAT and ex-VAT for corporate buyers',
    'pricing_transparency', 'D', 8, -1, 'dom'),

  // ── 3. Food & Beverage ──
  feat('HP16', 'menu_preview', 'Menu Preview',
    'Representative menu shown on tier page (not "TBC")',
    'food_beverage', 'A', 1, -3, 'hybrid'),
  feat('HP17', 'allergen_info', 'Allergen Info',
    'Allergen info available pre-booking (not only on the night)',
    'food_beverage', 'A', 1, -3, 'dom'),
  feat('HP18', 'vegetarian_options', 'Vegetarian Options',
    'Veggie / vegan option disclosure on menu preview',
    'food_beverage', 'A', 1, -3, 'dom'),
  feat('HP19', 'bar_type_indicator', 'Bar Type Indicator',
    'Complimentary / cash / premium-only bar clearly indicated',
    'food_beverage', 'A', 1, -3, 'dom'),
  feat('HP20', 'chef_attribution', 'Chef Attribution',
    'Chef or restaurant partner explicitly credited',
    'food_beverage', 'C', 5, -2, 'dom'),
  feat('HP21', 'kids_menu', 'Kids Menu',
    'Explicit kids menu or child-friendly hospitality indicator',
    'food_beverage', 'C', 5, -2, 'dom'),
  feat('HP22', 'meal_timing_visible', 'Meal Timing Visible',
    'Arrival / pre-match / post-match meal timing stated',
    'food_beverage', 'C', 5, -2, 'dom'),
  feat('HP23', 'post_match_service', 'Post-Match Service',
    'What stays open after final whistle',
    'food_beverage', 'C', 5, -2, 'dom'),

  // ── 4. Match Selector UX ──
  feat('HP24', 'fixture_list_visible', 'Fixture List Visible',
    'Standard fixture list on match-selector step',
    'match_selector_ux', 'A', 1, -3, 'hybrid'),
  feat('HP25', 'competition_filter', 'Competition Filter',
    'PL / UCL / Cup filter on selector',
    'match_selector_ux', 'A', 1, -3, 'dom'),
  feat('HP26', 'sold_out_indicator', 'Sold-Out Indicator',
    'Explicit sold-out state on fixture rows',
    'match_selector_ux', 'A', 1, -3, 'hybrid'),
  feat('HP27', 'multi_match_bundle_selector', 'Multi-Match Bundle Selector',
    'Bundle several fixtures in one flow',
    'match_selector_ux', 'C', 5, -2, 'hybrid'),
  feat('HP28', 'opponent_filter', 'Opponent Filter',
    'Search / filter by opponent',
    'match_selector_ux', 'D', 8, -1, 'dom'),
  feat('HP29', 'availability_heatmap', 'Availability Heatmap',
    'Availability calendar view (vs list)',
    'match_selector_ux', 'D', 8, -1, 'visual'),

  // ── 5. Enquiry Friction ──
  feat('HP30', 'enquiry_form_field_count_le_7', 'Enquiry Form Field Count ≤ 7',
    'Form ≤ 7 fields (Baymard: 13→7 lifts completion ~15%)',
    'enquiry_friction', 'A', 1, -3, 'dom'),
  feat('HP31', 'immediate_confirmation_email', 'Immediate Confirmation Email',
    'Confirmation email on submit (not "we\'ll be in touch")',
    'enquiry_friction', 'A', 1, -3, 'dom'),
  feat('HP32', 'accessible_booking_option', 'Accessible Booking Option',
    'Wheelchair / accessible-seating hospitality booking path explicitly offered (not "contact us")',
    'enquiry_friction', 'A', 1, -3, 'dom'),
  feat('HP33', 'buy_now_without_enquiry', 'Buy Now Without Enquiry',
    'Purchase without enquiry-first (self-serve checkout)',
    'enquiry_friction', 'C', 5, -2, 'dom'),
  feat('HP34', 'phone_booking_option', 'Phone Booking Option',
    'Phone alternative offered explicitly',
    'enquiry_friction', 'C', 5, -2, 'hybrid'),
  feat('HP35', 'live_chat_availability', 'Live Chat Availability',
    'Live-chat widget present on hospitality page (hidden for capture per D-11)',
    'enquiry_friction', 'C', 5, -2, 'hybrid'),
  feat('HP36', 'response_time_promise', 'Response Time Promise',
    'SLA visible (within 1 hour, same day)',
    'enquiry_friction', 'C', 5, -2, 'dom'),

  // ── 6. Premium Amenities ──
  feat('HP37', 'parking_included_indicator', 'Parking Included Indicator',
    'Parking inclusion / exclusion visible',
    'premium_amenities', 'A', 1, -3, 'dom'),
  feat('HP38', 'match_program_included', 'Match Program Included',
    'Printed match program included',
    'premium_amenities', 'A', 1, -3, 'dom'),
  feat('HP39', 'private_entrance_indicator', 'Private Entrance Indicator',
    'Dedicated entrance noted (queue-free ingress)',
    'premium_amenities', 'C', 5, -2, 'hybrid'),
  feat('HP40', 'stadium_tour_inclusion', 'Stadium Tour Inclusion',
    'Tour bundled into hospitality package',
    'premium_amenities', 'C', 5, -2, 'hybrid'),
  feat('HP41', 'concierge_service', 'Concierge Service',
    'Dedicated concierge / hostess on-package',
    'premium_amenities', 'C', 5, -2, 'hybrid'),
  feat('HP42', 'car_pickup_or_transfer', 'Car Pickup Or Transfer',
    'Car pickup / chauffeur / transfer included',
    'premium_amenities', 'D', 8, -1, 'dom'),
  feat('HP43', 'pitchside_or_tunnel_access', 'Pitchside Or Tunnel Access',
    'Tunnel-walk or pitchside viewing element',
    'premium_amenities', 'D', 8, -1, 'hybrid'),
  feat('HP44', 'player_meet_and_greet', 'Player Meet And Greet',
    'Player interaction guaranteed or scheduled',
    'premium_amenities', 'D', 8, -1, 'hybrid'),
  feat('HP45', 'merchandise_voucher', 'Merchandise Voucher',
    'Merchandise voucher included',
    'premium_amenities', 'D', 8, -1, 'dom'),
  feat('HP46', 'transport_package_bundling', 'Transport Package Bundling',
    'Flights / hotels / train bundled into hospitality package (broker-adjacent)',
    'premium_amenities', 'D', 8, -1, 'dom'),

  // ── 7. Post-Booking Comms ──
  feat('HP47', 'booking_change_policy_visible', 'Booking Change Policy Visible',
    'Change / cancellation policy visible pre-submit',
    'post_booking_comms', 'A', 1, -3, 'dom'),
  feat('HP48', 'seat_number_lead_time', 'Seat Number Lead Time',
    'When seat numbers are communicated (days before)',
    'post_booking_comms', 'A', 1, -3, 'dom'),
  feat('HP49', 'fixture_change_notification', 'Fixture Change Notification',
    'Schedule-change notification policy stated',
    'post_booking_comms', 'A', 1, -3, 'dom'),
  feat('HP50', 'dietary_preferences_capture', 'Dietary Preferences Capture',
    'Dietary prefs captured at booking (not re-asked on the night)',
    'post_booking_comms', 'A', 1, -3, 'dom'),
  feat('HP51', 'cancellation_refund_window', 'Cancellation Refund Window',
    'Cancellation-refund window disclosed (dates & amounts refundable vs policy-existence)',
    'post_booking_comms', 'A', 1, -3, 'dom'),
  feat('HP52', 'group_host_contact', 'Group Host Contact',
    'Host contact or allocation protocol for group bookings',
    'post_booking_comms', 'C', 5, -2, 'dom'),

  // ── 8. Booking Confirmation ──
  feat('HP53', 'confirmation_page_clarity', 'Confirmation Page Clarity',
    'What the form PROMISES will happen post-submit (copy-only evaluation)',
    'booking_confirmation', 'A', 1, -3, 'hybrid'),
  feat('HP54', 'saved_booking_in_account', 'Saved Booking In Account',
    'Past bookings visible in account area (login-gated clubs)',
    'booking_confirmation', 'C', 5, -2, 'visual'),
  feat('HP55', 'receipt_download', 'Receipt Download',
    'Self-serve receipt / VAT invoice download',
    'booking_confirmation', 'C', 5, -2, 'dom'),
];
