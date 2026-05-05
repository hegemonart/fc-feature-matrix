/* ================================================================
   /admin/settings

   Admin-only surface for editing site_settings rows. Layout-level
   middleware (app/admin/layout.tsx) already gates all /admin/* on
   isAdmin, so this page just reads the current value and hands it
   to the client form.
   ================================================================ */

import { getDisplayDate } from '@/lib/settings';
import { SettingsForm } from './_form';

export default async function AdminSettingsPage() {
  const displayDate = await getDisplayDate();
  const envFallback = process.env.BUILD_DATE ?? '';

  return (
    <div>
      <h1 className="admin-page-title">Settings</h1>
      <SettingsForm initialDisplayDate={displayDate} envFallback={envFallback} />
    </div>
  );
}
