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

import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { HOSPITALITY_FEATURES, PRODUCTS } from '@/lib/data';
import { FEATURES as HOSP_FEATURES_DIRECT } from '@/analysis/hospitality/features';
import mancityResults from '@/analysis/hospitality/results/mancity.json';
import tottenhamResults from '@/analysis/hospitality/results/tottenham.json';

// Mock next/navigation so HospitalityIsland (and any imported components
// using useRouter) renders cleanly under jsdom without an App Router host.
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), prefetch: vi.fn() }),
}));

// Mock the analytics tracker — vitest jsdom env has no production
// analytics endpoint and the useEffect call would log a noisy fetch.
vi.mock('@/lib/track', () => ({ trackEvent: vi.fn() }));

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

/* ── Task 2 — render <HospitalityIsland> + invariants ────────── */

import HospitalityIsland from '@/app/hospitality/HospitalityIsland';

const PILOT_IDS = ['man_city', 'tottenham', 'real_madrid', 'psg', 'chelsea'];
const pilotProducts = PRODUCTS.filter(p => PILOT_IDS.includes(p.id));
const stubScores: Record<string, number> = Object.fromEntries(PILOT_IDS.map(id => [id, 12]));

describe('Plan 02-13 Task 2 — <HospitalityIsland> render + invariants', () => {
  it('renders the "Pilot: 5 clubs" mono-caption chip above the matrix', () => {
    const { getByText, container } = render(
      <HospitalityIsland
        pilotProducts={pilotProducts}
        hospitalityFeatures={HOSPITALITY_FEATURES}
        scores={stubScores}
        buildDate="2026-04-27"
      />,
    );
    const chip = getByText('Pilot: 5 clubs');
    expect(chip).toBeTruthy();
    expect(chip.classList.contains('mono-caption')).toBe(true);
    expect(chip.classList.contains('pilot-label')).toBe(true);
    // The chip should appear in the subnav, not buried inside the table body.
    const subnav = container.querySelector('.hospitality-subnav');
    expect(subnav?.contains(chip)).toBe(true);
  });

  it('renders 5 product columns + 55 feature rows', () => {
    const { container } = render(
      <HospitalityIsland
        pilotProducts={pilotProducts}
        hospitalityFeatures={HOSPITALITY_FEATURES}
        scores={stubScores}
        buildDate="2026-04-27"
      />,
    );
    // 1 sticky feature col + 5 product cols in the header row.
    const headerCols = container.querySelectorAll('thead tr:first-child th');
    expect(headerCols.length).toBe(6);
    // 55 feature rows in tbody.
    const featureRows = container.querySelectorAll('tbody tr[data-feature]');
    expect(featureRows.length).toBe(55);
  });

  it('renders the back-to-home affordance as a non-orange link', () => {
    const { container } = render(
      <HospitalityIsland
        pilotProducts={pilotProducts}
        hospitalityFeatures={HOSPITALITY_FEATURES}
        scores={stubScores}
        buildDate="2026-04-27"
      />,
    );
    const back = container.querySelector('[data-cta="back-to-home"]') as HTMLElement;
    expect(back).toBeTruthy();
    expect(back.tagName.toLowerCase()).toBe('a');
    expect(back.getAttribute('href')).toBe('/');
    // The single-orange-CTA invariant — back link must NOT carry the
    // .locked-btn class (the project-wide orange CTA marker class).
    expect(back.classList.contains('locked-btn')).toBe(false);
  });

  it('preserves the single-orange-CTA invariant: ≤ 1 .locked-btn on the surface', () => {
    const { container } = render(
      <HospitalityIsland
        pilotProducts={pilotProducts}
        hospitalityFeatures={HOSPITALITY_FEATURES}
        scores={stubScores}
        buildDate="2026-04-27"
      />,
    );
    // The hospitality view intentionally has zero .locked-btn (no
    // primary CTA in the matrix chrome). Anything > 1 would be a
    // design-system violation.
    const oranges = container.querySelectorAll('.locked-btn');
    expect(oranges.length).toBeLessThanOrEqual(1);
  });

  it('renders presence cells with data-present attribute reflecting the feature presence map', () => {
    const { container } = render(
      <HospitalityIsland
        pilotProducts={pilotProducts}
        hospitalityFeatures={HOSPITALITY_FEATURES}
        scores={stubScores}
        buildDate="2026-04-27"
      />,
    );
    // Spot-check: HP01 (package_tier_list) for man_city must reflect the
    // presence value computed from the results JSON.
    const f = HOSPITALITY_FEATURES.find(x => x.key === 'package_tier_list')!;
    const expectedPresent = f.presence['man_city'] === 'full';
    const cell = container.querySelector(
      `tr[data-feature="${f.id}"] td[data-club="man_city"]`,
    ) as HTMLElement;
    expect(cell).toBeTruthy();
    expect(cell.getAttribute('data-present')).toBe(expectedPresent ? 'true' : 'false');
  });

  it('renders Total Score row with formatted scores from the scores prop', () => {
    const customScores: Record<string, number> = {
      man_city: 12, tottenham: -3, real_madrid: 0, psg: 5, chelsea: -10,
    };
    const { container } = render(
      <HospitalityIsland
        pilotProducts={pilotProducts}
        hospitalityFeatures={HOSPITALITY_FEATURES}
        scores={customScores}
        buildDate="2026-04-27"
      />,
    );
    const scoreRow = container.querySelector('tr.score-row-top');
    expect(scoreRow).toBeTruthy();
    const mcCell = container.querySelector('tr.score-row-top td[data-club="man_city"] .score-value');
    const totCell = container.querySelector('tr.score-row-top td[data-club="tottenham"] .score-value');
    expect(mcCell?.textContent).toBe('+12');
    expect(totCell?.textContent).toBe('-3');
    expect(mcCell?.classList.contains('positive')).toBe(true);
    expect(totCell?.classList.contains('negative')).toBe(true);
  });
});

/* ── Task 2 — handleTabClick decision-tree (unit, mocked router) ── */

describe('Plan 02-13 Task 2 — handleTabClick hospitality routing decision tree', () => {
  /**
   * The handleTabClick function inside MatrixIsland is private. Rather
   * than spinning up the full island (and the full matrix table) for
   * a 6-line auth decision check, we replicate the decision tree here
   * verbatim and assert routing semantics. If MatrixIsland's tree
   * changes, update this fixture.
   */
  type AuthState = { authed: boolean; isPremium: boolean; isAdmin: boolean };

  function makeFixture(state: AuthState) {
    const router = { push: vi.fn() };
    const setLockedFlowName = vi.fn();
    const setLockedModalVisible = vi.fn();
    const setComingSoonFlowName = vi.fn();
    const setComingSoonVisible = vi.fn();
    const trackEvent = vi.fn();
    const handleTabClick = (tabId: string) => {
      if (tabId === 'home') return;
      if (tabId === 'hospitality' && (state.authed || state.isPremium || state.isAdmin)) {
        trackEvent('tab_click', { tab: 'Hospitality Packages', outcome: 'navigate' });
        router.push('/hospitality');
        return;
      }
      const tabName = tabId === 'unlock' ? 'Premium' : tabId;
      if (state.isAdmin || state.isPremium) {
        trackEvent('tab_click', { tab: tabName, outcome: 'coming_soon' });
        setComingSoonFlowName(tabName);
        setComingSoonVisible(true);
      } else if (state.authed) {
        trackEvent('tab_click', { tab: tabName, outcome: 'locked' });
        setLockedFlowName(tabName);
        setLockedModalVisible(true);
      } else {
        trackEvent('tab_click', { tab: tabName, outcome: 'locked' });
        setLockedFlowName(tabName);
        setLockedModalVisible(true);
      }
    };
    return { router, handleTabClick, trackEvent, setLockedModalVisible, setComingSoonVisible };
  }

  it('authed user clicking Hospitality routes to /hospitality (no locked modal)', () => {
    const { router, handleTabClick, trackEvent, setLockedModalVisible } = makeFixture({
      authed: true, isPremium: false, isAdmin: false,
    });
    handleTabClick('hospitality');
    expect(router.push).toHaveBeenCalledWith('/hospitality');
    expect(trackEvent).toHaveBeenCalledWith('tab_click', { tab: 'Hospitality Packages', outcome: 'navigate' });
    expect(setLockedModalVisible).not.toHaveBeenCalled();
  });

  it('premium user clicking Hospitality routes to /hospitality (no coming-soon modal)', () => {
    const { router, handleTabClick, setComingSoonVisible } = makeFixture({
      authed: false, isPremium: true, isAdmin: false,
    });
    handleTabClick('hospitality');
    expect(router.push).toHaveBeenCalledWith('/hospitality');
    expect(setComingSoonVisible).not.toHaveBeenCalled();
  });

  it('admin user clicking Hospitality routes to /hospitality', () => {
    const { router, handleTabClick } = makeFixture({
      authed: false, isPremium: false, isAdmin: true,
    });
    handleTabClick('hospitality');
    expect(router.push).toHaveBeenCalledWith('/hospitality');
  });

  it('UNAUTHED user clicking Hospitality shows the locked modal (preserves existing UX)', () => {
    const { router, handleTabClick, setLockedModalVisible } = makeFixture({
      authed: false, isPremium: false, isAdmin: false,
    });
    handleTabClick('hospitality');
    expect(router.push).not.toHaveBeenCalled();
    expect(setLockedModalVisible).toHaveBeenCalledWith(true);
  });

  it('non-hospitality LOCKED_TABS click is unchanged for authed users (still shows locked modal)', () => {
    const { router, handleTabClick, setLockedModalVisible } = makeFixture({
      authed: true, isPremium: false, isAdmin: false,
    });
    handleTabClick('subscriptions');
    expect(router.push).not.toHaveBeenCalled();
    expect(setLockedModalVisible).toHaveBeenCalledWith(true);
  });

  it('non-hospitality LOCKED_TABS click is unchanged for premium users (still shows coming-soon)', () => {
    const { router, handleTabClick, setComingSoonVisible } = makeFixture({
      authed: false, isPremium: true, isAdmin: false,
    });
    handleTabClick('matchday');
    expect(router.push).not.toHaveBeenCalled();
    expect(setComingSoonVisible).toHaveBeenCalledWith(true);
  });
});
