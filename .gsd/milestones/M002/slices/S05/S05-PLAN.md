# S05: Deployment Runbook

**Goal:** Produce `docs/DEPLOY.md` — a complete, accurate PythonAnywhere deployment runbook for Bangko ng Seton that an operator can follow from zero to a passing `/api/health` call.

**Demo:** `docs/DEPLOY.md` exists and covers all eight required topics: env vars (both apps), service account setup, first-run migration, health check sequence, single-worker constraint, E.164 phone format, offline queue behavior on fresh deploy, and pre-deploy test suite invocation.

## Must-Haves

- `docs/DEPLOY.md` exists
- Every env var from the complete audit (both apps) is documented with required/optional classification and the startup-hard-fail flag noted where applicable
- WSGI config templates include corrected `sys.path` setup (not the verbatim `wsgi.py` files, which have wrong `project_home` depth)
- Single-worker constraint, E.164 phone format, Balance column C constraint, and offline queue auto-creation all documented under Known Operational Constraints
- First-run migration steps (`python backend/migrate_transactions.py`) and post-migration manual verification documented
- Health check sequence shows expected JSON and failure interpretation for both apps
- Pre-deploy test suite command (`pytest tests/test_cashier_routes.py tests/test_admin_critical.py`) included with expected output
- `config/credentials.json` and `config/firebase-credentials.json` placement documented; firebase noted as optional (FCM silently disabled when absent)

## Verification

- `test -f docs/DEPLOY.md` exits 0
- `grep -q "FLASK_SECRET_KEY" docs/DEPLOY.md` — env var table present
- `grep -q "WEB_CONCURRENCY" docs/DEPLOY.md` — single-worker constraint documented
- `grep -q "E.164" docs/DEPLOY.md` — phone format constraint documented
- `grep -q "migrate_transactions.py" docs/DEPLOY.md` — migration step documented
- `grep -q "queue_pending" docs/DEPLOY.md` — health check JSON fields documented
- `grep -q "offline_queue.db" docs/DEPLOY.md` — offline queue auto-creation documented
- `grep -q "firebase-credentials.json" docs/DEPLOY.md` — optional FCM credential documented

## Tasks

- [x] **T01: Write docs/DEPLOY.md from research** `est:45m`
  - Why: R019 requires a runbook covering env vars, service account, first-run migration, health check sequence, single-worker constraint, E.164 format, and offline queue behavior; no such document exists today
  - Files: `docs/DEPLOY.md`
  - Do: Write from scratch using S05-RESEARCH.md as the authoritative source. Structure as a numbered deployment sequence (Prerequisites → Clone & venv → Credentials → Env Vars → WSGI Config → First-Run Migration → Health Check → Known Constraints → Pre-Deploy Tests). Use the corrected WSGI templates from the research (not the verbatim wsgi.py files). Mark all startup-hard-fail env vars explicitly. Include the `YOUR_USERNAME` substitution instructions for both WSGI configs. Document all items in the "Known Operational Constraints" list from the research (single-worker, E.164, Balance col C, JWT_SECRET stability, offline queue auto-creation, same GOOGLE_SHEETS_ID for both apps, firebase optional). End with the pre-deploy test suite command and expected output.
  - Verify: `bash -c 'for pattern in "FLASK_SECRET_KEY" "WEB_CONCURRENCY" "E.164" "migrate_transactions.py" "queue_pending" "offline_queue.db" "firebase-credentials.json" "YOUR_USERNAME"; do grep -q "$pattern" docs/DEPLOY.md && echo "OK: $pattern" || echo "MISSING: $pattern"; done'`
  - Done when: All 8 grep checks print `OK`; document reads as a complete, operator-followable runbook end-to-end

## Observability / Diagnostics

- **Runtime signals:** `docs/DEPLOY.md` is a static artifact — no runtime signals of its own. The document itself instructs operators to inspect runtime signals: health endpoint JSON (`/api/health`), PythonAnywhere error log (Web tab → Log files → Error log), and SQLite queue file (`backend/offline_queue.db`).
- **Inspection surfaces:** `grep` checks in the Verification section serve as the primary inspection surface for this slice. The startup guard quick-reference table in `docs/DEPLOY.md` maps failure conditions to specific structured-log events (e.g., `event=startup_aborted reason=insecure_secret_key`).
- **Failure visibility:** Deployment failures are visible via PythonAnywhere error logs. Startup guard aborts emit CRITICAL-level structured log lines before `sys.exit(1)`. Health check failures surface in the `/api/health` JSON (`sheets_ok: false`, `latency_ms: 0` sentinel).
- **Redaction constraints:** `FLASK_SECRET_KEY`, `JWT_SECRET`, `FINANCE_PASSWORD`, and `ADMIN_PASSWORD` must never appear in log output or WSGI file. The runbook explicitly directs operators to use PythonAnywhere "Web → Environment variables" tab or `.env` file — never hardcode in WSGI.

## Files Likely Touched

- `docs/DEPLOY.md`
