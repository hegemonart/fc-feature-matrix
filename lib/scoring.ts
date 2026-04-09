import { FEATURES, PRODUCTS } from './data';

export function getProductScores(pid: string) {
  const fullCount = FEATURES.filter(f => f.presence[pid] === 'full').length;
  const partialCount = FEATURES.filter(f => f.presence[pid] === 'partial').length;
  const absentCount = FEATURES.filter(f => f.presence[pid] === 'absent').length;
  const rawScore = fullCount + partialCount;
  let weightedScore = 0, maxWeighted = 0;
  FEATURES.forEach(f => {
    maxWeighted += f.weight;
    if (f.presence[pid] === 'full') weightedScore += f.weight;
    else if (f.presence[pid] === 'partial') weightedScore += Math.round(f.weight * 0.5);
  });
  const coveragePct = Math.round((fullCount + partialCount) / FEATURES.length * 100);
  return { fullCount, partialCount, absentCount, rawScore, weightedScore, maxWeighted, coveragePct };
}

export function getRankedProducts() {
  return PRODUCTS.map(pr => {
    const { coveragePct } = getProductScores(pr.id);
    return { id: pr.id, name: pr.name, pct: coveragePct };
  }).sort((a, b) => b.pct - a.pct);
}
