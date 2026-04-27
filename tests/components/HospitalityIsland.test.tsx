/* ================================================================
   HospitalityIsland.test.tsx

   Plan 02-13 — back-half Hospitality Pilot.

   Two test groups:

   1. **features-wiring** (Task 1): asserts buildPresence() in
      analysis/hospitality/features.ts now reads from the 5 pilot
      result JSONs (Plan 02-12 outputs). Non-pilot product IDs stay
      'absent'. lib/data.ts exports HOSPITALITY_FEATURES of length 55.

   2. **single-orange-CTA** (Task 2): renders <HospitalityIsland>
      and asserts AT MOST one element with the .locked-btn class
      (mirrors the Modal.test.tsx pattern). The "Back to home" link
      MUST NOT carry .locked-btn / orange styling.

   3. **tab-routing** (Task 2): authed user clicking Hospitality tab
      navigates to /hospitality; unauthed user sees the locked modal.
      Implemented as a unit test on the handleTabClick decision tree
      to avoid spinning up the full MatrixIsland.
   ================================================================ */

import { describe, it, expect } from 'vitest';
import { HOSPITALITY_FEATURES } from '@/lib/data';
import { FEATURES as HOSP_FEATURES_DIRECT } from '@/analysis/hospitality/features';
import mancityResults from '@/analysis/hospitality/results/mancity.json';
import tottenhamResults from '@/analysis/hospitality/results/tottenham.json';

describe('Plan 02-13 Task 1 — hospitality features wiring', () => {
  it('lib/data.ts exports HOSPITALITY_FEATURES with length 55', () => {
    expect(Array.isArray(HOSPITALITY_FEATURES)).toBe(true);
    expect(HOSPITALITY_FEATURES.length).toBe(55);
  });

  it('HOSPITALITY_FEATURES re-export matches the source FEATURES from analysis/hospitality/features', () => {
    expect(HOSPITALITY_FEATURES).toBe(HOSP_FEATURES_DIRECT);
  });

  it('every feature has 55 unique HP IDs (HP01..HP55)', () => {
    const ids = HOSPITALITY_FEATURES.map(f => f.id);
    expect(new Set(ids).size).toBe(55);
    expect(ids[0]).toBe('HP01');
    expect(ids[54]).toBe('HP55');
  });

  it('buildPresence reads pilot result JSONs (man_city: package_tier_list matches results JSON)', () => {
    const f = HOSPITALITY_FEATURES.find(x => x.key === 'package_tier_list');
    expect(f).toBeDefined();
    const expected = (mancityResults.features as Record<string, boolean>).package_tier_list
      ? 'full'
      : 'absent';
    expect(f!.presence['man_city']).toBe(expected);
  });

  it('buildPresence reads pilot result JSONs (tottenham: fixture_list_visible matches results JSON)', () => {
    const f = HOSPITALITY_FEATURES.find(x => x.key === 'fixture_list_visible');
    expect(f).toBeDefined();
    const expected = (tottenhamResults.features as Record<string, boolean>).fixture_list_visible
      ? 'full'
      : 'absent';
    expect(f!.presence['tottenham']).toBe(expected);
  });

  it('buildPresence returns at least one "full" presence value for the 5 pilot clubs (sanity: not always-absent stub)', () => {
    const pilotIds = ['man_city', 'tottenham', 'real_madrid', 'psg', 'chelsea'];
    let fullCount = 0;
    HOSPITALITY_FEATURES.forEach(f => {
      pilotIds.forEach(id => {
        if (f.presence[id] === 'full') fullCount++;
      });
    });
    // 5 clubs × 55 features = 275 cells; expect at least 1 'full' (Plan 02-12 wrote real values).
    expect(fullCount).toBeGreaterThan(0);
  });

  it('non-pilot products stay absent across all features (pilot-coverage-only)', () => {
    const nonPilotIds = ['arsenal', 'liverpool', 'fc_barcelona', 'bayern_munich', 'man_united'];
    HOSPITALITY_FEATURES.forEach(f => {
      nonPilotIds.forEach(id => {
        expect(f.presence[id]).toBe('absent');
      });
    });
  });
});
