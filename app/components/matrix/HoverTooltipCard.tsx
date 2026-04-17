/* ================================================================
   <HoverTooltipCard>

   Per D-16 / RESEARCH.md P8:
     - Renders via createPortal(node, document.body) to escape any
       overflow: hidden on the matrix grid.
     - Anchored to the hovered cell — position computed from the
       captured anchorRect (cell.getBoundingClientRect()), NOT from
       cursor coordinates. This is a behavioral change from the
       legacy `cell-tooltip` cursor-follow tooltip.
     - Closes on mouseleave after a 100ms grace period (handled by
       useHoverTooltip; this component is purely presentational).

   Content (D-16 / D-21):
     - Club name (top, body-S)
     - Feature description (body-XS, muted)
     - "TIER:" badge (.mono-caption)
     - Yes +N / No −N scoring breakdown (.mono-caption)

   Position:
     - `top: anchorRect.bottom + 8`
     - `left: anchorRect.left`
     - Viewport-clamped on the right edge so a tooltip near the
       right of the screen shifts left rather than overflowing.

   The component is SSR-safe: the portal target is read at render
   time and guarded for `typeof document !== 'undefined'`.
   ================================================================ */

import * as React from 'react';
import { createPortal } from 'react-dom';
import styles from './HoverTooltipCard.module.css';
import type { HoverTooltipProps } from './types';

/** Tooltip width budget — kept in sync with the CSS max-width. */
const TOOLTIP_MAX_WIDTH = 320;
/** Distance below the anchor cell. */
const ANCHOR_GAP_PX = 8;
/** Right-edge breathing room when clamping. */
const VIEWPORT_PAD_PX = 8;

function computePosition(rect: DOMRect): { top: number; left: number } {
  const top = rect.bottom + ANCHOR_GAP_PX;
  let left = rect.left;
  if (typeof window !== 'undefined') {
    const maxLeft = window.innerWidth - TOOLTIP_MAX_WIDTH - VIEWPORT_PAD_PX;
    if (left > maxLeft) left = Math.max(VIEWPORT_PAD_PX, maxLeft);
  }
  return { top, left };
}

export function HoverTooltipCard({ data, features, clubs, scoring }: HoverTooltipProps) {
  // SSR safety — `document` only exists in the browser.
  if (typeof document === 'undefined') return null;
  if (!data) return null;

  const { featureId, clubId, anchorRect } = data;
  const feature = features.get(featureId);
  const club = clubs.get(clubId);
  const score = scoring.get(`${clubId}:${featureId}`);

  // Defensive: if any lookup misses, render nothing rather than a
  // broken card. Plan 04 should guarantee the maps are complete.
  if (!feature || !club || !score) return null;

  const { top, left } = computePosition(anchorRect);

  const node = (
    <div
      role="tooltip"
      data-testid="hover-tooltip-card"
      className={styles.card}
      style={{ top, left }}
    >
      <div className={styles.clubName}>{club.name}</div>
      <div className={styles.description}>{feature.desc}</div>
      <div className={styles.metaRow}>
        <span className={`${styles.tierBadge} mono-caption`}>
          TIER: {feature.tier}
        </span>
        <span className={`${styles.scoreBreakdown} mono-caption`}>
          <span className={styles.scoreYes}>Yes +{score.yes}</span>
          <span className={styles.scoreSep}>/</span>
          <span className={styles.scoreNo}>No −{score.no}</span>
        </span>
      </div>
    </div>
  );

  return createPortal(node, document.body);
}

export default HoverTooltipCard;
