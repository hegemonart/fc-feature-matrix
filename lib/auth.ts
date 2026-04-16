import { createHmac } from 'crypto';
import bcrypt from 'bcryptjs';
import { env } from './env';
import { db } from './db';
import { users } from './db/schema';
import { eq } from 'drizzle-orm';

const SECRET = env.AUTH_SECRET;
const COOKIE_NAME = 'fc_session';
const MAX_AGE = 60 * 60 * 24 * 7; // 7 days in seconds

// ── Password helpers ──

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

// ── Session helpers ──

function sign(payload: string): string {
  return createHmac('sha256', SECRET).update(payload).digest('hex');
}

export function createSessionToken(email: string): string {
  const payload = `${email}:${Date.now()}`;
  const sig = sign(payload);
  return `${payload}:${sig}`;
}

export function parseSessionToken(token: string): { email: string } | null {
  const parts = token.split(':');
  if (parts.length < 3) return null;
  const sig = parts.pop()!;
  const payload = parts.join(':');

  // Verify HMAC
  if (sign(payload) !== sig) return null;

  // Extract timestamp (last segment of payload) and enforce token age
  const lastColon = payload.lastIndexOf(':');
  if (lastColon === -1) return null;
  const email = payload.substring(0, lastColon);
  const tsStr = payload.substring(lastColon + 1);
  const ts = parseInt(tsStr, 10);
  if (isNaN(ts)) return null;

  const ageMs = Date.now() - ts;
  if (ageMs > MAX_AGE * 1000) return null; // expired

  return { email };
}

// ── Cookie helpers ──

export function sessionCookieHeader(token: string): string {
  return `${COOKIE_NAME}=${token}; HttpOnly; Path=/; SameSite=Lax; Max-Age=${MAX_AGE}`;
}

export function clearSessionCookieHeader(): string {
  return `${COOKIE_NAME}=; HttpOnly; Path=/; SameSite=Lax; Max-Age=0`;
}

export function getSessionFromCookie(cookieHeader: string | null): { email: string } | null {
  if (!cookieHeader) return null;
  const match = cookieHeader
    .split(';')
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${COOKIE_NAME}=`));
  if (!match) return null;
  const token = match.substring(COOKIE_NAME.length + 1);
  return parseSessionToken(token);
}

// ── DB-backed user lookup ──

export interface AuthUser {
  id: string;
  email: string;
  passwordHash: string;
  name: string | null;
  isAdmin: boolean;
}

export async function getUserByEmail(email: string): Promise<AuthUser | null> {
  const rows = await db
    .select({
      id: users.id,
      email: users.email,
      passwordHash: users.passwordHash,
      name: users.name,
      isAdmin: users.isAdmin,
    })
    .from(users)
    .where(eq(users.email, email.toLowerCase()))
    .limit(1);
  return rows[0] ?? null;
}
