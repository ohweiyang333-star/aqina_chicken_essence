# AGENTS.md

## Branch Policy (Mandatory)

Work directly on `main` for this project by default.

Do not create or switch to feature branches such as `codex/*` unless the user explicitly asks for a separate branch. Implement, verify, commit, and push from `main`.

## Unified GitHub CI/CD Policy (Mandatory)

This repository uses **GitHub Actions as the only production deployment path**.

Do not perform production deploy from local machine, including:
- `gcloud run deploy`
- `firebase deploy`

Use `deployment-targets.json` as the single source-of-truth for deploy target routing:
- `frontend.platform=cloud_run` -> `.github/workflows/deploy-frontend.yml`
- `frontend.platform=firebase_hosting` -> `.github/workflows/deploy-firebase-hosting.yml`
- `backend.platform=cloud_run` -> `.github/workflows/deploy-backend.yml`
- Firestore rules/indexes -> `.github/workflows/deploy-firestore.yml`

Release flow:
1. Implement + verify
2. Commit
3. Push to `main`
4. Monitor GitHub Actions until deployment success
