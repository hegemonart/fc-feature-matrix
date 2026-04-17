/* ================================================================
   HoverTooltipCard.test.tsx

   Specs for the portaled hover tooltip per D-16 / RESEARCH P8:
     (a) renders nothing when data is null
     (b) when data present, the rendered tooltip lives on document.body
         (proving createPortal target is the body)
     (c) top/left styles reflect anchorRect.bottom + 8 / anchorRect.left
     (d) club name + feature description + tier badge + score
         breakdown all appear in the rendered output
     (e) test fixtures use deterministic Maps so assertions stay stable
   ================================================================ */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { HoverTooltipCard } from '../../app/components/matrix/HoverTooltipCard';
import type {
  FeatureMeta,
  ClubMeta,
  CellScoring,
  TooltipData,
} from '../../app/components/matrix/types';

// ── Deterministic fixtures ──────────────────────────────────────
const features = new Map<string, FeatureMeta>([
  [
    'hero_video',
    {
      id: 'hero_video',
      name: 'Hero Video',
      desc: 'Auto-playing hero video block above the fold.',
      tier: 'B',
      weightYes: 6,
      weightNo: -3,
    },
  ],
]);

const clubs = new Map<string, ClubMeta>([
  ['real_madrid', { id: 'real_madrid', name: 'Real Madrid' }],
]);

const scoring = new Map<string, CellScoring>([
  ['real_madrid:hero_video', { yes: 6, no: -3 }],
]);

/** Helper — build a minimal DOMRect for tests. */
function makeRect(top: number, left: number, width = 40, height = 38): DOMRect {
  const right = left + width;
  const bottom = top + height;
  return {
    top,
    left,
    right,
    bottom,
    width,
    height,
    x: left,
    y: top,
    toJSON: () => ({}),
  } as DOMRect;
}

const presentData: TooltipData = {
  featureId: 'hero_video',
  clubId: 'real_madrid',
  anchorRect: makeRect(120, 200),
};

describe('<HoverTooltipCard> portal + visibility (D-16)', () => {
  it('renders nothing when data is null', () => {
    const { container } = render(
      <HoverTooltipCard data={null} features={features} clubs={clubs} scoring={scoring} />
    );
    // The component returns null and the portal never mounts.
    expect(container.firstChild).toBeNull();
    expect(document.body.querySelector('[data-testid="hover-tooltip-card"]')).toBeNull();
  });

  it('renders into document.body via createPortal when data is present', () => {
    render(
      <HoverTooltipCard data={presentData} features={features} clubs={clubs} scoring={scoring} />
    );
    const tooltip = screen.getByRole('tooltip');
    expect(tooltip).toBeTruthy();
    // Proves the portal target is document.body, not a child of the
    // RTL render container.
    expect(document.body.contains(tooltip)).toBe(true);
    expect(tooltip.getAttribute('data-testid')).toBe('hover-tooltip-card');
  });
});

describe('<HoverTooltipCard> position (RESEARCH P8 — anchored to cell)', () => {
  it('top = anchorRect.bottom + 8 and left = anchorRect.left', () => {
    render(
      <HoverTooltipCard data={presentData} features={features} clubs={clubs} scoring={scoring} />
    );
    const tooltip = screen.getByRole('tooltip') as HTMLElement;
    // anchorRect: top=120, height=38 → bottom=158 → top = 158 + 8 = 166
    expect(tooltip.style.top).toBe('166px');
    // left = anchorRect.left = 200
    expect(tooltip.style.left).toBe('200px');
  });

  it('clamps left edge so wide-right cells do not overflow viewport', () => {
    // jsdom default window.innerWidth is 1024. Place anchor at x=900
    // — naive left=900 + 320 max-width = 1220 → would overflow.
    // Expect clamped to (1024 - 320 - 8) = 696.
    const farRight: TooltipData = {
      featureId: 'hero_video',
      clubId: 'real_madrid',
      anchorRect: makeRect(120, 900),
    };
    render(
      <HoverTooltipCard data={farRight} features={features} clubs={clubs} scoring={scoring} />
    );
    const tooltip = screen.getByRole('tooltip') as HTMLElement;
    const leftPx = parseInt(tooltip.style.left, 10);
    expect(leftPx).toBeLessThanOrEqual(window.innerWidth - 320);
  });
});

describe('<HoverTooltipCard> content (D-16)', () => {
  it('renders club name, feature description, TIER badge, and score breakdown', () => {
    render(
      <HoverTooltipCard data={presentData} features={features} clubs={clubs} scoring={scoring} />
    );
    expect(screen.getByText('Real Madrid')).toBeTruthy();
    expect(screen.getByText('Auto-playing hero video block above the fold.')).toBeTruthy();
    expect(screen.getByText(/TIER:\s*B/)).toBeTruthy();
    expect(screen.getByText(/Yes \+6/)).toBeTruthy();
    expect(screen.getByText(/No −3/)).toBeTruthy();
  });

  it('renders nothing when feature lookup misses (defensive)', () => {
    const missing: TooltipData = {
      featureId: 'nonexistent',
      clubId: 'real_madrid',
      anchorRect: makeRect(0, 0),
    };
    render(
      <HoverTooltipCard data={missing} features={features} clubs={clubs} scoring={scoring} />
    );
    expect(document.body.querySelector('[data-testid="hover-tooltip-card"]')).toBeNull();
  });
});
