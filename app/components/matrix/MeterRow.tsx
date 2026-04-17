/* ================================================================
   <MeterRow>

   Mini progress bar + percentage caption (D-06). Width-driven by
   value (0-100). Color resolves from band → existing CSS var
   (--green | --yellow | --orange | --red) per lib/scoring.ts
   tier mapping. Component does NOT import scoring logic — the
   parent (plan 04) classifies and passes the band in as a prop.
   This keeps MeterRow pure-visual and independently testable.

   Band → CSS var mapping (mirrors lib/scoring.ts):
     competitive → --green
     mid         → --yellow
     weak        → --orange
     bottom      → --red
   ================================================================ */

import * as React from 'react';
import styles from './MeterRow.module.css';
import type { MeterRowProps, MeterBand } from './types';

const BAND_COLOR: Record<MeterBand, string> = {
  competitive: 'var(--green)',
  mid: 'var(--yellow)',
  weak: 'var(--orange)',
  bottom: 'var(--red)',
};

export function MeterRow({ band, value, meterColor }: MeterRowProps) {
  // Clamp 0..100 for safety; an out-of-range value would render as a
  // misleading bar (Rule 2 — input validation on a visual primitive).
  const pct = Math.max(0, Math.min(100, value));
  const color = meterColor ?? BAND_COLOR[band];

  return (
    <div className={styles.row} data-band={band} data-value={pct}>
      <div className={styles.track}>
        <div
          className={styles.fill}
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
      <span className={`${styles.caption} mono-caption`}>{pct}%</span>
    </div>
  );
}

export default MeterRow;
