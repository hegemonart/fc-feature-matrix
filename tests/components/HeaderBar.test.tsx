/* ================================================================
   HeaderBar.test.tsx

   D-12 — buildDate prop is rendered verbatim. Component does NOT
   call new Date(); this test guarantees the date is whatever the
   build pipeline supplied (i.e. process.env.BUILD_DATE).
   ================================================================ */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { HeaderBar } from '../../app/components/matrix/HeaderBar';

describe('<HeaderBar> (D-12)', () => {
  it('renders the buildDate prop formatted as "Nth Month, YYYY"', () => {
    const { getByText } = render(<HeaderBar buildDate="2026-04-17" />);
    // Figma node 43:37 shows "8th April, 2026" — our component formats
    // the ISO buildDate the same way.
    expect(getByText('17th April, 2026')).toBeTruthy();
  });

  it('exposes data-build-date attribute matching the raw ISO prop', () => {
    const { container } = render(<HeaderBar buildDate="2025-12-31" />);
    const dateEl = container.querySelector('[data-build-date]') as HTMLElement;
    expect(dateEl.getAttribute('data-build-date')).toBe('2025-12-31');
  });

  it('renders the FC Benchmark title', () => {
    const { getAllByText } = render(<HeaderBar buildDate="2026-04-17" />);
    // Parent + child both match; just confirm at least one element renders the title.
    expect(getAllByText('FC Benchmark').length).toBeGreaterThan(0);
  });

  it('renders the GET IN TOUCH CTA as a mailto link', () => {
    const { container } = render(<HeaderBar buildDate="2026-04-17" />);
    const cta = container.querySelector('[data-cta="get-in-touch"]') as HTMLAnchorElement;
    expect(cta).toBeTruthy();
    expect(cta.getAttribute('href')).toMatch(/^mailto:/);
  });

  it('renders the humbleteam wordmark as an image with alt text', () => {
    const { container } = render(<HeaderBar buildDate="2026-04-17" />);
    const brand = container.querySelector('[data-brand="humbleteam"]');
    expect(brand).toBeTruthy();
    const wordmark = brand?.querySelector('img[alt="humbleteam"]') as HTMLImageElement | null;
    expect(wordmark).toBeTruthy();
    expect(wordmark?.getAttribute('src')).toMatch(/humbleteam\.svg$/);
  });

  it('snapshot', () => {
    const { container } = render(<HeaderBar buildDate="2026-04-17" />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
