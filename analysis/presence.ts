/* ================================================================
   analysis/presence.ts  --  Feature × Product presence matrix

   Each feature maps every product to 'full' or 'absent'.
   The makePresence() helper defaults everything to 'absent',
   then marks listed IDs as 'full'.
   ================================================================ */

import type { PresenceStatus } from './types';
import { ALL_IDS } from './products';

export function makePresence(
  full: string[],
  partial: string[] = [],
): Record<string, PresenceStatus> {
  const m: Record<string, PresenceStatus> = {};
  ALL_IDS.forEach(id => (m[id] = 'absent'));
  full.forEach(id => (m[id] = 'full'));
  partial.forEach(id => (m[id] = 'full')); // partial treated as present
  return m;
}
