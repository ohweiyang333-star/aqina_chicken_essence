# GEMINI.md (frontend)

## Deployment Rule (Must Follow)

- Frontend production deploy must go through GitHub Actions.
- Deployment target is resolved by root `deployment-targets.json`.
- If target is `cloud_run`, use Cloud Run frontend workflow.
- If target is `firebase_hosting`, use Firebase Hosting workflow.
- Never do local production deploy.
