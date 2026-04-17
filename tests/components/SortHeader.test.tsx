/* ================================================================
   SortHeader.test.tsx

   3-state coverage (idle | asc | desc) per Figma 45:5542 + a click
   assertion that fires onSort. D-11.
   ================================================================ */

import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { SortHeader } from '../../app/components/matrix/SortHeader';

describe('<SortHeader> 3 states (D-11)', () => {
  (['idle', 'asc', 'desc'] as const).forEach(state => {
    it(`renders state="${state}" snapshot`, () => {
      const { container } = render(
        <SortHeader label="TOTAL" state={state} onSort={() => {}} />,
      );
      expect(container.firstChild).toMatchSnapshot();
    });
  });

  it('exposes data-sort-state attribute reflecting current state', () => {
    const { container, rerender } = render(
      <SortHeader label="TOTAL" state="idle" onSort={() => {}} />,
    );
    let btn = container.firstChild as HTMLElement;
    expect(btn.getAttribute('data-sort-state')).toBe('idle');

    rerender(<SortHeader label="TOTAL" state="desc" onSort={() => {}} />);
    btn = container.firstChild as HTMLElement;
    expect(btn.getAttribute('data-sort-state')).toBe('desc');
  });
});

describe('<SortHeader> click handler', () => {
  it('fires onSort when clicked', () => {
    const onSort = vi.fn();
    const { container } = render(
      <SortHeader label="TOTAL" state="idle" onSort={onSort} />,
    );
    const btn = container.firstChild as HTMLElement;
    fireEvent.click(btn);
    expect(onSort).toHaveBeenCalledTimes(1);
  });

  it('fires onSort once per click (multiple clicks → multiple calls)', () => {
    const onSort = vi.fn();
    const { container } = render(
      <SortHeader label="TOTAL" state="idle" onSort={onSort} />,
    );
    const btn = container.firstChild as HTMLElement;
    fireEvent.click(btn);
    fireEvent.click(btn);
    fireEvent.click(btn);
    expect(onSort).toHaveBeenCalledTimes(3);
  });
});
