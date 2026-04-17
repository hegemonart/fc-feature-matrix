/* ================================================================
   DataCell.test.tsx

   8 snapshot tests covering all combinations of
     selected (true|false) x intermediate (true|false) x state ('default'|'hover')
   per Figma node 45:5509 (D-10).

   Plus a focus-fires-mouseEnter parity test (a11y per D-21).
   ================================================================ */

import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { DataCell } from '../../app/components/matrix/DataCell';
import type { DataCellProps } from '../../app/components/matrix/types';

const baseProps: DataCellProps = {
  selected: false,
  intermediate: false,
  state: 'default',
  featureId: 'hero_video',
  clubId: 'real_madrid',
  value: true,
};

const combos: Array<{ name: string; props: Partial<DataCellProps> }> = [
  { name: 'unselected default no-intermediate', props: { selected: false, intermediate: false, state: 'default' } },
  { name: 'unselected hover  no-intermediate',  props: { selected: false, intermediate: false, state: 'hover'   } },
  { name: 'unselected default intermediate',    props: { selected: false, intermediate: true,  state: 'default' } },
  { name: 'unselected hover  intermediate',     props: { selected: false, intermediate: true,  state: 'hover'   } },
  { name: 'selected   default no-intermediate', props: { selected: true,  intermediate: false, state: 'default' } },
  { name: 'selected   hover  no-intermediate',  props: { selected: true,  intermediate: false, state: 'hover'   } },
  { name: 'selected   default intermediate',    props: { selected: true,  intermediate: true,  state: 'default' } },
  { name: 'selected   hover  intermediate',     props: { selected: true,  intermediate: true,  state: 'hover'   } },
];

describe('<DataCell> 8 visual states (D-10)', () => {
  combos.forEach(({ name, props }) => {
    it(`renders: ${name}`, () => {
      const { container } = render(<DataCell {...baseProps} {...props} />);
      expect(container.firstChild).toMatchSnapshot();
    });
  });
});

describe('<DataCell> a11y (D-21 focus mirrors hover)', () => {
  it('forwards onFocus and onMouseEnter — both fire tooltip in parent', () => {
    const onFocus = vi.fn();
    const onMouseEnter = vi.fn();
    const { container } = render(
      <DataCell {...baseProps} onFocus={onFocus} onMouseEnter={onMouseEnter} />,
    );
    const cell = container.firstChild as HTMLElement;
    expect(cell).toBeTruthy();

    fireEvent.mouseEnter(cell);
    expect(onMouseEnter).toHaveBeenCalledTimes(1);

    fireEvent.focus(cell);
    expect(onFocus).toHaveBeenCalledTimes(1);
  });

  it('renders with tabIndex=0 so it is keyboard-focusable', () => {
    const { container } = render(<DataCell {...baseProps} />);
    const cell = container.firstChild as HTMLElement;
    expect(cell.getAttribute('tabindex')).toBe('0');
  });

  it('exposes data-feature and data-club for the portaled tooltip', () => {
    const { container } = render(<DataCell {...baseProps} />);
    const cell = container.firstChild as HTMLElement;
    expect(cell.getAttribute('data-feature')).toBe('hero_video');
    expect(cell.getAttribute('data-club')).toBe('real_madrid');
  });

  it('omits the check when value is false', () => {
    const { container } = render(<DataCell {...baseProps} value={false} />);
    const svg = container.querySelector('svg');
    expect(svg).toBeNull();
  });
});
