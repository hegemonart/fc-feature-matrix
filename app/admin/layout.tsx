import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { getSessionFromCookie, getUserByEmail } from '@/lib/auth';
import Link from 'next/link';

export const metadata = { title: 'Admin — FC Benchmark' };

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const cookieStore = await cookies();
  const cookieHeader = cookieStore
    .getAll()
    .map((c) => `${c.name}=${c.value}`)
    .join('; ');

  const session = getSessionFromCookie(cookieHeader);
  if (!session) redirect('/');

  const user = await getUserByEmail(session.email);
  if (!user?.isAdmin) redirect('/');

  return (
    <div className="admin-shell">
      <nav className="admin-nav">
        <Link href="/" className="admin-nav-brand">
          <span>FC Benchmark</span>
        </Link>
        <div className="admin-nav-links">
          <Link href="/admin/users" className="admin-nav-link">Users</Link>
          <Link href="/admin/analytics" className="admin-nav-link">Analytics</Link>
          <Link href="/admin/requests" className="admin-nav-link">Requests</Link>
        </div>
        <div className="admin-nav-meta">
          <span className="admin-nav-email">{user.email}</span>
          <form action="/api/auth/logout" method="POST">
            <button type="submit" className="admin-nav-signout">Sign out</button>
          </form>
        </div>
      </nav>
      <main className="admin-main">{children}</main>
      <style>{`
        /* D-23 — admin chrome re-themed via design tokens (plan 05). */
        .admin-shell { display: flex; flex-direction: column; min-height: 100vh; font-family: var(--font-body, system-ui, sans-serif); background: var(--bg-page); color: var(--text); }
        .admin-nav { display: flex; align-items: center; gap: 16px; padding: 0 24px; height: 52px; background: var(--bg-cell); border-bottom: 1px solid var(--border); }
        .admin-nav-brand { color: var(--text); text-decoration: none; font-weight: 600; font-size: 14px; margin-right: 8px; }
        .admin-nav-links { display: flex; gap: 4px; flex: 1; }
        .admin-nav-link { color: var(--muted); text-decoration: none; font-size: 13px; padding: 4px 10px; border-radius: 4px; transition: color 0.15s, background 0.15s; }
        .admin-nav-link:hover { color: var(--text); background: var(--bg-hover); }
        .admin-nav-meta { display: flex; align-items: center; gap: 12px; margin-left: auto; }
        .admin-nav-email { font-size: 12px; color: var(--muted); }
        /* D-24 — Sign-out is a secondary action (white-outlined / muted), not orange. */
        .admin-nav-signout { background: none; border: 1px solid var(--border); color: var(--muted); font-size: 12px; padding: 3px 10px; border-radius: 4px; cursor: pointer; }
        .admin-nav-signout:hover { color: var(--text); border-color: var(--muted); }
        .admin-main { flex: 1; padding: 32px 24px; max-width: 1200px; margin: 0 auto; width: 100%; box-sizing: border-box; }
        /* D-08 / D-22 — section headers in mono-caption */
        .admin-page-title { font-family: var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 500; font-size: 12px; line-height: 15px; letter-spacing: -0.5px; text-transform: uppercase; color: var(--text); margin: 0 0 24px; }
        .admin-table { width: 100%; border-collapse: collapse; font-size: 13px; background: var(--bg-cell); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; table-layout: auto; }
        .admin-table th { text-align: left; padding: 14px 18px; border-bottom: 1px solid var(--border); color: var(--muted); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; background: var(--bg-cell); white-space: nowrap; }
        .admin-table td { padding: 14px 18px; border-bottom: 1px solid var(--border); vertical-align: middle; }
        .admin-table tr:last-child td { border-bottom: none; }
        .admin-table tr:hover td { background: var(--bg-hover); }
        /* Column-width hints: narrow columns shrink to content; dates stay on one line. */
        .admin-table .admin-col-role { width: 1%; white-space: nowrap; }
        .admin-table .admin-col-date { width: 1%; white-space: nowrap; font-size: 12px; color: var(--muted); }
        /* Name column stays on one line too — short display names fit in ~140px. */
        .admin-table .admin-col-name { white-space: nowrap; }
        .admin-badge { display: inline-block; font-size: 11px; padding: 2px 7px; border-radius: 10px; }
        /* Admin role — cyan so it never collides with the orange premium pill. */
        .admin-badge-admin { background: rgba(6,182,212,0.14); color: #22d3ee; }
        /* Premium role — the orange brand pill (admins inherit premium by default). */
        .admin-badge-premium { background: rgba(255,73,12,0.12); color: var(--accent); }
        .admin-badge-user { background: var(--bg-hover); color: var(--muted); }
        /* Fixed-width role dropdown so the Actions column doesn't jump between rows. */
        .admin-select { width: 110px; padding: 4px 8px; font-size: 12px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg-cell); color: var(--text); cursor: pointer; appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'><path fill='none' stroke='%23ababab' stroke-width='1.5' d='M3 5l3 3 3-3'/></svg>"); background-repeat: no-repeat; background-position: right 8px center; padding-right: 24px; }
        .admin-select:hover { border-color: var(--muted); }
        .admin-select:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
        /* Keep Actions column width constant regardless of row content. */
        .admin-actions-cell { white-space: nowrap; }
        .admin-actions-row { display: flex; gap: 6px; align-items: center; }
        .admin-actions-row .admin-btn { min-width: 72px; }
        .admin-btn { padding: 4px 10px; font-size: 12px; border-radius: 4px; cursor: pointer; border: 1px solid var(--border); background: transparent; color: var(--text); transition: all 0.15s; }
        .admin-btn:hover { background: var(--bg-hover); color: var(--text); }
        .admin-btn-danger { border-color: rgba(239,68,68,0.4); color: var(--red); }
        .admin-btn-danger:hover { background: rgba(239,68,68,0.1); color: var(--red); }
        /* D-24 — admin-btn-primary is the orange CTA (single per surface). */
        .admin-btn-primary { background: var(--accent); border-color: var(--accent); color: #fff; }
        .admin-btn-primary:hover { background: var(--accent); filter: brightness(1.1); color: #fff; }
        .admin-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
        .admin-modal { background: var(--bg-cell); border: 1px solid var(--border); border-radius: 8px; padding: 24px; min-width: 360px; max-width: 440px; }
        .admin-modal h3 { margin: 0 0 16px; font-size: 16px; color: var(--text); }
        .admin-form-row { margin-bottom: 12px; }
        .admin-form-row label { display: block; font-size: 12px; color: var(--muted); margin-bottom: 4px; }
        .admin-form-row input { width: 100%; padding: 7px 10px; border-radius: 4px; border: 1px solid var(--border); background: var(--bg-page); color: var(--text); font-size: 13px; box-sizing: border-box; }
        .admin-form-row input:focus { outline: none; border-color: var(--accent); }
        .admin-form-actions { display: flex; gap: 8px; margin-top: 16px; justify-content: flex-end; }
        .admin-error { color: var(--red); font-size: 12px; margin-top: 8px; }
      `}</style>
    </div>
  );
}
