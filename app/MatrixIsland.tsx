'use client';

/* ================================================================
   <MatrixIsland>

   D-17 — Client Component matrix island. Owns ALL interactive
   state from the legacy app/page.tsx (1072 LOC); the page itself
   is a Server Component shell that loads data + renders this
   island.

   Wires up the 9 atomic components + 2 hooks shipped in plans 02
   and 03:
     <DataCell>, <SortHeader>, <MeterRow>, <HeaderBar>, <TopNav>,
     <CategoryFilter>, <TypeFilter>, <HoverTooltipCard>, plus
     useColumnSelection + useHoverTooltip.

   selectedProduct stays the AUTHORITATIVE state for both the
   detail panel AND column-tint (D-18). All existing auth/login/
   locked-modal/coming-soon/access-request handlers are preserved
   verbatim per RESEARCH.md "Current Homepage Structural Map".

   Diverges from app/page.tsx:
     - handleCellMouseMove DELETED (cursor-follow positioning is
       gone; tooltip is anchored to the cell rect now)
     - handleCellMouseOver REWRITTEN to call useHoverTooltip.handleCellEnter
     - handleTableMouseLeave delegates to useHoverTooltip.handleCellLeave
     - <nav.flow-nav> + .locked-zone replaced by <TopNav>
     - <header> replaced by <HeaderBar>
     - sidebar Category list → <CategoryFilter>
     - sidebar Type list → <TypeFilter>
     - sortable <th> blocks → <SortHeader>
     - <td.cell> → <DataCell>
     - <div.freq-bar-wrap> → <MeterRow>
     - portaled <HoverTooltipCard> replaces .cell-tooltip

   Preserved verbatim:
     - <thead> + <tfoot> Total-Score rows (RESEARCH.md P7)
     - preview-blur-overlay (guest CTA)
     - detail-panel rendering FeatureDetail / ProductDetail
     - the three locked-overlay modals (re-skinned in plan 05 only)
   ================================================================ */

import { useState, useMemo, useCallback, useEffect } from 'react';
import {
  CATEGORIES,
  BAND_META,
  ALL_IDS,
  type CategoryId,
  type BandId,
  type Feature,
  type Product,
  type ProductType,
} from '@/lib/data';
import { trackEvent } from '@/lib/track';

import { useHoverTooltip } from './components/matrix/useHoverTooltip';
import { useColumnSelection } from './components/matrix/useColumnSelection';
import { HeaderBar } from './components/matrix/HeaderBar';
import { TopNav } from './components/matrix/TopNav';
import { CategoryFilter } from './components/matrix/CategoryFilter';
import { TypeFilter } from './components/matrix/TypeFilter';
import { SortHeader } from './components/matrix/SortHeader';
import { DataCell } from './components/matrix/DataCell';
import { MeterRow } from './components/matrix/MeterRow';
import { HoverTooltipCard } from './components/matrix/HoverTooltipCard';
import type {
  CategoryItem,
  FeatureMeta,
  ClubMeta,
  CellScoring,
  MeterBand,
  SortState,
} from './components/matrix/types';

/* ── Padlock SVG (reused in locked modal) ── */
const PadlockIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

/* ── Locked tabs data (preserved from app/page.tsx) ── */
export const LOCKED_TABS = [
  { id: 'ticketing', name: 'Ticket Purchase' },
  { id: 'merch', name: 'Merch Store' },
  { id: 'subscriptions', name: 'Subscriptions' },
  { id: 'matchday', name: 'Matchday Experience' },
  { id: 'hospitality', name: 'Hospitality Packages' },
  { id: 'sponsorship', name: 'Sponsorship Visibility' },
  { id: 'between-season', name: 'Between Season' },
  { id: 'past-seasons', name: 'Past Seasons' },
];

/* ── Band → CSS var color (preserved) ── */
function bandColorVar(band: BandId): string {
  switch (band) {
    case 'table_stakes': return 'var(--green)';
    case 'expected': return 'var(--yellow)';
    case 'competitive': return 'var(--orange)';
    case 'innovation': return 'var(--red)';
  }
}

/** Map analysis BandId → MeterRow's MeterBand contract (D-06). */
function bandToMeterBand(band: BandId | undefined): MeterBand {
  switch (band) {
    case 'table_stakes': return 'competitive';
    case 'expected': return 'mid';
    case 'competitive': return 'weak';
    case 'innovation': return 'bottom';
    default: return 'bottom';
  }
}

export interface MatrixIslandProps {
  /** Serialized list of products from the Server Component shell. */
  products: Product[];
  /** Serialized list of features (with computed bands + adoption). */
  features: Feature[];
  /** Per-product score map keyed by product id. */
  scores: Record<string, number>;
  /** Build date from process.env.BUILD_DATE (Server-resolved string). */
  buildDate: string;
}

export default function MatrixIsland({ products, features, buildDate }: MatrixIslandProps) {
  /* ── State (preserved verbatim from app/page.tsx) ── */
  const [filterTypes, setFilterTypes] = useState<Set<string>>(new Set(['club', 'governing', 'league']));
  const [activeCat, setActiveCat] = useState<CategoryId | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [featureAlphaSort, setFeatureAlphaSort] = useState(false);
  const [scoreSort, setScoreSort] = useState<'asc' | 'desc' | null>('desc');

  /* ── Auth (preserved verbatim) ── */
  const [authed, setAuthed] = useState(false);
  const [authEmail, setAuthEmail] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);
  const [isPremium, setIsPremium] = useState(false);
  const [loginModalVisible, setLoginModalVisible] = useState(false);
  const [ctaView, setCtaView] = useState<'cta' | 'login'>('cta');
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  /* ── Locked / Coming Soon modal (preserved verbatim) ── */
  const [lockedModalVisible, setLockedModalVisible] = useState(false);
  const [lockedFlowName, setLockedFlowName] = useState('');
  const [comingSoonVisible, setComingSoonVisible] = useState(false);
  const [comingSoonFlowName, setComingSoonFlowName] = useState('');
  const [requestSending, setRequestSending] = useState(false);
  const [, setRequestSent] = useState<string | null>(null);

  /* ── Tooltip + column selection (D-21 / D-18) ── */
  const { tooltipData, handleCellEnter, handleCellLeave } = useHoverTooltip();
  /* ── Crosshair highlight state ── */
  const [hoveredFid, setHoveredFid] = useState<string | null>(null);
  const [hoveredPid, setHoveredPid] = useState<string | null>(null);
  // selectedProduct is the AUTHORITATIVE column-tint state per D-18 directive.
  // useColumnSelection is referenced for parity / future migration but reads
  // off selectedProduct; isSelected delegates to a comparison so the existing
  // Product-detail panel keeps working without divergence.
  const _columnHelper = useColumnSelection();
  const isColumnSelected = useCallback((clubId: string) => selectedProduct === clubId, [selectedProduct]);
  void _columnHelper;

  const sendAccessRequest = useCallback(async (feature: string, source: string, email?: string) => {
    setRequestSending(true);
    try {
      const res = await fetch('/api/email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feature, source, email }),
      });
      if (!res.ok) throw new Error('Failed');
      setRequestSent(feature);
      setTimeout(() => setRequestSent(null), 3000);
    } catch {
      alert('Failed to send request. Please try again.');
    } finally {
      setRequestSending(false);
    }
  }, []);

  /* ── Derived data ── */

  /** Total score per product, filtered by active category */
  const productScores = useMemo(() => {
    const feats = activeCat ? features.filter(f => f.cat === activeCat) : features;
    const out: Record<string, number> = {};
    products.forEach(p => {
      let total = 0;
      feats.forEach(f => {
        total += f.presence[p.id] === 'full' ? f.weightYes : f.weightNo;
      });
      out[p.id] = total;
    });
    return out;
  }, [activeCat, features, products]);

  const visibleProds = useMemo(() => {
    const filtered = products.filter(p => filterTypes.has(p.type));
    if (scoreSort) {
      filtered.sort((a, b) => scoreSort === 'desc'
        ? productScores[b.id] - productScores[a.id]
        : productScores[a.id] - productScores[b.id]);
    } else {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    }
    return filtered;
  }, [products, filterTypes, scoreSort, productScores]);

  const visibleFeats = useMemo(() => {
    return features.filter(f => {
      if (activeCat && f.cat !== activeCat) return false;
      return true;
    });
  }, [activeCat, features]);

  const sortedFeats = useMemo(() => {
    const feats = [...visibleFeats];
    if (featureAlphaSort) {
      feats.sort((a, b) => {
        const catA = CATEGORIES.find(c => c.id === a.cat)!.name;
        const catB = CATEGORIES.find(c => c.id === b.cat)!.name;
        if (catA !== catB) return catA.localeCompare(catB);
        return a.name.localeCompare(b.name);
      });
    }
    return feats;
  }, [visibleFeats, featureAlphaSort]);

  /* ── Sidebar counts (always based on full dataset) ── */
  const catCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    CATEGORIES.forEach(c => (counts[c.id] = features.filter(f => f.cat === c.id).length));
    return counts;
  }, [features]);

  /* ── CategoryFilter source: derived from CATEGORIES + counts ── */
  const categoryItems: CategoryItem[] = useMemo(() => {
    return CATEGORIES.map(c => ({ id: c.id, name: c.name, count: catCounts[c.id] ?? 0 }));
  }, [catCounts]);

  /** Set<CategoryId> of collapsed categories. activeCat is "show only this
   *  category" (preserved single-select semantics). For CategoryFilter's
   *  collapse semantics we treat collapse-all-except-active when activeCat
   *  is set, else collapse none. */
  const collapsedCats: Set<CategoryId> = useMemo(() => {
    if (!activeCat) return new Set<CategoryId>();
    return new Set<CategoryId>(CATEGORIES.filter(c => c.id !== activeCat).map(c => c.id));
  }, [activeCat]);

  const handleCategoryToggle = useCallback((id: CategoryId) => {
    setActiveCat(prev => (prev === id ? null : id));
  }, []);

  /* ── Tooltip lookup maps (in-memory; D-21: no server hits on hover) ── */
  const featureMap: Map<string, FeatureMeta> = useMemo(() => {
    const m = new Map<string, FeatureMeta>();
    features.forEach(f => {
      m.set(f.id, {
        id: f.id,
        name: f.name,
        desc: f.desc,
        tier: f.tier,
        weightYes: f.weightYes,
        weightNo: f.weightNo,
      });
    });
    return m;
  }, [features]);

  const clubMap: Map<string, ClubMeta> = useMemo(() => {
    const m = new Map<string, ClubMeta>();
    products.forEach(p => m.set(p.id, { id: p.id, name: p.name }));
    return m;
  }, [products]);

  const scoringMap: Map<string, CellScoring> = useMemo(() => {
    const m = new Map<string, CellScoring>();
    features.forEach(f => {
      products.forEach(p => {
        m.set(`${p.id}:${f.id}`, { yes: f.weightYes, no: f.weightNo });
      });
    });
    return m;
  }, [features, products]);

  /* ── Sort state mappings to <SortHeader> contract (D-19) ── */
  const featureSortState: SortState = featureAlphaSort ? 'asc' : 'idle';
  const scoreSortState: SortState = scoreSort === 'asc' ? 'asc' : scoreSort === 'desc' ? 'desc' : 'idle';

  /* ── Auth: check session on mount (preserved verbatim) ── */
  useEffect(() => {
    fetch('/api/auth/me').then(r => r.json()).then(d => {
      if (d.authenticated) {
        setAuthed(true);
        setAuthEmail(d.email);
        setIsAdmin(d.isAdmin ?? false);
        setIsPremium(d.isPremium ?? false);
      }
    }).catch(() => {});
    trackEvent('page_view', { path: '/' });
  }, []);

  const handleLogin = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });
      const data = await res.json();
      if (res.ok && data.ok) {
        const meRes = await fetch('/api/auth/me');
        const meData = await meRes.json();
        setAuthed(true);
        setAuthEmail(data.email);
        setIsAdmin(meData.isAdmin ?? false);
        setIsPremium(meData.isPremium ?? false);
        setLoginModalVisible(false);
        setCtaView('cta');
        setLoginEmail('');
        setLoginPassword('');
      } else {
        setLoginError(data.error || 'Login failed');
      }
    } catch {
      setLoginError('Network error');
    } finally {
      setLoginLoading(false);
    }
  }, [loginEmail, loginPassword]);

  const handleLogout = useCallback(async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    setAuthed(false);
    setAuthEmail('');
    setIsAdmin(false);
    setIsPremium(false);
  }, []);

  const handleTabClick = useCallback((tabId: string) => {
    // Map tab id back to display name for tracking + modal copy.
    const tabName =
      tabId === 'home' ? 'Homepage' :
      tabId === 'unlock' ? 'Premium' :
      LOCKED_TABS.find(t => t.id === tabId)?.name ?? tabId;

    if (isAdmin || isPremium) {
      trackEvent('tab_click', { tab: tabName, outcome: 'coming_soon' });
      setComingSoonFlowName(tabName);
      setComingSoonVisible(true);
    } else if (authed) {
      trackEvent('tab_click', { tab: tabName, outcome: 'locked' });
      setLockedFlowName(tabName);
      setLockedModalVisible(true);
    } else {
      trackEvent('tab_click', { tab: tabName, outcome: 'locked' });
      setLockedFlowName(tabName);
      setLockedModalVisible(true);
    }
  }, [authed, isAdmin, isPremium]);

  /* ── Detail panel handlers (preserved) ── */
  const handleShowFeatureDetail = useCallback((fid: string) => {
    const f = features.find(x => x.id === fid);
    trackEvent('feature_click', { featureId: fid, featureName: f?.name });
    setSelectedFeature(fid);
    setSelectedProduct(null);
  }, [features]);

  const handleShowProductDetail = useCallback((pid: string) => {
    const p = products.find(x => x.id === pid);
    trackEvent('product_click', { productId: pid, productName: p?.name });
    setSelectedProduct(pid);
    setSelectedFeature(null);
  }, [products]);

  const handleCloseDetail = useCallback(() => {
    setSelectedFeature(null);
    setSelectedProduct(null);
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilterTypes(new Set(['club', 'governing', 'league']));
    setActiveCat(null);
    setSelectedFeature(null);
    setSelectedProduct(null);
    setFeatureAlphaSort(false);
    setScoreSort(null);
  }, []);

  /* ── Tooltip handlers — REWRITTEN per plan 04 spec ── */
  const handleCellMouseOver = useCallback((fid: string, pid: string, el: HTMLElement) => {
    handleCellEnter(fid, pid, el);
    setHoveredFid(fid);
    setHoveredPid(pid);
  }, [handleCellEnter]);

  const handleTableMouseLeave = useCallback(() => {
    handleCellLeave();
    setHoveredFid(null);
    setHoveredPid(null);
  }, [handleCellLeave]);

  /* ── Sort header click handlers (D-19 cycle) ── */
  const onFeatureSort = useCallback(() => {
    if (!authed) return;
    setScoreSort(null);
    setFeatureAlphaSort(prev => !prev);
  }, [authed]);

  const onScoreSort = useCallback(() => {
    if (!authed) return;
    // D-19 cycle: desc → asc → null
    setScoreSort(prev => prev === 'desc' ? 'asc' : prev === 'asc' ? null : 'desc');
  }, [authed]);

  /* ── Type filter handler ── */
  const handleTypeFilterChange = useCallback((next: Set<ProductType>) => {
    setFilterTypes(next as Set<string>);
  }, []);

  /* ── Detail panel content ── */
  const detailPanelCollapsed = !selectedFeature && !selectedProduct;

  /* ── TopNav tabs ── */
  const navTabs = useMemo(() => {
    const tabs: { id: string; label: string }[] = [
      { id: 'home', label: 'Homepage' },
    ];
    LOCKED_TABS.forEach(t => tabs.push({ id: t.id, label: t.name }));
    tabs.push({ id: 'unlock', label: 'Unlock everything' });
    return tabs;
  }, []);

  const lockedTabIds = useMemo(() => LOCKED_TABS.map(t => t.id), []);

  /* ── Render ── */
  return (
    <div className="matrix-shell">
      {/* ── HEADER (Admin + Sign out render inline via HeaderBar props) ── */}
      <HeaderBar
        buildDate={buildDate}
        authed={authed}
        isAdmin={isAdmin}
        onSignOut={handleLogout}
      />

      {/* ── TOP NAV (replaces <nav.flow-nav> + .locked-zone) ── */}
      <TopNav
        tabs={navTabs}
        activeTab="home"
        unlockTab="unlock"
        lockedTabs={lockedTabIds}
        onTabClick={handleTabClick}
      />

      {/* ── MAIN ── */}
      <div className="main">
        {/* ── SIDEBAR ── */}
        <div className={`sidebar${!authed ? ' locked-preview' : ''}`}>
          <h3>Category</h3>
          <CategoryFilter
            categories={categoryItems}
            collapsed={collapsedCats}
            onToggle={handleCategoryToggle}
          />

          <div className="sidebar-type-filter">
            <h3>Type</h3>
            <TypeFilter
              selected={filterTypes as Set<ProductType>}
              onChange={handleTypeFilterChange}
            />
          </div>

          <button className="clear-btn" onClick={handleClearFilters}>Clear filters</button>
        </div>

        {/* ── TABLE ── */}
        <div className={`table-wrapper${!authed ? ' preview-mode' : ''}`}>
          <div
            className="table-container"
            onMouseLeave={handleTableMouseLeave}
          >
            <table>
              <thead>
                <tr>
                  <th className="feature-col sortable">
                    <SortHeader
                      label="Feature"
                      state={featureSortState}
                      onSort={onFeatureSort}
                    />
                  </th>
                  {visibleProds.map(p => (
                    <th key={p.id} className={hoveredPid === p.id ? 'crosshair-col' : ''}>
                      <div
                        className={`col-header${selectedProduct === p.id ? ' highlighted' : ''}`}
                        onClick={() => { if (!authed) return; handleShowProductDetail(p.id); }}
                      >
                        <span className="col-label">{p.name}</span>
                        <div className={`col-logo${p.darkLogo ? ' dark-logo' : ''}`}>
                          {/* eslint-disable-next-line @next/next/no-img-element */}
                          <img src={p.logo} alt={p.name} />
                        </div>
                      </div>
                    </th>
                  ))}
                </tr>
                <tr className="score-row score-row-top">
                  <td className="feature-col score-label sortable">
                    <SortHeader
                      label={`Total Score`}
                      state={scoreSortState}
                      onSort={onScoreSort}
                    />
                  </td>
                  {visibleProds.map(p => {
                    const s = productScores[p.id];
                    return (
                      <td key={p.id} className={`score-cell${selectedProduct === p.id ? ' highlighted' : ''}`}>
                        <span className={`score-value ${s >= 0 ? 'positive' : 'negative'}`}>
                          {s >= 0 ? '+' : ''}{s}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {visibleFeats.length === 0 ? (
                  <tr>
                    <td colSpan={visibleProds.length + 2} className="no-results">
                      No features match your filters.
                    </td>
                  </tr>
                ) : (
                  <TableRows
                    feats={sortedFeats}
                    prods={visibleProds}
                    showCategorySeps={true}
                    selectedFeature={selectedFeature}
                    isColumnSelected={isColumnSelected}
                    onFeatureClick={authed ? handleShowFeatureDetail : () => {}}
                    onCellMouseOver={authed ? handleCellMouseOver : () => {}}
                    onCellLeave={handleCellLeave}
                    previewMode={!authed}
                    hoveredFid={hoveredFid}
                    hoveredPid={hoveredPid}
                  />
                )}
              </tbody>
            </table>
          </div>
          {!authed && (
            <div className="preview-blur-overlay">
              <div className="preview-cta">
                {ctaView === 'cta' ? (
                  <>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="32" height="32">
                      <rect x="3" y="11" width="18" height="11" rx="2" />
                      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                    </svg>
                    <div className="preview-cta-title">Sign in to unlock full matrix</div>
                    <div className="preview-cta-desc">Access all {features.length} features across {products.length} products with filters, sorting, and detailed breakdowns.</div>
                    <button className="preview-cta-btn" onClick={() => { setLoginError(''); setCtaView('login'); }}>
                      Sign in
                    </button>
                    <a className="preview-cta-btn preview-cta-request" href="mailto:sergey@humbleteam.com?subject=Access%20Request%20%E2%80%93%20FC%20Benchmark&body=Hi%2C%0A%0AI%E2%80%99d%20like%20to%20request%20access%20to%20the%20FC%20Benchmark%20matrix.%0A%0AThanks">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="2" y="4" width="20" height="16" rx="2" />
                        <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
                      </svg>
                      Request access
                    </a>
                  </>
                ) : (
                  <>
                    <div className="preview-cta-title">Sign in</div>
                    <div className="preview-cta-desc">Enter your credentials to access all analysis views.</div>
                    <form onSubmit={handleLogin} className="login-form">
                      <label className="login-label">
                        Email
                        <input
                          type="text"
                          className="login-input"
                          value={loginEmail}
                          onChange={e => setLoginEmail(e.target.value)}
                          placeholder="you@example.com"
                          autoComplete="email"
                          required
                        />
                      </label>
                      <label className="login-label">
                        Password
                        <input
                          type="password"
                          className="login-input"
                          value={loginPassword}
                          onChange={e => setLoginPassword(e.target.value)}
                          placeholder={'\u2022'.repeat(8)}
                          autoComplete="current-password"
                          required
                        />
                      </label>
                      {loginError && <div className="login-error">{loginError}</div>}
                      <button type="submit" className="preview-cta-btn login-submit" disabled={loginLoading}>
                        {loginLoading ? 'Signing in\u2026' : 'Sign in'}
                      </button>
                    </form>
                    <button className="locked-dismiss" onClick={() => { setCtaView('cta'); setLoginError(''); setLoginEmail(''); setLoginPassword(''); }}>Cancel</button>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* ── DETAIL PANEL ── */}
        <div className={`detail-panel${detailPanelCollapsed ? ' collapsed' : ''}`}>
          <div className="detail-inner">
            {selectedFeature && (
              <FeatureDetail
                fid={selectedFeature}
                features={features}
                products={products}
                onClose={handleCloseDetail}
                onProductClick={handleShowProductDetail}
              />
            )}
            {selectedProduct && (
              <ProductDetail
                pid={selectedProduct}
                features={features}
                products={products}
                onClose={handleCloseDetail}
                onFeatureClick={handleShowFeatureDetail}
              />
            )}
          </div>
        </div>
      </div>

      {/* ── LOCKED MODAL (preserved verbatim) ── */}
      <div
        className={`locked-overlay${lockedModalVisible ? ' visible' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="lockedTitle"
        onClick={e => { if (e.target === e.currentTarget) setLockedModalVisible(false); }}
      >
        <div className="locked-card">
          <div className="lock-big">
            <PadlockIcon />
          </div>
          <h3 id="lockedTitle">Analysis Restricted</h3>
          <p>The <span className="locked-flow-name">{lockedFlowName}</span> view is locked. This deep-dive flow requires admin access to unlock comparative analysis across products.</p>
          <button className="locked-btn" disabled={requestSending} onClick={() => { sendAccessRequest(lockedFlowName, 'locked_modal', authEmail); setLockedModalVisible(false); }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="4" width="20" height="16" rx="2" />
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
            </svg>
            {requestSending ? 'Sending...' : 'Request access from admin'}
          </button>
          <button className="locked-dismiss" onClick={() => setLockedModalVisible(false)}>Maybe later</button>
        </div>
      </div>

      {/* ── LOGIN MODAL (preserved verbatim) ── */}
      <div
        className={`locked-overlay${loginModalVisible ? ' visible' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="loginTitle"
        onClick={e => { if (e.target === e.currentTarget) { setLoginModalVisible(false); setLoginError(''); } }}
      >
        <div className="locked-card login-card">
          <h3 id="loginTitle">Sign in</h3>
          <p className="login-subtitle">Enter your credentials to access all analysis views.</p>
          <form onSubmit={handleLogin} className="login-form">
            <label className="login-label">
              Email
              <input
                type="email"
                className="login-input"
                value={loginEmail}
                onChange={e => setLoginEmail(e.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </label>
            <label className="login-label">
              Password
              <input
                type="password"
                className="login-input"
                value={loginPassword}
                onChange={e => setLoginPassword(e.target.value)}
                placeholder={'\u2022'.repeat(8)}
                autoComplete="current-password"
                required
              />
            </label>
            {loginError && <div className="login-error">{loginError}</div>}
            <button type="submit" className="locked-btn login-submit" disabled={loginLoading}>
              {loginLoading ? 'Signing in\u2026' : 'Sign in'}
            </button>
          </form>
          <button className="locked-dismiss" onClick={() => { setLoginModalVisible(false); setLoginError(''); }}>Cancel</button>
        </div>
      </div>

      {/* ── COMING SOON MODAL (preserved verbatim) ── */}
      <div
        className={`locked-overlay${comingSoonVisible ? ' visible' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby="comingSoonTitle"
        onClick={e => { if (e.target === e.currentTarget) setComingSoonVisible(false); }}
      >
        <div className="locked-card coming-soon-card">
          <div className="coming-soon-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          </div>
          <h3 id="comingSoonTitle">Coming Soon</h3>
          <p>The <span className="locked-flow-name">{comingSoonFlowName}</span> analysis is locked. Contact admin to unlock this view.</p>
          <button className="locked-btn" disabled={requestSending} onClick={() => { sendAccessRequest(comingSoonFlowName, 'coming_soon_modal', authEmail); setComingSoonVisible(false); }}>{requestSending ? 'Sending...' : 'Send request'}</button>
        </div>
      </div>

      {/* ── PORTALED HOVER TOOLTIP ── */}
      <HoverTooltipCard
        data={tooltipData}
        features={featureMap}
        clubs={clubMap}
        scoring={scoringMap}
      />
    </div>
  );
}

/* ================================================================
   TABLE ROWS — separated to keep MatrixIsland readable.

   Each cell now uses <DataCell> from plan 02 (selected/intermediate/state +
   data-feature/-club attrs that the portaled tooltip reads). The frequency
   column uses <MeterRow> from plan 02 (D-06).
   ================================================================ */

function TableRows({
  feats,
  prods,
  showCategorySeps,
  selectedFeature,
  isColumnSelected,
  onFeatureClick,
  onCellMouseOver,
  onCellLeave,
  previewMode,
  hoveredFid,
  hoveredPid,
}: {
  feats: Feature[];
  prods: Product[];
  showCategorySeps: boolean;
  selectedFeature: string | null;
  isColumnSelected: (clubId: string) => boolean;
  onFeatureClick: (fid: string) => void;
  onCellMouseOver: (fid: string, pid: string, el: HTMLElement) => void;
  onCellLeave: () => void;
  previewMode?: boolean;
  hoveredFid?: string | null;
  hoveredPid?: string | null;
}) {
  const rows: React.ReactNode[] = [];
  let lastCat: string | null = null;
  let featureRowIndex = 0;

  feats.forEach((f, idx) => {
    if (showCategorySeps && f.cat !== lastCat) {
      lastCat = f.cat;
      const cat = CATEGORIES.find(c => c.id === f.cat)!;
      const sepBlur = previewMode && featureRowIndex >= 2
        ? { filter: `blur(${Math.min((featureRowIndex - 2) * 1.5, 10)}px)` }
        : undefined;
      rows.push(
        <tr className="category-sep-row" key={`sep-${f.cat}-${idx}`} style={sepBlur}>
          <td className="category-sep" colSpan={1}>
            <div className="cat-sep-inner">
              <span className="cat-sep-label">{cat.name}</span>
            </div>
          </td>
          {prods.map(p => (
            <td className="cat-spacer" key={p.id}></td>
          ))}
        </tr>
      );
    }

    const blurAmount = previewMode && featureRowIndex >= 2
      ? Math.min((featureRowIndex - 2) * 1.8, 12)
      : 0;
    const rowStyle = blurAmount > 0
      ? { filter: `blur(${blurAmount}px)`, pointerEvents: 'none' as const }
      : undefined;

    featureRowIndex++;

    const hl = selectedFeature === f.id ? ' highlighted' : '';
    const rowCrossHair = hoveredFid === f.id ? ' crosshair-row' : '';
    const checkerClass = featureRowIndex % 2 === 0 ? ' row-even' : ' row-odd';
    rows.push(
      <tr className={`${hl}${rowCrossHair}${checkerClass}`} key={f.id} style={rowStyle}>
        <td className="feature-name" onClick={() => onFeatureClick(f.id)}>
          <div className={`feature-band ${f.band}`} />
          <div className="feature-inner">
            <span className="feature-text" title={f.name}>{f.name}</span>
            <div className="feature-meter">
              <MeterRow
                band={bandToMeterBand(f.band)}
                value={f.adoptionPct ?? 0}
              />
            </div>
          </div>
        </td>
        {prods.map(p => {
          const state = f.presence[p.id];
          const value = state === 'full';
          const selected = isColumnSelected(p.id);
          const colCrossHair = hoveredPid === p.id ? ' crosshair-col' : '';

          return (
            <td
              key={p.id}
              className={`cell${value ? ' has-full' : ''}${selected ? ' highlighted' : ''}${colCrossHair}`}
              onClick={() => onFeatureClick(f.id)}
            >
              <DataCell
                selected={selected}
                intermediate={false}
                state="default"
                featureId={f.id}
                clubId={p.id}
                value={value}
                onMouseEnter={(e) => onCellMouseOver(f.id, p.id, e.currentTarget)}
                onMouseLeave={onCellLeave}
                onFocus={(e) => onCellMouseOver(f.id, p.id, e.currentTarget)}
                onBlur={onCellLeave}
              />
            </td>
          );
        })}
      </tr>
    );
  });

  return <>{rows}</>;
}

/* ================================================================
   FEATURE DETAIL PANEL (preserved — token swap only in plan 05)
   ================================================================ */

function FeatureDetail({
  fid,
  features,
  products,
  onClose,
  onProductClick,
}: {
  fid: string;
  features: Feature[];
  products: Product[];
  onClose: () => void;
  onProductClick: (pid: string) => void;
}) {
  const f = features.find(x => x.id === fid);
  if (!f) return null;
  const cat = CATEGORIES.find(c => c.id === f.cat)!;
  const bandLabel = BAND_META.find(b => b.id === f.band)!.name;
  const fullList = ALL_IDS.filter(id => f.presence[id] === 'full');
  const absentList = ALL_IDS.filter(id => f.presence[id] === 'absent');
  const pName = (id: string) => products.find(p => p.id === id)!.name;
  const totalProductsLocal = products.length;

  return (
    <>
      <div className="detail-header">
        <button className="detail-close" onClick={onClose}>{'\u00D7'}</button>
        <div className="detail-category" style={{ color: cat.color }}>{cat.name}</div>
        <div className="detail-title">{f.name}</div>
      </div>
      <div className="detail-desc">{f.desc}</div>
      <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '14px' }}>
        <div className={`detail-band ${f.band}`} style={{ margin: 0 }}>{bandLabel}</div>
      </div>
      <div className="detail-freq">
        <div className="detail-freq-label">Adoption rate</div>
        <div className="detail-freq-row">
          <span className="detail-freq-big">{f.adoptionPct}%</span>
          <span className="detail-freq-sub">
            {fullList.length} of {totalProductsLocal} products
          </span>
        </div>
        <div
          className={`detail-freq-bar ${f.band}`}
          style={{
            width: `${f.adoptionPct}%`,
            background: bandColorVar(f.band!),
          }}
        ></div>
      </div>
      <div className="detail-divider"></div>

      {fullList.length > 0 && (
        <>
          <div className="detail-products-label">Present</div>
          <div className="detail-products">
            {fullList.map(id => (
              <span key={id} className="product-chip" onClick={() => onProductClick(id)}>
                {pName(id)}
              </span>
            ))}
          </div>
        </>
      )}
      {absentList.length > 0 && (
        <>
          <div className="detail-missing-label">Not present</div>
          <div className="detail-products">
            {absentList.map(id => (
              <span key={id} className="product-chip dim" onClick={() => onProductClick(id)}>
                {pName(id)}
              </span>
            ))}
          </div>
        </>
      )}
    </>
  );
}

/* ================================================================
   PRODUCT DETAIL PANEL (preserved — token swap only in plan 05)
   ================================================================ */

function ProductDetail({
  pid,
  features,
  products,
  onClose,
  onFeatureClick,
}: {
  pid: string;
  features: Feature[];
  products: Product[];
  onClose: () => void;
  onFeatureClick: (fid: string) => void;
}) {
  const p = products.find(x => x.id === pid);
  if (!p) return null;

  const fullCount = features.filter(f => f.presence[pid] === 'full').length;

  let weightedScore = 0;
  let maxWeighted = 0;
  features.forEach(f => {
    maxWeighted += f.weightYes;
    if (f.presence[pid] === 'full') {
      weightedScore += f.weightYes;
    } else {
      weightedScore += f.weightNo;
    }
  });
  const pct = Math.round(fullCount / features.length * 100);

  const missingHighImpact = features.filter(f => (f.tier === 'A' || f.tier === 'B' || f.tier === 'C') && f.presence[pid] === 'absent');
  const missingLowImpact = features.filter(f => (f.tier === 'D' || f.tier === 'E' || f.tier === 'F') && f.presence[pid] === 'absent');
  const featuresPresent = features.filter(f => f.presence[pid] === 'full');

  return (
    <>
      <div className="detail-header">
        <button className="detail-close" onClick={onClose}>{'\u00D7'}</button>
        <div className="detail-title">{p.name}</div>
      </div>
      <div style={{ display: 'flex', gap: '6px', marginBottom: '12px' }}>
        <span className="product-detail-badge">{p.type}</span>
        <span className="product-detail-badge">{p.sport}</span>
      </div>

      <a className="breakdown-btn" href={`/club/${pid}`}>
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        Full Club Breakdown
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginLeft: 'auto', width: '11px', height: '11px', opacity: 0.6 }}>
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline points="15 3 21 3 21 9" />
          <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
      </a>

      <div className="detail-divider" style={{ margin: '12px 0' }}></div>

      <div className="detail-freq">
        <div className="detail-freq-label">Feature coverage</div>
        <div className="detail-freq-row">
          <span className="detail-freq-big">{pct}%</span>
          <span className="detail-freq-sub">
            {fullCount} of {features.length} features
          </span>
        </div>
        <div className="detail-freq-bar" style={{ width: `${pct}%`, background: 'var(--accent)' }}></div>
      </div>

      <div style={{ display: 'flex', gap: '16px', margin: '10px 0 6px' }}>
        <div>
          <div className="detail-freq-label">Weighted Score</div>
          <div className="weighted-score">
            <span className="weighted-score-big" style={{ color: weightedScore >= 0 ? 'var(--green)' : 'var(--red)' }}>
              {weightedScore >= 0 ? '+' : ''}{weightedScore}
            </span>
            <span className="weighted-score-sub">/ {maxWeighted}</span>
          </div>
        </div>
      </div>

      <div className="detail-divider"></div>

      {missingHighImpact.length > 0 && (
        <div>
          <div className="detail-products-label" style={{ color: 'var(--red)' }}>
            Missing High-Impact (Tier A/B/C)
          </div>
          <div className="product-feature-list">
            {missingHighImpact.map(f => {
              const cat = CATEGORIES.find(c => c.id === f.cat)!;
              return (
                <div key={f.id} className="product-feature-item" onClick={() => onFeatureClick(f.id)}>
                  <span className="product-feature-check absent">{'\u00B7'}</span>
                  <span className="product-feature-name">{f.name}</span>
                  <div className="product-feature-cat" style={{ background: cat.color }}></div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {missingLowImpact.length > 0 && (
        <div>
          <div className="detail-products-label" style={{ marginTop: '10px', color: 'var(--orange)' }}>
            Missing (Tier D/E/F)
          </div>
          <div className="product-feature-list">
            {missingLowImpact.map(f => {
              const cat = CATEGORIES.find(c => c.id === f.cat)!;
              return (
                <div key={f.id} className="product-feature-item" onClick={() => onFeatureClick(f.id)}>
                  <span className="product-feature-check absent">{'\u00B7'}</span>
                  <span className="product-feature-name">{f.name}</span>
                  <div className="product-feature-cat" style={{ background: cat.color }}></div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {featuresPresent.length > 0 && (
        <div>
          <div className="detail-products-label" style={{ marginTop: '10px', color: 'var(--green)' }}>
            Features Present
          </div>
          <div className="product-feature-list">
            {featuresPresent.map(f => {
              const cat = CATEGORIES.find(c => c.id === f.cat)!;
              const state = f.presence[pid];
              return (
                <div key={f.id} className="product-feature-item" onClick={() => onFeatureClick(f.id)}>
                  <span className={`product-feature-check ${state}`}>
                    {'\u2713'}
                  </span>
                  <span className="product-feature-name">{f.name}</span>
                  <div className="product-feature-cat" style={{ background: cat.color }}></div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </>
  );
}
