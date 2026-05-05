'use client';

/* ================================================================
   <SettingsForm>

   Client-side form for /admin/settings. Currently surfaces a single
   field — DISPLAY_DATE (the date label rendered in HeaderBar) — but
   the layout is generic so additional settings can be added as new
   sections without restructuring.

   PATCH /api/admin/settings/display-date persists the new value.
   On success we mirror the value into local state and refresh the
   Server Component tree so the live header updates immediately.
   ================================================================ */

import { useRouter } from 'next/navigation';
import { useState, useTransition } from 'react';

interface Props {
  initialDisplayDate: string;
  envFallback: string;
}

export function SettingsForm({ initialDisplayDate, envFallback }: Props) {
  const router = useRouter();
  const [date, setDate] = useState(initialDisplayDate);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSavedAt(null);

    try {
      const res = await fetch('/api/admin/settings/display-date', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: date }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Failed to save');
        return;
      }
      setSavedAt(new Date().toLocaleTimeString());
      // Refresh layout so the HeaderBar picks up the new date.
      startTransition(() => router.refresh());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Network error');
    }
  };

  const handleReset = () => {
    setDate(envFallback);
  };

  return (
    <form onSubmit={handleSubmit} className="admin-settings-form">
      <fieldset>
        <legend>HeaderBar build date</legend>
        <p className="admin-settings-help">
          Shown next to &ldquo;FC Benchmark&rdquo; in the top header. ISO format <code>YYYY-MM-DD</code>;
          rendered as e.g. &ldquo;8th April, 2026&rdquo;. Leave blank to fall back to the
          build-time <code>BUILD_DATE</code> env value
          {envFallback ? (
            <>
              {' '}(currently <code>{envFallback}</code>)
            </>
          ) : null}
          .
        </p>

        <div className="admin-form-row">
          <label htmlFor="display-date">Display date</label>
          <input
            id="display-date"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
            pattern="\d{4}-\d{2}-\d{2}"
          />
        </div>

        {error && <div className="admin-error">{error}</div>}
        {savedAt && (
          <div className="admin-success">
            Saved at {savedAt}
            {pending ? ' (refreshing…)' : ''}
          </div>
        )}

        <div className="admin-form-actions">
          {envFallback && envFallback !== date && (
            <button
              type="button"
              className="admin-btn"
              onClick={handleReset}
              disabled={pending}
            >
              Reset to env default
            </button>
          )}
          <button
            type="submit"
            className="admin-btn admin-btn-primary"
            disabled={pending || !date}
          >
            {pending ? 'Saving…' : 'Save'}
          </button>
        </div>
      </fieldset>

      <style>{`
        .admin-settings-form fieldset {
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 20px 24px;
          background: var(--bg-cell);
          max-width: 560px;
        }
        .admin-settings-form legend {
          padding: 0 8px;
          font-family: var(--font-mono), ui-monospace, monospace;
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          color: var(--muted);
        }
        .admin-settings-help {
          margin: 0 0 18px;
          font-size: 13px;
          color: var(--muted);
          line-height: 1.5;
        }
        .admin-settings-help code {
          font-family: var(--font-mono), ui-monospace, monospace;
          font-size: 12px;
          padding: 1px 5px;
          background: var(--bg-hover);
          border-radius: 3px;
          color: var(--text);
        }
        .admin-success {
          color: #22c55e;
          font-size: 12px;
          margin: 8px 0;
        }
      `}</style>
    </form>
  );
}
