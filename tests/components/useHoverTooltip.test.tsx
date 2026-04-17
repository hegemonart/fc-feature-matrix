/* ================================================================
   useHoverTooltip.test.tsx

   Specs for the 100ms close grace per D-16. Uses vi.useFakeTimers()
   so the spec is deterministic and fast (never `setTimeout(resolve,
   100)` in tests — slow + flaky).

   Coverage:
     (a) handleCellEnter immediately sets tooltipData with rect
     (b) handleCellLeave schedules null after 100ms
         — advanceTimersByTime(99) keeps data
         — advanceTimersByTime(2) clears it
     (c) handleCellEnter while a close is pending cancels the timer
         (the re-enter grace prevents flicker between adjacent cells)
     (d) clearTooltip synchronously nulls data and cancels timers
   ================================================================ */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import {
  useHoverTooltip,
  TOOLTIP_CLOSE_GRACE_MS,
} from '../../app/components/matrix/useHoverTooltip';

/** Synthetic element with a deterministic getBoundingClientRect. */
function makeCell(top = 100, left = 200, width = 40, height = 38): HTMLElement {
  const el = document.createElement('div');
  const rect = {
    top,
    left,
    right: left + width,
    bottom: top + height,
    width,
    height,
    x: left,
    y: top,
    toJSON: () => ({}),
  } as DOMRect;
  el.getBoundingClientRect = () => rect;
  return el;
}

describe('useHoverTooltip — show/hide + 100ms grace (D-16)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('handleCellEnter immediately sets tooltipData with the cell rect', () => {
    const { result } = renderHook(() => useHoverTooltip());
    expect(result.current.tooltipData).toBeNull();

    const cell = makeCell(100, 200);
    act(() => {
      result.current.handleCellEnter('hero_video', 'real_madrid', cell);
    });

    expect(result.current.tooltipData).not.toBeNull();
    expect(result.current.tooltipData?.featureId).toBe('hero_video');
    expect(result.current.tooltipData?.clubId).toBe('real_madrid');
    expect(result.current.tooltipData?.anchorRect.top).toBe(100);
    expect(result.current.tooltipData?.anchorRect.left).toBe(200);
  });

  it('handleCellLeave schedules null after 100ms (not before)', () => {
    const { result } = renderHook(() => useHoverTooltip());
    const cell = makeCell();

    act(() => result.current.handleCellEnter('f', 'c', cell));
    expect(result.current.tooltipData).not.toBeNull();

    act(() => result.current.handleCellLeave());
    // 99ms in — still visible
    act(() => {
      vi.advanceTimersByTime(TOOLTIP_CLOSE_GRACE_MS - 1);
    });
    expect(result.current.tooltipData).not.toBeNull();

    // 2 more ms — now past 100, should be null
    act(() => {
      vi.advanceTimersByTime(2);
    });
    expect(result.current.tooltipData).toBeNull();
  });

  it('handleCellEnter while a close is pending cancels the timer (re-enter grace)', () => {
    const { result } = renderHook(() => useHoverTooltip());
    const cell1 = makeCell(100, 200);
    const cell2 = makeCell(140, 200);

    act(() => result.current.handleCellEnter('f1', 'c1', cell1));
    act(() => result.current.handleCellLeave());

    // Mid-grace — cursor enters adjacent cell
    act(() => {
      vi.advanceTimersByTime(50);
    });
    act(() => result.current.handleCellEnter('f2', 'c1', cell2));

    // Let the original timer's deadline pass — must NOT clear because
    // the second handleCellEnter cancelled it.
    act(() => {
      vi.advanceTimersByTime(TOOLTIP_CLOSE_GRACE_MS);
    });

    expect(result.current.tooltipData).not.toBeNull();
    expect(result.current.tooltipData?.featureId).toBe('f2');
    expect(result.current.tooltipData?.anchorRect.top).toBe(140);
  });

  it('clearTooltip synchronously nulls data and cancels any pending close', () => {
    const { result } = renderHook(() => useHoverTooltip());
    const cell = makeCell();

    act(() => result.current.handleCellEnter('f', 'c', cell));
    act(() => result.current.handleCellLeave());

    act(() => result.current.clearTooltip());
    expect(result.current.tooltipData).toBeNull();

    // Advance past the grace — should still be null (no spurious set).
    act(() => {
      vi.advanceTimersByTime(TOOLTIP_CLOSE_GRACE_MS + 5);
    });
    expect(result.current.tooltipData).toBeNull();
  });
});
