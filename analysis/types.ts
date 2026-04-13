/* ================================================================
   analysis/types.ts  --  Shared type definitions
   ================================================================ */

export type PresenceStatus = 'full' | 'absent';

export type CategoryId = 'revenue' | 'content' | 'brand' | 'ux' | 'diff';

export type BandId = 'table_stakes' | 'expected' | 'competitive' | 'innovation';

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
  name: string;
  desc: string;
  cat: CategoryId;
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
