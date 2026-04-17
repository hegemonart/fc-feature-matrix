/* ================================================================
   <TypeFilter>

   D-15 (corrected) — three checkboxes labeled FC / Federation /
   League. Filters clubs by their `type` field on
   analysis/products.ts PRODUCTS[].type (NOT from
   analysis/homepage/results/*.json — see RESEARCH.md
   "Type-Filter Data Audit").

   Internal value mapping:
     FC          → 'club'
     Federation  → 'governing'
     League      → 'league'

   The component does NOT import PRODUCTS directly — the parent
   passes selected: Set<ProductType> and onChange as props
   (test isolation).
   ================================================================ */

import * as React from 'react';
import styles from './TypeFilter.module.css';
import type { TypeFilterProps, ProductType } from './types';

interface Option {
  value: ProductType;
  label: string;
}

// Display order: FC first (most common in PRODUCTS), then Federation, then League.
const OPTIONS: Option[] = [
  { value: 'club', label: 'FC' },
  { value: 'governing', label: 'Federation' },
  { value: 'league', label: 'League' },
];

export function TypeFilter({ selected, onChange }: TypeFilterProps) {
  const handleToggle = (value: ProductType) => {
    const next = new Set(selected);
    if (next.has(value)) next.delete(value);
    else next.add(value);
    onChange(next);
  };

  return (
    <ul className={styles.list} role="list">
      {OPTIONS.map(opt => {
        const checked = selected.has(opt.value);
        const id = `type-filter-${opt.value}`;
        return (
          <li key={opt.value}>
            <label
              className={styles.row}
              data-type-value={opt.value}
              data-type-checked={checked ? 'true' : 'false'}
              htmlFor={id}
            >
              <input
                id={id}
                type="checkbox"
                className={styles.checkbox}
                checked={checked}
                onChange={() => handleToggle(opt.value)}
                data-testid={`type-filter-checkbox-${opt.value}`}
              />
              <span className={styles.label}>{opt.label}</span>
            </label>
          </li>
        );
      })}
    </ul>
  );
}

export default TypeFilter;
