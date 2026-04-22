<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## Deployment Discipline (Mandatory)

- All production deployment must run via GitHub Actions.
- Never run local production deploy commands (`gcloud run deploy`, `firebase deploy`) for release.
- Read root `deployment-targets.json` to decide deployment target:
  - `frontend.platform=cloud_run` -> Cloud Run workflow
  - `frontend.platform=firebase_hosting` -> Firebase Hosting workflow
- Default release path: commit -> push `main` -> GitHub Actions deploy.
