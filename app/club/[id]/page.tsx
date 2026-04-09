import { notFound } from 'next/navigation';
import Link from 'next/link';
import { CATEGORIES, PRODUCTS, FEATURES, BAND_META } from '@/lib/data';
import { getProductScores, getRankedProducts } from '@/lib/scoring';
import type { Metadata } from 'next';
import CategoryFilter from './CategoryFilter';

/* ── Static params for all 26 products ── */

export function generateStaticParams() {
  return PRODUCTS.map(p => ({ id: p.id }));
}

/* ── Per-page metadata ── */

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const p = PRODUCTS.find(x => x.id === id);
  if (!p) return { title: 'Not Found — FC Benchmark' };
  return { title: `${p.name} — FC Benchmark` };
}

/* ── Page component ── */

export default async function ClubDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id: pid } = await params;
  const p = PRODUCTS.find(x => x.id === pid);
  if (!p) notFound();

  // Scores
  const { coveragePct, rawScore, weightedScore, maxWeighted } =
    getProductScores(pid);

  // Rank
  const ranked = getRankedProducts();
  const myRank = ranked.findIndex(r => r.id === pid) + 1;
  const avgPct = Math.round(
    ranked.reduce((s, r) => s + r.pct, 0) / ranked.length,
  );

  // Ring
  const ringClass = coveragePct >= 70 ? 'high' : coveragePct >= 45 ? 'mid' : 'low';
  const R = 58;
  const circ = 2 * Math.PI * R;
  const offset = circ * (1 - coveragePct / 100);
  const showAlert = coveragePct < avgPct;

  // Category breakdown
  const catScores = CATEGORIES.map(cat => {
    const cf = FEATURES.filter(f => f.cat === cat.id);
    const got = cf.filter(f => f.presence[pid] !== 'absent').length;
    const pctCat = Math.round((got / cf.length) * 100);
    const verdict: 'ok' | 'warning' | 'danger' =
      pctCat >= 80 ? 'ok' : pctCat >= 50 ? 'warning' : 'danger';
    return { ...cat, got, total: cf.length, pctCat, verdict };
  });

  // All features with status for this product
  const allFeatures = FEATURES.map(f => ({
    id: f.id,
    name: f.name,
    desc: f.desc,
    cat: f.cat,
    band: f.band!,
    adoptionPct: f.adoptionPct!,
    status: f.presence[pid],
  }));

  // Crest initials
  const crestInitials = p.name.substring(0, 2).toUpperCase();

  return (
    <div className="club-detail-shell">
      {/* ── STICKY HEADER ── */}
      <header className="page-header">
        <Link className="header-back" href="/">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M19 12H5m7-7-7 7 7 7" />
          </svg>
          Back to matrix
        </Link>
        <div className="header-logo">
          FC Benchmark <span>&nbsp;//&nbsp;</span> 2026
        </div>
        <div className="header-crest">{crestInitials}</div>
        <div className="header-club">
          <div className="header-club-name">{p.name}</div>
          <div className="header-club-meta">
            {p.type} &middot; {p.sport}
          </div>
        </div>
        <div className="header-right">
          <div className="header-rank-chip">
            #{myRank} of {PRODUCTS.length}
          </div>
          <div className="header-pct-chip">{coveragePct}% coverage</div>
        </div>
      </header>

      <div className="page-body">
        {/* ── ALERT BANNER ── */}
        {showAlert && (
          <div className="bd-alert">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <div>
              <div className="bd-alert-title">Behind benchmark average</div>
              <div className="bd-alert-desc">
                {p.name} covers {coveragePct}% of homepage features &mdash;{' '}
                {avgPct - coveragePct} points below the benchmark average of{' '}
                {avgPct}%. Prioritise table stakes gaps immediately to avoid fan
                experience regression.
              </div>
            </div>
          </div>
        )}

        {/* ── SCORE ROW ── */}
        <div className="bd-score-row">
          {/* Score card with ring */}
          <div className="bd-score-card">
            <div className="bd-score-label">Feature Coverage Score</div>
            <div className="bd-ring-wrap">
              <svg className="bd-ring-svg" viewBox="0 0 128 128">
                <circle className="bd-ring-bg" cx="64" cy="64" r={R} />
                <circle
                  className={`bd-ring-fg ${ringClass}`}
                  cx="64"
                  cy="64"
                  r={R}
                  strokeDasharray={circ.toFixed(1)}
                  strokeDashoffset={offset.toFixed(1)}
                />
              </svg>
              <div className="bd-ring-text">
                <span className="bd-score-num">
                  {coveragePct}
                  <span>%</span>
                </span>
                <span className="bd-score-sub">of features</span>
              </div>
            </div>
            <div className="bd-divider" />
            <div className="bd-scores-row">
              <div className="bd-mini-score">
                <div className="bd-mini-label">Weighted</div>
                <div
                  className="bd-mini-val"
                  style={{
                    color: weightedScore >= 0 ? 'var(--green)' : 'var(--red)',
                  }}
                >
                  {weightedScore >= 0 ? '+' : ''}
                  {weightedScore}
                </div>
              </div>
              <div className="bd-mini-score">
                <div className="bd-mini-label">Global Rank</div>
                <div className="bd-mini-val" style={{ color: 'var(--yellow)' }}>
                  #{myRank}
                </div>
              </div>
            </div>
          </div>

          {/* Rank card */}
          <div className="bd-rank-card">
            <h3>All Products &mdash; Ranked by Coverage</h3>
            {ranked.map((r2, i) => {
              const isCurrent = r2.id === pid;
              const barColor =
                r2.pct >= avgPct
                  ? 'var(--green)'
                  : 'var(--yellow)';
              const showCutoff =
                r2.pct < avgPct && i > 0 && ranked[i - 1].pct >= avgPct;
              return (
                <span key={r2.id}>
                  {showCutoff && (
                    <div className="bd-rank-cutoff">
                      <span>Below average</span>
                    </div>
                  )}
                  <Link
                    href={`/club/${r2.id}`}
                    className={`bd-rank-item${isCurrent ? ' current' : ''}`}
                  >
                    <span className="bd-rank-pos">{i + 1}</span>
                    <span className="bd-rank-name">{r2.name}</span>
                    <div className="bd-rank-bar-wrap">
                      <div
                        className="bd-rank-bar"
                        style={{ width: `${r2.pct}%`, background: barColor }}
                      />
                    </div>
                    <span className="bd-rank-pct">{r2.pct}%</span>
                  </Link>
                </span>
              );
            })}
          </div>
        </div>

        <CategoryFilter
          catScores={catScores}
          allFeatures={allFeatures}
          clubName={p.name}
        />
      </div>
    </div>
  );
}
