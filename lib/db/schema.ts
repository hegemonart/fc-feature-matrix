import {
  pgTable,
  pgEnum,
  uuid,
  varchar,
  boolean,
  timestamp,
  text,
  index,
  check,
} from 'drizzle-orm/pg-core';
import { sql } from 'drizzle-orm';

// ---------- Enums ----------

export const eventTypeEnum = pgEnum('event_type', [
  'login',
  'logout',
  'page_view',
  'feature_view',
  'access_request',
  'admin_user_created',
  'admin_request_granted',
  'admin_request_dismissed',
  'retention_run',
]);

// ---------- Tables ----------

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: varchar('email', { length: 255 }).notNull().unique(),
  passwordHash: varchar('password_hash', { length: 255 }).notNull(),
  name: varchar('name', { length: 255 }),
  isAdmin: boolean('is_admin').notNull().default(false),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  lastLoginAt: timestamp('last_login_at', { withTimezone: true }),
});

export const events = pgTable(
  'events',
  {
    id: uuid('id').primaryKey().defaultRandom(),
    // Soft FK — kept as varchar so events survive user deletion
    userEmail: varchar('user_email', { length: 255 }),
    // Hard FK — set null on user deletion for audit trail preservation
    userId: uuid('user_id').references(() => users.id, { onDelete: 'set null' }),
    type: eventTypeEnum('type').notNull(),
    data: text('data'), // JSON string for arbitrary payload
    userAgent: text('user_agent'),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [index('events_created_at_idx').on(t.createdAt)]
);

export const accessRequests = pgTable(
  'access_requests',
  {
    id: uuid('id').primaryKey().defaultRandom(),
    email: varchar('email', { length: 255 }).notNull(),
    source: varchar('source', { length: 100 }),
    ip: varchar('ip', { length: 45 }),
    userAgent: text('user_agent'),
    status: varchar('status', { length: 20 }).notNull().default('pending'),
    // Set null if the granted user is later deleted
    grantedUserId: uuid('granted_user_id').references(() => users.id, {
      onDelete: 'set null',
    }),
    resolvedAt: timestamp('resolved_at', { withTimezone: true }),
    createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  },
  (t) => [
    check('access_requests_status_check', sql`${t.status} IN ('pending','granted','dismissed')`),
  ]
);

// ---------- Types ----------

export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type Event = typeof events.$inferSelect;
export type NewEvent = typeof events.$inferInsert;
export type AccessRequest = typeof accessRequests.$inferSelect;
export type NewAccessRequest = typeof accessRequests.$inferInsert;
