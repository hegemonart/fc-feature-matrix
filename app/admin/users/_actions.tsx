'use client';

import { useState, useCallback } from 'react';

interface UserRow {
  id: string;
  email: string;
  name: string | null;
  isAdmin: boolean;
  isPremium: boolean;
  createdAt: string;
  lastLoginAt: string | null;
}

function fmt(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', {
    day: '2-digit', month: 'short', year: '2-digit',
    hour: '2-digit', minute: '2-digit',
  });
}

// ── Add user modal ──
function AddUserModal({ onClose, onAdded }: { onClose: () => void; onAdded: (u: UserRow) => void }) {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch('/api/admin/users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, name, password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Failed to create user'); return; }
      onAdded(data.user);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-modal-overlay" onClick={onClose}>
      <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Add user</h3>
        <form onSubmit={handleSubmit}>
          <div className="admin-form-row">
            <label>Email</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required autoFocus />
          </div>
          <div className="admin-form-row">
            <label>Name (optional)</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} />
          </div>
          <div className="admin-form-row">
            <label>Password (min 12 chars)</label>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={12} required />
          </div>
          {error && <div className="admin-error">{error}</div>}
          <div className="admin-form-actions">
            <button type="button" className="admin-btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="admin-btn admin-btn-primary" disabled={loading}>
              {loading ? 'Creating…' : 'Create user'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Reset password modal ──
function ResetPasswordModal({ user, onClose }: { user: UserRow; onClose: () => void }) {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`/api/admin/users/${user.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ newPassword: password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Failed to reset password'); return; }
      setDone(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-modal-overlay" onClick={onClose}>
      <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Reset password</h3>
        {done ? (
          <>
            <p style={{ color: 'var(--green)', fontSize: 13 }}>Password reset successfully.</p>
            <div className="admin-form-actions"><button className="admin-btn" onClick={onClose}>Close</button></div>
          </>
        ) : (
          <form onSubmit={handleSubmit}>
            <p style={{ fontSize: 13, color: 'var(--muted)', margin: '0 0 12px' }}>{user.email}</p>
            <div className="admin-form-row">
              <label>New password (min 12 chars)</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} minLength={12} required autoFocus />
            </div>
            {error && <div className="admin-error">{error}</div>}
            <div className="admin-form-actions">
              <button type="button" className="admin-btn" onClick={onClose}>Cancel</button>
              <button type="submit" className="admin-btn admin-btn-primary" disabled={loading}>
                {loading ? 'Saving…' : 'Save'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

// ── Delete modal ──
function DeleteModal({ user, onClose, onDeleted }: { user: UserRow; onClose: () => void; onDeleted: (id: string) => void }) {
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDelete = async () => {
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`/api/admin/users/${user.id}`, { method: 'DELETE' });
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Failed to delete user'); return; }
      onDeleted(user.id);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-modal-overlay" onClick={onClose}>
      <div className="admin-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Delete user</h3>
        <p style={{ fontSize: 13, color: 'var(--muted)', margin: '0 0 12px' }}>
          Type <strong>{user.email}</strong> to confirm deletion. This cannot be undone.
        </p>
        <div className="admin-form-row">
          <input type="text" value={confirm} onChange={e => setConfirm(e.target.value)} placeholder={user.email} autoFocus />
        </div>
        {error && <div className="admin-error">{error}</div>}
        <div className="admin-form-actions">
          <button type="button" className="admin-btn" onClick={onClose}>Cancel</button>
          <button
            type="button"
            className="admin-btn admin-btn-danger"
            disabled={confirm !== user.email || loading}
            onClick={handleDelete}
          >
            {loading ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main client component ──
export function UsersActions({ initialUsers }: { initialUsers: UserRow[] }) {
  const [userList, setUserList] = useState<UserRow[]>(initialUsers);
  const [showAdd, setShowAdd] = useState(false);
  const [resetTarget, setResetTarget] = useState<UserRow | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<UserRow | null>(null);
  const [roleChangingId, setRoleChangingId] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Three-way role model. Admin implies premium (admins are premium by
  // default — that's the product rule). The UI exposes a single role
  // dropdown; the PATCH body carries both flags derived from the choice.
  type Role = 'user' | 'premium' | 'admin';
  const roleOf = (u: UserRow): Role =>
    u.isAdmin ? 'admin' : u.isPremium ? 'premium' : 'user';
  const flagsFor = (role: Role): { isAdmin: boolean; isPremium: boolean } => {
    if (role === 'admin') return { isAdmin: true, isPremium: true };
    if (role === 'premium') return { isAdmin: false, isPremium: true };
    return { isAdmin: false, isPremium: false };
  };

  const handleRoleChange = useCallback(async (user: UserRow, nextRole: Role) => {
    if (roleOf(user) === nextRole) return;
    const next = flagsFor(nextRole);
    setRoleChangingId(user.id);
    setErrors((prev) => ({ ...prev, [user.id]: '' }));
    try {
      const res = await fetch(`/api/admin/users/${user.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(next),
      });
      const data = await res.json();
      if (!res.ok) {
        setErrors((prev) => ({ ...prev, [user.id]: data.error || 'Failed' }));
        return;
      }
      setUserList((prev) =>
        prev.map((u) => (u.id === user.id ? { ...u, ...next } : u))
      );
    } finally {
      setRoleChangingId(null);
    }
  }, []);

  return (
    <>
      <div style={{ marginBottom: 16 }}>
        <button className="admin-btn admin-btn-primary" onClick={() => setShowAdd(true)}>+ Add user</button>
      </div>

      <table className="admin-table">
        <thead>
          <tr>
            <th>Email</th>
            <th className="admin-col-name">Name</th>
            <th className="admin-col-role">Role</th>
            <th className="admin-col-date">Created</th>
            <th className="admin-col-date">Last login</th>
            <th className="admin-actions-cell">Actions</th>
          </tr>
        </thead>
        <tbody>
          {userList.map((u) => {
            const role = roleOf(u);
            const badgeClass =
              role === 'admin' ? 'admin-badge-admin'
              : role === 'premium' ? 'admin-badge-premium'
              : 'admin-badge-user';
            const badgeLabel =
              role === 'admin' ? 'admin'
              : role === 'premium' ? 'premium'
              : 'user';
            return (
              <tr key={u.id}>
                <td className="admin-col-email">{u.email}</td>
                <td className="admin-col-name">{u.name ?? '—'}</td>
                <td className="admin-col-role">
                  <span className={`admin-badge ${badgeClass}`}>{badgeLabel}</span>
                </td>
                <td className="admin-col-date">{fmt(u.createdAt)}</td>
                <td className="admin-col-date">{fmt(u.lastLoginAt)}</td>
                <td className="admin-actions-cell">
                  <div className="admin-actions-row">
                    <select
                      className="admin-select"
                      aria-label={`Role for ${u.email}`}
                      value={role}
                      disabled={roleChangingId === u.id}
                      onChange={(e) => handleRoleChange(u, e.target.value as Role)}
                    >
                      <option value="user">User</option>
                      <option value="premium">Premium</option>
                      <option value="admin">Admin</option>
                    </select>
                    <button className="admin-btn" onClick={() => setResetTarget(u)}>Reset pw</button>
                    <button className="admin-btn admin-btn-danger" onClick={() => setDeleteTarget(u)}>Delete</button>
                    {errors[u.id] && <span className="admin-error">{errors[u.id]}</span>}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {showAdd && (
        <AddUserModal
          onClose={() => setShowAdd(false)}
          onAdded={(u) => setUserList((prev) => [...prev, u])}
        />
      )}
      {resetTarget && (
        <ResetPasswordModal user={resetTarget} onClose={() => setResetTarget(null)} />
      )}
      {deleteTarget && (
        <DeleteModal
          user={deleteTarget}
          onClose={() => setDeleteTarget(null)}
          onDeleted={(id) => setUserList((prev) => prev.filter((u) => u.id !== id))}
        />
      )}
    </>
  );
}
