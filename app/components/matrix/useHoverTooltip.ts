/* ================================================================
   useHoverTooltip

   Owns the tooltip state for the matrix island. Per D-16 + RESEARCH
   P8, the tooltip is anchored to the hovered cell — the hook
   captures `el.getBoundingClientRect()` at the moment of mouseenter
   and stores it on `tooltipData.anchorRect`. <HoverTooltipCard>
   reads that rect and positions the portal accordingly.

   100ms close grace period (D-16): on mouseleave, schedule a
   `setTooltipData(null)` via setTimeout. If a new mouseenter fires
   before the timeout elapses, cancel the pending close. Lets the
   cursor cross small gaps between adjacent cells without flicker.

   The hook does NOT touch the DOM directly except via the passed
   `el` argument (calls .getBoundingClientRect()).

   Usage (in plan 04 matrix island):
     const { tooltipData, handleCellEnter, handleCellLeave } = useHoverTooltip();
     <DataCell onMouseEnter={(e) => handleCellEnter(fid, cid, e.currentTarget)}
               onMouseLeave={handleCellLeave}
               onFocus={(e) => handleCellEnter(fid, cid, e.currentTarget)}
               onBlur={handleCellLeave} />
     <HoverTooltipCard data={tooltipData} ... />
   ================================================================ */

import { useState, useRef, useCallback, useEffect } from 'react';
import type { TooltipData } from './types';

/** 100ms grace per D-16 — cursor can cross gaps without flicker. */
export const TOOLTIP_CLOSE_GRACE_MS = 100;

export interface UseHoverTooltipReturn {
  tooltipData: TooltipData;
  handleCellEnter: (featureId: string, clubId: string, el: HTMLElement) => void;
  handleCellLeave: () => void;
  /** Synchronously clears state + cancels any pending close timer. */
  clearTooltip: () => void;
}

export function useHoverTooltip(): UseHoverTooltipReturn {
  const [tooltipData, setTooltipData] = useState<TooltipData>(null);
  const closeTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancelPendingClose = useCallback(() => {
    if (closeTimerRef.current !== null) {
      clearTimeout(closeTimerRef.current);
      closeTimerRef.current = null;
    }
  }, []);

  const handleCellEnter = useCallback(
    (featureId: string, clubId: string, el: HTMLElement) => {
      cancelPendingClose();
      const anchorRect = el.getBoundingClientRect();
      setTooltipData({ featureId, clubId, anchorRect });
    },
    [cancelPendingClose]
  );

  const handleCellLeave = useCallback(() => {
    cancelPendingClose();
    closeTimerRef.current = setTimeout(() => {
      setTooltipData(null);
      closeTimerRef.current = null;
    }, TOOLTIP_CLOSE_GRACE_MS);
  }, [cancelPendingClose]);

  const clearTooltip = useCallback(() => {
    cancelPendingClose();
    setTooltipData(null);
  }, [cancelPendingClose]);

  // Unmount cleanup so a stale timer doesn't fire setState on an
  // unmounted component (React would warn).
  useEffect(() => {
    return () => {
      if (closeTimerRef.current !== null) {
        clearTimeout(closeTimerRef.current);
        closeTimerRef.current = null;
      }
    };
  }, []);

  return { tooltipData, handleCellEnter, handleCellLeave, clearTooltip };
}

export default useHoverTooltip;
