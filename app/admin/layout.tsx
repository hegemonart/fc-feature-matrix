import { redirect } from 'next/navigation';
import { cookies } from 'next/headers';
import { getSessionFromCookie, getUserByEmail } from '@/lib/auth';
import { AdminNav } from './_nav';

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
      <AdminNav email={user.email} />
      <main className="admin-main">{children}</main>
      <style>{`
        /* D-23 — admin chrome re-themed via design tokens (plan 05). */
        .admin-shell { display: flex; flex-direction: column; min-height: 100vh; font-family: var(--font-body, system-ui, sans-serif); background: var(--bg-page); color: var(--text); }
        .admin-nav { display: flex; align-items: center; gap: 16px; padding: 0 24px; height: 52px; background: var(--bg-cell); border-bottom: 1px solid var(--border); }
        /* Back button — same visual family as the HeaderBar "Get in touch" CTA. */
        .admin-back { display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.2); color: #fff; padding: 7px 14px; border-radius: 4px; text-decoration: none; font-family: var(--font-mono, 'Roboto Mono'), ui-monospace, monospace; font-weight: 500; font-size: 12px; line-height: 14px; letter-spacing: -0.24px; text-transform: uppercase; white-space: nowrap; transition: background 120ms ease-out; }
        .admin-back:hover { background: rgba(255,255,255,0.28); }
        .admin-back svg { flex-shrink: 0; }
        .admin-nav-links { display: flex; gap: 4px; flex: 1; margin-left: 8px; }
        .admin-nav-link { color: var(--muted); text-decoration: none; font-size: 13px; padding: 6px 12px; border-radius: 4px; transition: color 0.15s, background 0.15s; }
        .admin-nav-link:hover { color: var(--text); background: var(--bg-hover); }
        .admin-nav-link.active { color: var(--text); background: var(--bg-hover); }
        .admin-nav-meta { display: flex; align-items: center; gap: 12px; margin-left: auto; }
        /* Signed-in email — readable, not buried in muted gray. */
        .admin-nav-email { font-size: 13px; font-weight: 500; color: var(--text); letter-spacing: -0.2px; }
        /* Sign out — same CTA family as the Back button (translucent white, Roboto Mono uppercase). D-24: still secondary (white, not orange). */
        .admin-nav-signout { display: inline-flex; align-items: center; gap: 6px; background: rgba(255,255,255,0.2); color: #fff; padding: 7px 14px; border: 0; border-radius: 4px; cursor: pointer; font-family: var(--font-mono, 'Roboto Mono'), ui-monospace, monospace; font-weight: 500; font-size: 12px; line-height: 14px; letter-spacing: -0.24px; text-transform: uppercase; white-space: nowrap; transition: background 120ms ease-out; }
        .admin-nav-signout:hover { background: rgba(255,255,255,0.28); }
        .admin-main { flex: 1; padding: 32px 24px; max-width: 1200px; margin: 0 auto; width: 100%; box-sizing: border-box; }
        /* D-08 / D-22 — section headers in mono-caption */
        .admin-page-title { font-family: var(--font-mono), ui-monospace, SFMono-Regular, Menlo, monospace; font-weight: 500; font-size: 12px; line-height: 15px; letter-spacing: -0.5px; text-transform: uppercase; color: var(--text); margin: 0 0 24px; }
        .admin-table { width: 100%; border-collapse: collapse; font-size: 13px; background: var(--bg-cell); border: 1px solid var(--border); border-radius: 8px; overflow: hidden; table-layout: auto; }
        .admin-table th { text-align: left; padding: 14px 18px; border-bottom: 1px solid var(--border); color: var(--muted); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; background: var(--bg-cell); white-space: nowrap; }
        .admin-table td { padding: 14px 18px; border-bottom: 1px solid var(--border); vertical-align: middle; }
        .admin-table tr:last-child td { border-bottom: none; }
        .admin-table tr:hover td { background: var(--bg-hover); }
        /* Shared column-width grid — Users, Pending, and Resolved tables all use the same
           percentages so columns visually align when the three tables are stacked. */
        .admin-table .admin-col-role { width: 8%; white-space: nowrap; }
        .admin-table .admin-col-date { width: 12%; white-space: nowrap; font-size: 12px; color: var(--muted); }
        /* Pending "Requested" spans two date slots (Created + Last login in Users). */
        .admin-table .admin-col-date-double { width: 24%; white-space: nowrap; font-size: 12px; color: var(--muted); }
        .admin-table .admin-col-name { width: 18%; white-space: nowrap; }
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
        /* Actions column: fixed 28% keeps all three tables on the same right-side grid.
           Resolved table renders an empty <td> here as a visual spacer. */
        .admin-actions-cell { width: 28%; white-space: nowrap; }
        .admin-actions-row { display: flex; gap: 6px; align-items: center; }
        .admin-actions-row .admin-btn { min-width: 72px; }
        /* Email cell — monospace, smaller, stable width rhythm across tables. */
        .admin-col-email { width: 22%; font-family: var(--font-mono, ui-monospace, monospace); font-size: 12px; white-space: nowrap; }
        .admin-col-source { width: 18%; font-size: 12px; color: var(--muted); }
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
