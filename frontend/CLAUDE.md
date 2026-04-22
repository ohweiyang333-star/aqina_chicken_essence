# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> See the root `CLAUDE.md` for full project context. This file covers frontend-specific details.

## Important: Next.js Version Notice

This project uses **Next.js 16**, which has breaking changes from earlier versions. APIs, conventions, and file structure may differ from training data. Check `node_modules/next/dist/docs/` before writing Next.js-specific code. Heed deprecation notices.

## Commands

```bash
npm run dev    # Dev server at http://localhost:3000
npm run build  # Production build
npm run lint   # ESLint
```

## Deployment Policy (Mandatory)

- Frontend deployment is **GitHub Actions only**.
- Do not run production deploy from local machine.
- Deployment target comes from root `deployment-targets.json`:
  - `frontend.platform=cloud_run` -> `.github/workflows/deploy-frontend.yml`
  - `frontend.platform=firebase_hosting` -> `.github/workflows/deploy-firebase-hosting.yml`
- Standard flow: code -> build/lint -> commit -> push `main` -> wait GitHub Actions.

## i18n

Translations live in `/messages/en.json` and `/messages/zh.json`. All user-visible strings must have entries in both files. The `[locale]` dynamic segment in `app/[locale]/` handles routing; `src/middleware.ts` uses `localePrefix: 'as-needed'` so English has no prefix.

## Form Validation

Use **React Hook Form** + **Zod** for all forms (already used in `CheckoutModal`). Define Zod schemas first, then pass to `zodResolver`.

## Firebase Usage

Import `db`, `auth`, `storage` from `src/lib/firebase.ts`. Never re-initialize Firebase — the singleton pattern in that file prevents duplicate app errors.

All Firestore writes from the frontend are unauthenticated (anonymous checkout). Admin reads/writes require the user to be in the `admin_users` collection (checked in `src/lib/auth-service.ts`).
