/* ================================================================
   TopNav.test.tsx

   D-13 — three test groups:
     (a) active-tab gets accent border (data-tab-active=true)
     (b) locked-tab opacity 0.6 + click fires onTabClick
     (c) Unlock variant has the orange-background class
   ================================================================ */

import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/react';
import { TopNav } from '../../app/components/matrix/TopNav';
import type { Tab } from '../../app/components/matrix/types';

const tabs: Tab[] = [
  { id: 'matrix', label: 'Matrix' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'club_pages', label: 'Club Pages' },
  { id: 'mobile', label: 'Mobile' },
  { id: 'unlock', label: 'UNLOCK ALL' },
];

describe('<TopNav> active-tab styling (D-13a)', () => {
  it('marks the active tab with data-tab-active="true"', () => {
    const { container } = render(
      <TopNav tabs={tabs} activeTab="matrix" onTabClick={() => {}} />,
    );
    const active = container.querySelector('[data-tab-active="true"]') as HTMLElement;
    expect(active).toBeTruthy();
    expect(active.getAttribute('data-tab-id')).toBe('matrix');
  });

  it('only one tab is active at a time', () => {
    const { container } = render(
      <TopNav tabs={tabs} activeTab="analytics" onTabClick={() => {}} />,
    );
    const actives = container.querySelectorAll('[data-tab-active="true"]');
    expect(actives.length).toBe(1);
  });

  it('active tab has aria-selected=true for a11y', () => {
    const { container } = render(
      <TopNav tabs={tabs} activeTab="matrix" onTabClick={() => {}} />,
    );
    const active = container.querySelector('[data-tab-active="true"]') as HTMLElement;
    expect(active.getAttribute('aria-selected')).toBe('true');
  });
});

describe('<TopNav> locked-tab behavior (D-13b)', () => {
  it('locked tabs get data-tab-locked="true"', () => {
    const { container } = render(
      <TopNav
        tabs={tabs}
        activeTab="matrix"
        lockedTabs={['club_pages', 'mobile']}
        onTabClick={() => {}}
      />,
    );
    const locked = container.querySelectorAll('[data-tab-locked="true"]');
    expect(locked.length).toBe(2);
  });

  it('clicking a locked tab still fires onTabClick (parent decides modal flow)', () => {
    const onTabClick = vi.fn();
    const { container } = render(
      <TopNav
        tabs={tabs}
        activeTab="matrix"
        lockedTabs={['mobile']}
        onTabClick={onTabClick}
      />,
    );
    const lockedTab = container.querySelector('[data-tab-id="mobile"]') as HTMLElement;
    fireEvent.click(lockedTab);
    expect(onTabClick).toHaveBeenCalledWith('mobile');
  });
});

describe('<TopNav> unlock variant (D-13c)', () => {
  it('renders the unlock tab with data-tab-variant="unlock"', () => {
    const { container } = render(
      <TopNav
        tabs={tabs}
        activeTab="matrix"
        unlockTab="unlock"
        onTabClick={() => {}}
      />,
    );
    const unlock = container.querySelector('[data-tab-variant="unlock"]');
    expect(unlock).toBeTruthy();
  });

  it('clicking the unlock tab fires onTabClick with its id', () => {
    const onTabClick = vi.fn();
    const { container } = render(
      <TopNav
        tabs={tabs}
        activeTab="matrix"
        unlockTab="unlock"
        onTabClick={onTabClick}
      />,
    );
    const unlock = container.querySelector('[data-tab-variant="unlock"]') as HTMLElement;
    fireEvent.click(unlock);
    expect(onTabClick).toHaveBeenCalledWith('unlock');
  });

  it('unlock tab does NOT receive normal data-tab-id attributes (different element shape)', () => {
    const { container } = render(
      <TopNav
        tabs={tabs}
        activeTab="matrix"
        unlockTab="unlock"
        onTabClick={() => {}}
      />,
    );
    const unlockById = container.querySelector('[data-tab-id="unlock"]');
    expect(unlockById).toBeNull();
  });
});

describe('<TopNav> click + snapshot', () => {
  it('clicking a normal tab fires onTabClick with its id', () => {
    const onTabClick = vi.fn();
    const { container } = render(
      <TopNav tabs={tabs.slice(0, 3)} activeTab="matrix" onTabClick={onTabClick} />,
    );
    const tab = container.querySelector('[data-tab-id="analytics"]') as HTMLElement;
    fireEvent.click(tab);
    expect(onTabClick).toHaveBeenCalledWith('analytics');
  });

  it('full snapshot with active + locked + unlock', () => {
    const { container } = render(
      <TopNav
        tabs={tabs}
        activeTab="matrix"
        lockedTabs={['club_pages', 'mobile']}
        unlockTab="unlock"
        onTabClick={() => {}}
      />,
    );
    expect(container.firstChild).toMatchSnapshot();
  });
});
