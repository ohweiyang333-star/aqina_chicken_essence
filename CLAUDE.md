# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

E-commerce and admin platform for Aqina 滴鸡精 (chicken essence health supplement), targeting the Singapore market. Consists of a bilingual (English/Simplified Chinese) marketing landing page with checkout, and an admin console for order management.

## Repository Structure

```
aqina-chicken-essence/
├── frontend/          # Next.js 16 app (landing page + admin)
├── backend/           # FastAPI Python service (app/ dir is empty — not yet implemented)
├── .github/workflows/ # CI/CD: Cloud Run / Firebase Hosting / Firestore deploy
├── deployment-targets.json # Deployment target source-of-truth
├── firestore.rules    # Firestore security rules
└── firebase.json      # Firebase project config (region: asia-southeast1)
```

## Commands

### Frontend

```bash
cd frontend
npm run dev       # Dev server at http://localhost:3000
npm run build     # Production build
npm run lint      # ESLint
```

### Backend

The backend `app/` directory is currently empty. The Dockerfile expects `app.main:app` (FastAPI entry point):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload  # Dev server at http://localhost:8000
```

### Firebase

```bash
# Local debug only (NO production deploy from local machine)
firebase emulators:start
```

## Unified Deployment Policy (Mandatory)

All deployment must go through **GitHub Actions** only.  
Do not deploy from local machine with `gcloud run deploy` or `firebase deploy` for production.

Single source-of-truth:
- `deployment-targets.json`

Workflows:
- `.github/workflows/deploy-frontend.yml` → Frontend to Cloud Run (when `frontend.platform=cloud_run`)
- `.github/workflows/deploy-backend.yml` → Backend to Cloud Run (when `backend.platform=cloud_run`)
- `.github/workflows/deploy-firebase-hosting.yml` → Frontend to Firebase Hosting (when `frontend.platform=firebase_hosting`)
- `.github/workflows/deploy-firestore.yml` → Firestore rules/indexes deploy

Release flow:
1. Implement changes
2. Run local checks (`npm run build`, tests)
3. Commit and push to `main`
4. Wait for GitHub Actions deployment job(s)

If deployment target changes (Cloud Run <-> Firebase Hosting), update **only** `deployment-targets.json`, then push.

## Frontend Architecture

**Next.js 16 with App Router** — note: this version has breaking API changes from earlier Next.js versions. Check `node_modules/next/dist/docs/` before writing Next.js-specific code (per AGENTS.md).

### Routing

- `/` and `/en/*` — English landing page
- `/zh/*` — Simplified Chinese landing page
- `/admin/login` — Google OAuth login
- `/admin` — Protected admin dashboard

Locale routing uses `next-intl` middleware (`src/middleware.ts`) with `localePrefix: 'as-needed'` (English is the default, no `/en/` prefix needed).

### Key Source Files

```
frontend/src/
├── app/[locale]/          # Localized landing page routes
├── app/admin/             # Admin section (login + dashboard)
├── components/            # UI components (Header, CheckoutModal, CartDrawer, WhatsAppButton)
├── lib/
│   ├── firebase.ts        # Firebase SDK initialization (db, auth, storage exports)
│   ├── auth-service.ts    # Google OAuth + admin role check (admin_users collection)
│   └── order-service.ts   # Firestore CRUD for orders
├── i18n/request.ts        # next-intl server config
└── middleware.ts          # Locale routing middleware
messages/
├── en.json                # English translations
└── zh.json                # Simplified Chinese translations
```

### Order Flow

1. User selects product on landing page → `CheckoutModal` opens
2. Form validated with React Hook Form + Zod
3. `createOrder()` in `order-service.ts` writes directly to Firestore `orders` collection (no backend call currently)
4. Admin reads orders via `getOrders()` and updates status via `updateOrderStatus()`

### Admin Auth Flow

1. Google OAuth via Firebase Auth (`/admin/login`)
2. `auth-service.ts` checks if the signed-in user's UID exists in the `admin_users` Firestore collection
3. Admin is redirected to `/admin` dashboard on success

## Firestore Data Model

| Collection | Read | Write |
|---|---|---|
| `products` | Public | Admin only |
| `orders` | Admin | Public create (anonymous checkout) |
| `payments` | Admin | Admin only |
| `customers` | Admin | Admin only |
| `chatbotSettings` | Public | Admin only |
| `admin_users` | Self (own UID) | Never (server-managed) |

Admin = authenticated user with UID present in `admin_users` collection.

## Environment Variables

Required in `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=https://aqina-backend-api-c3amale25a-as.a.run.app
NEXT_PUBLIC_FIREBASE_API_KEY=
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=
NEXT_PUBLIC_FIREBASE_PROJECT_ID=aqina-chicken-essence
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=aqina-chicken-essence.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=
NEXT_PUBLIC_FIREBASE_APP_ID=
NEXT_PUBLIC_WHATSAPP_DISPLAY="+65 9000 0000"
NEXT_PUBLIC_WHATSAPP_LINK=6590000000
NEXT_PUBLIC_CONTACT_EMAIL=sg-sales@aqina.com
NEXT_PUBLIC_PAYMENT_QR_IMAGE=
NEXT_PUBLIC_PAYMENT_QR_ALT="Boong Poultry Pte Ltd PayNow QR"
NEXT_PUBLIC_PAYMENT_ACCOUNT_NAME="Boong Poultry Pte Ltd"
NEXT_PUBLIC_WHATSAPP_PREFILL=
```

See `frontend/.env.example` and `backend/.env.example` for the full runtime key list. Sensitive backend values such as Meta tokens, Gemini API key, and internal task secret must come from GitHub Secrets or Cloud Run secrets, not source code.

## Deployment

GitHub Actions deploys on push to `main`, based on `deployment-targets.json`.
