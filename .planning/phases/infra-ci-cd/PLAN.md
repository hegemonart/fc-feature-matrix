# Infrastructure Phase — CI/CD pipeline

> **Status:** Out-of-band infrastructure work, not part of the v2–v11 product roadmap. Numbered `infra-ci-cd` rather than a sequential phase number to keep `ROADMAP.md` (Phases 1–6 product flows) untouched.

## Goal

Every push and PR against `master` runs lint → typecheck → test → build before merge. Vercel deployment behavior is preserved.

## Why now

- Vercel is the only existing build gate, and it runs *after* merge to `master` — broken code can land before anyone notices.
- `npm run lint` was broken on master (ESLint 9 flat config required, none present).
- No test framework was configured; `npm test` exited with "missing script".
- The flow phases ahead (1–6) will add Python capture scripts and rubric files that benefit from a green-by-default repo to merge into.

## Scope

| Layer    | Tool                    | Trigger                         |
|----------|-------------------------|---------------------------------|
| Lint     | `eslint` (flat config)  | GitHub Actions on push/PR to `master` |
| Types    | `tsc --noEmit`          | GitHub Actions on push/PR to `master` |
| Tests    | `vitest run`            | GitHub Actions on push/PR to `master` |
| Build    | `next build`            | GitHub Actions on push/PR to `master` |
| Deploy   | Vercel                  | Push to `master` (auto, unchanged) |

## Files

| File                           | Purpose                                                  |
|--------------------------------|----------------------------------------------------------|
| `.github/workflows/ci.yml`     | Pipeline — checkout, setup-node@20, npm ci, 4 checks     |
| `eslint.config.mjs`            | ESLint 9 flat config wrapping `eslint-config-next`       |
| `vitest.config.ts`             | Vitest with `@/` alias mirroring `tsconfig.json`         |
| `lib/scoring.test.ts`          | Smoke tests for `getProductScores` and `getRankedProducts` |
| `package.json`                 | Add `typecheck`, `test`, `test:watch` scripts; vitest devDep |
| `app/page.tsx:303`             | Wrap `//` in JSX expression to fix `react/jsx-no-comment-textnodes` (pre-existing lint error) |
| `.gitignore`                   | Exclude `tsconfig.tsbuildinfo` (TS incremental build cache) |
| `CHANGELOG.md`                 | Add v5.0 entry per CLAUDE.md push rules                  |

## Out of scope

- Branch protection rules — must be configured in the GitHub repo settings UI, can't be code-defined
- Test coverage reporting (`vitest --coverage`)
- Matrix builds (Node 18 + 20)
- E2E or visual-regression tests
- Performance budgets
- Backfilling tests for `app/`, `lib/data.ts`, or `analysis/` modules

## Reuse

- `eslint-config-next@16.2.2` (already in devDependencies) — flat config exports an array, spread directly into `eslint.config.mjs`
- `@/` path alias from `tsconfig.json` — vitest config mirrors it so test imports match app imports
- `lib/scoring.ts` exports `getProductScores` and `getRankedProducts` — stable on master, used as test surface

## Risks

| Risk | Mitigation |
|------|-----------|
| `app/page.tsx:303` JSX change breaks header rendering | `<span>{'//'}</span>` and `<span>//</span>` produce identical DOM; `next build` validates compilation |
| GitHub-hosted Linux runner diverges from local macOS | `npm ci` for deterministic installs, Node 20 LTS, no platform-specific deps |
| Vitest incompatible with Next.js 16 / React 19 | Pin `vitest@^2.1.8` (known compatible with React 19) |
| Pipeline catches more lint warnings on first run | Lint exits 0 with warnings — only errors fail the gate |

## Follow-ups (not in this phase)

- Configure branch protection on `master` requiring the `ci` check
- Expand tests beyond smoke-level — at minimum `lib/scoring.ts` arithmetic, `analysis/` exports
- Silence the `import/no-anonymous-default-export` warning in `eslint.config.mjs`
- Address pre-existing `<img>` warnings in `app/page.tsx` (recommend `next/image`)
- Consider adding `.nvmrc` so local Node version matches CI (Node 20)
