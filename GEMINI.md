# GEMINI.md

## Deployment Rule (Must Follow)

- Production deployment is GitHub Actions only.
- No local production deploy commands.
- Read `deployment-targets.json` before modifying any deployment workflow.
- Push to `main` triggers the target-specific workflow:
  - Cloud Run frontend/backend
  - Firebase Hosting frontend (when configured)
  - Firestore rules/indexes
