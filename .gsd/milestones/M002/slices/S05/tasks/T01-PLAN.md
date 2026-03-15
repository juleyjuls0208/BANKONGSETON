---
estimated_steps: 6
estimated_files: 1
---

# T01: Write docs/DEPLOY.md from research

**Slice:** S05 — Deployment Runbook
**Milestone:** M002

## Description

Write `docs/DEPLOY.md` from scratch as a numbered, task-oriented deployment runbook for PythonAnywhere. All content is already captured in S05-RESEARCH.md; this task assembles it into a document an operator can follow from zero to a passing `/api/health` call. Do not repurpose the existing `DEPLOYMENT_PYTHONANYHERE.md` or `DEPLOYMENT_GUIDE.md` — the research found stale paths, wrong port conventions, and missing M002 changes in both. Write fresh.

## Steps

1. Create `docs/` directory if it doesn't exist; create `docs/DEPLOY.md`.
2. Write the document in sections:
   - **Prerequisites** — Python 3.10+, git, PythonAnywhere account (note: free tier = one WSGI web app; dashboard + API both requires paid tier or second account)
   - **Clone & Virtual Environment** — `git clone`, `mkvirtualenv bangko-env`, `pip install -r backend/dashboard/requirements.txt`, `pip install -r backend/api/requirements_api.txt`
   - **Credentials Files** — `config/credentials.json` (required, both apps) and `config/firebase-credentials.json` (optional, FCM silently disabled if absent); placement is project root `config/` directory; both apps look for `config/credentials.json` first then fallback to cwd
   - **Environment Variables** — two sub-tables: Dashboard App vars (with required/optional, startup-hard-fail flag, description) and API App vars; use the complete audit from the research; note `JWT_SECRET` must match across both apps and must be explicitly set (api_server fallback generates a new random secret on every restart)
   - **PythonAnywhere WSGI Configuration** — corrected templates for both Dashboard (from `web_app import app as application`) and API (from `api_server import app as application`); use `YOUR_USERNAME` substitution throughout; explain that secrets go in PythonAnywhere "Web → Environment variables" or a `.env` file loaded by `load_dotenv()`, never hardcoded in the WSGI file
   - **First-Run Migration** — `python backend/migrate_transactions.py`; what each of the 3 functions does; post-migration manual verification checklist (ParentPhone column, Balance in column C, ItemsJson as last column in Transactions Log)
   - **Health Check Sequence** — expected 200 JSON for both apps; failure interpretation table (`sheets_ok: false, latency_ms: 0` = client never initialized; `sheets_ok: false, latency_ms: N` = connectivity probe failed; HTTP 503 = Sheets unreachable; `queue_pending > 0` = write backlog)
   - **Known Operational Constraints** — numbered list of all 8 constraints from the research: single-worker, E.164 phone format, offline queue auto-creation, Balance column C position, JWT_SECRET must be stable and shared, same GOOGLE_SHEETS_ID for both apps, `config/credentials.json` placement, no CI pipeline
   - **Pre-Deploy Test Suite** — `python -m pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short`; expected: 35 passed, ~2–4s, zero HTTP requests; reference `bash scripts/verify-s03.sh` and `bash scripts/verify-s02.sh` for structural regression checks
3. Include the startup guard quick-reference table (which env/condition → which file → what error).
4. Include the Google Sheets required-vs-auto-created table so operators know which sheets to create manually before first start.
5. Run the 8 grep verification checks to confirm all required topics are present.

## Must-Haves

- [ ] `docs/DEPLOY.md` exists
- [ ] Env var table for Dashboard App covers all vars from research audit with required/optional and startup-hard-fail flag
- [ ] Env var table for API App present with `JWT_SECRET` "must match dashboard" note
- [ ] Corrected WSGI templates (not verbatim wsgi.py) with `YOUR_USERNAME` substitution
- [ ] `python backend/migrate_transactions.py` migration step with post-migration verification checklist
- [ ] Health check section with failure interpretation table
- [ ] All 8 Known Operational Constraints present
- [ ] Pre-deploy test command with expected output

## Verification

```bash
test -f docs/DEPLOY.md && echo "FILE: OK" || echo "FILE: MISSING"
for pattern in "FLASK_SECRET_KEY" "WEB_CONCURRENCY" "E.164" "migrate_transactions.py" "queue_pending" "offline_queue.db" "firebase-credentials.json" "YOUR_USERNAME"; do
  grep -q "$pattern" docs/DEPLOY.md && echo "OK: $pattern" || echo "MISSING: $pattern"
done
```

All 9 lines should print OK.

## Inputs

- `.gsd/milestones/M002/slices/S05/S05-RESEARCH.md` — complete content source: env var audit, WSGI templates, health endpoint shapes, migration steps, constraints, Google Sheets schema
- S03-SUMMARY.md — confirmed health endpoint response shape: `{status, sheets_ok, latency_ms, queue_pending, timestamp}`; latency_ms=0 sentinel meaning; 503 on Sheets failure
- S04-SUMMARY.md — confirmed test suite command and output: 35 tests, 2.40s, zero live Sheets calls
- S01-SUMMARY.md — confirmed requirements files are valid; both apps install cleanly

## Observability Impact

This task produces a static documentation artifact (`docs/DEPLOY.md`). No runtime signals change as a result.

**What becomes inspectable after this task:**
- `grep` checks in the Verification section allow a future agent to confirm all required deployment topics are present without reading the full document.
- The startup guard quick-reference table in the document maps env var conditions to structured-log event names (`event=startup_aborted reason=*`), giving future agents a direct lookup for diagnosing deploy failures.
- The health endpoint failure-interpretation table makes `/api/health` JSON fields machine-readable from the runbook.

**Failure state that becomes visible:**
- If `docs/DEPLOY.md` is absent or incomplete, `test -f docs/DEPLOY.md` returns non-zero and the grep checks return `MISSING:` lines. These are the observable failure signals for this task.

**No redaction constraints apply** to the document itself — it describes env var *names* and *categories* (required/optional), not values.

## Expected Output

- `docs/DEPLOY.md` — complete PythonAnywhere deployment runbook covering all 8 required topics; readable end-to-end by a developer familiar with Python and git but unfamiliar with this specific project
