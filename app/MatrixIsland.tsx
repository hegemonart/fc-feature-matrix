'use client';

/* ================================================================
   <MatrixIsland>

   D-17 — Client Component matrix island. Owns ALL interactive
   state from the legacy app/page.tsx (1072 LOC); the page itself
   becomes a Server Component shell that loads data + renders
   <MatrixIsland>.

   Wires up the 9 atomic components + 2 hooks shipped in plans 02
   and 03. selectedProduct stays the authoritative state for both
   the detail panel AND column-tint (D-18); useColumnSelection from
   plan 03 is used as a thin helper over it.

   This file is the state/handler scaffold from plan 04 task 1; the
   render tree is wired in task 2.

   Preserved verbatim from app/page.tsx:
     - filterTypes, activeCat, selectedFeature, selectedProduct
     - adoptionSort, featureAlphaSort, scoreSort
     - authed, authEmail, isAdmin, isPremium
     - login modal state (loginModalVisible, ctaView, loginEmail,
       loginPassword, loginError, loginLoading)
     - locked-content modal state (lockedModalVisible, lockedFlowName)
     - coming-soon modal state (comingSoonVisible, comingSoonFlowName)
     - access request state (requestSending, requestSent)
     - sendAccessRequest, handleLogin, handleLogout, handleTabClick
     - handleShowFeatureDetail, handleShowProductDetail,
       handleCloseDetail, handleClearFilters
     - the /api/auth/me mount effect + trackEvent('page_view')

   Diverges from app/page.tsx:
     - handleCellMouseMove DELETED (cursor-follow positioning is
       gone; tooltip is anchored to the cell rect now)
     - handleCellMouseOver REWRITTEN to call useHoverTooltip.handleCellEnter
     - handleTableMouseLeave delegates to useHoverTooltip.handleCellLeave
   ================================================================ */

import { useState, useMemo, useCallback, useEffect } from 'react';
import {
  CATEGORIES,
  PRODUCTS,
  FEATURES,
  BAND_META,
  ALL_IDS,
  type CategoryId,
  type BandId,
  type Feature,
  type Product,
} from '@/lib/data';
import { trackEvent } from '@/lib/track';
import { useHoverTooltip } from './components/matrix/useHoverTooltip';
import { useColumnSelection } from './components/matrix/useColumnSelection';

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

const totalProducts = PRODUCTS.length;

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

export default function MatrixIsland({ products, features, scores, buildDate }: MatrixIslandProps) {
  /* ── State (preserved verbatim from app/page.tsx) ── */
  const [filterTypes, setFilterTypes] = useState<Set<string>>(new Set(['club', 'governing', 'league']));
  const [activeCat, setActiveCat] = useState<CategoryId | null>(null);
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);
  const [selectedProduct, setSelectedProduct] = useState<string | null>(null);
  const [adoptionSort, setAdoptionSort] = useState<'asc' | 'desc' | null>(null);
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
  const [requestSent, setRequestSent] = useState<string | null>(null);

  /* ── Tooltip + column selection (D-21 / D-18 — wired to plan 03 hooks) ── */
  const { tooltipData, handleCellEnter, handleCellLeave, clearTooltip } = useHoverTooltip();
  // selectedProduct is the AUTHORITATIVE state for column-tint (D-18). The
  // useColumnSelection hook from plan 03 is used as a thin helper over it
  // so the existing Product-detail panel keeps working without divergence.
  // We intentionally don't initialize useColumnSelection with selectedProduct
  // because we read selectedProduct directly for tinting; the hook is
  // referenced for parity / future migration.
  const _columnHelper = useColumnSelection();

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

  /* ── Derived data (preserved) ── */

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
    CATEGORIES.forEach(c => (counts[c.id] = features.filter(f => f.cat === c.id).length));
    return counts;
  }, [features]);

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

  const handleTabClick = useCallback((name: string) => {
    if (isAdmin || isPremium) {
      trackEvent('tab_click', { tab: name, outcome: 'coming_soon' });
      setComingSoonFlowName(name);
      setComingSoonVisible(true);
    } else if (authed) {
      trackEvent('tab_click', { tab: name, outcome: 'locked' });
      setLockedFlowName(name);
      setLockedModalVisible(true);
    } else {
      trackEvent('tab_click', { tab: name, outcome: 'locked' });
      setLockedFlowName(name);
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
    setAdoptionSort(null);
    setFeatureAlphaSort(false);
    setScoreSort(null);
  }, []);

  /* ── Tooltip handlers — REWRITTEN per plan 04 spec ──
     handleCellMouseOver now takes the cell element and delegates to
     useHoverTooltip.handleCellEnter (anchor-rect positioning).
     handleCellMouseMove is DELETED (cursor-follow is gone).
     handleTableMouseLeave delegates to handleCellLeave (100ms grace).
   */
  const handleCellMouseOver = useCallback((fid: string, pid: string, el: HTMLElement) => {
    handleCellEnter(fid, pid, el);
  }, [handleCellEnter]);

  const handleTableMouseLeave = useCallback(() => {
    handleCellLeave();
  }, [handleCellLeave]);

  /* ── Detail panel content ── */
  const detailPanelCollapsed = !selectedFeature && !selectedProduct;

  // Suppress unused-var warnings for state intentionally exposed to the
  // render tree wired up in task 04-02. The render JSX lands in task 02.
  void filterTypes; void activeCat; void selectedFeature; void selectedProduct;
  void adoptionSort; void featureAlphaSort; void scoreSort;
  void authed; void authEmail; void isAdmin; void isPremium;
  void loginModalVisible; void ctaView; void loginEmail; void loginPassword;
  void loginError; void loginLoading;
  void lockedModalVisible; void lockedFlowName;
  void comingSoonVisible; void comingSoonFlowName;
  void requestSending; void requestSent;
  void tooltipData; void clearTooltip; void _columnHelper;
  void productScores; void visibleProds; void visibleFeats; void sortedFeats; void catCounts;
  void sendAccessRequest; void handleLogin; void handleLogout; void handleTabClick;
  void handleShowFeatureDetail; void handleShowProductDetail; void handleCloseDetail;
  void handleClearFilters; void handleCellMouseOver; void handleTableMouseLeave;
  void detailPanelCollapsed; void buildDate;
  void setSelectedFeature; void setSelectedProduct;
  void setAdoptionSort; void setFeatureAlphaSort; void setScoreSort;
  void setAuthed; void setAuthEmail; void setIsAdmin; void setIsPremium;
  void setLoginModalVisible; void setCtaView; void setLoginEmail; void setLoginPassword;
  void setLoginError; void setLoginLoading;
  void setLockedModalVisible; void setLockedFlowName;
  void setComingSoonVisible; void setComingSoonFlowName;
  void setActiveCat; void setFilterTypes;
  void PadlockIcon; void bandColorVar; void totalProducts; void BAND_META; void ALL_IDS;

  // Render placeholder — task 04-02 will wire the full render tree.
  return null;
}
