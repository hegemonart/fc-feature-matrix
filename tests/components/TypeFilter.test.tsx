/* ================================================================
   TypeFilter.test.tsx

   D-15 — renders three checkboxes with correct labels, click
   toggles the selected Set, and the D-15 contract: importing
   PRODUCTS from analysis/products.ts and filtering by ProductType
   yields the expected subset.
   ================================================================ */

import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { TypeFilter } from '../../app/components/matrix/TypeFilter';
import type { ProductType } from '../../app/components/matrix/types';
import { PRODUCTS } from '../../analysis/products';

describe('<TypeFilter> rendering (D-15)', () => {
  it('renders three checkboxes with FC / Federation / League labels', () => {
    const { getByText } = render(
      <TypeFilter selected={new Set()} onChange={() => {}} />,
    );
    expect(getByText('FC')).toBeTruthy();
    expect(getByText('Federation')).toBeTruthy();
    expect(getByText('League')).toBeTruthy();
  });

  it('reflects selected set via data-type-checked attr', () => {
    const selected = new Set<ProductType>(['club', 'league']);
    const { container } = render(
      <TypeFilter selected={selected} onChange={() => {}} />,
    );
    const club = container.querySelector('[data-type-value="club"]') as HTMLElement;
    const fed = container.querySelector('[data-type-value="governing"]') as HTMLElement;
    const league = container.querySelector('[data-type-value="league"]') as HTMLElement;
    expect(club.getAttribute('data-type-checked')).toBe('true');
    expect(fed.getAttribute('data-type-checked')).toBe('false');
    expect(league.getAttribute('data-type-checked')).toBe('true');
  });
});

describe('<TypeFilter> change handler', () => {
  it('clicking an unchecked option fires onChange with that value added', () => {
    const onChange = vi.fn();
    const { getByTestId } = render(
      <TypeFilter selected={new Set<ProductType>(['club'])} onChange={onChange} />,
    );
    fireEvent.click(getByTestId('type-filter-checkbox-league'));
    expect(onChange).toHaveBeenCalledTimes(1);
    const next: Set<ProductType> = onChange.mock.calls[0][0];
    expect(Array.from(next).sort()).toEqual(['club', 'league']);
  });

  it('clicking a checked option fires onChange with that value removed', () => {
    const onChange = vi.fn();
    const { getByTestId } = render(
      <TypeFilter
        selected={new Set<ProductType>(['club', 'league'])}
        onChange={onChange}
      />,
    );
    fireEvent.click(getByTestId('type-filter-checkbox-club'));
    expect(onChange).toHaveBeenCalledTimes(1);
    const next: Set<ProductType> = onChange.mock.calls[0][0];
    expect(Array.from(next)).toEqual(['league']);
  });
});

// ── D-15 contract: filter math against the real PRODUCTS dataset ──
describe('<TypeFilter> D-15 contract — PRODUCTS[].type filter math', () => {
  it('every PRODUCTS entry has a type that is one of club|governing|league', () => {
    const valid = new Set<ProductType>(['club', 'governing', 'league']);
    PRODUCTS.forEach(p => {
      expect(valid.has(p.type)).toBe(true);
    });
  });

  it('filtering PRODUCTS by Set<"club"> returns only clubs', () => {
    const allowed = new Set<ProductType>(['club']);
    const filtered = PRODUCTS.filter(p => allowed.has(p.type));
    expect(filtered.length).toBeGreaterThan(0);
    filtered.forEach(p => expect(p.type).toBe('club'));
  });

  it('filtering by Set<"governing"> returns only governing bodies', () => {
    const allowed = new Set<ProductType>(['governing']);
    const filtered = PRODUCTS.filter(p => allowed.has(p.type));
    expect(filtered.length).toBeGreaterThan(0);
    filtered.forEach(p => expect(p.type).toBe('governing'));
  });

  it('filtering by Set<"league"> returns only leagues', () => {
    const allowed = new Set<ProductType>(['league']);
    const filtered = PRODUCTS.filter(p => allowed.has(p.type));
    expect(filtered.length).toBeGreaterThan(0);
    filtered.forEach(p => expect(p.type).toBe('league'));
  });

  it('filtering by all three types returns all PRODUCTS', () => {
    const allowed = new Set<ProductType>(['club', 'governing', 'league']);
    const filtered = PRODUCTS.filter(p => allowed.has(p.type));
    expect(filtered.length).toBe(PRODUCTS.length);
  });

  it('filtering by empty set returns no PRODUCTS', () => {
    const allowed = new Set<ProductType>();
    const filtered = PRODUCTS.filter(p => allowed.has(p.type));
    expect(filtered.length).toBe(0);
  });
});
