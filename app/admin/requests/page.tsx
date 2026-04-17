import { redirect } from 'next/navigation';

// /admin/requests was folded into /admin/users per the admin nav rework
// (Sergey's call — one fewer tab). Keep the route alive as a 308 redirect
// so bookmarks and old emails still land somewhere useful.
export default function AdminRequestsPage() {
  redirect('/admin/users');
}
