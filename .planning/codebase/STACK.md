# Tech Stack

## Runtime & Framework

- **Language:** TypeScript 5.x (strict mode, `noEmit`, `isolatedModules`)
- **Runtime:** Node.js (version unspecified; Next.js 16 requires Node 18+)
- **Framework:** Next.js 16.2.2 with the App Router (`/app` directory)
- **UI library:** React 19.2.4 + ReactDOM 19.2.4
- **Rendering model:** Mixed — the main matrix page (`app/page.tsx`) uses `'use client'` (client-side rendering); the club detail pages (`app/club/[id]/page.tsx`) are async React Server Components with `generateStaticParams()` for static generation at build time.

## Build & Tooling

- **Bundler/compiler:** Next.js built-in (SWC/Webpack under the hood, configured via `next.config.ts`)
- **TypeScript compiler:** `tsc` with `noEmit: true` — type-checking only, Next.js handles transpilation
- **Module resolution:** `"bundler"` (tsconfig)
- **Path alias:** `@/*` maps to the repo root (e.g. `@/lib/data`)
- **Linter:** ESLint 9.x with `eslint-config-next` 16.2.2
- **Formatter:** None configured (no Prettier or similar)
- **Scripts:**
  - `npm run dev` — local dev server via `next dev`
  - `npm run build` — production build via `next build`
  - `npm run start` — production server via `next start`
  - `npm run lint` — runs `eslint`
  - `npm run concept` — runs `npm run dev` inside a `concept/` subdirectory (separate prototype, excluded from main tsconfig)

## Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `next` | 16.2.2 | Full-stack React framework (App Router, SSG, server components) |
| `react` | 19.2.4 | UI library |
| `react-dom` | 19.2.4 | DOM renderer |
| `@types/node` | ^20 | Node.js TypeScript types (dev) |
| `@types/react` | ^19 | React TypeScript types (dev) |
| `@types/react-dom` | ^19 | ReactDOM TypeScript types (dev) |
| `eslint` | ^9 | Static analysis (dev) |
| `eslint-config-next` | 16.2.2 | Next.js ESLint rule set (dev) |
| `typescript` | ^5 | TypeScript compiler (dev) |

No third-party UI component library, no CSS framework, no charting library, no state management library, no animation library. All styling is hand-written CSS via `app/globals.css` using CSS custom properties.

## Deployment

- **Platform:** Vercel (declared via `vercel.json` with `"framework": "nextjs"`)
- **CI/CD:** None configured in the repo (no GitHub Actions, no CircleCI, etc.)
- **Environments:** Single environment inferred (no staging/preview config beyond Vercel's default branch previews)
- **Static generation:** Club detail pages (`/club/[id]`) are statically pre-rendered for all 26 product IDs at build time via `generateStaticParams()`

## Environment Config

- **Environment variables:** None detected — no `.env` files, no `process.env` references in source code
- **Secrets management:** N/A — the app is entirely static/client-side data with no API keys, authentication tokens, or external service credentials
- **Config files:** `next.config.ts` (empty config object, no customisation), `tsconfig.json`, `vercel.json`
