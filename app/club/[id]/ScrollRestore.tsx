'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

export default function ScrollRestore() {
  const pathname = usePathname();

  // Continuously save scroll position
  useEffect(() => {
    const save = () => {
      sessionStorage.setItem('club-scroll', String(Math.round(window.scrollY)));
    };
    window.addEventListener('scroll', save, { passive: true });
    return () => window.removeEventListener('scroll', save);
  }, []);

  // Restore on club-to-club navigation
  useEffect(() => {
    const prev = sessionStorage.getItem('club-path');
    const isClubNav = prev && prev !== pathname && prev.startsWith('/club/');

    if (isClubNav) {
      const y = parseInt(sessionStorage.getItem('club-scroll') || '0', 10);
      if (y > 0) {
        // Double rAF to run after Next.js scroll reset
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            window.scrollTo(0, y);
          });
        });
      }
    }

    sessionStorage.setItem('club-path', pathname);
  }, [pathname]);

  return null;
}
