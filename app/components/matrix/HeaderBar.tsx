/* ================================================================
   <HeaderBar>

   D-12 — humbleteam wordmark + dot, centered "FC Benchmark" + the
   build date, right-aligned GET IN TOUCH CTA. Matches Figma node
   43:37 1:1 (translucent rounded bar, Suisse Intl Medium 22px
   title, #6b6b6b date, Roboto Mono uppercase white-translucent CTA).

   buildDate prop is consumed from process.env.BUILD_DATE (defined
   in plan 01-03 next.config.ts env block). The component does NOT
   call new Date() — that would trigger a hydration mismatch
   (RESEARCH.md P4).
   ================================================================ */

import * as React from 'react';
import styles from './HeaderBar.module.css';
import type { HeaderBarProps } from './types';

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

function ordinal(n: number): string {
  const s = ['th', 'st', 'nd', 'rd'];
  const v = n % 100;
  return n + (s[(v - 20) % 10] ?? s[v] ?? s[0]);
}

/** Format an ISO `YYYY-MM-DD` string to "8th April, 2026". Returns the
 *  input unchanged if it doesn't match the ISO shape. */
function formatBuildDate(iso: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!m) return iso;
  const year = m[1];
  const month = MONTHS[parseInt(m[2], 10) - 1];
  const day = parseInt(m[3], 10);
  return `${ordinal(day)} ${month}, ${year}`;
}

export function HeaderBar({
  buildDate,
  authed = false,
  isAdmin = false,
  onSignOut,
  adminHref = '/admin',
}: HeaderBarProps) {
  const formatted = formatBuildDate(buildDate);
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
          <span className={styles.date} data-build-date={buildDate}>
            {formatted}
          </span>
        </span>

        <span className={styles.actions}>
          <a
            className={styles.cta}
            href="mailto:hello@humbleteam.com"
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
