'use client';

import { useState } from 'react';

interface RequestRow {
  id: string;
  email: string;
  source: string | null;
  ip: string | null;
  userAgent: string | null;
  status: string;
  grantedUserId: string | null;
  resolvedAt: string | null;
  createdAt: string;
}

function fmt(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, { bg: string; color: string }> = {
    pending: { bg: 'var(--yellow-bg)', color: 'var(--yellow)' },
    granted: { bg: 'rgba(34,197,94,0.12)', color: 'var(--green)' },
    dismissed: { bg: 'var(--bg-hover)', color: 'var(--muted)' },
  };
  const s = styles[status] ?? styles.dismissed;
  return (
    <span className="admin-badge" style={{ background: s.bg, color: s.color }}>{status}</span>
  );
}

// ── Grant modal ──
function GrantModal({ req, onClose, onGranted }: {
  req: RequestRow;
  onClose: () => void;
  onGranted: (id: string) => void;
}) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGrant = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`/api/admin/requests/${req.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'grant', password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Failed'); return; }
      onGranted(req.id);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-modal-overlay" onClick={onClose}>
      <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Grant access</h3>
        <p style={{ fontSize: 13, color: 'var(--muted)', margin: '0 0 12px' }}>
          Creates an account for <strong>{req.email}</strong>
        </p>
        <form onSubmit={handleGrant}>
          <div className="admin-form-row">
            <label>Password for new account (min 12 chars)</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={12}
              required
              autoFocus
            />
          </div>
          {error && <div className="admin-error">{error}</div>}
          <div className="admin-form-actions">
            <button type="button" className="admin-btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="admin-btn admin-btn-primary" disabled={loading}>
              {loading ? 'Granting…' : 'Grant access'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function RequestsActions({ initialRequests }: { initialRequests: RequestRow[] }) {
  const [requests, setRequests] = useState<RequestRow[]>(initialRequests);
  const [grantTarget, setGrantTarget] = useState<RequestRow | null>(null);
  const [dismissingId, setDismissingId] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleDismiss = async (req: RequestRow) => {
    if (!confirm(`Dismiss request from ${req.email}?`)) return;
    setDismissingId(req.id);
    try {
      const res = await fetch(`/api/admin/requests/${req.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'dismiss' }),
      });
      const data = await res.json();
      if (!res.ok) { setErrors((p) => ({ ...p, [req.id]: data.error || 'Failed' })); return; }
      setRequests((prev) =>
        prev.map((r) => r.id === req.id ? { ...r, status: 'dismissed', resolvedAt: new Date().toISOString() } : r)
      );
    } finally {
      setDismissingId(null);
    }
  };

  const handleGranted = (id: string) => {
    setRequests((prev) =>
      prev.map((r) => r.id === id ? { ...r, status: 'granted', resolvedAt: new Date().toISOString() } : r)
    );
  };

  const pending = requests.filter((r) => r.status === 'pending');
  const resolved = requests.filter((r) => r.status !== 'pending');

  const RequestTable = ({ rows, showActions }: { rows: RequestRow[]; showActions: boolean }) => (
    <table className="admin-table" style={{ marginBottom: 32 }}>
      <thead>
        <tr>
          <th>Email</th>
          <th>Source</th>
          <th className="admin-col-role">Status</th>
          <th className="admin-col-date">Requested</th>
          <th className="admin-col-date">Resolved</th>
          {showActions && <th className="admin-actions-cell">Actions</th>}
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 && (
          <tr><td colSpan={showActions ? 6 : 5} style={{ color: 'var(--muted)', padding: '16px 12px', fontSize: 13 }}>No requests.</td></tr>
        )}
        {rows.map((r) => (
          <tr key={r.id}>
            <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{r.email}</td>
            <td style={{ fontSize: 12, color: 'var(--muted)' }}>{r.source ?? '—'}</td>
            <td className="admin-col-role"><StatusBadge status={r.status} /></td>
            <td className="admin-col-date">{fmt(r.createdAt)}</td>
            <td className="admin-col-date">{fmt(r.resolvedAt)}</td>
            {showActions && (
              <td>
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <button className="admin-btn admin-btn-primary" onClick={() => setGrantTarget(r)}>Grant</button>
                  <button
                    className="admin-btn"
                    disabled={dismissingId === r.id}
                    onClick={() => handleDismiss(r)}
                  >
                    Dismiss
                  </button>
                  {errors[r.id] && <span className="admin-error">{errors[r.id]}</span>}
                </div>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );

  return (
    <>
      <h2 className="mono-caption" style={{ margin: '0 0 12px', color: 'var(--text)', fontSize: 12, lineHeight: '15px', textTransform: 'uppercase' }}>
        Pending ({pending.length})
      </h2>
      <RequestTable rows={pending} showActions />

      <h2 className="mono-caption" style={{ margin: '0 0 12px', color: 'var(--muted)', fontSize: 12, lineHeight: '15px', textTransform: 'uppercase' }}>
        Resolved ({resolved.length})
      </h2>
      <RequestTable rows={resolved} showActions={false} />

      {grantTarget && (
        <GrantModal
          req={grantTarget}
          onClose={() => setGrantTarget(null)}
          onGranted={handleGranted}
        />
      )}
    </>
  );
}
