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

  const activeTabData = tabs.find(t => t.id === activeTab && t.id !== unlockTab);
  const railTabs = tabs.filter(t => t.id !== activeTab && t.id !== unlockTab);
  const unlockTabData = unlockTab ? tabs.find(t => t.id === unlockTab) : null;

  return (
    <nav className={styles.nav} role="tablist">
      {activeTabData && (
        <button
          type="button"
          role="tab"
          aria-selected={true}
          className={styles.activeTab}
          data-tab-id={activeTabData.id}
          data-tab-active="true"
          data-tab-locked="false"
          onClick={() => onTabClick(activeTabData.id)}
        >
          {activeTabData.label}
        </button>
      )}

      <div className={styles.lockedRail}>
        {railTabs.map(tab => {
          const isLocked = lockedSet.has(tab.id);
          return (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={false}
              className={`${styles.tab} ${isLocked ? styles.tabLocked : styles.tabUnlocked}`}
              data-tab-id={tab.id}
              data-tab-active="false"
              data-tab-locked={isLocked ? 'true' : 'false'}
              onClick={() => onTabClick(tab.id)}
            >
              {tab.label}
            </button>
          );
        })}

        {unlockTabData && (
          <button
            type="button"
            className={styles.unlockTab}
            onClick={() => onTabClick(unlockTabData.id)}
            data-tab-variant="unlock"
          >
            {unlockTabData.label}
          </button>
        )}
      </div>
    </nav>
  );
}

export default TopNav;
