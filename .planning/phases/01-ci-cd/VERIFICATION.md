# Phase 01 — Verification

Run on: 2026-04-16, branch `claude/quirky-feistel`, Node 20, local macOS.

## Goal-backward check

> "Every push and PR against `master` must run lint, typecheck, tests, and a production build before merge."

| Step       | Command           | Result | Notes                              |
|------------|-------------------|--------|------------------------------------|
| Lint       | `npm run lint`    | ✅ pass | 0 errors, 1 cosmetic warning       |
| Typecheck  | `npm run typecheck` | ✅ pass | `tsc --noEmit` clean               |
| Tests      | `npm test`        | ✅ pass | 2/2 in `lib/scoring.test.ts`       |
| Build      | `npm run build`   | ✅ pass | 30 static pages generated          |

All four steps are wired into `.github/workflows/ci.yml` in the same order. Pipeline triggers: `push` to `master`, `pull_request` targeting `master`.

## What this proves

- The pipeline definition matches what runs locally — no drift.
- The repo's existing code passes all four checks, so the gate is enforceable today (not aspirational).
- Vercel's existing config (`vercel.json`) is unchanged; deployment behavior is preserved.

## What this does NOT prove

- Pipeline will run successfully on GitHub-hosted runners (validated only on push).
- Branch protection is enforced (must be configured in GitHub repo settings).
- Tests catch real regressions — current suite is smoke-level only.

## Follow-up to confirm post-merge

1. Check Actions tab: workflow runs on this PR and exits 0.
2. Configure branch protection on `master` to require the `ci` check to pass.
3. Confirm Vercel still deploys on merge.
