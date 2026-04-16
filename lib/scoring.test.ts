import { describe, it, expect } from 'vitest';
import { getProductScores, getRankedProducts } from './scoring';
import { PRODUCTS } from './data';

describe('scoring', () => {
  it('returns coverage between 0 and 100 for every product', () => {
    for (const p of PRODUCTS) {
      const { coveragePct } = getProductScores(p.id);
      expect(coveragePct).toBeGreaterThanOrEqual(0);
      expect(coveragePct).toBeLessThanOrEqual(100);
    }
  });

  it('ranks products in descending order by coverage', () => {
    const ranked = getRankedProducts();
    expect(ranked.length).toBe(PRODUCTS.length);
    for (let i = 1; i < ranked.length; i++) {
      expect(ranked[i - 1].pct).toBeGreaterThanOrEqual(ranked[i].pct);
    }
  });
});
