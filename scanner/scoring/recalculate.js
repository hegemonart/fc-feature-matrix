#!/usr/bin/env node
/**
 * scanner/scoring/recalculate.js — area-parameterized score recalc.
 *
 * Port of analysis/homepage/crosscheck/recalculate-scores.js (D-24 leaves
 * that file untouched). The source hard-codes ROOT = analysis/homepage/;
 * this port accepts `--area <name>`, looks the area up in
 * scanner/config/areas.json, and resolves features_ts + results_dir
 * relative to the repo root.
 *
 * Phase-1 empty-seed behaviour (D-25): when the hospitality entry has
 * features_ts=null / rubric_path=null, the script prints an informative
 * "not yet populated" message and exits 0 — Phase 2 will flip the null
 * to a real path when analysis/hospitality/ ships.
 *
 * Usage:
 *   node scanner/scoring/recalculate.js --area hospitality
 *
 * Exit codes:
 *   0 — success (or phase-1 empty-seed skip)
 *   1 — unknown area OR (later) a score-compute error
 *   2 — missing --area argument
 *   3 — areas.json not found
 *   4 — configured features_ts not found
 *   5 — configured results_dir not found
 *
 * The score-computation body below is copied verbatim from
 * analysis/homepage/crosscheck/recalculate-scores.js (the reference
 * implementation). The only changes: the hard-coded ROOT/RESULTS_DIR/
 * FEATURES_TS constants are replaced with values resolved from
 * areas.json. All weight-parsing, rescore, aggregation, and output
 * semantics are identical.
 */
'use strict';

const fs = require('fs');
const path = require('path');

// ---------------------------------------------------------------------------
// Argument parsing — `--area <name>` only.
//
// A minimal hand-rolled parser so the tests don't require `commander`
// (commander is declared in package.json for future CLI polish but not
// required for Phase 1).
// ---------------------------------------------------------------------------

function parseArea(argv) {
  const idx = argv.indexOf('--area');
  if (idx === -1 || idx === argv.length - 1) {
    console.error('Usage: recalculate.js --area <name>');
    process.exit(2);
  }
  return argv[idx + 1];
}

// ---------------------------------------------------------------------------
// Weight extraction — verbatim regex from recalculate-scores.js.
// ---------------------------------------------------------------------------

function parseWeights(featuresTsPath) {
  const src = fs.readFileSync(featuresTsPath, 'utf8').replace(/\n\s*/g, ' ');
  const weights = {};
  // feat calls span multiple lines in the source; strip newlines then match
  // 6 quoted args (id, key, name, desc, category, tier) followed by
  // yes_weight + no_weight numbers. Plan 02-12 Rule-1 fix: each quoted
  // arg uses a backslash-aware string-body pattern so descriptions
  // containing parentheses (e.g. "(smart, smart-casual, formal)") are
  // not truncated by the prior `[^)]*` middle group. The original regex
  // dropped 21 of 55 hospitality features whose descriptions contained
  // parens.
  const QUO = String.raw`'(?:[^'\\]|\\.)*'`;
  // Plan 02-17: features.ts may have an optional 9th `detection` string arg
  // after the two integer weights. Match `, '<mode>'` non-greedily before the
  // closing paren so legacy 8-arg calls AND new 9-arg calls both parse.
  const reSrc = String.raw`feat\(\s*${QUO}\s*,\s*'([^']+)'\s*,\s*${QUO}\s*,\s*${QUO}\s*,\s*${QUO}\s*,\s*'([A-F])'\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*(?:,\s*${QUO}\s*)?\)`;
  const re = new RegExp(reSrc, 'g');
  let m;
  while ((m = re.exec(src)) !== null) {
    // m[1] = key, m[2] = tier, m[3] = yes weight, m[4] = no weight
    weights[m[1]] = { yes: parseInt(m[3], 10), no: parseInt(m[4], 10) };
  }
  return weights;
}

// ---------------------------------------------------------------------------
// Rescore body — adapted verbatim from recalculate-scores.js.
//
// Only differences: RESULTS_DIR is a parameter, weights are passed in, and
// the function returns the computed clubs array so main() can log the count.
// ---------------------------------------------------------------------------

function rescoreArea(resultsDir, weights) {
  const files = fs
    .readdirSync(resultsDir)
    .filter((f) => f.endsWith('.json') && !f.startsWith('_'))
    .sort();

  const clubs = [];
  for (const fname of files) {
    const fpath = path.join(resultsDir, fname);
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
      console.log(`  ${d.product_id}: ${oldScore} -> ${score}`);
    }

    clubs.push(d);
  }

  // ── Regenerate _scores.json (only when there are clubs) ──
  if (clubs.length === 0) return clubs;

  clubs.sort((a, b) => b.total_score - a.total_score);
  const scores = {
    generated_at: new Date().toISOString().split('T')[0],
    total_clubs: clubs.length,
    rankings: clubs.map((c, i) => ({
      rank: i + 1,
      product_id: c.product_id,
      screenshot: c.screenshot,
      total_score: c.total_score,
      yes_count: Object.values(c.features).filter((v) => v === true).length,
      no_count: Object.values(c.features).filter((v) => v === false).length,
      feature_count: Object.keys(c.features).length,
    })),
  };
  fs.writeFileSync(path.join(resultsDir, '_scores.json'), JSON.stringify(scores, null, 2) + '\n');

  // ── Regenerate _aggregate.json ──
  const allFeatureKeys = Object.keys(clubs[0].features).sort();
  const aggregate = {
    generated_at: scores.generated_at,
    total_clubs: clubs.length,
    total_features: allFeatureKeys.length,
    features: {},
  };
  for (const key of allFeatureKeys) {
    const adoption = clubs.filter((c) => c.features[key] === true).length;
    aggregate.features[key] = {
      adoption_count: adoption,
      adoption_pct: Math.round((adoption / clubs.length) * 100),
      clubs_yes: clubs.filter((c) => c.features[key] === true).map((c) => c.product_id),
      clubs_no: clubs.filter((c) => c.features[key] !== true).map((c) => c.product_id),
    };
  }
  fs.writeFileSync(path.join(resultsDir, '_aggregate.json'), JSON.stringify(aggregate, null, 2) + '\n');

  return clubs;
}

// ---------------------------------------------------------------------------
// Main — resolves paths through areas.json, then delegates to rescoreArea.
// ---------------------------------------------------------------------------

function main() {
  const area = parseArea(process.argv);
  // scanner/scoring/recalculate.js -> scanner/scoring -> scanner -> repoRoot
  const repoRoot = path.resolve(__dirname, '..', '..');
  const areasPath = path.join(repoRoot, 'scanner', 'config', 'areas.json');

  if (!fs.existsSync(areasPath)) {
    console.error(`areas.json not found: ${areasPath}`);
    process.exit(3);
  }

  const areas = JSON.parse(fs.readFileSync(areasPath, 'utf8'));
  const cfg = areas[area];
  if (!cfg) {
    const known = Object.keys(areas).join(', ') || '(none)';
    console.error(`Unknown area: ${area}. Known: ${known}`);
    process.exit(1);
  }

  // Phase-1 empty-seed guard (D-25). Early-exit before touching any files.
  if (!cfg.features_ts || !cfg.rubric_path) {
    console.log(
      `Area '${area}' not yet populated (features_ts/rubric_path=null) — ` +
        `skipping score computation (Phase 2 gate).`,
    );
    process.exit(0);
  }

  // Resolve configured paths; if either is missing on disk bail with an
  // explicit error so operators see exactly what to fix.
  //
  // Plan 02-12 additive: scoring_results_dir overrides results_dir when set.
  // The results_dir field stays as the home for vision intermediate JSONs
  // ({steps: {step: {opus, sonnet}}}); scoring_results_dir points at the
  // canonical flat-presence-map results ({features: {key: bool}}) consumed
  // by this scorer. Default-fallback preserves Phase-1 behavior.
  const featuresTsPath = path.join(repoRoot, cfg.features_ts);
  const scoringDirRel = cfg.scoring_results_dir || cfg.results_dir;
  const resultsDir = path.join(repoRoot, scoringDirRel);
  if (!fs.existsSync(featuresTsPath)) {
    console.error(`features.ts not found: ${featuresTsPath}`);
    process.exit(4);
  }
  if (!fs.existsSync(resultsDir)) {
    console.error(`results_dir not found: ${resultsDir}`);
    process.exit(5);
  }

  // Parse weights — identical to recalculate-scores.js.
  const weights = parseWeights(featuresTsPath);
  const featureCount = Object.keys(weights).length;
  console.log(`Parsed ${featureCount} features from features.ts`);

  if (featureCount === 0) {
    console.error('ERROR: No features parsed. Check the regex against features.ts format.');
    process.exit(1);
  }

  const clubs = rescoreArea(resultsDir, weights);
  console.log(`scores computed for ${clubs.length} clubs`);
  if (clubs.length > 0) {
    const top = clubs
      .slice(0, 5)
      .map((c) => `${c.product_id}=${c.total_score}`)
      .join(', ');
    console.log(`Top ${Math.min(5, clubs.length)}: ${top}`);
  }
}

if (require.main === module) {
  main();
}

module.exports = { main, parseWeights, rescoreArea };
