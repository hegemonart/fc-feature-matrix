/* ================================================================
   analysis/types.ts  --  Shared type definitions
   ================================================================ */

export type PresenceStatus = 'full' | 'absent';

export type CategoryId =
  // ── Homepage categories (analysis/homepage/) ──
  | 'header_nav'
  | 'hero'
  | 'match_fixtures'
  | 'content'
  | 'tickets_hospitality'
  | 'commerce'
  | 'community'
  | 'heritage'
  | 'players_teams'
  | 'partners_sponsors'
  | 'personalization'
  | 'footer_nav'
  // ── Hospitality categories (analysis/hospitality/) — Phase 2 ──
  | 'package_discovery'
  | 'pricing_transparency'
  | 'food_beverage'
  | 'match_selector_ux'
  | 'enquiry_friction'
  | 'premium_amenities'
  | 'post_booking_comms'
  | 'booking_confirmation';

export type BandId = 'table_stakes' | 'expected' | 'competitive' | 'innovation';

export type TierId = 'A' | 'B' | 'C' | 'D' | 'E' | 'F';

/**
 * Plan 02-15 Wave D — detection-mode tag for hybrid DOM+vision routing.
 *
 * - `dom`    Programmatic DOM detection only (e.g. count form inputs).
 * - `visual` Vision-judge only (e.g. hero-image impactfulness).
 * - `hybrid` DOM rule first; vision fallback if DOM is inconclusive.
 *
 * Defaults to `'visual'` on Feature objects so the homepage rubric
 * (which never declared this) keeps validating unchanged.
 */
export type DetectionMode = 'dom' | 'visual' | 'hybrid';

export type ProductType = 'club' | 'league' | 'governing';

export type SportType = 'football' | 'motorsport' | 'basketball' | 'baseball' | 'tennis';

export interface Category {
  id: CategoryId;
  name: string;
  color: string;
}

export interface Product {
  id: string;
  name: string;
  type: ProductType;
  sport: SportType;
  logo: string;
  darkLogo?: boolean;
}

export interface Feature {
  id: string;
  key: string;
  name: string;
  desc: string;
  cat: CategoryId;
  tier: TierId;
  weightYes: number;
  weightNo: number;
  weight: number;
  presence: Record<string, PresenceStatus>;
  /** Computed by computeBands() */
  adoption?: number;
  /** Computed by computeBands() */
  adoptionPct?: number;
  /** Computed by computeBands() */
  band?: BandId;
  /**
   * Plan 02-15 Wave D — scanner detection-mode hint.
   * Optional and defaults to `'visual'` for back-compat with homepage features
   * (which never declared this). Hospitality features set this explicitly.
   */
  detection?: DetectionMode;
}

export interface BandMeta {
  id: BandId;
  name: string;
  cls: string;
}
