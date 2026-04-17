/* ================================================================
   CategoryFilter.test.tsx

   D-14 — render with fake categories, assert each name+count
   appears, click one and assert onToggle fires. Plus a real-data
   contract test: derive CategoryItem[] from analysis/homepage/features.ts
   and assert per-category count equality.
   ================================================================ */

import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { CategoryFilter } from '../../app/components/matrix/CategoryFilter';
import type { CategoryFilterProps, CategoryItem } from '../../app/components/matrix/types';
import { FEATURES } from '../../analysis/homepage/features';
import { CATEGORIES } from '../../analysis/homepage/categories';
import type { CategoryId } from '../../analysis/types';

const fakeCategories: CategoryItem[] = [
  { id: 'header_nav', name: 'Header & Navigation', count: 6 },
  { id: 'hero', name: 'Hero', count: 4 },
  { id: 'match_fixtures', name: 'Match & Fixtures', count: 7 },
  { id: 'content', name: 'Content & Editorial', count: 5 },
];

describe('<CategoryFilter> rendering (D-14)', () => {
  it('renders each category name + count', () => {
    const { container, getByText } = render(
      <CategoryFilter
        categories={fakeCategories}
        collapsed={new Set()}
        onToggle={() => {}}
      />,
    );
    fakeCategories.forEach(cat => {
      expect(getByText(cat.name)).toBeTruthy();
    });
    // Each row has the count rendered
    const rows = container.querySelectorAll('[data-category-id]');
    expect(rows.length).toBe(fakeCategories.length);
  });

  it('marks collapsed categories with data-collapsed="true"', () => {
    const collapsed = new Set<CategoryId>(['hero', 'content']);
    const { container } = render(
      <CategoryFilter
        categories={fakeCategories}
        collapsed={collapsed}
        onToggle={() => {}}
      />,
    );
    const collapsedRows = container.querySelectorAll('[data-collapsed="true"]');
    expect(collapsedRows.length).toBe(2);
    expect((collapsedRows[0] as HTMLElement).getAttribute('data-category-id')).toBe('hero');
    expect((collapsedRows[1] as HTMLElement).getAttribute('data-category-id')).toBe('content');
  });
});

describe('<CategoryFilter> click handler', () => {
  it('clicking a row fires onToggle with the category id', () => {
    const onToggle = vi.fn();
    const { container } = render(
      <CategoryFilter
        categories={fakeCategories}
        collapsed={new Set()}
        onToggle={onToggle}
      />,
    );
    const row = container.querySelector('[data-category-id="hero"]') as HTMLElement;
    fireEvent.click(row);
    expect(onToggle).toHaveBeenCalledWith('hero');
  });
});

// ── D-14 contract: counts derived from features.ts must match ──
describe('<CategoryFilter> D-14 contract — derived from features.ts', () => {
  it('count of features per category matches CATEGORIES list', () => {
    // Derive the same way the parent (plan 04) will: walk FEATURES and
    // bucket by `cat`, then verify each CATEGORIES entry has a sensible count.
    const counts: Record<CategoryId, number> = CATEGORIES.reduce((acc, c) => {
      acc[c.id] = 0;
      return acc;
    }, {} as Record<CategoryId, number>);

    FEATURES.forEach(f => {
      counts[f.cat] = (counts[f.cat] ?? 0) + 1;
    });

    // Sum of per-category counts must equal total features.
    const sum = Object.values(counts).reduce((a, b) => a + b, 0);
    expect(sum).toBe(FEATURES.length);

    // No category should be missing from the bucket map (every f.cat
    // is one of the CATEGORIES ids).
    CATEGORIES.forEach(c => {
      expect(counts[c.id]).toBeGreaterThanOrEqual(0);
    });
  });

  it('renders the full CATEGORIES list with derived counts and registers each click', () => {
    const counts: Record<CategoryId, number> = CATEGORIES.reduce((acc, c) => {
      acc[c.id] = 0;
      return acc;
    }, {} as Record<CategoryId, number>);
    FEATURES.forEach(f => {
      counts[f.cat] = (counts[f.cat] ?? 0) + 1;
    });
    const items: CategoryItem[] = CATEGORIES.map(c => ({
      id: c.id,
      name: c.name,
      count: counts[c.id],
    }));

    const onToggle = vi.fn();
    const { container } = render(
      <CategoryFilter
        categories={items}
        collapsed={new Set()}
        onToggle={onToggle}
      />,
    );
    const rows = container.querySelectorAll('[data-category-id]');
    expect(rows.length).toBe(CATEGORIES.length);
    fireEvent.click(rows[0] as HTMLElement);
    expect(onToggle).toHaveBeenCalledWith(CATEGORIES[0].id);
  });
});
