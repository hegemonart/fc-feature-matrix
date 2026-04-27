'use client';

/* ================================================================
   <HospitalityIsland> — Plan 02-13 (D-19, HOSP-03)

   Client Component for the Hospitality Packages back-half pilot.
   Renders a 5-club × 55-feature matrix with the explicit "Pilot:
   5 clubs" mono-caption chip directly above the matrix.

   Design-system invariants honored (CLAUDE.md):
     - Single orange CTA per surface: zero `var(--accent)`-background
       elements on this page (the "Back to home" link is plain text
       with a `var(--border)` outline; the matrix has no chrome CTAs).
     - All colors via CSS vars (`--bg-page`, `--bg-cell`, `--border`,
       `--text`, `--muted`). No hex literals in chrome.
     - Type stack via `var(--font-body)` / `var(--font-mono)`.
     - Score-data invariant: this component does NOT call
       lib/scoring.getProductScores; pre-computed `scores` are passed
       in as a prop from the Server Component (page.tsx).

   Mirrors the homepage matrix shell (HeaderBar + main + table) but
   intentionally minimal — no sidebar filters, no tooltip, no detail
   panel. The pilot view is read-only and pre-launch.
   ================================================================ */

import { useEffect } from 'react';
import Link from 'next/link';
import type { Feature, Product } from '@/lib/data';
import { trackEvent } from '@/lib/track';
import { HeaderBar } from '../components/matrix/HeaderBar';

interface HospitalityIslandProps {
  pilotProducts: Product[];
  hospitalityFeatures: Feature[];
  scores: Record<string, number>;
  buildDate: string;
}

export default function HospitalityIsland({
  pilotProducts,
  hospitalityFeatures,
  scores,
  buildDate,
}: HospitalityIslandProps) {
  useEffect(() => {
    trackEvent('page_view', { path: '/hospitality' });
  }, []);

  return (
    <div className="matrix-shell hospitality-shell">
      <HeaderBar buildDate={buildDate} />

      {/* Back-to-home affordance — text-only / white-outlined.
          MUST NOT carry orange-accent styling (single-orange-CTA invariant). */}
      <nav className="hospitality-subnav" aria-label="Hospitality navigation">
        <Link href="/" className="hospitality-back-link" data-cta="back-to-home">
          ← Back to homepage matrix
        </Link>
        <span className="mono-caption pilot-label" data-pilot-label="true">
          Pilot: 5 clubs
        </span>
      </nav>

      <div className="main hospitality-main">
        <div className="table-wrapper hospitality-table-wrapper">
          <div className="table-container">
            <table className="hospitality-matrix" data-matrix="hospitality">
              <thead>
                <tr>
                  <th className="feature-col">
                    <span>Hospitality Feature</span>
                  </th>
                  {pilotProducts.map(p => (
                    <th key={p.id} data-club={p.id}>
                      <div className="col-header">
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
                  <td className="feature-col score-label">
                    <span>Total Score</span>
                  </td>
                  {pilotProducts.map(p => {
                    const s = scores[p.id] ?? 0;
                    return (
                      <td key={p.id} data-club={p.id} className="score-cell">
                        <span className={`score-value ${s >= 0 ? 'positive' : 'negative'}`}>
                          {s >= 0 ? '+' : ''}{s}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {hospitalityFeatures.map(f => (
                  <tr key={f.id} data-feature={f.id}>
                    <td className="feature-col">
                      <span className="feature-name">{f.name}</span>
                      <span className="mono-caption feature-tier" data-tier={f.tier}>
                        Tier {f.tier} · +{f.weightYes}/{f.weightNo}
                      </span>
                    </td>
                    {pilotProducts.map(p => {
                      const present = f.presence[p.id] === 'full';
                      return (
                        <td
                          key={p.id}
                          data-club={p.id}
                          data-feature={f.id}
                          data-present={present ? 'true' : 'false'}
                          className={`hospitality-cell${present ? ' present' : ' absent'}`}
                        >
                          {present ? (
                            <svg
                              viewBox="0 0 14 14"
                              fill="none"
                              xmlns="http://www.w3.org/2000/svg"
                              aria-label="Present"
                              width="14"
                              height="14"
                            >
                              <path
                                d="M2.5 7.5L5.5 10.5L11.5 4"
                                stroke="currentColor"
                                strokeWidth="1.6"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                              />
                            </svg>
                          ) : null}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
