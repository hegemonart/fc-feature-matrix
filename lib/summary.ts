import { FEATURES, CATEGORIES, PRODUCTS, type CategoryId } from './data';
import { getProductScores, getRankedProducts } from './scoring';

export interface ClubSummary {
  headline: string;
  overview: string;
  strengths: string[];
  priorities: { name: string; adoptionPct: number; band: string; category: string }[];
  conclusion: string;
}

const CAT_NAMES: Record<CategoryId, string> = {
  revenue: 'Revenue & Commerce',
  content: 'Content & Engagement',
  brand: 'Brand & Identity',
  ux: 'UX & Utility',
  diff: 'Differentiators',
};

export function generateClubSummary(pid: string): ClubSummary {
  const product = PRODUCTS.find(p => p.id === pid)!;
  const { coveragePct, weightedScore } = getProductScores(pid);
  const ranked = getRankedProducts();
  const rank = ranked.findIndex(r => r.id === pid) + 1;
  const avgPct = Math.round(ranked.reduce((s, r) => s + r.pct, 0) / ranked.length);

  // Category scores
  const catResults = CATEGORIES.map(cat => {
    const cf = FEATURES.filter(f => f.cat === cat.id);
    const got = cf.filter(f => f.presence[pid] !== 'absent').length;
    const pct = Math.round((got / cf.length) * 100);
    return { id: cat.id, name: cat.name, got, total: cf.length, pct };
  });

  const strongCats = catResults.filter(c => c.pct >= 80).sort((a, b) => b.pct - a.pct);
  const weakCats = catResults.filter(c => c.pct < 60).sort((a, b) => a.pct - b.pct);
  const weakestCat = catResults.reduce((a, b) => (a.pct <= b.pct ? a : b));

  // Missing features sorted by priority: band order then weight desc
  const bandOrder = { table_stakes: 0, expected: 1, competitive: 2, innovation: 3 };
  const missing = FEATURES
    .filter(f => f.presence[pid] === 'absent')
    .sort((a, b) => {
      const bo = bandOrder[a.band!] - bandOrder[b.band!];
      if (bo !== 0) return bo;
      return b.weight - a.weight;
    });

  // --- Headline ---
  let tier: string;
  if (coveragePct >= 75) tier = 'Comprehensive digital presence';
  else if (coveragePct >= 60) tier = 'Solid digital foundation';
  else if (coveragePct >= 45) tier = 'Developing digital presence';
  else tier = 'Early-stage digital presence';

  const weakArea = weakCats.length > 0 ? weakCats[0].name : null;
  const headline = weakArea
    ? `${tier} with opportunity in ${weakArea}`
    : `${tier} across all categories`;

  // --- Overview ---
  const positionWord = coveragePct >= avgPct ? 'above' : 'below';
  const diff = Math.abs(coveragePct - avgPct);
  const strongestCat = catResults.reduce((a, b) => (a.pct >= b.pct ? a : b));

  let overview = `${product.name} ranks #${rank} of ${PRODUCTS.length} products with ${coveragePct}% feature coverage, `;
  overview += diff === 0
    ? `exactly at the benchmark average.`
    : `${diff} points ${positionWord} the benchmark average of ${avgPct}%.`;
  overview += ` Strongest area is ${strongestCat.name} (${strongestCat.pct}%)`;
  if (weakestCat.id !== strongestCat.id) {
    overview += `, while ${weakestCat.name} (${weakestCat.pct}%) presents the most room for growth`;
  }
  overview += '.';

  // --- Strengths ---
  const strengths: string[] = [];
  for (const cat of strongCats.slice(0, 3)) {
    strengths.push(`${cat.name} — ${cat.got}/${cat.total} features covered (${cat.pct}%)`);
  }
  if (strengths.length === 0 && strongestCat.pct >= 60) {
    strengths.push(`${strongestCat.name} leads with ${strongestCat.got}/${strongestCat.total} features (${strongestCat.pct}%)`);
  }

  // --- Priorities ---
  const priorities: { name: string; adoptionPct: number; band: string; category: string }[] = [];
  const topMissing = missing.slice(0, 3);
  for (const f of topMissing) {
    const bandLabel = f.band === 'table_stakes' ? 'Table Stakes'
      : f.band === 'expected' ? 'Expected'
      : f.band === 'competitive' ? 'Competitive' : 'Innovation';
    priorities.push({ name: f.name, adoptionPct: f.adoptionPct!, band: bandLabel, category: CAT_NAMES[f.cat] });
  }

  // --- Conclusion (editorial, varied by data shape) ---
  const strongNames = strongCats.slice(0, 2).map(c => c.name);
  const weakNames = weakCats.slice(0, 2).map(c => c.name);
  const hasTableStakesGaps = missing.some(f => f.band === 'table_stakes');
  const onlyInnovationGaps = missing.length > 0 && missing.every(f => f.band === 'innovation');
  const perfectCats = catResults.filter(c => c.pct === 100);
  const zeroCats = catResults.filter(c => c.pct === 0);
  const name = product.name;

  let conclusion: string;

  if (missing.length === 0) {
    conclusion = `${name}'s homepage ticks every box in the benchmark. Full marks across all five categories.`;
  } else if (zeroCats.length > 0) {
    // Dramatic contrast: some categories at 0%
    const zeros = zeroCats.map(c => c.name);
    if (perfectCats.length > 0) {
      conclusion = `A tale of two homepages. ${name} nails ${perfectCats.map(c => c.name).join(' and ')} completely, but ${zeros.join(' and ')} ${zeros.length > 1 ? 'sit' : 'sits'} at zero. `;
      conclusion += `That imbalance shapes how the homepage reads against competitors who spread their investment more evenly.`;
    } else {
      conclusion = `${name}'s homepage has real blind spots. ${zeros.join(' and ')} ${zeros.length > 1 ? 'are' : 'is'} entirely absent, which stands out when most peers in the benchmark have at least partial coverage there.`;
    }
  } else if (rank <= 3) {
    // Top 3
    conclusion = `${name} sits near the top of the benchmark. The homepage delivers across categories`;
    if (weakNames.length > 0) {
      conclusion += `, though ${weakNames.join(' and ')} could still catch up to the rest of the site`;
    }
    conclusion += `. What's missing is mostly niche, not foundational.`;
  } else if (hasTableStakesGaps) {
    // Missing basics
    const tsGaps = missing.filter(f => f.band === 'table_stakes');
    conclusion = `${name}'s homepage is missing features that virtually every competitor has. `;
    conclusion += `${tsGaps.map(f => f.name).slice(0, 2).join(' and ')} ${tsGaps.length === 1 ? 'is' : 'are'} standard across the benchmark`;
    if (strongNames.length > 0) {
      conclusion += `, and ${strongNames.length > 1 ? 'their' : 'its'} absence undercuts the otherwise solid ${strongNames.join(' and ')} presence`;
    }
    conclusion += '.';
  } else if (onlyInnovationGaps) {
    // Only missing innovation-tier stuff
    conclusion = `${name} has all the expected homepage features in place. The gaps that remain are in the innovation tier, features that fewer than half the benchmark has adopted. `;
    if (strongNames.length > 0) {
      conclusion += `Strong showing in ${strongNames.join(' and ')}.`;
    }
  } else if (coveragePct < avgPct && diff >= 10) {
    // Significantly below average
    conclusion = `${name}'s homepage lags the benchmark by a meaningful margin. `;
    if (weakNames.length >= 2) {
      conclusion += `${weakNames[0]} and ${weakNames[1]} are both underdeveloped compared to peers. `;
    } else if (weakNames.length === 1) {
      conclusion += `${weakNames[0]} is notably thin compared to peers. `;
    }
    conclusion += `The site covers the basics but doesn't go much further.`;
  } else if (coveragePct < avgPct) {
    // Slightly below average
    conclusion = `${name}'s homepage lands just under the benchmark average. `;
    if (strongNames.length > 0 && weakNames.length > 0) {
      conclusion += `${strongNames.join(' and ')} ${strongNames.length > 1 ? 'carry' : 'carries'} the site, while ${weakNames.join(' and ')} ${weakNames.length > 1 ? 'leave' : 'leaves'} visible gaps next to competitors. `;
    } else if (weakNames.length > 0) {
      conclusion += `The biggest drag comes from ${weakNames.join(' and ')}, where the homepage offers less than most peers. `;
    }
    conclusion += `The foundations are there, but the site doesn't go far beyond them.`;
  } else if (strongCats.length >= 3) {
    // Strong across the board
    conclusion = `${name} is strong across most categories. ${strongNames.join(', ')} all clear the 80% mark. `;
    if (weakNames.length > 0) {
      conclusion += `Only ${weakNames.join(' and ')} ${weakNames.length > 1 ? 'trail' : 'trails'} behind, and even there the gaps are competitive-tier features, not basics.`;
    } else {
      conclusion += `No major category falls short.`;
    }
  } else {
    // Generic above average
    conclusion = `${name}'s homepage performs above average in the benchmark. `;
    if (strongNames.length > 0) {
      conclusion += `${strongNames.join(' and ')} ${strongNames.length > 1 ? 'stand' : 'stands'} out. `;
    }
    if (weakNames.length > 0) {
      conclusion += `${weakNames.join(' and ')} ${weakNames.length > 1 ? 'have' : 'has'} room to grow, with features that most competitors already offer.`;
    } else {
      conclusion += `The missing pieces are mostly edge cases rather than expected features.`;
    }
  }

  return { headline, overview, strengths, priorities, conclusion };
}
