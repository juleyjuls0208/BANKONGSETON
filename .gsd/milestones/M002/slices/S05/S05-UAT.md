# S05: Deployment Runbook — UAT

**Milestone:** M002
**Written:** 2026-03-15

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: `docs/DEPLOY.md` is a static document artifact. Its correctness is fully verifiable by grep-based completeness checks (all 8 required topics present) and by manually following the numbered steps on a real PythonAnywhere account. No runtime components were changed in this slice — runtime behavior (health checks, startup guards, test suite) was verified in S03 and S04. This UAT confirms the document is complete, accurate, and operator-followable.

## Preconditions

- `docs/DEPLOY.md` exists in the project root's `docs/` directory
- The test suite from S04 passes locally (`pytest tests/test_cashier_routes.py tests/test_admin_critical.py`)
- A working internet connection (for the optional PythonAnywhere live-deploy path)

## Smoke Test

```bash
test -f docs/DEPLOY.md && echo "EXISTS" || echo "MISSING"
```
Expected: `EXISTS`

## Test Cases

### 1. All required topics present (grep completeness check)

Run from the project root:

```bash
for pattern in "FLASK_SECRET_KEY" "WEB_CONCURRENCY" "E.164" "migrate_transactions.py" \
               "queue_pending" "offline_queue.db" "firebase-credentials.json" "YOUR_USERNAME"; do
  grep -q "$pattern" docs/DEPLOY.md && echo "OK: $pattern" || echo "MISSING: $pattern"
done
```

**Expected:** All 8 lines print `OK: <pattern>`. Any `MISSING:` line is a failure.

---

### 2. Environment variable tables — both apps documented

Open `docs/DEPLOY.md` and locate the **Environment Variables** section.

1. Confirm there is a table for the **Dashboard App** (admin_dashboard.py).
2. Confirm `FLASK_SECRET_KEY`, `JWT_SECRET`, `ADMIN_PASSWORD`, `FINANCE_PASSWORD`, `GOOGLE_SHEETS_ID`, `GOOGLE_CREDENTIALS_FILE`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER`, `SMTP_*` are all listed.
3. Confirm each row includes required/optional classification.
4. Confirm startup-hard-fail env vars are explicitly flagged (e.g., `FLASK_SECRET_KEY` set to "changeme").
5. Confirm there is a separate table for the **API App** (api_server.py).
6. Confirm `JWT_SECRET` appears in the API table with a note that it must match the Dashboard's value.

**Expected:** Both tables present; all critical vars listed; startup-hard-fail note present; JWT_SECRET match-required note present.

---

### 3. WSGI config templates — corrected sys.path

Open `docs/DEPLOY.md` and locate the **PythonAnywhere WSGI Configuration** section.

1. Confirm the Dashboard WSGI template includes `sys.path.insert(0, '/home/YOUR_USERNAME/BANKONGSETON')` (project root).
2. Confirm the Dashboard WSGI template includes `sys.path.insert(0, '/home/YOUR_USERNAME/BANKONGSETON/backend')`.
3. Confirm the Dashboard WSGI template includes `sys.path.insert(0, '/home/YOUR_USERNAME/BANKONGSETON/backend/dashboard')`.
4. Confirm the API WSGI template similarly has 3 sys.path entries ending in `backend/api`.
5. Confirm `YOUR_USERNAME` appears as a substitution marker (not a real username).
6. Confirm the document explains why the existing `wsgi.py` path is wrong.

**Expected:** Both templates have the 3-level sys.path; `YOUR_USERNAME` present; explanation of wrong-depth pitfall documented.

---

### 4. Startup guard quick reference table

Open `docs/DEPLOY.md` and locate the **Startup Guard Quick Reference** section.

1. Confirm `WEB_CONCURRENCY` appears as one of the abort conditions.
2. Confirm a structured log event name (e.g., `event=startup_aborted`) is shown for each condition.
3. Confirm at least 3 distinct abort conditions are tabulated (WEB_CONCURRENCY > 1, insecure secret key, etc.).

**Expected:** Table present; WEB_CONCURRENCY row present; structured log event names shown.

---

### 5. First-run migration documented

Open `docs/DEPLOY.md` and locate the **First-Run Migration** section.

1. Confirm the exact command `python backend/migrate_transactions.py` is shown.
2. Confirm the section describes what the migration does (auto-creates worksheets, etc.).
3. Confirm a post-migration verification checklist is included (e.g., open Sheets, confirm worksheets exist).

**Expected:** Migration command present; description of what it does present; verification checklist present.

---

### 6. Health check sequence — expected JSON and failure interpretation

Open `docs/DEPLOY.md` and locate the **Health Check Sequence** section.

1. Confirm the expected JSON shape includes `status`, `sheets_ok`, `latency_ms`, `queue_pending`, `timestamp`.
2. Confirm the `queue_pending` field appears in the documented response (verifies grep check).
3. Confirm a failure-interpretation table is present mapping JSON variants to root causes.
4. Confirm both app health endpoints (`/api/health` on Dashboard and `/api/health` on API) are shown.
5. Confirm 503 response behavior is documented (when Sheets is unreachable).

**Expected:** Full JSON shape shown; queue_pending present; failure table present; both apps shown; 503 documented.

---

### 7. Known Operational Constraints — all 8 items

Open `docs/DEPLOY.md` and locate the **Known Operational Constraints** section.

Confirm all of the following are documented:

1. Single-worker only (`WEB_CONCURRENCY=1`) — FraudDetector split-brain risk
2. E.164 phone format requirement for SMS
3. Balance column C constraint (or equivalent Balance sheet structure note)
4. JWT_SECRET must stay stable across deploys
5. `offline_queue.db` is auto-created on first run (empty on fresh deploy)
6. Same `GOOGLE_SHEETS_ID` must be used for both apps
7. Firebase credentials (`firebase-credentials.json`) are optional — FCM silently disabled if absent
8. `ParentPhone` column must exist in Users sheet for SMS to work

**Expected:** All 8 constraints documented; `offline_queue.db` and `firebase-credentials.json` appear (verified by grep check).

---

### 8. Pre-deploy test suite command

Open `docs/DEPLOY.md` and locate the **Pre-Deploy Test Suite** section.

1. Confirm the exact command `pytest tests/test_cashier_routes.py tests/test_admin_critical.py` is shown.
2. Confirm expected output (e.g., "35 passed") is shown.
3. Run the command locally:

```bash
pytest tests/test_cashier_routes.py tests/test_admin_critical.py
```

**Expected:** Command present in doc; local run exits 0; 35 tests pass; no live Sheets calls (no network errors in output).

---

### 9. Credentials file placement documented

Open `docs/DEPLOY.md` and locate the **Credentials Files** section.

1. Confirm `config/credentials.json` placement is documented as required.
2. Confirm `config/firebase-credentials.json` placement is documented as optional.
3. Confirm the document notes that FCM is silently disabled when `firebase-credentials.json` is absent.
4. Confirm the path is relative to the project root (not an absolute path).

**Expected:** Both files documented; optional/required classification correct; silent-disable behavior noted.

---

## Edge Cases

### Missing GOOGLE_CREDENTIALS_FILE path

1. In `docs/DEPLOY.md`, locate the env var `GOOGLE_CREDENTIALS_FILE`.
2. Confirm the documented value (e.g., `config/credentials.json`) matches the actual file placed in step 3 of the runbook.

**Expected:** Path is consistent between the credentials section and the env var table.

---

### Operator forgets to replace YOUR_USERNAME

1. Search `docs/DEPLOY.md` for `YOUR_USERNAME`.
2. Confirm the document explicitly instructs the operator to replace `YOUR_USERNAME` with their actual PythonAnywhere username.

**Expected:** Substitution instruction is present and unambiguous.

---

### JWT_SECRET mismatch between apps

1. In `docs/DEPLOY.md`, locate the `JWT_SECRET` rows in both the Dashboard and API env var tables.
2. Confirm both rows include a note that the values must match.
3. Confirm a consequence of mismatch is explained (cashier tokens rejected by API, or vice versa).

**Expected:** Match-required note present in both tables; consequence noted.

---

## Failure Signals

- Any `MISSING:` in the grep completeness check output → document is incomplete or truncated
- `test -f docs/DEPLOY.md` exits non-zero → file was not created or was deleted
- Section heading for any of the 11 sections missing → document was partially written
- `YOUR_USERNAME` not appearing as a substitution marker → operator has already substituted a specific username (acceptable) OR the template was omitted (failure)
- Pre-deploy `pytest` run exits non-zero → S04 regressions introduced; fix before considering runbook complete

## Requirements Proved By This UAT

- R019 — Deployment Runbook: `docs/DEPLOY.md` exists; all 8 required topics are present (grep-verified); document covers PythonAnywhere setup, env vars, service account config, first-run migration, health check sequence, and known operational constraints including single-worker constraint, E.164 format, and offline queue behavior on fresh deploy

## Not Proven By This UAT

- Live PythonAnywhere deploy following the runbook end-to-end (would require a real PythonAnywhere account and service account credentials — operational verification, not artifact verification)
- That the corrected WSGI sys.path actually resolves all imports on PythonAnywhere (confirmed by reading the implementation; not live-tested in CI)
- That a fresh deploy with empty `offline_queue.db` behaves exactly as documented (the queue auto-creation is tested in S04 unit tests, not re-tested here)

## Notes for Tester

- The grep checks (Test Case 1) are the definitive machine-readable completeness gate. If all 8 pass, the document has the minimum required content.
- The manual review test cases (2–9) catch structural problems: missing tables, missing classification columns, missing failure-interpretation rows. These require opening the document and reading it.
- The pre-deploy test suite command (Test Case 8) is the only runtime check in this UAT. It should complete in under 10 seconds with no network I/O.
- The existing `backend/api/wsgi.py` and `backend/dashboard/wsgi.py` files still have the wrong `project_home` depth. The runbook documents the corrected path. Do not confuse the template in `docs/DEPLOY.md` with the uncorrected files.
