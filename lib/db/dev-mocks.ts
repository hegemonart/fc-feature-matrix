/* ================================================================
   lib/db/dev-mocks.ts

   Local-preview fixture data for admin pages that otherwise query
   Neon Postgres. These fixtures are consumed ONLY when
   `env.DATABASE_URL` is empty — which is impossible in production
   per lib/env.ts. Purpose: let Sergey eyeball the admin redesign
   without wiring Neon locally.

   Shape matches the serialised payloads in:
     - app/admin/users/page.tsx
     - app/admin/requests/page.tsx
   ================================================================ */

export type MockUserRow = {
  id: string;
  email: string;
  name: string | null;
  isAdmin: boolean;
  isPremium: boolean;
  createdAt: string; // ISO
  lastLoginAt: string | null; // ISO or null
};

export const MOCK_USERS: MockUserRow[] = [
  {
    id: 'dev-user-00000000-0000-0000-0000-000000000000',
    email: 'sergey@humbleteam.com',
    name: 'Sergey (dev)',
    isAdmin: true,
    isPremium: true,
    createdAt: '2026-01-12T09:15:00.000Z',
    lastLoginAt: '2026-04-17T10:22:00.000Z',
  },
  {
    id: '11111111-1111-1111-1111-111111111111',
    email: 'alice@humbleteam.com',
    name: 'Alice Johnson',
    isAdmin: true,
    isPremium: true,
    createdAt: '2026-02-03T14:40:00.000Z',
    lastLoginAt: '2026-04-16T18:02:00.000Z',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    email: 'marco@fcbarcelona.com',
    name: 'Marco Ferrari',
    isAdmin: false,
    isPremium: true,
    createdAt: '2026-02-28T11:07:00.000Z',
    lastLoginAt: '2026-04-15T08:45:00.000Z',
  },
  {
    id: '33333333-3333-3333-3333-333333333333',
    email: 'kim@liverpoolfc.com',
    name: 'Kim Park',
    isAdmin: false,
    isPremium: true,
    createdAt: '2026-03-10T16:30:00.000Z',
    lastLoginAt: '2026-04-12T20:10:00.000Z',
  },
  {
    id: '44444444-4444-4444-4444-444444444444',
    email: 'jamie@bayern.com',
    name: 'Jamie Rivera',
    isAdmin: false,
    isPremium: false,
    createdAt: '2026-03-22T07:55:00.000Z',
    lastLoginAt: null,
  },
  {
    id: '55555555-5555-5555-5555-555555555555',
    email: 'research@humbleteam.com',
    name: null,
    isAdmin: false,
    isPremium: true,
    createdAt: '2026-04-01T12:00:00.000Z',
    lastLoginAt: '2026-04-17T09:50:00.000Z',
  },
];

export type MockRequestRow = {
  id: string;
  email: string;
  source: string | null;
  ip: string | null;
  userAgent: string | null;
  status: 'pending' | 'granted' | 'dismissed';
  grantedUserId: string | null;
  resolvedAt: string | null; // ISO or null
  createdAt: string; // ISO
};

export const MOCK_REQUESTS: MockRequestRow[] = [
  {
    id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    email: 'marketing@chelseafc.com',
    source: 'locked_modal:Ticket Purchase',
    ip: '86.24.11.203',
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
    status: 'pending',
    grantedUserId: null,
    resolvedAt: null,
    createdAt: '2026-04-17T09:12:00.000Z',
  },
  {
    id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    email: 'product@atletico.com',
    source: 'locked_modal:Merch Store',
    ip: '192.168.42.17',
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64)',
    status: 'pending',
    grantedUserId: null,
    resolvedAt: null,
    createdAt: '2026-04-16T14:48:00.000Z',
  },
  {
    id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
    email: 'kim@liverpoolfc.com',
    source: 'coming_soon_modal:Matchday Experience',
    ip: '82.9.47.100',
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X)',
    status: 'granted',
    grantedUserId: '33333333-3333-3333-3333-333333333333',
    resolvedAt: '2026-03-11T10:00:00.000Z',
    createdAt: '2026-03-10T15:02:00.000Z',
  },
  {
    id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
    email: 'spam-bot-42@mailinator.com',
    source: 'locked_modal:Hospitality Packages',
    ip: '45.12.88.201',
    userAgent: 'curl/8.1.0',
    status: 'dismissed',
    grantedUserId: null,
    resolvedAt: '2026-04-05T11:20:00.000Z',
    createdAt: '2026-04-05T11:15:00.000Z',
  },
  {
    id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    email: 'research@humbleteam.com',
    source: 'locked_modal:Sponsorship Visibility',
    ip: '127.0.0.1',
    userAgent: 'Mozilla/5.0 (X11; Linux x86_64)',
    status: 'granted',
    grantedUserId: '55555555-5555-5555-5555-555555555555',
    resolvedAt: '2026-04-01T12:00:00.000Z',
    createdAt: '2026-04-01T11:45:00.000Z',
  },
];
