/* ================================================================
   useColumnSelection

   Owns the active-column state per D-18: at most one club column
   can be "selected" at a time. Click-toggle semantics — clicking
   the same id again deselects.

   The hook plumbs state only. The visual contract is owned by
   <DataCell selected={...}> (built in plan 02), which composes the
   --column-tint gradient overlay (D-03 token from plan 01).

   Usage (in plan 04 matrix island):
     const { selectedClubId, isSelected, toggle } = useColumnSelection();
     // For every cell in the matrix:
     <DataCell selected={isSelected(clubId)} ... />
     // For the click handler on a cell or its column header:
     <th onClick={() => toggle(clubId)}>...</th>
   ================================================================ */

import { useState, useCallback } from 'react';

export interface UseColumnSelectionReturn {
  selectedClubId: string | null;
  isSelected: (clubId: string) => boolean;
  toggle: (clubId: string) => void;
}

export function useColumnSelection(initial: string | null = null): UseColumnSelectionReturn {
  const [selectedClubId, setSelectedClubId] = useState<string | null>(initial);

  const toggle = useCallback((clubId: string) => {
    setSelectedClubId((curr) => (curr === clubId ? null : clubId));
  }, []);

  const isSelected = useCallback(
    (clubId: string) => selectedClubId === clubId,
    [selectedClubId]
  );

  return { selectedClubId, isSelected, toggle };
}

export default useColumnSelection;
