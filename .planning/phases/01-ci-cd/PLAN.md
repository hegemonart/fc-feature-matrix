# Phase 01 — CI/CD

## Goal

Every push and PR against `master` must run lint, typecheck, tests, and a production build before merge. Vercel handles deployment.

## Why

Until now, nothing prevented broken code from being merged. The repo had no test framework, no lint config (ESLint 9 flat config missing), and only Vercel's build step as a backstop — and Vercel only runs on the deployed branch, not on PRs as a gate.

## Scope

| Layer    | Tool             | Trigger                |
|----------|------------------|------------------------|
| Lint     | `eslint` (flat)  | GitHub Actions on PR/push |
| Types    | `tsc --noEmit`   | GitHub Actions on PR/push |
| Tests    | `vitest run`     | GitHub Actions on PR/push |
| Build    | `next build`     | GitHub Actions on PR/push |
| Deploy   | Vercel           | Push to `master` (auto) |

## Files

| File                          | Purpose                                         |
|-------------------------------|-------------------------------------------------|
| `.github/workflows/ci.yml`    | Pipeline: checkout → setup-node → npm ci → 4 checks |
| `eslint.config.mjs`           | ESLint 9 flat config wrapping `eslint-config-next` |
| `vitest.config.ts`            | Vitest with `@/` alias matching `tsconfig.json`  |
| `lib/scoring.test.ts`         | Smoke tests: coverage in [0,100], ranked desc    |
| `package.json`                | Scripts: `typecheck`, `test`, `test:watch`; dev dep: `vitest` |

## Out of scope

- Test coverage reporting
- Branch protection rules (configured in GitHub UI, not code)
- Caching beyond `actions/setup-node` npm cache
- Matrix builds across Node versions (Node 20 only)

## Pre-existing issue fixed in scope

`app/page.tsx:198` had `<span>//</span>` which `react/jsx-no-comment-textnodes` flags as an error. Wrapped in a JSX expression `{'//'}` — renders identically, lint passes.

## Known follow-ups

- ESLint config emits one warning (`import/no-anonymous-default-export`) — cosmetic, doesn't fail CI
- Smoke tests are minimal; real coverage is backlog
