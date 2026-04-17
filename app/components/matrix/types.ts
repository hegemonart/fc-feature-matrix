/* ================================================================
   app/components/matrix/types.ts

   Contract source of truth for all atomic matrix components shipped
   in plan infra-redesign-v2-02. Plans 03 (HoverTooltipCard) and 04
   (page.tsx refactor) import from here so the prop shapes are
   defined exactly once.

   See .planning/phases/infra-redesign-v2/CONTEXT.md
     D-10 — DataCell 8 visual states (selected x intermediate x state)
     D-11 — SortHeader 3 states (idle | asc | desc)
     D-06 — MeterRow band semantics preserved from lib/scoring.ts
     D-12 — HeaderBar consumes process.env.BUILD_DATE
     D-13 — TopNav + UnlockTab + locked-tab opacity
     D-14 — CategoryFilter sourced from analysis/homepage/features.ts
     D-15 — TypeFilter sourced from analysis/products.ts PRODUCTS[].type
   ================================================================ */

import type { CategoryId, ProductType } from '../../../analysis/types';

// Re-export ProductType so consumers can import it from this module
// rather than reaching into analysis/types.ts directly.
export type { ProductType } from '../../../analysis/types';
export type { CategoryId } from '../../../analysis/types';

// ── DataCell ────────────────────────────────────────────────────
// 8 visual combinations: selected (true|false) x intermediate (true|false) x state ('default'|'hover')
export type DataCellState = 'default' | 'hover';

export interface DataCellProps {
  selected: boolean;
  intermediate: boolean;
  state: DataCellState;
  featureId: string;
  clubId: string;
  value: boolean;
  onMouseEnter?: (e: React.MouseEvent<HTMLDivElement>) => void;
  onMouseLeave?: (e: React.MouseEvent<HTMLDivElement>) => void;
  onFocus?: (e: React.FocusEvent<HTMLDivElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLDivElement>) => void;
}

// ── SortHeader ──────────────────────────────────────────────────
export type SortState = 'idle' | 'asc' | 'desc';

export interface SortHeaderProps {
  label: string;
  state: SortState;
  onSort: () => void;
}

// ── MeterRow ────────────────────────────────────────────────────
// Band names mirror the four BandId values in analysis/types.ts but
// are restated here as a UI-facing label set so the component does
// not import scoring logic (D-06). Mapping:
//   competitive → --green
//   mid         → --yellow
//   weak        → --orange
//   bottom      → --red
export type MeterBand = 'competitive' | 'mid' | 'weak' | 'bottom';

export interface MeterRowProps {
  band: MeterBand;
  /** 0–100 percentage for the bar fill width */
  value: number;
  /** Optional override; if omitted, the component picks the band's CSS var. */
  meterColor?: string;
}

// ── HeaderBar ───────────────────────────────────────────────────
export interface HeaderBarProps {
  /** ISO date slice (YYYY-MM-DD) sourced from process.env.BUILD_DATE (D-12). */
  buildDate: string;
  /** When `true`, renders the Sign Out action (and Admin when `isAdmin`). */
  authed?: boolean;
  /** When `true` and `authed` is true, renders the Admin link. */
  isAdmin?: boolean;
  /** Click handler for the Sign Out button. Required when `authed` is true. */
  onSignOut?: () => void;
  /** Destination of the Admin link. Defaults to `/admin`. */
  adminHref?: string;
}

// ── TopNav ──────────────────────────────────────────────────────
export interface Tab {
  id: string;
  label: string;
}

export interface TopNavProps {
  tabs: Tab[];
  activeTab: string;
  onTabClick: (id: string) => void;
  /** Optional id of a tab that should render as the special <UnlockTab> variant. */
  unlockTab?: string;
  /** Ids of tabs that render at 60% opacity and route to the locked-content modal in the parent. */
  lockedTabs?: string[];
}

// ── CategoryFilter ──────────────────────────────────────────────
export interface CategoryItem {
  id: CategoryId;
  name: string;
  /** Number of features in this category — derived from analysis/homepage/features.ts in the parent. */
  count: number;
}

export interface CategoryFilterProps {
  categories: CategoryItem[];
  /** Set of category ids currently collapsed in the matrix view. */
  collapsed: Set<CategoryId>;
  onToggle: (id: CategoryId) => void;
}

// ── TypeFilter ──────────────────────────────────────────────────
export interface TypeFilterProps {
  selected: Set<ProductType>;
  onChange: (next: Set<ProductType>) => void;
}

// ── HoverTooltipCard (plan 03 — D-16, D-21) ─────────────────────
// The tooltip is portaled to document.body and positioned from the
// hovered cell's getBoundingClientRect() (RESEARCH.md P8 — anchored
// to cell, NOT cursor). Content is looked up in-memory from maps
// passed as props; no server requests on hover (D-21).

/**
 * Subset of `analysis/types.ts` Feature needed to render a tooltip
 * row. Pick is used so HoverTooltipProps stays decoupled from any
 * future scoring / band / presence fields added to Feature.
 */
export interface FeatureMeta {
  id: string;
  name: string;
  desc: string;
  /** TierId from analysis/types.ts (A–F). Rendered as "TIER:" badge. */
  tier: string;
  weightYes: number;
  weightNo: number;
}

/**
 * Subset of `analysis/types.ts` Product needed to render the club
 * name in the tooltip header.
 */
export interface ClubMeta {
  id: string;
  name: string;
}

/** Per-cell scoring breakdown (Yes +N / No −N). */
export interface CellScoring {
  yes: number;
  no: number;
}

/**
 * Tooltip state owned by `useHoverTooltip`. `anchorRect` is captured
 * from `cell.getBoundingClientRect()` at the moment of mouseenter;
 * the tooltip is positioned `top: rect.bottom + 8` / `left: rect.left`
 * with viewport-clamp logic in <HoverTooltipCard>.
 */
export type TooltipData = {
  featureId: string;
  clubId: string;
  anchorRect: DOMRect;
} | null;

export interface HoverTooltipProps {
  data: TooltipData;
  features: Map<string, FeatureMeta>;
  clubs: Map<string, ClubMeta>;
  /** Keyed by `${clubId}:${featureId}` for O(1) lookup. */
  scoring: Map<string, CellScoring>;
}
