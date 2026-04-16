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
        .admin-shell { display: flex; flex-direction: column; min-height: 100vh; font-family: var(--font-sans, system-ui, sans-serif); }
        .admin-nav { display: flex; align-items: center; gap: 16px; padding: 0 24px; height: 52px; background: #0a0a0a; border-bottom: 1px solid #222; }
        .admin-nav-brand { color: #fff; text-decoration: none; font-weight: 600; font-size: 14px; margin-right: 8px; }
        .admin-nav-links { display: flex; gap: 4px; flex: 1; }
        .admin-nav-link { color: #aaa; text-decoration: none; font-size: 13px; padding: 4px 10px; border-radius: 4px; transition: color 0.15s, background 0.15s; }
        .admin-nav-link:hover { color: #fff; background: #1a1a1a; }
        .admin-nav-meta { display: flex; align-items: center; gap: 12px; margin-left: auto; }
        .admin-nav-email { font-size: 12px; color: #666; }
        .admin-nav-signout { background: none; border: 1px solid #333; color: #888; font-size: 12px; padding: 3px 10px; border-radius: 4px; cursor: pointer; }
        .admin-nav-signout:hover { color: #fff; border-color: #555; }
        .admin-main { flex: 1; padding: 32px 24px; max-width: 1200px; margin: 0 auto; width: 100%; box-sizing: border-box; }
        .admin-page-title { font-size: 20px; font-weight: 600; margin: 0 0 24px; }
        .admin-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .admin-table th { text-align: left; padding: 8px 12px; border-bottom: 1px solid #222; color: #666; font-weight: 500; }
        .admin-table td { padding: 10px 12px; border-bottom: 1px solid #111; vertical-align: middle; }
        .admin-table tr:hover td { background: #0d0d0d; }
        .admin-badge { display: inline-block; font-size: 11px; padding: 2px 7px; border-radius: 10px; }
        .admin-badge-admin { background: #1a3a1a; color: #4ade80; }
        .admin-badge-user { background: #1a1a1a; color: #666; }
        .admin-btn { padding: 4px 10px; font-size: 12px; border-radius: 4px; cursor: pointer; border: 1px solid #333; background: none; color: #ccc; }
        .admin-btn:hover { background: #1a1a1a; color: #fff; }
        .admin-btn-danger { border-color: #5a1a1a; color: #f87171; }
        .admin-btn-danger:hover { background: #2a0a0a; }
        .admin-btn-primary { background: #1a3a1a; border-color: #2d5a2d; color: #4ade80; }
        .admin-btn-primary:hover { background: #234a23; }
        .admin-modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 100; }
        .admin-modal { background: #111; border: 1px solid #222; border-radius: 8px; padding: 24px; min-width: 360px; max-width: 440px; }
        .admin-modal h3 { margin: 0 0 16px; font-size: 16px; }
        .admin-form-row { margin-bottom: 12px; }
        .admin-form-row label { display: block; font-size: 12px; color: #888; margin-bottom: 4px; }
        .admin-form-row input { width: 100%; padding: 7px 10px; border-radius: 4px; border: 1px solid #333; background: #0a0a0a; color: #fff; font-size: 13px; box-sizing: border-box; }
        .admin-form-actions { display: flex; gap: 8px; margin-top: 16px; justify-content: flex-end; }
        .admin-error { color: #f87171; font-size: 12px; margin-top: 8px; }
      `}</style>
    </div>
  );
}
