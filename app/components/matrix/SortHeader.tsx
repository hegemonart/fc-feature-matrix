/* ================================================================
   <SortHeader>

   3 states (idle | asc | desc) per Figma node 45:5542 (D-11).

   - idle: both arrows render at 40% opacity
   - asc:  up arrow active (full opacity), down arrow dimmed
   - desc: down arrow active (full opacity), up arrow dimmed

   Click handler fires onSort(); the parent owns the
   desc → asc → idle cycle (kept here for testability).

   Inline SVG arrow variants — no PNG fetch from Figma asset URLs
   (those expire in 7 days).
   ================================================================ */

import * as React from 'react';
import styles from './SortHeader.module.css';
import type { SortHeaderProps } from './types';

function ArrowUp({ active }: { active: boolean }) {
  return (
    <svg
      className={[styles.arrow, active ? styles.arrowActive : ''].filter(Boolean).join(' ')}
      viewBox="0 0 8 5"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M4 0.5L7.5 4.5H0.5L4 0.5Z" fill="currentColor" />
    </svg>
  );
}

function ArrowDown({ active }: { active: boolean }) {
  return (
    <svg
      className={[styles.arrow, active ? styles.arrowActive : ''].filter(Boolean).join(' ')}
      viewBox="0 0 8 5"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      focusable="false"
    >
      <path d="M4 4.5L0.5 0.5H7.5L4 4.5Z" fill="currentColor" />
    </svg>
  );
}

export function SortHeader({ label, state, onSort }: SortHeaderProps) {
  const upActive = state === 'asc';
  const downActive = state === 'desc';

  return (
    <button
      type="button"
      className={styles.header}
      onClick={onSort}
      data-sort-state={state}
      aria-label={`Sort by ${label} (${state})`}
    >
      <span className={styles.label}>{label}</span>
      <span className={styles.icons}>
        <ArrowUp active={upActive} />
        <ArrowDown active={downActive} />
      </span>
    </button>
  );
}

export default SortHeader;
