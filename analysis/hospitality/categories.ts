/* ================================================================
   analysis/hospitality/categories.ts  --  Plan 02-21

   8 hospitality category sections used by the /hospitality matrix
   sidebar. CategoryIds are declared in analysis/types.ts; this file
   adds the human-readable name + accent color used by the
   <CategoryFilter> component.

   Mirrors analysis/homepage/categories.ts in shape so MatrixIsland
   can consume either array via the `categories` prop without
   special-casing.
   ================================================================ */

import type { Category } from '../types';

export const HOSPITALITY_CATEGORIES: Category[] = [
  { id: 'package_discovery',    name: 'Package Discovery',     color: '#06b6d4' },
  { id: 'pricing_transparency', name: 'Pricing Transparency',  color: '#8b5cf6' },
  { id: 'food_beverage',        name: 'Food & Beverage',       color: '#22c55e' },
  { id: 'match_selector_ux',    name: 'Match Selector UX',     color: '#3b82f6' },
  { id: 'enquiry_friction',     name: 'Enquiry Friction',      color: '#ef4444' },
  { id: 'premium_amenities',    name: 'Premium Amenities',     color: '#f97316' },
  { id: 'post_booking_comms',   name: 'Post-Booking Comms',    color: '#ec4899' },
  { id: 'booking_confirmation', name: 'Booking Confirmation',  color: '#a855f7' },
];
