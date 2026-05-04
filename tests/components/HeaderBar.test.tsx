/* ================================================================
   HeaderBar.test.tsx

   D-12 — humbleteam wordmark + centered title + right-aligned CTAs.
   The build date used to render here but was removed 2026-05-04;
   buildDate is preserved on HeaderBarProps as a no-op for compat.
   ================================================================ */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { HeaderBar } from '../../app/components/matrix/HeaderBar';

describe('<HeaderBar> (D-12)', () => {
  it('does not render any build-date text or attribute', () => {
    const { container, queryByText } = render(<HeaderBar buildDate="2026-04-17" />);
    expect(queryByText(/April, 2026/)).toBeNull();
    expect(container.querySelector('[data-build-date]')).toBeNull();
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
