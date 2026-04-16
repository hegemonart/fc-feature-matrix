import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from 'ws';
import * as schema from './schema';

// Required for Neon WebSocket connections outside the browser
neonConfig.webSocketConstructor = ws;

// Singleton pool — Next.js hot-reload-safe because module is cached
const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  throw new Error('DATABASE_URL environment variable is not set');
}

export const pool = new Pool({ connectionString });
export const db = drizzle(pool, { schema });
