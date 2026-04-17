/* ================================================================
   <HeaderBar>

   D-12 — humbleteam wordmark + dot, centered "FC Benchmark" + the
   build date, right-aligned outlined GET IN TOUCH CTA.

   buildDate prop is consumed from process.env.BUILD_DATE (defined
   in plan 01-03 next.config.ts env block). The component does NOT
   call new Date() — that would trigger a hydration mismatch
   (RESEARCH.md P4).
   ================================================================ */

import * as React from 'react';
import styles from './HeaderBar.module.css';
import type { HeaderBarProps } from './types';

export function HeaderBar({ buildDate }: HeaderBarProps) {
  return (
    <header className={styles.bar} role="banner">
      <span className={styles.brand} data-brand="humbleteam">
        humbleteam
        <span className={styles.dot} aria-hidden="true" />
      </span>

      <span className={styles.center}>
        <span className={styles.title}>FC Benchmark</span>
        <span className={`${styles.date} mono-caption`} data-build-date={buildDate}>
          {buildDate}
        </span>
      </span>

      <a
        className={styles.cta}
        href="mailto:hello@humbleteam.com"
        data-cta="get-in-touch"
      >
        GET IN TOUCH
      </a>
    </header>
  );
}

export default HeaderBar;
