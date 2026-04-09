import { notFound } from 'next/navigation';
import Link from 'next/link';
import { CATEGORIES, PRODUCTS, FEATURES, BAND_META } from '@/lib/data';
import { getProductScores, getRankedProducts } from '@/lib/scoring';
import type { Metadata } from 'next';

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
  const showAlert = coveragePct < avgPct - 5;

  // Category breakdown
  const catScores = CATEGORIES.map(cat => {
    const cf = FEATURES.filter(f => f.cat === cat.id);
    const got = cf.filter(f => f.presence[pid] !== 'absent').length;
    const pctCat = Math.round((got / cf.length) * 100);
    const verdict: 'ok' | 'warning' | 'danger' =
      pctCat >= 80 ? 'ok' : pctCat >= 50 ? 'warning' : 'danger';
    return { ...cat, got, total: cf.length, pctCat, verdict };
  });

  // Feature groups
  const mustHaveMissing = FEATURES.filter(
    f =>
      (f.band === 'table_stakes' || f.band === 'expected') &&
      f.presence[pid] === 'absent',
  );
  const differentiators = FEATURES.filter(
    f => f.band === 'innovation' && f.presence[pid] !== 'absent',
  );
  const alreadyHave = FEATURES.filter(
    f => f.presence[pid] !== 'absent' && f.band !== 'innovation',
  );

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
                r2.pct >= 70
                  ? 'var(--green)'
                  : r2.pct >= 45
                    ? 'var(--yellow)'
                    : 'var(--red)';
              return (
                <Link
                  key={r2.id}
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
              );
            })}
          </div>
        </div>

        {/* ── CATEGORY BREAKDOWN GRID ── */}
        <div className="bd-cat-grid">
          {catScores.map(c => {
            const barColor =
              c.pctCat >= 80
                ? 'var(--green)'
                : c.pctCat >= 50
                  ? 'var(--yellow)'
                  : 'var(--red)';
            const verdictLabel =
              c.verdict === 'ok'
                ? '\u2713 Good shape'
                : c.verdict === 'warning'
                  ? '\u26A0 Needs work'
                  : '\u2715 Critical gap';
            return (
              <div key={c.id} className="bd-cat-card">
                <div className="bd-cat-header">
                  <div
                    className="bd-cat-dot"
                    style={{ background: c.color }}
                  />
                  <span className="bd-cat-title">{c.name}</span>
                </div>
                <div className="bd-cat-score-row">
                  <span className="bd-cat-big">{c.got}</span>
                  <span className="bd-cat-of">/ {c.total}</span>
                </div>
                <div className="bd-cat-bar-wrap">
                  <div
                    className="bd-cat-bar"
                    style={{ width: `${c.pctCat}%`, background: barColor }}
                  />
                </div>
                <span className={`bd-cat-verdict ${c.verdict}`}>
                  {verdictLabel}
                </span>
              </div>
            );
          })}
        </div>

        {/* ── MUST HAVES ── */}
        {mustHaveMissing.length > 0 && (
          <>
            <div className="section-sep" />
            <div className="bd-section">
              <div className="bd-section-header">
                <div className="bd-section-icon" style={{ background: 'var(--red-bg)' }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="var(--red)" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                </div>
                <div className="bd-section-title">
                  Must Haves &mdash; You&apos;re Missing the Basics
                </div>
                <span className="bd-section-count">
                  {mustHaveMissing.length} missing
                </span>
              </div>
              <p className="bd-section-desc">
                These table stakes and expected features are already present on
                most competitor sites. Every gap here costs {p.name} fan
                engagement and commercial performance.
              </p>
              <div className="bd-feature-list">
                {mustHaveMissing.map(f => {
                  const bandTag =
                    f.band === 'table_stakes' ? 'ts' : 'exp';
                  const bandLabel =
                    f.band === 'table_stakes' ? 'Table Stakes' : 'Expected';
                  return (
                    <div key={f.id} className="bd-feature-item">
                      <div className="bd-feature-status missing">
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                        >
                          <path d="M18 6 6 18M6 6l12 12" />
                        </svg>
                      </div>
                      <div className="bd-feature-info">
                        <div className="bd-feature-name">{f.name}</div>
                        <div className="bd-feature-desc">{f.desc}</div>
                      </div>
                      <div className="bd-feature-tags">
                        <span className={`bd-feature-tag ${bandTag}`}>
                          {bandLabel}
                        </span>
                        <span className="bd-feature-tag w">W{f.weight}</span>
                        <span className="bd-adoption">
                          {f.adoptionPct}% adopt
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* ── DIFFERENTIATORS ── */}
        {differentiators.length > 0 && (
          <>
            <div className="section-sep" />
            <div className="bd-section">
              <div className="bd-section-header">
                <div
                  className="bd-section-icon"
                  style={{ background: 'rgba(234,179,8,.12)' }}
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--yellow)"
                    strokeWidth="2"
                  >
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                  </svg>
                </div>
                <div className="bd-section-title">
                  Differentiators &mdash; You&apos;re Ahead
                </div>
                <span className="bd-section-count">
                  {differentiators.length} features
                </span>
              </div>
              <p className="bd-section-desc">
                Innovation features adopted by fewer than 40% of products. These
                give {p.name} a competitive edge &mdash; highlight and invest in
                them.
              </p>
              <div className="bd-feature-list">
                {differentiators.map(f => {
                  const isPartial = f.presence[pid] === 'partial';
                  return (
                    <div key={f.id} className="bd-feature-item">
                      <div
                        className={`bd-feature-status ${isPartial ? 'partial' : 'has'}`}
                      >
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                      <div className="bd-feature-info">
                        <div className="bd-feature-name">
                          {f.name}
                          {isPartial && (
                            <span
                              style={{
                                fontWeight: 400,
                                color: 'var(--muted)',
                                fontSize: '11px',
                              }}
                            >
                              {' '}
                              (partial)
                            </span>
                          )}
                        </div>
                        <div className="bd-feature-desc">{f.desc}</div>
                      </div>
                      <div className="bd-feature-tags">
                        <span className="bd-feature-tag innov">Innovation</span>
                        <span className="bd-feature-tag w">W{f.weight}</span>
                        <span className="bd-adoption">
                          {f.adoptionPct}% adopt
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}

        {/* ── ALREADY WORKING ── */}
        {alreadyHave.length > 0 && (
          <>
            <div className="section-sep" />
            <div className="bd-section">
              <div className="bd-section-header">
                <div
                  className="bd-section-icon"
                  style={{ background: 'var(--green-bg)' }}
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="var(--green)"
                    strokeWidth="2"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                </div>
                <div className="bd-section-title">Already Working</div>
                <span className="bd-section-count">
                  {alreadyHave.length} features
                </span>
              </div>
              <p className="bd-section-desc">
                Core, expected, and competitive features {p.name} already
                delivers. Maintain these and watch for regression.
              </p>
              <div className="bd-feature-list">
                {alreadyHave.map(f => {
                  const isPartial = f.presence[pid] === 'partial';
                  const bandTag =
                    f.band === 'table_stakes'
                      ? 'ts'
                      : f.band === 'expected'
                        ? 'exp'
                        : f.band === 'competitive'
                          ? 'comp'
                          : 'innov';
                  const bandLabel =
                    f.band === 'table_stakes'
                      ? 'Table Stakes'
                      : f.band === 'expected'
                        ? 'Expected'
                        : f.band === 'competitive'
                          ? 'Competitive'
                          : 'Innovation';
                  return (
                    <div key={f.id} className="bd-feature-item">
                      <div
                        className={`bd-feature-status ${isPartial ? 'partial' : 'has'}`}
                      >
                        <svg
                          width="14"
                          height="14"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2.5"
                        >
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                      <div className="bd-feature-info">
                        <div className="bd-feature-name">
                          {f.name}
                          {isPartial && (
                            <span
                              style={{
                                fontWeight: 400,
                                color: 'var(--muted)',
                                fontSize: '11px',
                              }}
                            >
                              {' '}
                              (partial)
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="bd-feature-tags">
                        <span className={`bd-feature-tag ${bandTag}`}>
                          {bandLabel}
                        </span>
                        <span className="bd-feature-tag w">W{f.weight}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
