/* ================================================================
   <TopNav> + <UnlockTab>

   D-13 — single horizontal tab strip across the full page width.
   - Active tab gets border-bottom: 2px solid var(--accent)
   - Locked tabs render at opacity 0.6 and call onTabClick(name) —
     the parent (plan 04) decides whether to open the locked-content
     modal, preserving existing app/page.tsx handler logic.
   - <UnlockTab> sub-component renders with solid var(--accent) bg
   - Component does NOT itself open any modal (separation of concerns).
   ================================================================ */

import * as React from 'react';
import styles from './TopNav.module.css';
import type { TopNavProps } from './types';

interface UnlockTabProps {
  label: string;
  onClick: () => void;
}

export function UnlockTab({ label, onClick }: UnlockTabProps) {
  return (
    <button
      type="button"
      className={styles.unlockTab}
      onClick={onClick}
      data-tab-variant="unlock"
    >
      {label}
    </button>
  );
}

export function TopNav({
  tabs,
  activeTab,
  onTabClick,
  unlockTab,
  lockedTabs = [],
}: TopNavProps) {
  const lockedSet = new Set(lockedTabs);

  return (
    <nav className={styles.nav} role="tablist">
      {tabs.map(tab => {
        // Unlock variant — solid orange bg, single-orange-CTA exception.
        if (unlockTab && tab.id === unlockTab) {
          return (
            <UnlockTab
              key={tab.id}
              label={tab.label}
              onClick={() => onTabClick(tab.id)}
            />
          );
        }

        const isActive = tab.id === activeTab;
        const isLocked = lockedSet.has(tab.id);
        const className = [
          styles.tab,
          isActive ? styles.tabActive : '',
          isLocked ? styles.tabLocked : '',
        ]
          .filter(Boolean)
          .join(' ');

        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            className={className}
            data-tab-id={tab.id}
            data-tab-active={isActive ? 'true' : 'false'}
            data-tab-locked={isLocked ? 'true' : 'false'}
            onClick={() => onTabClick(tab.id)}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}

export default TopNav;
