import { db } from '@/lib/db';
import { accessRequests } from '@/lib/db/schema';
import { desc } from 'drizzle-orm';
import { RequestsActions } from './_actions';

export const metadata = { title: 'Access Requests — Admin' };

export default async function AdminRequestsPage() {
  const rows = await db
    .select()
    .from(accessRequests)
    .orderBy(desc(accessRequests.createdAt));

  const serialised = rows.map((r) => ({
    ...r,
    createdAt: r.createdAt.toISOString(),
    resolvedAt: r.resolvedAt?.toISOString() ?? null,
  }));

  return (
    <>
      <h1 className="admin-page-title">Access Requests</h1>
      <RequestsActions initialRequests={serialised} />
    </>
  );
}
