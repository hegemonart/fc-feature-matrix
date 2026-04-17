import { db } from '@/lib/db';
import { users, accessRequests } from '@/lib/db/schema';
import { asc, desc } from 'drizzle-orm';
import { env } from '@/lib/env';
import { MOCK_USERS, MOCK_REQUESTS } from '@/lib/db/dev-mocks';
import { UsersActions } from './_actions';
import { RequestsActions } from '../requests/_actions';

export const metadata = { title: 'Users — Admin' };

export default async function AdminUsersPage() {
  // Dev-mode fallback — serve fixture data when no Neon is wired
  // (lib/env.ts makes DATABASE_URL optional outside prod).
  if (!env.DATABASE_URL) {
    return (
      <>
        <h1 className="admin-page-title">Users</h1>
        <UsersActions initialUsers={MOCK_USERS} />
        <h2 className="admin-page-title" style={{ marginTop: 40 }}>Access Requests</h2>
        <RequestsActions initialRequests={MOCK_REQUESTS} />
      </>
    );
  }

  const [allUsers, reqRows] = await Promise.all([
    db
      .select({
        id: users.id,
        email: users.email,
        name: users.name,
        isAdmin: users.isAdmin,
        isPremium: users.isPremium,
        createdAt: users.createdAt,
        lastLoginAt: users.lastLoginAt,
      })
      .from(users)
      .orderBy(asc(users.createdAt)),
    db.select().from(accessRequests).orderBy(desc(accessRequests.createdAt)),
  ]);

  const serialised = allUsers.map((u) => ({
    ...u,
    createdAt: u.createdAt.toISOString(),
    lastLoginAt: u.lastLoginAt?.toISOString() ?? null,
  }));

  const serialisedRequests = reqRows.map((r) => ({
    ...r,
    createdAt: r.createdAt.toISOString(),
    resolvedAt: r.resolvedAt?.toISOString() ?? null,
  }));

  return (
    <>
      <h1 className="admin-page-title">Users</h1>
      <UsersActions initialUsers={serialised} />
      <h2 className="admin-page-title" style={{ marginTop: 40 }}>Access Requests</h2>
      <RequestsActions initialRequests={serialisedRequests} />
    </>
  );
}
