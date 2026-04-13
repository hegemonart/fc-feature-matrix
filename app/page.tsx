'use client';

import { useState, useMemo, useRef, useCallback, useEffect } from 'react';
import {
  CATEGORIES,
  PRODUCTS,
  FEATURES,
  BAND_META,
  ALL_IDS,
  type PresenceStatus,
  type CategoryId,
  type BandId,
  type Feature,
  type Product,
  type Category,
} from '@/lib/data';
import { trackEvent } from '@/lib/track';

/* ── Padlock SVG (reused in flow nav) ── */
const PadlockIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

/* ── Locked tabs data ── */
const LOCKED_TABS = [
  { id: 'ticketing', name: 'Ticket Purchase', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="6" width="20" height="12" rx="2"/><path d="M2 10h20"/></svg> },
  { id: 'merch', name: 'Merch Store', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20.38 3.46L16 2 12 3.46 8 2 3.62 3.46A2 2 0 002 5.38V21l4-2 4 2 4-2 4 2 4-2V5.38a2 2 0 00-1.62-1.92z"/></svg> },
  { id: 'subscriptions', name: 'Subscriptions', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M23 4v6h-6M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg> },
  { id: 'matchday', name: 'Matchday Experience', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3"/></svg> },
  { id: 'hospitality', name: 'Hospitality Packages', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg> },
  { id: 'sponsorship', name: 'Sponsorship Visibility', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg> },
  { id: 'between-season', name: 'Between Season', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg> },
  { id: 'past-seasons', name: 'Past Seasons', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg> },
];

/* ── Band to CSS var color ── */
function bandColorVar(band: BandId): string {
  switch (band) {
    case 'table_stakes': return 'var(--green)';
    case 'expected': return 'var(--yellow)';
    case 'competitive': return 'var(--orange)';
    case 'innovation': return 'var(--red)';
  }
}

const totalProducts = PRODUCTS.length;

export default function FeatureMatrixPage() {
  /* ── State ── */
  const [filterTypes, setFilterTypes] = useState<Set<string>>(new Set(['club', 'governing', 'league']));
  const [activeCat, setActiveCat] = useState<CategoryId | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [adoptionSort, setAdoptionSort] = useState<'asc' | 'desc' | null>(null);
  const [featureAlphaSort, setFeatureAlphaSort] = useState(false);
  const [scoreSort, setScoreSort] = useState<'asc' | 'desc' | null>('desc');

  /* ── Auth ── */
  const [authed, setAuthed] = useState(false);
  const [authEmail, setAuthEmail] = useState('');
  const [loginModalVisible, setLoginModalVisible] = useState(false);
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);

  /* ── Locked / Coming Soon modal ── */
  const [lockedModalVisible, setLockedModalVisible] = useState(false);
  const [lockedFlowName, setLockedFlowName] = useState('');
  const [comingSoonVisible, setComingSoonVisible] = useState(false);
  const [comingSoonFlowName, setComingSoonFlowName] = useState('');

  /* ── Tooltip ── */
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipData, setTooltipData] = useState<{
    feature: string;
    desc: string;
    product: string;
    status: PresenceStatus;
    tier: string;
    weightYes: number;
    weightNo: number;
  } | null>(null);


  /* ── Derived data ── */

  /** Total score per product, filtered by active category */
  const productScores = useMemo(() => {
    const feats = activeCat ? FEATURES.filter(f => f.cat === activeCat) : FEATURES;
    const scores: Record<string, number> = {};
    PRODUCTS.forEach(p => {
      let total = 0;
      feats.forEach(f => {
        total += f.presence[p.id] === 'full' ? f.weightYes : f.weightNo;
      });
      scores[p.id] = total;
    });
    return scores;
  }, [activeCat]);

  const visibleProds = useMemo(() => {
    const filtered = PRODUCTS.filter(p => filterTypes.has(p.type));
    if (scoreSort) {
      filtered.sort((a, b) => scoreSort === 'desc'
        ? productScores[b.id] - productScores[a.id]
        : productScores[a.id] - productScores[b.id]);
    } else {
      filtered.sort((a, b) => a.name.localeCompare(b.name));
    }
    return filtered;
  }, [filterTypes, scoreSort, productScores]);

  const visibleFeats = useMemo(() => {
    return FEATURES.filter(f => {
      if (activeCat && f.cat !== activeCat) return false;
      return true;
    });
  }, [activeCat]);

  const sortedFeats = useMemo(() => {
    const feats = [...visibleFeats];
    if (adoptionSort) {
      feats.sort((a, b) => adoptionSort === 'asc'
        ? (a.adoptionPct ?? 0) - (b.adoptionPct ?? 0)
        : (b.adoptionPct ?? 0) - (a.adoptionPct ?? 0));
    } else if (featureAlphaSort) {
      feats.sort((a, b) => {
        const catA = CATEGORIES.find(c => c.id === a.cat)!.name;
        const catB = CATEGORIES.find(c => c.id === b.cat)!.name;
        if (catA !== catB) return catA.localeCompare(catB);
        return a.name.localeCompare(b.name);
      });
    }
    return feats;
  }, [visibleFeats, adoptionSort, featureAlphaSort]);

  /* ── Sidebar counts (always based on full dataset) ── */
  const catCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    CATEGORIES.forEach(c => (counts[c.id] = FEATURES.filter(f => f.cat === c.id).length));
    return counts;
  }, []);


  /* ── Auth: check session on mount ── */
  useEffect(() => {
    fetch('/api/auth/me').then(r => r.json()).then(d => {
      if (d.authenticated) { setAuthed(true); setAuthEmail(d.email); }
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
        setAuthed(true);
        setAuthEmail(data.email);
        setLoginModalVisible(false);
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
  }, []);

  const handleTabClick = useCallback((name: string) => {
    if (authed) {
      trackEvent('tab_click', { tab: name, outcome: 'coming_soon' });
      setComingSoonFlowName(name);
      setComingSoonVisible(true);
    } else {
      trackEvent('tab_click', { tab: name, outcome: 'locked' });
      setLockedFlowName(name);
      setLockedModalVisible(true);
    }
  }, [authed]);

  /* ── Handlers ── */
  const handleShowFeatureDetail = useCallback((fid: string) => {
    const f = FEATURES.find(x => x.id === fid);
    trackEvent('feature_click', { featureId: fid, featureName: f?.name });
    setSelectedFeature(fid);
    setSelectedProduct(null);
  }, []);

  const handleShowProductDetail = useCallback((pid: string) => {
    const p = PRODUCTS.find(x => x.id === pid);
    trackEvent('product_click', { productId: pid, productName: p?.name });
    setSelectedProduct(pid);
    setSelectedFeature(null);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedFeature(null);
    setSelectedProduct(null);
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilterTypes(new Set(['club', 'governing', 'league']));
    setActiveCat(null);
    setSelectedFeature(null);
    setSelectedProduct(null);
    setAdoptionSort(null);
    setFeatureAlphaSort(false);
    setScoreSort(null);
  }, []);


  /* ── Tooltip handlers ── */
  const handleCellMouseOver = useCallback((fid: string, pid: string) => {
    const f = FEATURES.find(x => x.id === fid);
    const p = PRODUCTS.find(x => x.id === pid);
    if (!f || !p) return;
    setTooltipData({
      feature: f.name,
      desc: f.desc,
      product: p.name,
      status: f.presence[pid],
      tier: f.tier,
      weightYes: f.weightYes,
      weightNo: f.weightNo,
    });
    setTooltipVisible(true);
  }, []);

  const handleCellMouseMove = useCallback((e: React.MouseEvent) => {
    if (!tooltipRef.current) return;
    const margin = 14;
    let left = e.clientX + margin;
    let top = e.clientY + margin;
    const tw = tooltipRef.current.offsetWidth || 300;
    const th = tooltipRef.current.offsetHeight || 120;
    if (left + tw > window.innerWidth - 8) left = e.clientX - tw - margin;
    if (top + th > window.innerHeight - 8) top = e.clientY - th - margin;
    tooltipRef.current.style.left = left + 'px';
    tooltipRef.current.style.top = top + 'px';
  }, []);

  const handleTableMouseLeave = useCallback(() => {
    setTooltipVisible(false);
  }, []);

  /* ── Detail panel content ── */
  const detailPanelCollapsed = !selectedFeature && !selectedProduct;

  /* ── Render ── */
  return (
    <div className="matrix-shell">
      {/* ── HEADER ── */}
      <header>
        <img src="/img/logo.svg" alt="Humbleteam" className="header-logo" />
        <div className="header-center">FC Benchmark <span>//</span> April 2026</div>
        {authed ? (
          <button className="sign-in-btn" onClick={handleLogout}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign out
          </button>
        ) : (
          <button className="sign-in-btn" onClick={() => setLoginModalVisible(true)}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            Sign in
          </button>
        )}
      </header>

      {/* ── FLOW NAV ── */}
      <nav className={`flow-nav${!authed ? ' locked-preview' : ''}`} role="tablist" aria-label="Analysis views">
        <button className="flow-tab active" role="tab" aria-selected="true">
          Homepage
        </button>
        <div className="locked-zone">
          <div className="locked-particles">
            <div className="lp"></div><div className="lp"></div><div className="lp"></div>
            <div className="lp"></div><div className="lp"></div><div className="lp"></div>
            <div className="lp"></div><div className="lp"></div>
          </div>
          {LOCKED_TABS.map(tab => (
            <button
              key={tab.id}
              className={`flow-tab flow-tab-locked${authed ? ' flow-tab-coming-soon' : ''}`}
              role="tab"
              aria-selected="false"
              onClick={() => handleTabClick(tab.name)}
            >
              <span className="locked-tab-icon">{tab.icon}</span>
              <span className="locked-tab-label">{tab.name}</span>
            </button>
          ))}
          <button className="unlock-cta" onClick={() => handleTabClick('Premium')}>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            Unlock
          </button>
        </div>
      </nav>

      {/* ── MAIN ── */}
      <div className="main">
        {/* ── SIDEBAR ── */}
        <div className={`sidebar${!authed ? ' locked-preview' : ''}`}>
          <h3>Category</h3>
          <div>
            {CATEGORIES.map(c => (
              <div
                key={c.id}
                className={`cat-item${activeCat === c.id ? ' active' : ''}`}
                onClick={() => setActiveCat(activeCat === c.id ? null : c.id)}
              >
                <span className="cat-name">{c.name}</span>
                <span className="cat-count">{catCounts[c.id]}</span>
              </div>
            ))}
          </div>

          <div className="sidebar-type-filter">
            <h3>Type</h3>
            {[
              { val: 'club', label: 'FC' },
              { val: 'governing', label: 'Federation' },
              { val: 'league', label: 'League' },
            ].map(t => (
              <label key={t.val} className="type-checkbox">
                <input
                  type="checkbox"
                  checked={filterTypes.has(t.val)}
                  onChange={() => {
                    setFilterTypes(prev => {
                      const next = new Set(prev);
                      if (next.has(t.val)) next.delete(t.val);
                      else next.add(t.val);
                      return next;
                    });
                  }}
                />
                <span className="type-checkbox-label">{t.label}</span>
              </label>
            ))}
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
                  <th
                    className="feature-col sortable"
                    onClick={() => { if (!authed) return; setAdoptionSort(null); setScoreSort(null); setFeatureAlphaSort(prev => !prev); }}
                  >
                    Feature {featureAlphaSort ? '\u25B2' : ''}
                  </th>
                  {visibleProds.map(p => (
                    <th key={p.id}>
                      <div
                        className={`col-header${selectedProduct === p.id ? ' highlighted' : ''}`}
                        onClick={() => { if (!authed) return; handleShowProductDetail(p.id); }}
                      >
                        <span className="col-label">{p.name}</span>
                        <div className={`col-logo${p.darkLogo ? ' dark-logo' : ''}`}>
                          <img src={p.logo} alt={p.name} />
                        </div>
                      </div>
                    </th>
                  ))}
                  <th
                    className="freq-col sortable"
                    onClick={() => {
                      if (!authed) return;
                      setFeatureAlphaSort(false);
                      setScoreSort(null);
                      setAdoptionSort(prev => prev === 'asc' ? 'desc' : prev === 'desc' ? null : 'asc');
                    }}
                  >
                    Adoption {adoptionSort === 'asc' ? '\u25B2' : adoptionSort === 'desc' ? '\u25BC' : ''}
                  </th>
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
                    showCategorySeps={!adoptionSort}
                    selectedFeature={selectedFeature}
                    selectedProduct={selectedProduct}
                    onFeatureClick={authed ? handleShowFeatureDetail : () => {}}
                    onCellMouseOver={authed ? handleCellMouseOver : () => {}}
                    onCellMouseMove={authed ? handleCellMouseMove : () => {}}
                    previewMode={!authed}
                  />
                )}
              </tbody>
              <tfoot>
                <tr className="score-row">
                  <td
                    className="feature-col score-label sortable"
                    onClick={() => {
                      if (!authed) return;
                      setScoreSort(prev => prev === 'desc' ? 'asc' : prev === 'asc' ? null : 'desc');
                    }}
                  >
                    Total Score {scoreSort === 'desc' ? '\u25BC' : scoreSort === 'asc' ? '\u25B2' : ''}
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
                  <td className="freq-col"></td>
                </tr>
              </tfoot>
            </table>
          </div>
          {!authed && (
            <div className="preview-blur-overlay">
              <div className="preview-cta">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="32" height="32">
                  <rect x="3" y="11" width="18" height="11" rx="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
                <div className="preview-cta-title">Sign in to unlock full matrix</div>
                <div className="preview-cta-desc">Access all {FEATURES.length} features across {PRODUCTS.length} products with filters, sorting, and detailed breakdowns.</div>
                <button className="preview-cta-btn" onClick={() => setLoginModalVisible(true)}>
                  Sign in
                </button>
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
                onClose={handleCloseDetail}
                onProductClick={handleShowProductDetail}
              />
            )}
            {selectedProduct && (
              <ProductDetail
                pid={selectedProduct}
                onClose={handleCloseDetail}
                onFeatureClick={handleShowFeatureDetail}
              />
            )}
          </div>
        </div>
      </div>


      {/* ── LOCKED MODAL ── */}
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
          <a className="locked-btn" href="mailto:atillyard@brentfordfc.com?subject=Access%20Request%20%E2%80%93%20FC%20Benchmark&body=Hi%2C%0A%0AI%E2%80%99d%20like%20to%20request%20access%20to%20the%20locked%20analysis%20views%20on%20FC%20Benchmark.%0A%0AThanks">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="4" width="20" height="16" rx="2" />
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
            </svg>
            Request access from admin
          </a>
          <button className="locked-dismiss" onClick={() => setLockedModalVisible(false)}>Maybe later</button>
        </div>
      </div>

      {/* ── LOGIN MODAL ── */}
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

      {/* ── COMING SOON MODAL ── */}
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
          <p>The <span className="locked-flow-name">{comingSoonFlowName}</span> analysis is currently being built. This view will be available in a future update.</p>
          <button className="locked-btn" onClick={() => setComingSoonVisible(false)}>Got it</button>
        </div>
      </div>

      {/* ── CELL TOOLTIP ── */}
      <div
        className={`cell-tooltip${tooltipVisible ? ' visible' : ''}`}
        ref={tooltipRef}
        role="tooltip"
        aria-hidden={!tooltipVisible}
      >
        {tooltipData && (
          <>
            <div className="tt-feature">{tooltipData.product}</div>
            <div className="tt-product">{tooltipData.feature}</div>
            <div className="tt-desc">{tooltipData.desc}</div>
            <div className="tt-weights">
              <span className="tt-tier">Tier: {{ A: 'Must-have', B: 'Commercial table stakes', C: 'ROI driver', D: 'Differentiator', E: 'Content depth', F: 'Experimental' }[tooltipData.tier] || tooltipData.tier}</span>
              <span className="tt-weight yes">Yes {tooltipData.weightYes >= 0 ? '+' : ''}{tooltipData.weightYes}</span>
              <span className="tt-weight no">No {tooltipData.weightNo}</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ================================================================
   TABLE ROWS — separated to keep main component readable
   ================================================================ */

function TableRows({
  feats,
  prods,
  showCategorySeps,
  selectedFeature,
  selectedProduct,
  onFeatureClick,
  onCellMouseOver,
  onCellMouseMove,
  previewMode,
}: {
  feats: Feature[];
  prods: Product[];
  showCategorySeps: boolean;
  selectedFeature: string | null;
  selectedProduct: string | null;
  onFeatureClick: (fid: string) => void;
  onCellMouseOver: (fid: string, pid: string) => void;
  onCellMouseMove: (e: React.MouseEvent) => void;
  previewMode?: boolean;
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
          <td className="cat-spacer"></td>
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
    rows.push(
      <tr className={hl} key={f.id} style={rowStyle}>
        <td className="feature-name" onClick={() => onFeatureClick(f.id)}>
          <div className="feature-inner">
            <div className={`feature-band ${f.band}`}></div>
            <span className="feature-text" title={f.name}>{f.name}</span>
          </div>
        </td>
        {prods.map(p => {
          const state = f.presence[p.id];
          let cls = 'cell';
          if (state === 'full') cls += ' has-full';
          if (selectedProduct === p.id) cls += ' highlighted';

          return (
            <td
              key={p.id}
              className={cls}
              onClick={() => onFeatureClick(f.id)}
              onMouseOver={() => onCellMouseOver(f.id, p.id)}
              onMouseMove={onCellMouseMove}
            >
              {state === 'full' && <span className="check">{'\u2713'}</span>}
              {state === 'absent' && <span className="no-check">{'\u00B7'}</span>}
            </td>
          );
        })}
        <td className="freq-col">
          <div className="freq-inner">
            <div className="freq-bar-wrap">
              <div className={`freq-bar ${f.band}`} style={{ width: `${f.adoptionPct}%` }}></div>
            </div>
            <span className="freq-label">{f.adoptionPct}%</span>
          </div>
        </td>
      </tr>
    );
  });

  return <>{rows}</>;
}

/* ================================================================
   FEATURE DETAIL PANEL
   ================================================================ */

function FeatureDetail({
  fid,
  onClose,
  onProductClick,
}: {
  fid: string;
  onClose: () => void;
  onProductClick: (pid: string) => void;
}) {
  const f = FEATURES.find(x => x.id === fid);
  if (!f) return null;
  const cat = CATEGORIES.find(c => c.id === f.cat)!;
  const bandLabel = BAND_META.find(b => b.id === f.band)!.name;
  const fullList = ALL_IDS.filter(id => f.presence[id] === 'full');
  const absentList = ALL_IDS.filter(id => f.presence[id] === 'absent');
  const pName = (id: string) => PRODUCTS.find(p => p.id === id)!.name;

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
            {fullList.length} of {totalProducts} products
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
   PRODUCT DETAIL PANEL
   ================================================================ */

function ProductDetail({
  pid,
  onClose,
  onFeatureClick,
}: {
  pid: string;
  onClose: () => void;
  onFeatureClick: (fid: string) => void;
}) {
  const p = PRODUCTS.find(x => x.id === pid);
  if (!p) return null;

  const fullCount = FEATURES.filter(f => f.presence[pid] === 'full').length;

  let weightedScore = 0;
  let maxWeighted = 0;
  FEATURES.forEach(f => {
    maxWeighted += f.weightYes;
    if (f.presence[pid] === 'full') {
      weightedScore += f.weightYes;
    } else {
      weightedScore += f.weightNo;
    }
  });
  const pct = Math.round(fullCount / FEATURES.length * 100);

  /* ── Group features into 3 sections ── */
  const missingHighImpact = FEATURES.filter(f => (f.tier === 'A' || f.tier === 'B' || f.tier === 'C') && f.presence[pid] === 'absent');
  const missingLowImpact = FEATURES.filter(f => (f.tier === 'D' || f.tier === 'E' || f.tier === 'F') && f.presence[pid] === 'absent');
  const featuresPresent = FEATURES.filter(f => f.presence[pid] === 'full');

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

      {/* ── Full Club Breakdown link ── */}
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
            {fullCount} of {FEATURES.length} features
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
