/* ================================================================
   <TopNav> — Figma node 43:53

   Active tab → solid white pill (left).
   All other tabs → gray rail with justify-between (right).
   Unlock → orange block flush to the right end of the rail.
   ================================================================ */

import * as React from 'react';
import styles from './TopNav.module.css';
import type { TopNavProps } from './types';

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
      <div className={styles.lockedRail}>
        {tabs.map(tab => {
          if (tab.id === unlockTab) {
            return (
              <button
                key={tab.id}
                type="button"
                className={styles.unlockTab}
                onClick={() => onTabClick(tab.id)}
                data-tab-variant="unlock"
              >
                {tab.label}
              </button>
            );
          }
          const isActive = tab.id === activeTab;
          const isLocked = !isActive && lockedSet.has(tab.id);
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              className={isActive ? styles.activeTab : `${styles.tab} ${isLocked ? styles.tabLocked : styles.tabUnlocked}`}
              data-tab-id={tab.id}
              data-tab-active={isActive ? 'true' : 'false'}
              data-tab-locked={isLocked ? 'true' : 'false'}
              onClick={() => onTabClick(tab.id)}
            >
              {tab.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}

export default TopNav;
