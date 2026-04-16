'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';

interface AnalyticsEvent {
  type: string;
  email: string;
  timestamp: string;
  [key: string]: unknown;
}

const EVENT_COLORS: Record<string, string> = {
  login: '#22c55e',
  logout: '#ef4444',
  page_view: '#3b82f6',
  tab_click: '#f59e0b',
  feature_click: '#8b5cf6',
  product_click: '#06b6d4',
};

function formatTime(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString('en-GB', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

function EventDetail({ event }: { event: AnalyticsEvent }) {
  const extras = Object.entries(event).filter(
    ([k]) => !['type', 'email', 'timestamp'].includes(k),
  );
  if (extras.length === 0) return null;
  return (
    <span className="analytics-detail">
      {extras.map(([k, v]) => (
        <span key={k} className="analytics-kv">
          <span className="analytics-key">{k}:</span> {String(v)}
        </span>
      ))}
    </span>
  );
}

export default function AnalyticsPage() {
  const [events, setEvents] = useState<AnalyticsEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [authed, setAuthed] = useState(false);
  const [filterType, setFilterType] = useState('');
  const [filterEmail, setFilterEmail] = useState('');

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set('limit', '200');
      if (filterType) params.set('type', filterType);
      if (filterEmail) params.set('email', filterEmail);

      const res = await fetch(`/api/analytics/view?${params}`);
      if (res.status === 401) { setAuthed(false); setLoading(false); return; }
      setAuthed(true);
      const data = await res.json();
      setEvents(data);
    } catch {
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [filterType, filterEmail]);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  // Get unique types and emails for filter dropdowns
  const types = [...new Set(events.map(e => e.type))].sort();
  const emails = [...new Set(events.map(e => e.email))].sort();

  if (!loading && !authed) {
    return (
      <div className="analytics-shell">
        <div className="analytics-unauth">
          <h2>Analytics</h2>
          <p>Analytics is restricted to Humbleteam accounts.</p>
          <Link href="/admin" className="analytics-back">Go to matrix</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-shell">
      <header className="analytics-header">
        <Link href="/admin" className="analytics-back">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M19 12H5m7-7-7 7 7 7" />
          </svg>
          Back
        </Link>
        <h1>Analytics</h1>
        <span className="analytics-count">{events.length} events</span>
        <button className="analytics-refresh" onClick={fetchEvents} disabled={loading}>
          {loading ? 'Loading\u2026' : 'Refresh'}
        </button>
      </header>

      <div className="analytics-filters">
        <select value={filterType} onChange={e => setFilterType(e.target.value)}>
          <option value="">All types</option>
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={filterEmail} onChange={e => setFilterEmail(e.target.value)}>
          <option value="">All users</option>
          {emails.map(e => <option key={e} value={e}>{e}</option>)}
        </select>
      </div>

      <div className="analytics-table-wrap">
        <table className="analytics-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Type</th>
              <th>User</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 && !loading && (
              <tr><td colSpan={4} className="analytics-empty">No events found.</td></tr>
            )}
            {events.map((ev, i) => (
              <tr key={i}>
                <td className="analytics-time">{formatTime(ev.timestamp)}</td>
                <td>
                  <span
                    className="analytics-type-badge"
                    style={{ background: EVENT_COLORS[ev.type] || 'var(--muted)' }}
                  >
                    {ev.type}
                  </span>
                </td>
                <td className="analytics-email">{ev.email}</td>
                <td><EventDetail event={ev} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
