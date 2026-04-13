import { FEATURES, PRODUCTS } from './data';

export function getProductScores(pid: string) {
  const fullCount = FEATURES.filter(f => f.presence[pid] === 'full').length;
  const absentCount = FEATURES.filter(f => f.presence[pid] === 'absent').length;
  const rawScore = fullCount;
  let weightedScore = 0, maxWeighted = 0;
  FEATURES.forEach(f => {
    maxWeighted += f.weight;
    if (f.presence[pid] === 'full') weightedScore += f.weight;
  });
  const coveragePct = Math.round(fullCount / FEATURES.length * 100);
  return { fullCount, absentCount, rawScore, weightedScore, maxWeighted, coveragePct };
}

export function getRankedProducts() {
  return PRODUCTS.map(pr => {
    const { coveragePct } = getProductScores(pr.id);
    return { id: pr.id, name: pr.name, pct: coveragePct };
  }).sort((a, b) => b.pct - a.pct);
}
