---
phase: infra-redesign-v2
plan_id: 05
wave: 3
depends_on: [01, 02, 03, 04]
files_modified:
  - app/club/[id]/page.tsx
  - app/admin/analytics/page.tsx
  - app/admin/users/page.tsx
  - app/admin/access-requests/page.tsx
  - app/globals.css
  - tests/components/Modal.test.tsx
  - tests/visual/club-page.spec.ts
  - tests/visual/admin.spec.ts
  - tests/visual/lighthouse/homepage-a11y.png
  - CLAUDE.md
  - CHANGELOG.md
  - README.md
autonomous: true
decisions_addressed: [D-22, D-23, D-24, D-25, D-26, D-28]
must_haves:
  - '`/club/[id]` re-themed via token swap only (D-22). Stat labels gain `.mono-caption` treatment. Charts unchanged. Single orange CTA per page — the "Back to matrix" button is white-outlined (`border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF`); only one true accent CTA per page.'
  - '`/admin/analytics/page.tsx` Recharts dashboard re-colored per RESEARCH.md "Recharts Re-Theme — Diff Sketch" (D-23). All 13 numbered rows of color substitutions applied. Hard-code `#FF490C` in SVG `<linearGradient stopColor>` for safety (RESEARCH.md P2). No structural Recharts API changes.'
  - '`/admin/users/page.tsx` and `/admin/access-requests/page.tsx` re-themed: section-header mono-caption style applied; tables get the new `--bg-cell` / `--border` chrome. No structural changes.'
  - 'The three modals (sign-in, locked-content, coming-soon) audited. Token swap from plan 01 already propagates via `var(--accent)` etc. Verify each modal has exactly ONE orange CTA (`background: var(--accent)`) and the secondary action is text-only or white-outlined (D-24). Add `tests/components/Modal.test.tsx` rendering each of the three modal markups (extracted into a small fixture) and asserting per modal: exactly one element with the orange-CTA class, plus a white-outlined or text-only secondary.'
  - '`tests/visual/club-page.spec.ts` captures + commits a baseline for `/club/real_madrid` at 1440×900 with `maxDiffPixelRatio: 0.02` (D-26 extended).'
  - '`tests/visual/admin.spec.ts` captures + commits a baseline for `/admin/analytics`. Auth gate handled via Playwright `storageState` fixture (Claude''s Discretion: log in once via the API in a `globalSetup`, save cookies, reuse for the visual test). If `storageState` setup turns out to require a real DB user, fall back to skipping the admin spec with a TODO and capturing the screenshot manually for the v6.4 commit (acceptable since admin a11y is not in scope for D-29).'
  - '`CLAUDE.md` gains a new top-level "Design system" section (or appended block under "Commit and push rules") documenting the **single-orange-CTA-per-surface** rule (D-25). Exact wording: "Every page, panel, or modal must contain at most one element styled with `background: var(--accent)` (`#FF490C`). Secondary actions are text-only or white-outlined. This keeps the brand accent semantically meaningful — orange means ''this is the primary action.''"'
  - 'Lighthouse a11y ≥ 90 verified on the redesigned `/` (D-29 gate). Run `npx lighthouse http://localhost:3000 --only-categories=accessibility --chrome-flags="--headless" --output=json --output-path=tests/visual/lighthouse/homepage-a11y.json`, generate the matching PNG report, commit it. Score must be ≥ 90.'
  - 'Score data invariant verified at phase gate (D-28): `node analysis/homepage/crosscheck/recalculate-scores.js` then `git diff --quiet analysis/homepage/results/_scores.json analysis/homepage/results/_aggregate.json` returns 0.'
  - 'Full suite green: `npm test && npx playwright test && npx next build && node analysis/homepage/crosscheck/recalculate-scores.js && git diff --quiet analysis/homepage/results/`.'
  - 'CHANGELOG.md v7.0 major entry — system-wide visual rollout closes the redesign phase.'
---

<objective>
Extrapolate the redesign across the rest of the app: `/club/[id]` (D-22), `/admin/*` including the Recharts dashboard (D-23), and the three modals (D-24). Codify the single-orange-CTA-per-surface rule in `CLAUDE.md` (D-25) so future contributors don't accidentally add a second accent CTA. Capture the remaining visual-regression baselines (`/club/real_madrid`, `/admin/analytics`) per D-26 extended scope. Run Lighthouse a11y gate and commit the report (D-29). Run the score-data invariant check (D-28). This plan closes the phase.

Decisions landed: D-22, D-23, D-24, D-25, D-26 (full-coverage), D-28 (final gate).
</objective>

<tasks>

<task>
  <id>05-01</id>
  <description>Re-theme `app/club/[id]/page.tsx` via token swap (D-22). Audit for any hard-coded `#3b82f6` / `#4f6ef7` / `rgba(79,110,247,...)` / `#0d0d14` etc. — all replaced with `var(--accent)` / `var(--bg-page)` / `var(--bg-cell)` / `var(--border)`. Stat labels get `.mono-caption` (10/13/-1px) per D-08. Single orange CTA rule: change "Back to matrix" button to white-outlined (`border: 1px solid #FFFFFF; background: transparent; color: #FFFFFF`). If a future "Compare" or other primary CTA exists on this page, that one keeps the orange. Charts on the club page are NOT re-designed — only token swap applied. Run `npx next build` to confirm.</description>
  <files>app/club/[id]/page.tsx</files>
  <commit>refactor(infra-redesign-v2-05): token-swap /club/[id] re-theme (D-22)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>05-02</id>
  <description>Re-color the Recharts dashboard at `app/admin/analytics/page.tsx` per RESEARCH.md "Recharts Re-Theme — Diff Sketch" (D-23). Apply all 13 numbered substitutions verbatim: RankTable bar `rgba(255,73,12,0.07)`; metric-toggle active state orange-tinted; SVG `<linearGradient><stop>` hard-coded `#FF490C` (NOT `var(--accent)` — RESEARCH.md P2 mitigation); `<CartesianGrid stroke="var(--border)">`; XAxis/YAxis tick `#ABABAB`; Tooltip cursor `var(--border)`; Area stroke + activeDot `#FF490C`; ChartTooltip inner `var(--bg-cell)` / `var(--border)`; stat card `var(--bg-cell)` / `var(--border)`; stat card label/value/sub `#ABABAB / #FFFFFF / #ABABAB`; RankTable wrapper `var(--bg-cell)` / `var(--border)`; admin-link `var(--accent)`. No structural Recharts API changes. Confirm with `npx next build` and a quick local visual sanity check (no automated visual baseline yet — that's task 05-04).</description>
  <files>app/admin/analytics/page.tsx</files>
  <commit>refactor(infra-redesign-v2-05): re-color Recharts dashboard with new tokens (D-23)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>05-03</id>
  <description>Re-theme `app/admin/users/page.tsx` and `app/admin/access-requests/page.tsx`. Token-swap any hard-coded blue / dark-blue colors to the new `var(--accent)` / `var(--bg-page)` / `var(--bg-cell)` / `var(--border)`. Apply `.mono-caption` style to section headers (e.g. "USERS", "ACCESS REQUESTS"). Tables: `background: var(--bg-cell); border: 1px solid var(--border);`. No structural changes — same columns, same actions. Confirm with `npx next build`.</description>
  <files>app/admin/users/page.tsx, app/admin/access-requests/page.tsx</files>
  <commit>refactor(infra-redesign-v2-05): re-theme admin users + access-requests pages (D-23)</commit>
  <automated>npx next build</automated>
</task>

<task>
  <id>05-04</id>
  <description>Audit modals for D-24 single-orange-CTA compliance. The three modals are the locked-content, sign-in (login-card), and coming-soon, all rendered from `app/MatrixIsland.tsx` (post plan 04). Inspect each markup: exactly one element with `background: var(--accent)` (the primary CTA — "Sign in", "Send request", or "Got it"); the secondary (close, cancel, dismiss) is text-only (`color: var(--muted)`) or white-outlined. If any modal has two orange buttons, swap one to white-outlined. Write `tests/components/Modal.test.tsx` that imports the three modal renderings (or a small fixture component if they're not directly exportable from MatrixIsland — Claude's Discretion: extract them into `app/components/matrix/Modal.tsx` exporting `LockedModal`, `SignInModal`, `ComingSoonModal` if cleaner) and asserts per modal: (a) exactly one orange CTA element exists, (b) at least one white-outlined or text-only secondary action exists. Run the spec.</description>
  <files>tests/components/Modal.test.tsx</files>
  <commit>test(infra-redesign-v2-05): assert single-orange-CTA per modal (D-24)</commit>
  <automated>npm test -- --run tests/components/Modal.test.tsx</automated>
</task>

<task>
  <id>05-05</id>
  <description>Capture visual-regression baselines for `/club/real_madrid` and `/admin/analytics` (D-26 extended). Write `tests/visual/club-page.spec.ts` modeled on `tests/visual/homepage.spec.ts`: viewport 1440×900, `animations: 'disabled'`, `await page.waitForFunction(() => document.fonts.ready)`, `maxDiffPixelRatio: 0.02`. Write `tests/visual/admin.spec.ts` similarly but use a Playwright `storageState` fixture from `playwright.config.ts` to authenticate. Add a `globalSetup` script that posts to `/api/auth/login` with a fixture admin email/password (use the existing test admin if one exists, else create one as part of `globalSetup` and tear it down in `globalTeardown`). If `storageState` setup proves blocked by missing seed data, fall back to `test.skip(true, 'admin auth gate — manual screenshot in tests/visual/admin-1440x900.png committed instead')` and commit a manually-captured screenshot — flag this in the commit message. Capture baselines: `npm run dev &`, `npx playwright test --update-snapshots tests/visual/club-page.spec.ts tests/visual/admin.spec.ts`, kill server, commit baselines.</description>
  <files>tests/visual/club-page.spec.ts, tests/visual/admin.spec.ts</files>
  <commit>test(infra-redesign-v2-05): visual-regression baselines for /club + /admin (D-26)</commit>
  <automated>npx playwright test tests/visual/club-page.spec.ts tests/visual/admin.spec.ts</automated>
</task>

<task>
  <id>05-06</id>
  <description>Document the single-orange-CTA-per-surface rule in `CLAUDE.md` (D-25). Append a new section near the bottom of the project-level CLAUDE.md (`D:/AI/fc feature matrix/.claude/worktrees/thirsty-chaplygin-783e49/CLAUDE.md`), titled `## Design system rules`, with a bullet list. First bullet — exact text: "**Single orange CTA per surface.** Every page, panel, or modal must contain at most one element styled with `background: var(--accent)` (`#FF490C`). Secondary actions are text-only or white-outlined. This keeps the brand accent semantically meaningful — orange means 'this is the primary action.'" Second bullet documents the design tokens (point to `app/globals.css :root`). Third bullet documents the type stack (Inter Tight + Roboto Mono via `next/font`). Verify the file change includes the literal phrase via `grep -q "single orange CTA" CLAUDE.md`.</description>
  <files>CLAUDE.md</files>
  <commit>docs(infra-redesign-v2-05): document design-system rules in CLAUDE.md (D-25)</commit>
  <automated>grep -q "single orange CTA" CLAUDE.md</automated>
</task>

<task>
  <id>05-07</id>
  <description>Capture Lighthouse a11y report (D-29). Start the dev server (`npm run dev &`). Run `npx lighthouse http://localhost:3000 --only-categories=accessibility --chrome-flags="--headless" --output=html --output-path=tests/visual/lighthouse/homepage-a11y.html`. Open the HTML, screenshot the score panel as `tests/visual/lighthouse/homepage-a11y.png` (use Playwright headed or any screenshot tool). The captured a11y score MUST be ≥ 90. If it's below 90, fix the most common failures first: (a) ensure all interactive elements have accessible names; (b) ensure color contrast on `#ABABAB` over `#0F0F0F` passes (it should — about 5.5:1, AA-large); (c) ensure all `<button>` and `<DataCell>` are reachable by keyboard. Re-run until ≥ 90. Commit both the JSON output and the PNG.</description>
  <files>tests/visual/lighthouse/homepage-a11y.png</files>
  <commit>test(infra-redesign-v2-05): commit Lighthouse a11y report ≥ 90 (D-29)</commit>
  <automated>node -e "const r=require('./tests/visual/lighthouse/homepage-a11y.json'); if(r.categories.accessibility.score &lt; 0.9) process.exit(1);"</automated>
</task>

<task>
  <id>05-08</id>
  <description>Final phase gate. Run the full suite: `npm test && npx playwright test && npx next build && node analysis/homepage/crosscheck/recalculate-scores.js && git diff --quiet analysis/homepage/results/`. The `git diff --quiet` is the D-28 score-data invariant — if it fails, the redesign accidentally touched scoring; STOP and revert (per CONTEXT.md D-28). Add CHANGELOG.md v7.0 major entry: "System-wide visual redesign rollout: /club/[id] re-themed, /admin/* + Recharts dashboard re-colored, modals audited for single-orange-CTA compliance, Lighthouse a11y ≥ 90, design-system rules documented in CLAUDE.md. Closes infra-redesign-v2." Keep under 300 chars. Update README.md if any section now lists the design-system rules or links to CLAUDE.md design section.</description>
  <files>CHANGELOG.md, README.md</files>
  <commit>docs(infra-redesign-v2-05): changelog v7.0 + README final pass — phase close</commit>
  <automated>npm test &amp;&amp; npx playwright test &amp;&amp; npx next build &amp;&amp; node analysis/homepage/crosscheck/recalculate-scores.js &amp;&amp; git diff --quiet analysis/homepage/results/</automated>
</task>

</tasks>

<verification>
- Wave merge: full suite green (`npm test && npx playwright test && npx next build`).
- Phase gate: D-28 score-invariant proven (`git diff --quiet analysis/homepage/results/` returns 0 after `recalculate-scores.js`).
- Phase gate: Lighthouse a11y ≥ 90 PNG committed at `tests/visual/lighthouse/homepage-a11y.png`.
- Phase gate: visual baselines committed for homepage (plan 04), `/club/real_madrid` (plan 05), and `/admin/analytics` (plan 05) — `maxDiffPixelRatio: 0.02` enforced.
- `grep -q "single orange CTA" CLAUDE.md` returns 0 (D-25 documented).
- Decision-verification rows appended to VALIDATION.md.
- Manual sign-off: Sergey eyeballs `/` against Figma node `43:36` at 1440×900 (D-26 manual gate).
</verification>
