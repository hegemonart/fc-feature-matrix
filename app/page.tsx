'use client';

import { useState, useMemo, useRef, useCallback } from 'react';
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
  type BandMeta,
} from '@/lib/data';

/* ── Padlock SVG (reused in flow nav) ── */
const PadlockIcon = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

/* ── Locked tabs data ── */
const LOCKED_TABS = [
  { id: 'ticketing', name: 'Ticket Purchase' },
  { id: 'merch', name: 'Merch Store' },
  { id: 'subscriptions', name: 'Subscriptions' },
  { id: 'matchday', name: 'Matchday Experience' },
  { id: 'hospitality', name: 'Hospitality Packages' },
  { id: 'sponsorship', name: 'Sponsorship Visibility' },
  { id: 'between-season', name: 'Between Season' },
  { id: 'past-seasons', name: 'Past Seasons' },
];

/* ── Weight labels ── */
const WEIGHT_LABELS: Record<number, string> = {
  1: 'Differentiator',
  2: 'UX & Utility',
  3: 'Brand & Identity',
  4: 'Engagement Core',
  5: 'Revenue Critical',
};

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
  const [filterType, setFilterType] = useState<string>('all');
  const [filterSport, setFilterSport] = useState<string>('all');
  const [searchText, setSearchText] = useState('');
  const [activeCat, setActiveCat] = useState<CategoryId | null>(null);
  const [activeBand, setActiveBand] = useState<BandId | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);

  /* ── Locked modal ── */
  const [lockedModalVisible, setLockedModalVisible] = useState(false);
  const [lockedFlowName, setLockedFlowName] = useState('');

  /* ── Tooltip ── */
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipVisible, setTooltipVisible] = useState(false);
  const [tooltipData, setTooltipData] = useState<{
    feature: string;
    product: string;
    status: PresenceStatus;
  } | null>(null);

  const searchInputRef = useRef<HTMLInputElement>(null);

  /* ── Derived data ── */
  const visibleProds = useMemo(() => {
    return PRODUCTS.filter(p => {
      if (filterType === 'club' && p.type !== 'club') return false;
      if (filterType === 'league' && p.type === 'club') return false;
      if (filterSport === 'football' && p.sport !== 'football') return false;
      if (filterSport === 'other' && p.sport === 'football') return false;
      return true;
    });
  }, [filterType, filterSport]);

  const visibleFeats = useMemo(() => {
    const s = searchText.toLowerCase().trim();
    return FEATURES.filter(f => {
      if (s && !f.name.toLowerCase().includes(s) && !f.desc.toLowerCase().includes(s)) return false;
      if (activeCat && f.cat !== activeCat) return false;
      if (activeBand && f.band !== activeBand) return false;
      return true;
    });
  }, [searchText, activeCat, activeBand]);

  /* ── Header stats (always based on full dataset) ── */
  const bandCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    BAND_META.forEach(b => (counts[b.id] = 0));
    FEATURES.forEach(f => { if (f.band) counts[f.band]++; });
    return counts;
  }, []);

  /* ── Sidebar counts (always based on full dataset) ── */
  const catCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    CATEGORIES.forEach(c => (counts[c.id] = FEATURES.filter(f => f.cat === c.id).length));
    return counts;
  }, []);

  const bandSidebarCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    BAND_META.forEach(b => (counts[b.id] = FEATURES.filter(f => f.band === b.id).length));
    return counts;
  }, []);

  /* ── Handlers ── */
  const handleShowFeatureDetail = useCallback((fid: string) => {
    setSelectedFeature(fid);
    setSelectedProduct(null);
  }, []);

  const handleShowProductDetail = useCallback((pid: string) => {
    setSelectedProduct(pid);
    setSelectedFeature(null);
  }, []);

  const handleCloseDetail = useCallback(() => {
    setSelectedFeature(null);
    setSelectedProduct(null);
  }, []);

  const handleClearFilters = useCallback(() => {
    setFilterType('all');
    setFilterSport('all');
    setSearchText('');
    setActiveCat(null);
    setActiveBand(null);
    setSelectedFeature(null);
    setSelectedProduct(null);
    if (searchInputRef.current) searchInputRef.current.value = '';
  }, []);

  const handleLockedTabClick = useCallback((name: string) => {
    setLockedFlowName(name);
    setLockedModalVisible(true);
  }, []);

  /* ── Tooltip handlers ── */
  const handleCellMouseOver = useCallback((fid: string, pid: string) => {
    const f = FEATURES.find(x => x.id === fid);
    const p = PRODUCTS.find(x => x.id === pid);
    if (!f || !p) return;
    setTooltipData({
      feature: f.name,
      product: p.name,
      status: f.presence[pid],
    });
    setTooltipVisible(true);
  }, []);

  const handleCellMouseMove = useCallback((e: React.MouseEvent) => {
    if (!tooltipRef.current) return;
    const margin = 14;
    let left = e.clientX + margin;
    let top = e.clientY + margin;
    const tw = tooltipRef.current.offsetWidth || 180;
    const th = tooltipRef.current.offsetHeight || 70;
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
        <div className="logo">FC Benchmark <span>//</span> 2026</div>
        <div className="header-title">Feature Matrix</div>
        <div className="header-stats">
          <div className="stat-chip"><strong>{FEATURES.length}</strong> features</div>
          <div className="stat-chip"><strong>{PRODUCTS.length}</strong> products</div>
          {BAND_META.map(b => (
            <div className="stat-chip" key={b.id}><strong>{bandCounts[b.id]}</strong> {b.name}</div>
          ))}
        </div>
      </header>

      {/* ── FLOW NAV ── */}
      <nav className="flow-nav" role="tablist" aria-label="Analysis views">
        <button className="flow-tab active" role="tab" aria-selected="true">
          Homepage <span className="tab-badge">LIVE</span>
        </button>
        {LOCKED_TABS.map(tab => (
          <button
            key={tab.id}
            className="flow-tab locked"
            role="tab"
            aria-selected="false"
            onClick={() => handleLockedTabClick(tab.name)}
          >
            <span className="lock-icon"><PadlockIcon /></span>
            {tab.name}
          </button>
        ))}
      </nav>

      {/* ── TOOLBAR ── */}
      <div className="toolbar">
        <div className="search-wrap">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            ref={searchInputRef}
            placeholder="Search features..."
            onChange={e => setSearchText(e.target.value)}
          />
        </div>
        <div className="divider"></div>
        <div className="filter-group">
          <span className="filter-label">Type:</span>
          {[
            { val: 'all', label: 'All' },
            { val: 'club', label: 'Club' },
            { val: 'league', label: 'League / Org' },
          ].map(f => (
            <button
              key={f.val}
              className={`filter-btn${filterType === f.val ? ' active' : ''}`}
              onClick={() => setFilterType(f.val)}
            >{f.label}</button>
          ))}
        </div>
        <div className="divider"></div>
        <div className="filter-group">
          <span className="filter-label">Sport:</span>
          {[
            { val: 'all', label: 'All' },
            { val: 'football', label: 'Football' },
            { val: 'other', label: 'Other Sports' },
          ].map(f => (
            <button
              key={f.val}
              className={`filter-btn${filterSport === f.val ? ' active' : ''}`}
              onClick={() => setFilterSport(f.val)}
            >{f.label}</button>
          ))}
        </div>
        <div className="toolbar-right">
          <button className="clear-btn" onClick={handleClearFilters}>Clear filters</button>
        </div>
      </div>

      {/* ── MAIN ── */}
      <div className="main">
        {/* ── SIDEBAR ── */}
        <div className="sidebar">
          <h3>Category</h3>
          <div>
            {CATEGORIES.map(c => (
              <div
                key={c.id}
                className={`cat-item${activeCat === c.id ? ' active' : ''}`}
                onClick={() => setActiveCat(activeCat === c.id ? null : c.id)}
              >
                <div className="cat-dot" style={{ background: c.color }}></div>
                <span className="cat-name">{c.name}</span>
                <span className="cat-count">{catCounts[c.id]}</span>
              </div>
            ))}
          </div>
          <div className="sidebar-section">
            <h3>Band</h3>
            <div>
              {BAND_META.map(b => (
                <div
                  key={b.id}
                  className={`band-item${activeBand === b.id ? ' active' : ''}`}
                  onClick={() => setActiveBand(activeBand === b.id ? null : b.id)}
                >
                  <div className={`band-swatch ${b.cls}`}></div>
                  <span className="band-name">{b.name}</span>
                  <span className="band-count">{bandSidebarCounts[b.id]}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── TABLE ── */}
        <div
          className="table-container"
          onMouseLeave={handleTableMouseLeave}
        >
          <table>
            <thead>
              <tr>
                <th className="feature-col">Feature</th>
                {visibleProds.map(p => (
                  <th key={p.id}>
                    <div
                      className={`col-header${selectedProduct === p.id ? ' highlighted' : ''}`}
                      onClick={() => handleShowProductDetail(p.id)}
                    >
                      <span className="col-label">{p.name}</span>
                    </div>
                  </th>
                ))}
                <th className="freq-col">Adoption</th>
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
                  feats={visibleFeats}
                  prods={visibleProds}
                  selectedFeature={selectedFeature}
                  selectedProduct={selectedProduct}
                  onFeatureClick={handleShowFeatureDetail}
                  onCellMouseOver={handleCellMouseOver}
                  onCellMouseMove={handleCellMouseMove}
                  onProductClick={handleShowProductDetail}
                />
              )}
            </tbody>
          </table>
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

      {/* ── LEGEND ── */}
      <div className="legend">
        <div className="legend-item"><div className="legend-swatch table_stakes"></div>Table Stakes {'\u2265'}90%</div>
        <div className="legend-item"><div className="legend-swatch expected"></div>Expected 70{'\u2013'}89%</div>
        <div className="legend-item"><div className="legend-swatch competitive"></div>Competitive 40{'\u2013'}69%</div>
        <div className="legend-item"><div className="legend-swatch innovation"></div>Innovation {'<'}40%</div>
        <div className="legend-sep"></div>
        <div className="legend-item"><span style={{ color: 'var(--accent)', fontSize: '14px' }}>{'\u2713'}</span> Present</div>
        <div className="legend-item"><span style={{ color: 'var(--accent)', fontSize: '14px', opacity: 0.35 }}>{'\u2713'}</span> Partial</div>
        <div className="legend-item"><span style={{ color: 'var(--border)', fontSize: '11px' }}>{'\u00B7'}</span> Absent</div>
        <div className="legend-right">
          Showing {visibleFeats.length} of {FEATURES.length} features across {visibleProds.length} products
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
          <button className="locked-btn" onClick={() => setLockedModalVisible(false)}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12a19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 3.6 1.19h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 9a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
            </svg>
            Request access from admin
          </button>
          <button className="locked-dismiss" onClick={() => setLockedModalVisible(false)}>Maybe later</button>
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
            <div className="tt-feature">{tooltipData.feature}</div>
            <div className="tt-product">{tooltipData.product}</div>
            <div className={`tt-status ${tooltipData.status}`}>
              {tooltipData.status === 'full'
                ? '\u2713 Present'
                : tooltipData.status === 'partial'
                ? '\u2713 Partial'
                : '\u00B7 Absent'}
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
  selectedFeature,
  selectedProduct,
  onFeatureClick,
  onCellMouseOver,
  onCellMouseMove,
  onProductClick,
}: {
  feats: Feature[];
  prods: Product[];
  selectedFeature: string | null;
  selectedProduct: string | null;
  onFeatureClick: (fid: string) => void;
  onCellMouseOver: (fid: string, pid: string) => void;
  onCellMouseMove: (e: React.MouseEvent) => void;
  onProductClick: (pid: string) => void;
}) {
  const rows: React.ReactNode[] = [];
  let lastCat: string | null = null;

  feats.forEach((f, idx) => {
    if (f.cat !== lastCat) {
      lastCat = f.cat;
      const cat = CATEGORIES.find(c => c.id === f.cat)!;
      rows.push(
        <tr className="category-sep-row" key={`sep-${f.cat}`}>
          <td className="category-sep" colSpan={1}>
            <div className="cat-sep-inner">
              <div className="cat-sep-dot" style={{ background: cat.color }}></div>
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

    const hl = selectedFeature === f.id ? ' highlighted' : '';
    rows.push(
      <tr className={hl} key={f.id}>
        <td className="feature-name" onClick={() => onFeatureClick(f.id)}>
          <div className="feature-inner">
            <div className={`feature-band ${f.band}`}></div>
            <span className={`feature-weight w${f.weight}`}>W{f.weight}</span>
            <span className="feature-text" title={f.name}>{f.name}</span>
          </div>
        </td>
        {prods.map(p => {
          const state = f.presence[p.id];
          let cls = 'cell';
          if (state === 'full') cls += ' has-full';
          else if (state === 'partial') cls += ' has-partial';
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
              {state === 'partial' && <span className="partial-check">{'\u2713'}</span>}
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
  const partialList = ALL_IDS.filter(id => f.presence[id] === 'partial');
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
        <div className={`detail-weight-badge w${f.weight}`}>W{f.weight}</div>
        <span className="detail-weight-label">{WEIGHT_LABELS[f.weight] || ''}</span>
      </div>
      <div className="detail-freq">
        <div className="detail-freq-label">Adoption rate</div>
        <div className="detail-freq-row">
          <span className="detail-freq-big">{f.adoptionPct}%</span>
          <span className="detail-freq-sub">
            {fullList.length} full + {partialList.length} partial<br />of {totalProducts} products
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
          <div className="detail-products-label">Present (full)</div>
          <div className="detail-products">
            {fullList.map(id => (
              <span key={id} className="product-chip" onClick={() => onProductClick(id)}>
                {pName(id)}
              </span>
            ))}
          </div>
        </>
      )}
      {partialList.length > 0 && (
        <>
          <div className="detail-products-label" style={{ marginTop: '10px' }}>Partial / Nav-only</div>
          <div className="detail-products">
            {partialList.map(id => (
              <span key={id} className="product-chip" onClick={() => onProductClick(id)}>
                <span className="chip-state" style={{ opacity: 0.5 }}>{'\u2713'}</span> {pName(id)}
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
  const partialCount = FEATURES.filter(f => f.presence[pid] === 'partial').length;
  const absentCount = FEATURES.filter(f => f.presence[pid] === 'absent').length;
  const rawScore = (fullCount + partialCount) - absentCount;

  let weightedScore = 0;
  let maxWeighted = 0;
  FEATURES.forEach(f => {
    maxWeighted += f.weight;
    if (f.presence[pid] === 'full') weightedScore += f.weight;
    else if (f.presence[pid] === 'partial') weightedScore += Math.round(f.weight * 0.5);
    else weightedScore -= f.weight;
  });
  const pct = Math.round((fullCount + partialCount) / FEATURES.length * 100);

  /* ── Weight colors ── */
  const weightColors: Record<number, string> = {
    1: '#6b6b8a',
    2: '#22d3ee',
    3: '#facc15',
    4: '#fb923c',
    5: '#f87171',
  };

  /* ── Group features by category ── */
  const featuresByCat: { cat: Category; features: Feature[] }[] = [];
  let currentCat: string | null = null;
  FEATURES.forEach(f => {
    if (f.cat !== currentCat) {
      currentCat = f.cat;
      const cat = CATEGORIES.find(c => c.id === f.cat)!;
      featuresByCat.push({ cat, features: [] });
    }
    featuresByCat[featuresByCat.length - 1].features.push(f);
  });

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
            {fullCount} full + {partialCount} partial<br />of {FEATURES.length} features
          </span>
        </div>
        <div className="detail-freq-bar" style={{ width: `${pct}%`, background: 'var(--accent)' }}></div>
      </div>

      <div style={{ display: 'flex', gap: '16px', margin: '10px 0 6px' }}>
        <div>
          <div className="detail-freq-label">Raw Score (+1/{'\u2212'}1)</div>
          <div className="weighted-score">
            <span className="weighted-score-big" style={{ color: rawScore >= 0 ? 'var(--green)' : 'var(--red)' }}>
              {rawScore >= 0 ? '+' : ''}{rawScore}
            </span>
            <span className="weighted-score-sub">/ {FEATURES.length}</span>
          </div>
        </div>
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

      {featuresByCat.map(({ cat, features }, catIdx) => (
        <div key={cat.id}>
          <div
            className="detail-products-label"
            style={{ marginTop: catIdx === 0 ? 0 : '10px', color: cat.color }}
          >
            {cat.name}
          </div>
          <div className="product-feature-list">
            {features.map(f => {
              const state = f.presence[pid];
              return (
                <div
                  key={f.id}
                  className="product-feature-item"
                  onClick={() => onFeatureClick(f.id)}
                >
                  <span className={`product-feature-check ${state}`}>
                    {state === 'full' || state === 'partial' ? '\u2713' : '\u00B7'}
                  </span>
                  <span className="product-feature-name">{f.name}</span>
                  <span
                    className={`product-feature-weight w${f.weight}`}
                    style={{ color: weightColors[f.weight] || '#6b6b8a' }}
                  >
                    W{f.weight}
                  </span>
                  <div className="product-feature-cat" style={{ background: cat.color }}></div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </>
  );
}
