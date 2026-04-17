/* ================================================================
   useColumnSelection.test.tsx

   Specs for the column-tint state hook per D-18:
     (a) initial selectedClubId is null, isSelected returns false
     (b) toggle(id) sets selectedClubId; isSelected returns true for
         that id and false for any other
     (c) toggle(sameId) clears the selection (D-18 click-again-deselect)
     (d) toggle(otherId) after toggle(firstId) switches selection
         (no multi-select)
   ================================================================ */

import { describe, it, expect } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { useColumnSelection } from '../../app/components/matrix/useColumnSelection';

describe('useColumnSelection — toggle + isSelected (D-18)', () => {
  it('initial state: selectedClubId is null and isSelected returns false', () => {
    const { result } = renderHook(() => useColumnSelection());
    expect(result.current.selectedClubId).toBeNull();
    expect(result.current.isSelected('real_madrid')).toBe(false);
    expect(result.current.isSelected('barca')).toBe(false);
  });

  it('toggle(id) sets the selection; isSelected reflects only that id', () => {
    const { result } = renderHook(() => useColumnSelection());

    act(() => result.current.toggle('real_madrid'));

    expect(result.current.selectedClubId).toBe('real_madrid');
    expect(result.current.isSelected('real_madrid')).toBe(true);
    expect(result.current.isSelected('barca')).toBe(false);
  });

  it('toggle(sameId) deselects (D-18 click-again-deselect contract)', () => {
    const { result } = renderHook(() => useColumnSelection());

    act(() => result.current.toggle('real_madrid'));
    expect(result.current.selectedClubId).toBe('real_madrid');

    act(() => result.current.toggle('real_madrid'));
    expect(result.current.selectedClubId).toBeNull();
    expect(result.current.isSelected('real_madrid')).toBe(false);
  });

  it('toggle(otherId) after toggle(firstId) switches selection (no multi-select)', () => {
    const { result } = renderHook(() => useColumnSelection());

    act(() => result.current.toggle('real_madrid'));
    expect(result.current.selectedClubId).toBe('real_madrid');

    act(() => result.current.toggle('barca'));
    expect(result.current.selectedClubId).toBe('barca');
    expect(result.current.isSelected('real_madrid')).toBe(false);
    expect(result.current.isSelected('barca')).toBe(true);
  });

  it('honors initial value if provided', () => {
    const { result } = renderHook(() => useColumnSelection('psg'));
    expect(result.current.selectedClubId).toBe('psg');
    expect(result.current.isSelected('psg')).toBe(true);
  });
});
