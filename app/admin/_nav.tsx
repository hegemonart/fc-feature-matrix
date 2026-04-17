'use client';

/* ================================================================
   AdminNav

   Client nav island for the admin layout. Uses usePathname() to
   highlight the active tab. Back button (leftmost) routes to "/",
   styled to match the HeaderBar "Get in touch" CTA (translucent
   white, Roboto Mono uppercase, 4px radius). Order per Sergey's
   spec: Back · Users · Requests · Analytics.
   ================================================================ */

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const LINKS = [
  { href: '/admin/users',    label: 'Users' },
  { href: '/admin/requests', label: 'Requests' },
  { href: '/admin/analytics', label: 'Analytics' },
];

export function AdminNav({ email }: { email: string }) {
  const pathname = usePathname();
  return (
    <nav className="admin-nav" aria-label="Admin">
      <Link href="/" className="admin-back" aria-label="Back to benchmark">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M19 12H5m7-7-7 7 7 7" />
        </svg>
        Back
      </Link>
      <div className="admin-nav-links">
        {LINKS.map((l) => {
          // Treat `/admin` itself as the Users tab so the default
          // landing page gets a correctly-highlighted tab.
          const active =
            pathname === l.href ||
            (l.href === '/admin/users' && pathname === '/admin');
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`admin-nav-link${active ? ' active' : ''}`}
              aria-current={active ? 'page' : undefined}
            >
              {l.label}
            </Link>
          );
        })}
      </div>
      <div className="admin-nav-meta">
        <span className="admin-nav-email">{email}</span>
        <form action="/api/auth/logout" method="POST">
          <button type="submit" className="admin-nav-signout">Sign out</button>
        </form>
      </div>
    </nav>
  );
}
