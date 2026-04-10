import { createHmac } from 'crypto';
import bcrypt from 'bcryptjs';

const SECRET = process.env.AUTH_SECRET || 'fc-benchmark-dev-secret-change-in-prod';
const COOKIE_NAME = 'fc_session';
const MAX_AGE = 60 * 60 * 24 * 7; // 7 days

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
  if (sign(payload) !== sig) return null;
  // Extract email (everything before the last : which was timestamp)
  const lastColon = payload.lastIndexOf(':');
  if (lastColon === -1) return null;
  const email = payload.substring(0, lastColon);
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
  const match = cookieHeader.split(';').map(c => c.trim()).find(c => c.startsWith(`${COOKIE_NAME}=`));
  if (!match) return null;
  const token = match.substring(COOKIE_NAME.length + 1);
  return parseSessionToken(token);
}

// ── User store ──

export interface StoredUser {
  email: string;
  passwordHash: string;
  name?: string;
}

export function getUsersFilePath(): string {
  const path = require('path');
  return path.join(process.cwd(), 'data', 'users.json');
}

export function loadUsers(): StoredUser[] {
  const fs = require('fs');
  const filePath = getUsersFilePath();
  try {
    const raw = fs.readFileSync(filePath, 'utf-8');
    return JSON.parse(raw);
  } catch {
    return [];
  }
}
