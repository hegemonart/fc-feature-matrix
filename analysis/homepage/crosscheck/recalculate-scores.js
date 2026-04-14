#!/usr/bin/env node
/**
 * Recalculate total_score for all club JSONs using weights from features.ts.
 * Also regenerates _scores.json and _aggregate.json.
 *
 * Usage:
 *   node analysis/crosscheck/recalculate-scores.js
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const RESULTS_DIR = path.join(ROOT, 'results');
const FEATURES_TS = path.join(ROOT, 'features.ts');

// ── Parse weights from features.ts ──
// feat() calls span 2 lines, so we strip newlines and match the key + last two numbers.
const src = fs.readFileSync(FEATURES_TS, 'utf8').replace(/\n\s*/g, ' ');
const weights = {};
const re = /feat\(\s*'[^']+'\s*,\s*'([^']+)'\s*,\s*[^)]*,\s*'[A-F]'\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\)/g;
let m;
while ((m = re.exec(src)) !== null) {
  weights[m[1]] = { yes: parseInt(m[2], 10), no: parseInt(m[3], 10) };
}

const featureCount = Object.keys(weights).length;
console.log(`Parsed ${featureCount} features from features.ts`);

if (featureCount === 0) {
  console.error('ERROR: No features parsed. Check the regex against features.ts format.');
  process.exit(1);
}

// ── Recalculate scores ──
const files = fs.readdirSync(RESULTS_DIR)
  .filter(f => f.endsWith('.json') && !f.startsWith('_'))
  .sort();

const clubs = [];
for (const fname of files) {
  const fpath = path.join(RESULTS_DIR, fname);
  const d = JSON.parse(fs.readFileSync(fpath, 'utf8'));
  const oldScore = d.total_score;

  let score = 0;
  for (const [key, val] of Object.entries(d.features)) {
    if (weights[key]) {
      score += val ? weights[key].yes : weights[key].no;
    }
  }

  d.total_score = score;
  fs.writeFileSync(fpath, JSON.stringify(d, null, 2) + '\n');

  if (oldScore !== score) {
    console.log(`  ${d.product_id}: ${oldScore} → ${score}`);
  }

  clubs.push(d);
}

// ── Regenerate _scores.json ──
clubs.sort((a, b) => b.total_score - a.total_score);

const scores = {
  generated_at: new Date().toISOString().split('T')[0],
  total_clubs: clubs.length,
  rankings: clubs.map((c, i) => ({
    rank: i + 1,
    product_id: c.product_id,
    screenshot: c.screenshot,
    total_score: c.total_score,
    yes_count: Object.values(c.features).filter(v => v === true).length,
    no_count: Object.values(c.features).filter(v => v === false).length,
    feature_count: Object.keys(c.features).length,
  })),
};
fs.writeFileSync(path.join(RESULTS_DIR, '_scores.json'), JSON.stringify(scores, null, 2) + '\n');

// ── Regenerate _aggregate.json ──
const allFeatureKeys = Object.keys(clubs[0].features).sort();
const aggregate = {
  generated_at: scores.generated_at,
  total_clubs: clubs.length,
  total_features: allFeatureKeys.length,
  features: {},
};
for (const key of allFeatureKeys) {
  const adoption = clubs.filter(c => c.features[key] === true).length;
  aggregate.features[key] = {
    adoption_count: adoption,
    adoption_pct: Math.round((adoption / clubs.length) * 100),
    clubs_yes: clubs.filter(c => c.features[key] === true).map(c => c.product_id),
    clubs_no: clubs.filter(c => c.features[key] !== true).map(c => c.product_id),
  };
}
fs.writeFileSync(path.join(RESULTS_DIR, '_aggregate.json'), JSON.stringify(aggregate, null, 2) + '\n');

console.log(`\nDone: ${clubs.length} clubs, ${featureCount} scored features`);
console.log(`Top 5: ${clubs.slice(0, 5).map(c => `${c.product_id}=${c.total_score}`).join(', ')}`);
