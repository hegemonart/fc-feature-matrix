import { FEATURES, PRODUCTS } from './data';

export function getProductScores(pid: string) {
  const fullCount = FEATURES.filter(f => f.presence[pid] === 'full').length;
  const absentCount = FEATURES.filter(f => f.presence[pid] === 'absent').length;
  const rawScore = fullCount;

  // Asymmetric scoring: Yes adds weightYes, No adds weightNo (often negative)
  let totalScore = 0;
  let maxPossible = 0;
  FEATURES.forEach(f => {
    maxPossible += f.weightYes;
    if (f.presence[pid] === 'full') {
      totalScore += f.weightYes;
    } else {
      totalScore += f.weightNo;
    }
  });

  const coveragePct = Math.round(fullCount / FEATURES.length * 100);
  return {
    fullCount,
    absentCount,
    rawScore,
    weightedScore: totalScore,
    maxWeighted: maxPossible,
    coveragePct,
  };
}

export function getRankedProducts() {
  return PRODUCTS.map(pr => {
    const { coveragePct } = getProductScores(pr.id);
    return { id: pr.id, name: pr.name, pct: coveragePct };
  }).sort((a, b) => b.pct - a.pct);
}
