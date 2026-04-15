/* ================================================================
   analysis/types.ts  --  Shared type definitions
   ================================================================ */

export type PresenceStatus = 'full' | 'absent';

export type CategoryId =
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
  | 'footer_nav';

export type BandId = 'table_stakes' | 'expected' | 'competitive' | 'innovation';

export type TierId = 'A' | 'B' | 'C' | 'D' | 'E' | 'F';

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
}

export interface BandMeta {
  id: BandId;
  name: string;
  cls: string;
}
