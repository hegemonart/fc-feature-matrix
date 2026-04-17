/* ================================================================
   MeterRow.test.tsx

   1 snapshot per band (4 total) + value-clamp test. D-06 — band
   semantics preserved.
   ================================================================ */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { MeterRow } from '../../app/components/matrix/MeterRow';
import type { MeterBand } from '../../app/components/matrix/types';

describe('<MeterRow> per-band snapshots (D-06)', () => {
  const bands: MeterBand[] = ['competitive', 'mid', 'weak', 'bottom'];
  const valuesByBand: Record<MeterBand, number> = {
    competitive: 92,
    mid: 71,
    weak: 48,
    bottom: 22,
  };

  bands.forEach(band => {
    it(`renders band="${band}"`, () => {
      const { container } = render(<MeterRow band={band} value={valuesByBand[band]} />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  it('exposes data-band + data-value attributes', () => {
    const { container } = render(<MeterRow band="competitive" value={88} />);
    const row = container.firstChild as HTMLElement;
    expect(row.getAttribute('data-band')).toBe('competitive');
    expect(row.getAttribute('data-value')).toBe('88');
  });
});

describe('<MeterRow> value clamping', () => {
  it('clamps negative values to 0', () => {
    const { container } = render(<MeterRow band="bottom" value={-50} />);
    const row = container.firstChild as HTMLElement;
    expect(row.getAttribute('data-value')).toBe('0');
  });

  it('clamps values above 100 to 100', () => {
    const { container } = render(<MeterRow band="competitive" value={150} />);
    const row = container.firstChild as HTMLElement;
    expect(row.getAttribute('data-value')).toBe('100');
  });

  it('honors meterColor override when provided', () => {
    const { container } = render(
      <MeterRow band="competitive" value={50} meterColor="rebeccapurple" />,
    );
    // The fill div is the deepest element with an inline-style background.
    const allDivs = container.querySelectorAll('div');
    const fill = Array.from(allDivs).find(d => d.style.background) as HTMLElement;
    expect(fill).toBeTruthy();
    expect(fill.style.background).toContain('rebeccapurple');
  });
});
