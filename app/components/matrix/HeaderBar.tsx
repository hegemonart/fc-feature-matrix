/* ================================================================
   <HeaderBar>

   D-12 — humbleteam wordmark + dot, centered "FC Benchmark" title,
   right-aligned GET IN TOUCH CTA. Translucent rounded bar, Suisse
   Intl Medium 22px title, Roboto Mono uppercase white-translucent
   CTA.

   buildDate prop is preserved on the props contract for callers
   (process.env.BUILD_DATE → MatrixIsland → HeaderBar) but is no
   longer rendered. Date display removed 2026-05-04.
   ================================================================ */

import * as React from 'react';
import styles from './HeaderBar.module.css';
import type { HeaderBarProps } from './types';

export function HeaderBar({
  authed = false,
  isAdmin = false,
  onSignOut,
  adminHref = '/admin',
}: HeaderBarProps) {
  return (
    <div className={styles.wrap}>
      <header className={styles.bar} role="banner">
        <span className={styles.brand} data-brand="humbleteam">
          {/* humbleteam wordmark — Figma node I43:39;3676:11920 */}
          <img
            src="/humbleteam.svg"
            alt="humbleteam"
            className={styles.wordmark}
            width={123}
            height={14}
          />
          {/* red dot — Figma node I43:39;3676:11921 */}
          <img
            src="/humbleteam-dot.svg"
            alt=""
            aria-hidden="true"
            className={styles.dot}
            width={11}
            height={11}
          />
        </span>

        <span className={styles.center}>
          <span className={styles.title}>FC Benchmark</span>
        </span>

        <span className={styles.actions}>
          <a
            className={styles.cta}
            href="mailto:hi@humbleteam.com"
            data-cta="get-in-touch"
          >
            Get in touch
          </a>
          {authed && isAdmin && (
            <a
              className={styles.cta}
              href={adminHref}
              data-cta="admin"
            >
              Admin
            </a>
          )}
          {authed && (
            <button
              type="button"
              className={styles.cta}
              onClick={onSignOut}
              data-cta="sign-out"
            >
              Sign out
            </button>
          )}
        </span>
      </header>
    </div>
  );
}

export default HeaderBar;
