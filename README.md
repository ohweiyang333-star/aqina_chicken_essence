# Aqina Chicken Essence - Singapore Platform

## Project Overview
High-conversion marketing platform for Aqina Chicken Essence in Singapore, featuring a bilingual Landing Page and a comprehensive Admin Console.

## Tech Stack
- **Frontend**: Next.js 15, Tailwind CSS v4, TypeScript, next-intl
- **Backend**: FastAPI, Python 3.11, Firebase Admin SDK
- **Database/Auth**: Firebase Firestore, Firebase Auth, Firebase Storage
- **Deployment**: Google Cloud Run
- **CI/CD**: GitHub Actions

## Directory Structure
- `frontend/`: Next.js web application
- `backend/`: FastAPI Python implementation
- `.github/workflows/`: CI/CD automation logic

## Deployment
Automated deployment via GitHub Actions.

- Target routing source-of-truth: `deployment-targets.json`
- Frontend: Cloud Run or Firebase Hosting (based on target config)
- Backend: Cloud Run
- Firestore rules/indexes: GitHub Actions deploy workflow

Production deploy policy: use GitHub Actions only (no local production deploy).
