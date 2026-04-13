'use client';

import { useState } from 'react';
import type { CategoryId } from '@/lib/data';

interface CatScore {
  id: CategoryId;
  name: string;
  color: string;
  got: number;
  total: number;
  pctCat: number;
  verdict: 'ok' | 'warning' | 'danger';
}

interface FeatureData {
  id: string;
  name: string;
  desc: string;
  cat: CategoryId;
  band: string;
  adoptionPct: number;
  status: 'full' | 'absent';
}

export default function CategoryFilter({
  catScores,
  allFeatures,
  clubName,
}: {
  catScores: CatScore[];
  allFeatures: FeatureData[];
  clubName: string;
}) {
  const [activeCats, setActiveCats] = useState<Set<CategoryId>>(new Set());

  const toggle = (id: CategoryId) => {
    setActiveCats(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const filtered = activeCats.size > 0
    ? allFeatures.filter(f => activeCats.has(f.cat))
    : allFeatures;

  const missing = filtered.filter(f => f.status === 'absent');
  const diffBands = ['innovation', 'competitive'];
  const differentiators = filtered.filter(
    f => diffBands.includes(f.band) && f.status !== 'absent',
  );
  const alreadyHave = filtered.filter(
    f => !diffBands.includes(f.band) && f.status !== 'absent',
  );

  const bandTag = (band: string) =>
    band === 'table_stakes'
      ? 'ts'
      : band === 'expected'
        ? 'exp'
        : band === 'competitive'
          ? 'comp'
          : 'innov';

  const bandLabel = (band: string) =>
    band === 'table_stakes'
      ? 'Table Stakes'
      : band === 'expected'
        ? 'Expected'
        : band === 'competitive'
          ? 'Competitive'
          : 'Innovation';

  return (
    <>
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
          const isActive = activeCats.has(c.id);
          return (
            <div
              key={c.id}
              className={`bd-cat-card${isActive ? ' active' : ''}`}
              onClick={() => toggle(c.id)}
            >
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

      {/* ── MISSING FEATURES ── */}
      {missing.length > 0 && (
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
              <div className="bd-section-title">Missing Features</div>
              <span className="bd-section-count">{missing.length} missing</span>
            </div>
            <p className="bd-section-desc">
              Features not found on {clubName}&apos;s homepage. Table stakes
              and expected gaps should be prioritised first.
            </p>
            <div className="bd-feature-list">
              {missing.map(f => (
                <div key={f.id} className="bd-feature-item">
                  <div className="bd-feature-status missing">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <path d="M18 6 6 18M6 6l12 12" />
                    </svg>
                  </div>
                  <div className="bd-feature-info">
                    <div className="bd-feature-name">{f.name}</div>
                    <div className="bd-feature-desc">{f.desc}</div>
                  </div>
                  <div className="bd-feature-tags">
                    <span className={`bd-feature-tag ${bandTag(f.band)}`}>
                      {bandLabel(f.band)}
                    </span>
                    <span className="bd-adoption">{f.adoptionPct}% adopt</span>
                  </div>
                </div>
              ))}
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
              <div className="bd-section-icon" style={{ background: 'rgba(234,179,8,.12)' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="var(--yellow)" strokeWidth="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                </svg>
              </div>
              <div className="bd-section-title">Differentiators &mdash; You&apos;re Ahead</div>
              <span className="bd-section-count">{differentiators.length} features</span>
            </div>
            <p className="bd-section-desc">
              Competitive and innovation features that give {clubName} an edge
              &mdash; highlight and invest in them.
            </p>
            <div className="bd-feature-list">
              {differentiators.map(f => {
                return (
                  <div key={f.id} className="bd-feature-item">
                    <div className="bd-feature-status has">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </div>
                    <div className="bd-feature-info">
                      <div className="bd-feature-name">
                        {f.name}
                      </div>
                      <div className="bd-feature-desc">{f.desc}</div>
                    </div>
                    <div className="bd-feature-tags">
                      <span className={`bd-feature-tag ${bandTag(f.band)}`}>
                        {bandLabel(f.band)}
                      </span>
                      <span className="bd-adoption">{f.adoptionPct}% adopt</span>
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
              <div className="bd-section-icon" style={{ background: 'var(--green-bg)' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="var(--green)" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
              <div className="bd-section-title">Already Working</div>
              <span className="bd-section-count">{alreadyHave.length} features</span>
            </div>
            <p className="bd-section-desc">
              Core, expected, and competitive features {clubName} already
              delivers. Maintain these and watch for regression.
            </p>
            <div className="bd-feature-list">
              {alreadyHave.map(f => {
                return (
                  <div key={f.id} className="bd-feature-item">
                    <div className="bd-feature-status has">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </div>
                    <div className="bd-feature-info">
                      <div className="bd-feature-name">
                        {f.name}
                      </div>
                    </div>
                    <div className="bd-feature-tags">
                      <span className={`bd-feature-tag ${bandTag(f.band)}`}>
                        {bandLabel(f.band)}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </>
  );
}
