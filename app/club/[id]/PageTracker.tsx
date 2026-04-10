'use client';

import { useEffect } from 'react';
import { trackEvent } from '@/lib/track';

export default function PageTracker({ clubId }: { clubId: string }) {
  useEffect(() => {
    trackEvent('page_view', { path: `/club/${clubId}`, clubId });
  }, [clubId]);

  return null;
}
