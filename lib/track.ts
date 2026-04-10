/**
 * Client-side analytics helper.
 * Fire-and-forget POST to /api/analytics.
 */
export function trackEvent(type: string, data: Record<string, unknown> = {}): void {
  try {
    fetch('/api/analytics', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, data }),
      keepalive: true,
    }).catch(() => {});
  } catch {
    // Silently fail — analytics should never break the app
  }
}
