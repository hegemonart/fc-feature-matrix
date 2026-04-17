/* ================================================================
   <DataCell>

   8 visual combinations of selected x intermediate x state per
   Figma node 45:5509 (D-10).

   Cell metrics (D-05):
     - Fixed 40 x 38, 12px padding
     - 1px solid var(--border) on left/right/top borders only
     - letter-spacing -0.3px

   Selected state composes a column-tint gradient overlay over
   --bg-cell (D-03). Tokens defined in plan 01-01.

   tabIndex={0} so focus mirrors hover for a11y (D-21). Forwards
   onMouseEnter/onMouseLeave/onFocus/onBlur to the parent — the
   cell does NOT own tooltip state itself (plan 03 wires it).

   data-feature + data-club attributes are read by the portaled
   tooltip in plan 03.
   ================================================================ */

import * as React from 'react';
import styles from './DataCell.module.css';
import type { DataCellProps } from './types';

// Inline SVG check icon — single component reused across selected
// variants. No PNG fetch from Figma asset URLs (those expire in 7
// days); standard checkmark path is clean enough at 14px.
function CheckIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      viewBox="0 0 14 14"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <path
        d="M2.5 7.5L5.5 10.5L11.5 4"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function DataCell({
  selected,
  intermediate,
  state,
  featureId,
  clubId,
  value,
  onMouseEnter,
  onMouseLeave,
  onFocus,
  onBlur,
}: DataCellProps) {
  const classNames = [
    styles.cell,
    selected ? styles.selected : '',
    state === 'hover' ? styles.hover : '',
  ]
    .filter(Boolean)
    .join(' ');

  // The check shows whenever value is true, regardless of selected/hover.
  // intermediate dims it to 40% opacity (D-10 forward-compat).
  const showCheck = value;

  return (
    <div
      className={classNames}
      tabIndex={0}
      data-feature={featureId}
      data-club={clubId}
      data-selected={selected ? 'true' : 'false'}
      data-state={state}
      data-intermediate={intermediate ? 'true' : 'false'}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
      onFocus={onFocus}
      onBlur={onBlur}
    >
      {showCheck ? (
        <CheckIcon
          className={[styles.check, intermediate ? styles.intermediate : '']
            .filter(Boolean)
            .join(' ')}
        />
      ) : null}
    </div>
  );
}

export default DataCell;
