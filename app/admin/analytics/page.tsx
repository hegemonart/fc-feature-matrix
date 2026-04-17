'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts';

// ── Types ──

interface DayPoint { date: string; label: string; visitors: number; pageViews: number; total: number }
interface TopEvent { type: string; count: number; visitors: number }
interface TopUser { email: string; count: number }
interface TopFeature { name: string; count: number }

interface Stats {
  days: number;
  totalVisitors: number;
  totalPageViews: number;
  totalEvents: number;
  dailySeries: DayPoint[];
  topEvents: TopEvent[];
  topUsers: TopUser[];
  topFeatures: TopFeature[];
}

// ── Chart tooltip ──
// D-23 — re-coloured per RESEARCH.md "Recharts Re-Theme — Diff Sketch":
// background var(--bg-cell), border var(--border), label/secondary var(--muted).

function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'var(--bg-cell)', border: '1px solid var(--border)', borderRadius: 6, padding: '8px 12px', fontSize: 12 }}>
      <div style={{ color: 'var(--muted)', marginBottom: 6 }}>{label}</div>
      {payload.map((p) => (
        <div key={p.name} style={{ color: p.color, display: 'flex', gap: 8, justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--muted)' }}>{p.name}</span>
          <span style={{ fontWeight: 600 }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
}

// ── Stat card ──
// D-23 — chrome var(--bg-cell)/var(--border); label #ABABAB, value #FFFFFF, sub #ABABAB.

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <div style={{
      background: 'var(--bg-cell)', border: '1px solid var(--border)', borderRadius: 8,
      padding: '20px 24px', minWidth: 0,
    }}>
      <div style={{ fontSize: 12, color: '#ABABAB', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 700, color: '#FFFFFF', lineHeight: 1 }}>{value}</div>
      {sub && <div style={{ fontSize: 12, color: '#ABABAB', marginTop: 8 }}>{sub}</div>}
    </div>
  );
}

// ── Row table ──
// D-23 — chrome var(--bg-cell)/var(--border); bar tint orange (rgba(255,73,12,0.07)).

function RankTable({ title, rows, colA, colB }: {
  title: string;
  rows: Array<{ label: string; count: number; sub?: string }>;
  colA: string; colB: string;
}) {
  void colA;
  const max = rows[0]?.count ?? 1;
  return (
    <div style={{ background: 'var(--bg-cell)', border: '1px solid var(--border)', borderRadius: 8, padding: '0 0 4px', overflow: 'hidden' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', padding: '14px 20px 10px', borderBottom: '1px solid var(--border)' }}>
        <span style={{ fontWeight: 600, fontSize: 13 }}>{title}</span>
        <span style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.07em' }}>{colB}</span>
      </div>
      {rows.length === 0 && (
        <div style={{ padding: '24px 20px', color: 'var(--muted)', fontSize: 13 }}>No data yet</div>
      )}
      {rows.map((r) => (
        <div key={r.label} style={{ position: 'relative', padding: '9px 20px', borderBottom: '1px solid var(--border)' }}>
          {/* bar — neutral gray fill (var(--bg-hover)) so it stays
              readable over the dark cell bg; single-orange-CTA rule
              keeps the accent reserved for primary actions (D-25). */}
          <div style={{
            position: 'absolute', inset: 0, right: 'auto',
            width: `${Math.round((r.count / max) * 100)}%`,
            background: 'var(--bg-hover)', borderRadius: 0,
          }} />
          <div style={{ position: 'relative', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <span style={{ fontSize: 12, color: 'var(--text)' }}>{r.label}</span>
              {r.sub && <span style={{ fontSize: 11, color: 'var(--muted)', marginLeft: 8 }}>{r.sub}</span>}
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text)' }}>{r.count}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Main ──

export default function AnalyticsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [authed, setAuthed] = useState(true);
  const [days, setDays] = useState(14);
  const [metric, setMetric] = useState<'visitors' | 'pageViews' | 'total'>('visitors');

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/analytics/stats?days=${days}`);
      if (res.status === 401) { setAuthed(false); return; }
      setStats(await res.json());
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  if (!authed) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <p style={{ color: 'var(--muted)', marginBottom: 16 }}>Analytics is restricted to admin accounts.</p>
          <Link href="/admin" style={{ color: 'var(--accent)', textDecoration: 'none', fontSize: 14 }}>← Back</Link>
        </div>
      </div>
    );
  }

  const metricLabel: Record<typeof metric, string> = {
    visitors: 'Visitors', pageViews: 'Page Views', total: 'Total Events',
  };

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '0 0 48px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28, paddingTop: 8 }}>
        <Link href="/admin" style={{
          display: 'flex', alignItems: 'center', gap: 6, color: 'var(--muted)', textDecoration: 'none',
          fontSize: 13, transition: 'color 0.15s',
        }}>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" width={14} height={14}>
            <path d="M19 12H5m7-7-7 7 7 7" />
          </svg>
          Admin
        </Link>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0 }}>Analytics</h1>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
          {([7, 14, 30] as const).map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              style={{
                background: days === d ? 'var(--bg-hover)' : 'transparent',
                border: `1px solid ${days === d ? 'var(--border)' : 'transparent'}`,
                color: days === d ? 'var(--text)' : 'var(--muted)',
                borderRadius: 6, padding: '4px 12px', fontSize: 12, cursor: 'pointer',
              }}
            >{d}d</button>
          ))}
          <button
            onClick={fetchStats}
            disabled={loading}
            style={{
              background: 'transparent', border: '1px solid var(--border)', color: 'var(--muted)',
              borderRadius: 6, padding: '4px 12px', fontSize: 12, cursor: 'pointer', marginLeft: 4,
            }}
          >{loading ? '…' : '↻'}</button>
        </div>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 20 }}>
        <StatCard label="Visitors" value={stats?.totalVisitors ?? '—'} sub={`last ${days} days`} />
        <StatCard label="Page Views" value={stats?.totalPageViews ?? '—'} sub={`last ${days} days`} />
        <StatCard label="Total Events" value={stats?.totalEvents ?? '—'} sub={`last ${days} days`} />
      </div>

      {/* Chart */}
      <div style={{
        background: 'var(--bg-cell)', border: '1px solid var(--border)', borderRadius: 8,
        padding: '20px 20px 12px', marginBottom: 20,
      }}>
        <div style={{ display: 'flex', gap: 8, marginBottom: 20 }}>
          {(['visitors', 'pageViews', 'total'] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMetric(m)}
              style={{
                background: metric === m ? 'rgba(255,73,12,0.12)' : 'transparent',
                border: `1px solid ${metric === m ? 'rgba(255,73,12,0.4)' : 'transparent'}`,
                color: metric === m ? 'var(--accent)' : 'var(--muted)',
                borderRadius: 6, padding: '4px 12px', fontSize: 12, cursor: 'pointer',
              }}
            >{metricLabel[m]}</button>
          ))}
        </div>

        <ResponsiveContainer width="100%" height={240}>
          <AreaChart data={stats?.dailySeries ?? []} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              {/* RESEARCH P2 mitigation: hard-code #FF490C in SVG gradient stops
                  rather than var(--accent) for older Recharts safety. */}
              <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#FF490C" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#FF490C" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="var(--border)" />
            <XAxis
              dataKey="label"
              tick={{ fill: '#ABABAB', fontSize: 11 }}
              axisLine={false} tickLine={false}
              interval="preserveStartEnd"
            />
            <YAxis
              tick={{ fill: '#ABABAB', fontSize: 11 }}
              axisLine={false} tickLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--border)', strokeWidth: 1 }} />
            <Area
              type="monotone"
              dataKey={metric}
              name={metricLabel[metric]}
              stroke="#FF490C"
              strokeWidth={1.5}
              fill="url(#grad)"
              dot={false}
              activeDot={{ r: 4, fill: '#FF490C', stroke: 'var(--bg-page)', strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Two-column tables */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
        <RankTable
          title="Top Events"
          colA="Type"
          colB="Count"
          rows={stats?.topEvents.map(e => ({ label: e.type, count: e.count, sub: `${e.visitors} users` })) ?? []}
        />
        <RankTable
          title="Top Features"
          colA="Feature"
          colB="Clicks"
          rows={stats?.topFeatures.map(f => ({ label: f.name, count: f.count })) ?? []}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <RankTable
          title="Top Users"
          colA="Email"
          colB="Events"
          rows={stats?.topUsers.map(u => ({ label: u.email, count: u.count })) ?? []}
        />
        {/* placeholder to keep grid balanced */}
        <div />
      </div>
    </div>
  );
}
