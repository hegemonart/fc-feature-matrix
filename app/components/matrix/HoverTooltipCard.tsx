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
/** Distance from the anchor cell. */
const ANCHOR_GAP_PX = 8;
/** Right-edge breathing room when clamping. */
const VIEWPORT_PAD_PX = 8;
/**
 * If fewer than this many px remain below the anchor cell, flip the tooltip
 * above. 260px covers the text-only card comfortably; screenshots extend
 * further but are still partially visible and scrollable.
 */
const FLIP_THRESHOLD_PX = 260;

function computePosition(rect: DOMRect): { top: number; left: number; flipUp: boolean } {
  if (typeof window === 'undefined') return { top: rect.bottom + ANCHOR_GAP_PX, left: rect.left, flipUp: false };

  const spaceBelow = window.innerHeight - rect.bottom;
  const flipUp = spaceBelow < FLIP_THRESHOLD_PX && rect.top > spaceBelow;

  // When flipping up: anchor to rect.top and translate upward in CSS.
  // When normal: anchor to rect.bottom.
  const top = flipUp
    ? rect.top - ANCHOR_GAP_PX
    : rect.bottom + ANCHOR_GAP_PX;

  let left = rect.left;
  const maxLeft = window.innerWidth - TOOLTIP_MAX_WIDTH - VIEWPORT_PAD_PX;
  if (left > maxLeft) left = Math.max(VIEWPORT_PAD_PX, maxLeft);

  return { top, left, flipUp };
}

export function HoverTooltipCard({ data, features, clubs, scoring, area = 'homepage' }: HoverTooltipProps) {
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

  const { top, left, flipUp } = computePosition(anchorRect);

  const node = (
    <div
      role="tooltip"
      data-testid="hover-tooltip-card"
      className={styles.card}
      style={{
        top,
        left,
        backdropFilter: 'blur(28px) saturate(200%) brightness(1.6)',
        ...(flipUp ? { transform: 'translateY(-100%)' } : {}),
      }}
    >
      <div className={styles.clubName}>{club.name}</div>
      <div className={styles.description}>{feature.desc}</div>
      <div className={styles.metaRow}>
        <span className={`${styles.tierBadge} mono-caption`}>
          TIER: {feature.tier}
        </span>
        <span className={`${styles.scoreBreakdown} mono-caption`}>
          <span className={styles.scoreYes}>Yes +{Math.abs(score.yes)}</span>
          <span className={styles.scoreSep}>/</span>
          <span className={styles.scoreNo}>No −{Math.abs(score.no)}</span>
        </span>
      </div>
      {data.value && area === 'homepage' && (() => {
        const src = `/api/crosscheck-img?area=${area}&file=${clubId}_${feature.key}.png`;
        return (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            key={src}
            className={styles.screenshot}
            src={src}
            alt={`${club.name} — ${feature.name}`}
            loading="eager"
            onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = 'none'; }}
          />
        );
      })()}
    </div>
  );

  // Portal into .matrix-shell so the tooltip shares the same compositing
  // layer as the matrix content — required for backdrop-filter to blur through.
  const portalTarget =
    typeof document !== 'undefined'
      ? (document.querySelector('.matrix-shell') ?? document.body)
      : null;
  if (!portalTarget) return null;
  return createPortal(node, portalTarget);
}

export default HoverTooltipCard;
