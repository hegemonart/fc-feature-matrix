# Roadmap

## Milestone: foundations

| #  | Phase  | Status     | Notes                                              |
|----|--------|------------|----------------------------------------------------|
| 01 | ci-cd  | ✅ shipped | GitHub Actions (lint/typecheck/test/build) + Vercel |

## Backlog

- Expand test coverage beyond `lib/scoring.test.ts` smoke tests
- Tighten ESLint config (silence anonymous-default-export warning, audit rules)
- Add coverage reporting (`vitest --coverage`) and PR comment integration
