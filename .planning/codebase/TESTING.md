# Testing Patterns

**Analysis Date:** 2026-04-16

## Test Framework

**Status:** No testing framework currently installed

- No `jest`, `vitest`, or any other test runner in `package.json`
- No test configuration files (`jest.config.ts`, `vitest.config.ts`)
- No test files found in source code (only tests in `node_modules/` from dependencies)
- No test scripts in `package.json`

**Recommendation for Implementation:**
- Given Next.js 16.2.2 and TypeScript 5, `vitest` is preferred for unit tests
- `@testing-library/react` for component testing
- Playwright or Cypress for E2E testing (especially useful for feature matrix verification)

## Current Testing Approach

**Manual Testing:**
- No automated test suite exists
- Project uses manual cross-check procedures documented in `analysis/homepage/crosscheck/CLAUDE.md`
- Browser verification via Python Playwright scripts: `capture_elements.py`, `redo_bad_weak.py`
- Screenshot-based evidence collection for feature validation

## Testable Areas (Not Yet Covered)

### Unit Test Candidates

**Authentication (`lib/auth.ts`):**
- Password hashing: `hashPassword(password)` should hash and verify correctly
- Password verification: `verifyPassword(password, hash)` should validate correctly
- Session token creation: `createSessionToken(email)` should generate valid tokens
- Session token parsing: `parseSessionToken(token)` should extract email correctly and reject invalid tokens
- Session token tampering: Modified tokens should fail validation
- Cookie helpers: Cookie string generation and parsing

**Scoring (`lib/scoring.ts`):**
- `getProductScores(pid)` should calculate coverage percentage correctly
- Asymmetric scoring: features with `weightYes` and `weightNo` should sum correctly
- `getRankedProducts()` should sort by coverage percentage

**Analytics (`lib/analytics.ts`):**
- `logEvent()` should structure events with type, email, timestamp
- Event limiting: `ltrim` should maintain `MAX_EVENTS` limit
- Redis fallback: events should log to console if Redis unavailable
- `getEvents()` should filter by type and email correctly

**Summary Generation (`lib/summary.ts`):**
- Category strength classification (ok/warning/danger based on thresholds)
- Headline generation logic based on coverage tier
- Priority selection (top 3 missing features by band order)
- Conclusion narrative generation across various data shapes

### Component Test Candidates

**CategoryFilter.tsx:**
- Toggle category activation/deactivation
- Filter features by selected categories
- Render category grid with correct verdict colors (ok/warning/danger)
- Feature grouping by band (table_stakes, expected, competitive, innovation)

**ScrollRestore.tsx:**
- Restore scroll position on navigation
- Clear scroll state when appropriate

**PageTracker.tsx:**
- Track page views on mount
- Include correct metadata in tracked events

### Integration Test Candidates

**API Routes:**
- `POST /api/auth/login` — Valid credentials should return session token
- `POST /api/auth/login` — Invalid credentials should return 401
- `POST /api/auth/login` — Missing fields should return 400
- `POST /api/auth/logout` — Should clear session cookie
- `GET /api/auth/me` — Valid session should return user data
- `POST /api/analytics` — Event logging with session context
- `GET /api/analytics/view` — Retrieve analytics events with filtering

**Data Flow:**
- Feature presence data loading from JSON results
- Band computation on startup
- Product ranking calculations
- Club summary generation with narrative

## What's NOT Tested

**Areas without test coverage:**
1. `CategoryFilter.tsx` — Interactive state management
2. `ScrollRestore.tsx` — Scroll position persistence
3. `PageTracker.tsx` — Analytics event tracking
4. `app/club/[id]/page.tsx` — Full page rendering and static generation
5. File I/O in `lib/auth.ts` (`loadUsers()`, `getUsersFilePath()`)
6. Redis connection and caching in `lib/analytics.ts`
7. Authentication flow end-to-end
8. Cookie handling and session management
9. Error handling across all modules
10. Edge cases in summary generation logic

## Build Verification

**Current approach:**
- `npx next build` — Verifies TypeScript compilation and Next.js build success
- No automated tests run before build
- Linting: `npm run lint` — ESLint checks code style (runs on demand, not in CI)

## Feature Verification Process (Current)

**Cross-check methodology (documented in `analysis/homepage/crosscheck/CLAUDE.md`):**
1. Capture full-page or element-level screenshots of homepages
2. Evaluate against rubric in `analysis/homepage/HOME-PAGE.md`
3. Write presence data to `analysis/homepage/results/{club_id}.json`
4. Run `node analysis/homepage/crosscheck/recalculate-scores.js` to update rankings

**Evidence artifacts:**
- `analysis/homepage/screenshots/` — Full-page PNGs
- `analysis/homepage/crosscheck/img/` — Element-level screenshots (536 files for Chelsea, FC Barcelona, Arsenal)
- `analysis/homepage/results/` — JSON results per club

## Recommended Testing Strategy

### Immediate (Unit Tests)

```typescript
// Example: lib/auth.test.ts
describe('auth', () => {
  it('should hash and verify passwords', async () => {
    const password = 'test123';
    const hash = await hashPassword(password);
    const valid = await verifyPassword(password, hash);
    expect(valid).toBe(true);
  });

  it('should reject invalid passwords', async () => {
    const hash = await hashPassword('correct');
    const valid = await verifyPassword('wrong', hash);
    expect(valid).toBe(false);
  });

  it('should create and parse valid session tokens', () => {
    const token = createSessionToken('user@example.com');
    const parsed = parseSessionToken(token);
    expect(parsed?.email).toBe('user@example.com');
  });
});
```

### Medium Term (Component & Integration Tests)

```typescript
// Example: lib/scoring.test.ts
describe('scoring', () => {
  it('should calculate coverage percentage', () => {
    const scores = getProductScores('real_madrid');
    expect(scores.coveragePct).toBeGreaterThan(0);
    expect(scores.coveragePct).toBeLessThanOrEqual(100);
  });
});

// Example: app/api/auth/login/login.test.ts
describe('POST /api/auth/login', () => {
  it('should return session token for valid credentials', async () => {
    const response = await fetch('http://localhost:3000/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: 'test@example.com', password: 'correct' }),
    });
    expect(response.status).toBe(200);
  });
});
```

### Long Term (E2E Tests)

```bash
# Playwright test example
npx playwright test

# Tests would cover:
# - Full authentication flow (login → protected page → logout)
# - Feature matrix navigation and filtering
# - Category breakdown calculations
# - Data persistence across page reloads
```

## Test File Organization (Recommended)

**Location:** Co-located with source files

```
lib/
  ├── auth.ts
  ├── auth.test.ts
  ├── analytics.ts
  ├── analytics.test.ts
  └── ...

app/api/
  ├── auth/
  │   ├── login/
  │   │   ├── route.ts
  │   │   └── route.test.ts
  │   └── ...
  └── ...

app/club/
  ├── [id]/
  │   ├── CategoryFilter.tsx
  │   ├── CategoryFilter.test.tsx
  │   └── ...
```

## Coverage Goals

**Priority order:**
1. **High:** Authentication, session management, password hashing
2. **High:** Scoring calculations (most critical business logic)
3. **Medium:** API route validation and error handling
4. **Medium:** Component interactivity and state management
5. **Low:** Analytics event structure and Redis fallback

**Recommended coverage threshold:** 70% for critical paths (auth, scoring)

---

*Testing analysis: 2026-04-16*
