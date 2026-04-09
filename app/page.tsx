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
  const [filterSport, setFilterSport] = useState<string>('all');
  const [activeCat, setActiveCat] = useState<CategoryId | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [adoptionSort, setAdoptionSort] = useState<'asc' | 'desc' | null>(null);
  const [featureAlphaSort, setFeatureAlphaSort] = useState(false);

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


  /* ── Derived data ── */
  const visibleProds = useMemo(() => {
    return PRODUCTS.filter(p => {
      if (filterSport === 'fc' && p.type !== 'club') return false;
      if (filterSport === 'federation' && p.type !== 'governing') return false;
      if (filterSport === 'league' && p.type !== 'league') return false;
      return true;
    });
  }, [filterSport]);

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
    setFilterSport('all');
    setActiveCat(null);
    setSelectedFeature(null);
    setSelectedProduct(null);
    setAdoptionSort(null);
    setFeatureAlphaSort(false);
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
        <div className="logo">FC Benchmark <span>//</span> April 2026</div>
        <div className="header-title">Feature Matrix</div>
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
        <div className="filter-group">
          <span className="filter-label">Type:</span>
          {[
            { val: 'all', label: 'All' },
            { val: 'fc', label: 'FC' },
            { val: 'federation', label: 'Federation' },
            { val: 'league', label: 'League' },
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
            {[...CATEGORIES].sort((a, b) => a.name.localeCompare(b.name)).map(c => (
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
        </div>

        {/* ── TABLE ── */}
        <div
          className="table-container"
          onMouseLeave={handleTableMouseLeave}
        >
          <table>
            <thead>
              <tr>
                <th
                  className="feature-col sortable"
                  onClick={() => { setAdoptionSort(null); setFeatureAlphaSort(prev => !prev); }}
                >
                  Feature {featureAlphaSort ? '\u25B2' : ''}
                </th>
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
                <th
                  className="freq-col sortable"
                  onClick={() => {
                    setFeatureAlphaSort(false);
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
  showCategorySeps,
  selectedFeature,
  selectedProduct,
  onFeatureClick,
  onCellMouseOver,
  onCellMouseMove,
  onProductClick,
}: {
  feats: Feature[];
  prods: Product[];
  showCategorySeps: boolean;
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
    if (showCategorySeps && f.cat !== lastCat) {
      lastCat = f.cat;
      const cat = CATEGORIES.find(c => c.id === f.cat)!;
      rows.push(
        <tr className="category-sep-row" key={`sep-${f.cat}-${idx}`}>
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

  let weightedScore = 0;
  let maxWeighted = 0;
  FEATURES.forEach(f => {
    maxWeighted += f.weight;
    if (f.presence[pid] === 'full') weightedScore += f.weight;
    else if (f.presence[pid] === 'partial') weightedScore += Math.round(f.weight * 0.5);
    else weightedScore -= f.weight;
  });
  const pct = Math.round((fullCount + partialCount) / FEATURES.length * 100);

  /* ── Group features into 3 sections ── */
  const missingDiff = FEATURES.filter(f => f.cat === 'diff' && f.presence[pid] === 'absent');
  const missingMustHave = FEATURES.filter(f => f.cat !== 'diff' && f.presence[pid] === 'absent');
  const featuresPresent = FEATURES.filter(f => f.presence[pid] === 'full' || f.presence[pid] === 'partial');

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

      {missingDiff.length > 0 && (
        <div>
          <div className="detail-products-label" style={{ color: 'var(--red)' }}>
            Missing Differentiators
          </div>
          <div className="product-feature-list">
            {missingDiff.map(f => {
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

      {missingMustHave.length > 0 && (
        <div>
          <div className="detail-products-label" style={{ marginTop: '10px', color: 'var(--orange)' }}>
            Missing Must-Haves
          </div>
          <div className="product-feature-list">
            {missingMustHave.map(f => {
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
