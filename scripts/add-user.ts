/**
 * Add a user to data/users.json
 * Usage: npx tsx scripts/add-user.ts <email> <password> [name]
 */
import fs from 'fs';
import path from 'path';
import bcrypt from 'bcryptjs';

const [, , email, password, name] = process.argv;

if (!email || !password) {
  console.error('Usage: npx tsx scripts/add-user.ts <email> <password> [name]');
  process.exit(1);
}

const filePath = path.join(process.cwd(), 'data', 'users.json');

let users: { email: string; passwordHash: string; name?: string }[] = [];
try {
  users = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
} catch {
  users = [];
}

if (users.some(u => u.email.toLowerCase() === email.toLowerCase())) {
  console.error(`User ${email} already exists.`);
  process.exit(1);
}

const passwordHash = bcrypt.hashSync(password, 10);
users.push({ email, passwordHash, ...(name ? { name } : {}) });
fs.writeFileSync(filePath, JSON.stringify(users, null, 2) + '\n');

console.log(`Added user: ${email}`);
