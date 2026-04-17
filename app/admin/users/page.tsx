import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';
import { asc } from 'drizzle-orm';
import { env } from '@/lib/env';
import { MOCK_USERS } from '@/lib/db/dev-mocks';
import { UsersActions } from './_actions';

export const metadata = { title: 'Users — Admin' };

export default async function AdminUsersPage() {
  // Dev-mode fallback — serve fixture data when no Neon is wired
  // (lib/env.ts makes DATABASE_URL optional outside prod).
  if (!env.DATABASE_URL) {
    return (
      <>
        <h1 className="admin-page-title">Users</h1>
        <UsersActions initialUsers={MOCK_USERS} />
      </>
    );
  }

  const allUsers = await db
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
    .orderBy(asc(users.createdAt));

  const serialised = allUsers.map((u) => ({
    ...u,
    createdAt: u.createdAt.toISOString(),
    lastLoginAt: u.lastLoginAt?.toISOString() ?? null,
  }));

  return (
    <>
      <h1 className="admin-page-title">Users</h1>
      <UsersActions initialUsers={serialised} />
    </>
  );
}
