import { Pool, neonConfig } from '@neondatabase/serverless';
import { drizzle } from 'drizzle-orm/neon-serverless';
import ws from 'ws';
import * as schema from './schema';

// Required for Neon WebSocket connections outside the browser
neonConfig.webSocketConstructor = ws;

// During `next build` (NEXT_PHASE=phase-production-build), DATABASE_URL may
// be absent. We create a stub pool that will throw only when actually queried —
// which never happens at build time (only at request time on the server).
const connectionString = process.env.DATABASE_URL || 'postgresql://build-placeholder:x@localhost/x';

export const pool = new Pool({ connectionString });
export const db = drizzle(pool, { schema });
