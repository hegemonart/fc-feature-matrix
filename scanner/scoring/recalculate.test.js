/**
 * scanner/scoring/recalculate.test.js — Node built-in test runner.
 *
 * Covers the four behaviours in 01-05-PLAN Task 2:
 *
 *   1. Phase-1 empty-seed ('hospitality' with features_ts=null) exits 0
 *      and prints a "not yet populated" message.
 *   2. Unknown area exits 1 (stderr mentions the area).
 *   3. Script is importable without side-effects (main is a function).
 *   4. With a stubbed areas.json pointing at a real features.ts + results
 *      directory, the script parses both and reports the computed count.
 *
 * Uses only Node built-ins (node:test, node:assert, node:child_process,
 * node:fs, node:path, node:os). No npm install required to run the suite.
 */
'use strict';

const test = require('node:test');
const assert = require('node:assert');
const { execFileSync, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const SCRIPT = path.resolve(__dirname, 'recalculate.js');
const REPO_ROOT = path.resolve(__dirname, '..', '..');

function run(args, opts = {}) {
  return spawnSync('node', [SCRIPT, ...args], {
    encoding: 'utf8',
    cwd: REPO_ROOT,
    env: { ...process.env, ...(opts.env || {}) },
  });
}

// ---------------------------------------------------------------------------
// 1. Phase-1 empty-seed exits 0 with "not yet populated".
// ---------------------------------------------------------------------------

test('phase-1 empty-seed hospitality exits 0 with not-yet-populated message', () => {
  const result = run(['--area', 'hospitality']);
  assert.strictEqual(result.status, 0, `stderr: ${result.stderr}`);
  assert.match(result.stdout, /not yet populated/);
});

// ---------------------------------------------------------------------------
// 2. Unknown area exits 1.
// ---------------------------------------------------------------------------

test('unknown area exits 1 and stderr mentions the area', () => {
  const result = run(['--area', 'bogus']);
  assert.strictEqual(result.status, 1);
  assert.match(result.stderr, /Unknown area/);
  assert.match(result.stderr, /bogus/);
});

// ---------------------------------------------------------------------------
// 2b. Missing --area argument exits non-zero with usage message.
// ---------------------------------------------------------------------------

test('missing --area prints usage and exits non-zero', () => {
  const result = run([]);
  assert.notStrictEqual(result.status, 0);
  assert.match(result.stderr, /--area/);
});

// ---------------------------------------------------------------------------
// 3. Script is importable without side effects; exports main.
// ---------------------------------------------------------------------------

test('script is importable without side effects', () => {
  const mod = require(SCRIPT);
  assert.strictEqual(typeof mod.main, 'function');
});

// ---------------------------------------------------------------------------
// 4. Stubbed areas.json with populated fixture feeds real-data path.
//
// We build a tiny throw-away repo root in os.tmpdir():
//   tmp/
//     scanner/config/areas.json          (points at tmp/analysis/demo)
//     analysis/demo/features.ts          (2 features)
//     analysis/demo/results/alpha.json   (scoreable)
//     analysis/demo/results/beta.json
//
// Then invoke `node recalculate.js --area demo` with cwd=tmp to exercise
// the populated path. This must print "scores computed for 2 clubs".
// ---------------------------------------------------------------------------

test('populated area path rescoring reports N clubs', () => {
  const tmpRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'fc-recalc-'));
  try {
    // Build tmp/scanner/scoring and tmp/scanner/config.
    const tmpScoring = path.join(tmpRoot, 'scanner', 'scoring');
    const tmpConfig = path.join(tmpRoot, 'scanner', 'config');
    fs.mkdirSync(tmpScoring, { recursive: true });
    fs.mkdirSync(tmpConfig, { recursive: true });

    // Copy the script under test into the tmp tree so its
    // `path.resolve(__dirname, '..', '..')` resolves to tmpRoot.
    fs.copyFileSync(SCRIPT, path.join(tmpScoring, 'recalculate.js'));

    // features.ts shaped exactly like analysis/homepage/features.ts:
    // feat('id', 'key', 'name', 'tier', yes_weight, no_weight).
    const featuresTs = [
      "// stub",
      "export const features = [",
      "  feat('f1', 'has_hero', 'Hero image', 'A', 3, 0),",
      "  feat('f2', 'has_cta', 'Primary CTA', 'B', 2, -1),",
      "];",
      "",
    ].join('\n');
    const analysisDir = path.join(tmpRoot, 'analysis', 'demo');
    const resultsDir = path.join(analysisDir, 'results');
    fs.mkdirSync(resultsDir, { recursive: true });
    fs.writeFileSync(path.join(analysisDir, 'features.ts'), featuresTs);

    // Two result JSONs.
    fs.writeFileSync(
      path.join(resultsDir, 'alpha.json'),
      JSON.stringify({
        product_id: 'alpha',
        screenshot: 'alpha.png',
        total_score: 0,
        features: { has_hero: true, has_cta: true },
      }),
    );
    fs.writeFileSync(
      path.join(resultsDir, 'beta.json'),
      JSON.stringify({
        product_id: 'beta',
        screenshot: 'beta.png',
        total_score: 0,
        features: { has_hero: false, has_cta: true },
      }),
    );

    // Stub areas.json points features_ts + results_dir at the fixtures
    // using paths relative to the tmp repo root (the script joins with
    // repoRoot internally).
    const areas = {
      demo: {
        evidence_dir: 'analysis/demo/evidence/',
        results_dir: 'analysis/demo/results/',
        rubric_path: 'analysis/demo/DEMO.md',
        features_ts: 'analysis/demo/features.ts',
        flow_maps_dir: null,
        status: 'pilot',
      },
    };
    fs.writeFileSync(path.join(tmpConfig, 'areas.json'), JSON.stringify(areas, null, 2));

    // Execute the tmp-tree copy.
    const tmpScript = path.join(tmpScoring, 'recalculate.js');
    const result = spawnSync('node', [tmpScript, '--area', 'demo'], {
      encoding: 'utf8',
      cwd: tmpRoot,
    });
    assert.strictEqual(result.status, 0, `stderr: ${result.stderr}`);
    assert.match(result.stdout, /scores computed for 2 clubs/);

    // Score math: alpha gets 3+2=5; beta gets 0+2=2.
    const alpha = JSON.parse(fs.readFileSync(path.join(resultsDir, 'alpha.json'), 'utf8'));
    const beta = JSON.parse(fs.readFileSync(path.join(resultsDir, 'beta.json'), 'utf8'));
    assert.strictEqual(alpha.total_score, 5, 'alpha should score 3+2=5');
    assert.strictEqual(beta.total_score, 2, 'beta should score 0+2=2');
  } finally {
    fs.rmSync(tmpRoot, { recursive: true, force: true });
  }
});

// ---------------------------------------------------------------------------
// 5. D-24 invariant: running on phase-1 empty seed does NOT mutate analysis/.
// ---------------------------------------------------------------------------

test('phase-1 run does not mutate analysis/ (D-24)', () => {
  // Snapshot git status of analysis/ before.
  const before = execFileSync('git', ['status', '--porcelain', 'analysis/'], {
    encoding: 'utf8',
    cwd: REPO_ROOT,
  });
  const result = run(['--area', 'hospitality']);
  assert.strictEqual(result.status, 0);
  const after = execFileSync('git', ['status', '--porcelain', 'analysis/'], {
    encoding: 'utf8',
    cwd: REPO_ROOT,
  });
  assert.strictEqual(after, before, 'analysis/ must remain untouched');
});
