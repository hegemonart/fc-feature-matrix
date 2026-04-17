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
  it('renders the buildDate prop string verbatim', () => {
    const { getByText } = render(<HeaderBar buildDate="2026-04-17" />);
    expect(getByText('2026-04-17')).toBeTruthy();
  });

  it('exposes data-build-date attribute matching the prop', () => {
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

  it('renders the humbleteam wordmark', () => {
    const { container } = render(<HeaderBar buildDate="2026-04-17" />);
    const brand = container.querySelector('[data-brand="humbleteam"]');
    expect(brand).toBeTruthy();
    expect(brand?.textContent).toMatch(/humbleteam/i);
  });

  it('snapshot', () => {
    const { container } = render(<HeaderBar buildDate="2026-04-17" />);
    expect(container.firstChild).toMatchSnapshot();
  });
});
