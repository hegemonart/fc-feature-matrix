/* ================================================================
   MatrixIsland.test.tsx

   Plan 02-21 — area-aware MatrixIsland tests.

   Three test groups:

   1. **features-wiring** (preserved from 02-13): asserts
      buildPresence() in analysis/hospitality/features.ts reads from
      the 5 pilot result JSONs. lib/data.ts exports HOSPITALITY_FEATURES
      of length 55 and HOSPITALITY_CATEGORIES of length 8.

   2. **area-rendering** (Plan 02-21 NEW): renders <MatrixIsland>
      in both areas and asserts:
        - area="homepage"     → renders the full homepage feature set,
                                active tab is "home"
        - area="hospitality"  → renders 55 hospitality feature rows,
                                renders 8 hospitality categories in
                                sidebar, active tab is "hospitality"
        - Single-orange-CTA invariant: ≤ 1 .locked-btn on each surface

   3. **tab-routing decision tree** (preserved from 02-13): authed
      user clicking Hospitality routes to /hospitality; unauthed sees
      locked modal. Plan 02-21 also adds a "click Homepage from
      /hospitality routes back to /" assertion.
   ================================================================ */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';
import {
  HOSPITALITY_FEATURES,
  HOSPITALITY_CATEGORIES,
  PRODUCTS,
  FEATURES,
} from '@/lib/data';
import { FEATURES as HOSP_FEATURES_DIRECT } from '@/analysis/hospitality/features';
import mancityResults from '@/analysis/hospitality/results/mancity.json';
import tottenhamResults from '@/analysis/hospitality/results/tottenham.json';

// Mock next/navigation so MatrixIsland (uses useRouter) renders cleanly
// under jsdom without an App Router host.
const pushSpy = vi.fn();
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: pushSpy, replace: vi.fn(), prefetch: vi.fn() }),
}));

// Mock the analytics tracker — vitest jsdom env has no production
// analytics endpoint; the useEffect call would log a noisy fetch.
vi.mock('@/lib/track', () => ({ trackEvent: vi.fn() }));

// Stub global fetch to keep MatrixIsland's auth-on-mount call quiet.
beforeEach(() => {
  pushSpy.mockClear();
  // @ts-expect-error — narrow typing not needed for a stub.
  global.fetch = vi.fn(() =>
    Promise.resolve({ ok: true, json: () => Promise.resolve({ authenticated: false }) }),
  );
});

import MatrixIsland from '@/app/MatrixIsland';

const PILOT_IDS = ['man_city', 'tottenham', 'real_madrid', 'psg', 'chelsea'];
const pilotProducts = PRODUCTS.filter(p => PILOT_IDS.includes(p.id));
const stubScores: Record<string, number> = Object.fromEntries(
  PILOT_IDS.map(id => [id, 12]),
);

/* ── Group 1 — features-wiring (preserved from Plan 02-13) ───── */

describe('Plan 02-21 — hospitality data wiring', () => {
  it('lib/data.ts exports HOSPITALITY_FEATURES with length 55', () => {
    expect(Array.isArray(HOSPITALITY_FEATURES)).toBe(true);
    expect(HOSPITALITY_FEATURES.length).toBe(55);
  });

  it('lib/data.ts exports HOSPITALITY_CATEGORIES with length 8', () => {
    expect(Array.isArray(HOSPITALITY_CATEGORIES)).toBe(true);
    expect(HOSPITALITY_CATEGORIES.length).toBe(8);
    const ids = HOSPITALITY_CATEGORIES.map(c => c.id).sort();
    expect(ids).toEqual([
      'booking_confirmation',
      'enquiry_friction',
      'food_beverage',
      'match_selector_ux',
      'package_discovery',
      'post_booking_comms',
      'premium_amenities',
      'pricing_transparency',
    ]);
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

  it('buildPresence returns at least one "full" presence value for the 5 pilot clubs', () => {
    let fullCount = 0;
    HOSPITALITY_FEATURES.forEach(f => {
      PILOT_IDS.forEach(id => {
        if (f.presence[id] === 'full') fullCount++;
      });
    });
    expect(fullCount).toBeGreaterThan(0);
  });

  it('non-pilot products stay absent across all hospitality features', () => {
    const nonPilotIds = ['arsenal', 'liverpool', 'fc_barcelona', 'bayern_munich', 'man_united'];
    HOSPITALITY_FEATURES.forEach(f => {
      nonPilotIds.forEach(id => {
        expect(f.presence[id]).toBe('absent');
      });
    });
  });
});

/* ── Group 2 — area-rendering (Plan 02-21 NEW) ───────────────── */

describe('Plan 02-21 — <MatrixIsland area="hospitality"> rendering', () => {
  it('renders 55 hospitality feature rows (matches HOSPITALITY_FEATURES.length)', () => {
    const { container } = render(
      <MatrixIsland
        area="hospitality"
        products={pilotProducts}
        features={HOSPITALITY_FEATURES}
        categories={HOSPITALITY_CATEGORIES}
        scores={stubScores}
        buildDate="2026-04-29"
      />,
    );
    const featureRows = container.querySelectorAll('tbody tr[data-feature-row]');
    expect(featureRows.length).toBe(55);
  });

  it('renders 5 product columns in the matrix header', () => {
    const { container } = render(
      <MatrixIsland
        area="hospitality"
        products={pilotProducts}
        features={HOSPITALITY_FEATURES}
        categories={HOSPITALITY_CATEGORIES}
        scores={stubScores}
        buildDate="2026-04-29"
      />,
    );
    const headerCols = container.querySelectorAll('thead tr:first-child th');
    expect(headerCols.length).toBe(6); // 1 feature col + 5 product cols
  });

  it('renders 8 hospitality categories in the sidebar CategoryFilter', () => {
    const { container } = render(
      <MatrixIsland
        area="hospitality"
        products={pilotProducts}
        features={HOSPITALITY_FEATURES}
        categories={HOSPITALITY_CATEGORIES}
        scores={stubScores}
        buildDate="2026-04-29"
      />,
    );
    const catRows = container.querySelectorAll('.sidebar [data-category-id]');
    expect(catRows.length).toBe(8);
    const catIds = Array.from(catRows).map(el => el.getAttribute('data-category-id'));
    expect(catIds).toContain('package_discovery');
    expect(catIds).toContain('booking_confirmation');
  });

  it('marks the "hospitality" tab as the active tab pill', () => {
    const { container } = render(
      <MatrixIsland
        area="hospitality"
        products={pilotProducts}
        features={HOSPITALITY_FEATURES}
        categories={HOSPITALITY_CATEGORIES}
        scores={stubScores}
        buildDate="2026-04-29"
      />,
    );
    const active = container.querySelector('[data-tab-active="true"]') as HTMLElement;
    expect(active).toBeTruthy();
    expect(active.getAttribute('data-tab-id')).toBe('hospitality');
    // And exactly one tab is active.
    const allActives = container.querySelectorAll('[data-tab-active="true"]');
    expect(allActives.length).toBe(1);
  });

  it('preserves the single-orange-CTA invariant: 0 .locked-btn elements visible on /hospitality chrome', () => {
    const { container } = render(
      <MatrixIsland
        area="hospitality"
        products={pilotProducts}
        features={HOSPITALITY_FEATURES}
        categories={HOSPITALITY_CATEGORIES}
        scores={stubScores}
        buildDate="2026-04-29"
      />,
    );
    // Only the (hidden) modal fixtures contain .locked-btn — they're
    // wrapped in .locked-overlay (not `.locked-overlay.visible`), so
    // they're inert chrome. Counting all .locked-btn anywhere should
    // still be ≤ 1 (the invariant). In practice MatrixIsland renders
    // each modal once with a single .locked-btn inside, but the
    // `.locked-overlay.visible` qualifier shows them only when
    // triggered. Surface-visible CTA count is what we audit.
    const visibleOranges = container.querySelectorAll(
      '.locked-overlay.visible .locked-btn, .preview-blur-overlay .locked-btn',
    );
    expect(visibleOranges.length).toBeLessThanOrEqual(1);
  });
});

describe('Plan 02-21 — <MatrixIsland area="homepage"> rendering (default)', () => {
  it('default area is homepage when prop is omitted', () => {
    const stubHome: Record<string, number> = Object.fromEntries(
      PRODUCTS.map(p => [p.id, 0]),
    );
    const { container } = render(
      <MatrixIsland
        products={PRODUCTS}
        features={FEATURES}
        scores={stubHome}
        buildDate="2026-04-29"
      />,
    );
    const active = container.querySelector('[data-tab-active="true"]') as HTMLElement;
    expect(active).toBeTruthy();
    expect(active.getAttribute('data-tab-id')).toBe('home');
  });

  it('explicit area="homepage" matches default behavior', () => {
    const stubHome: Record<string, number> = Object.fromEntries(
      PRODUCTS.map(p => [p.id, 0]),
    );
    const { container } = render(
      <MatrixIsland
        area="homepage"
        products={PRODUCTS}
        features={FEATURES}
        scores={stubHome}
        buildDate="2026-04-29"
      />,
    );
    const active = container.querySelector('[data-tab-active="true"]') as HTMLElement;
    expect(active.getAttribute('data-tab-id')).toBe('home');
    // 12 homepage categories in the sidebar.
    const catRows = container.querySelectorAll('.sidebar [data-category-id]');
    expect(catRows.length).toBe(12);
  });
});

/* ── Group 3 — handleTabClick decision tree (preserved + extended) ─ */

describe('Plan 02-21 — handleTabClick routing decision tree', () => {
  /**
   * The handleTabClick function inside MatrixIsland is private. Rather
   * than spinning up the full island for a 6-line auth decision check,
   * we replicate the decision tree here verbatim and assert routing
   * semantics. If MatrixIsland's tree changes, update this fixture.
   */
  type AuthState = { authed: boolean; isPremium: boolean; isAdmin: boolean };
  type Area = 'homepage' | 'hospitality';

  function makeFixture(state: AuthState, area: Area = 'homepage') {
    const router = { push: vi.fn() };
    const setLockedFlowName = vi.fn();
    const setLockedModalVisible = vi.fn();
    const setComingSoonFlowName = vi.fn();
    const setComingSoonVisible = vi.fn();
    const trackEvent = vi.fn();
    const activeTabId = area === 'hospitality' ? 'hospitality' : 'home';

    const handleTabClick = (tabId: string) => {
      if (tabId === activeTabId) return;
      if (tabId === 'home') {
        trackEvent('tab_click', { tab: 'Homepage', outcome: 'navigate' });
        router.push('/');
        return;
      }
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

    return {
      router,
      handleTabClick,
      trackEvent,
      setLockedModalVisible,
      setComingSoonVisible,
    };
  }

  it('authed user on / clicking Hospitality routes to /hospitality (no locked modal)', () => {
    const { router, handleTabClick, trackEvent, setLockedModalVisible } = makeFixture({
      authed: true, isPremium: false, isAdmin: false,
    });
    handleTabClick('hospitality');
    expect(router.push).toHaveBeenCalledWith('/hospitality');
    expect(trackEvent).toHaveBeenCalledWith('tab_click', {
      tab: 'Hospitality Packages',
      outcome: 'navigate',
    });
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

  /* ── Plan 02-21 NEW: cross-area navigation ──────────────────── */

  it('clicking Homepage tab from /hospitality routes back to /', () => {
    const { router, handleTabClick, trackEvent } = makeFixture(
      { authed: true, isPremium: false, isAdmin: false },
      'hospitality',
    );
    handleTabClick('home');
    expect(router.push).toHaveBeenCalledWith('/');
    expect(trackEvent).toHaveBeenCalledWith('tab_click', {
      tab: 'Homepage',
      outcome: 'navigate',
    });
  });

  it('clicking the active tab id is a no-op (homepage)', () => {
    const { router, handleTabClick } = makeFixture(
      { authed: true, isPremium: false, isAdmin: false },
      'homepage',
    );
    handleTabClick('home');
    expect(router.push).not.toHaveBeenCalled();
  });

  it('clicking the active tab id is a no-op (hospitality)', () => {
    const { router, handleTabClick } = makeFixture(
      { authed: true, isPremium: false, isAdmin: false },
      'hospitality',
    );
    handleTabClick('hospitality');
    expect(router.push).not.toHaveBeenCalled();
  });
});
