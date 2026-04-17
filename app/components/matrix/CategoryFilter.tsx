/* ================================================================
   <CategoryFilter>

   D-14 — vertical list of feature categories. Each row: name +
   right-aligned count. Click toggles a category in the collapsed
   set via onToggle(categoryId).

   Categories + counts are derived from analysis/homepage/features.ts
   (no new data source). The component receives derived
   CategoryItem[] as a prop; it does NOT import features.ts directly
   so the test can pass mock data. The parent (plan 04) does the
   derivation.
   ================================================================ */

import * as React from 'react';
import styles from './CategoryFilter.module.css';
import type { CategoryFilterProps } from './types';

export function CategoryFilter({
  categories,
  collapsed,
  onToggle,
}: CategoryFilterProps) {
  return (
    <ul className={styles.list} role="list">
      {categories.map(cat => {
        const isCollapsed = collapsed.has(cat.id);
        const className = [styles.row, isCollapsed ? styles.collapsed : '']
          .filter(Boolean)
          .join(' ');
        return (
          <li key={cat.id}>
            <button
              type="button"
              className={className}
              data-category-id={cat.id}
              data-collapsed={isCollapsed ? 'true' : 'false'}
              aria-pressed={isCollapsed}
              onClick={() => onToggle(cat.id)}
            >
              <span className={styles.name}>{cat.name}</span>
              <span className={`${styles.count} mono-caption`}>{cat.count}</span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export default CategoryFilter;
