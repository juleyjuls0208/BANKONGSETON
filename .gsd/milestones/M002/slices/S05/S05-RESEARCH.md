# S05: Deployment Runbook — Research

**Date:** 2026-03-15

## Summary

S05 produces `docs/DEPLOY.md` — the authoritative PythonAnywhere deployment runbook for Bangko ng Seton. This is a documentation-only slice: no code changes, no new logic. All of the implementation details it must document (env var guards, health check shapes, single-worker constraint, offline queue behavior) were built and validated in S01–S04.

The research task is to audit the actual code for every detail `docs/DEPLOY.md` must document — env var names, credentials file paths, startup guard behavior, health endpoint response schema, sheet column requirements, migration steps — and capture anything the existing docs or `.env.example` get wrong or omit.

Key findings: (1) `web_app.py` has three hard startup guards that abort with `sys.exit(1)` if env vars are missing or equal to known-insecure defaults; the runbook must call each one out explicitly. (2) `ParentPhone` is used by all three apps for SMS but is absent from the documented Users sheet column list — the runbook must add this as a required column constraint. (3) Firebase credentials are located by file path (`config/firebase-credentials.json`), not by `GOOGLE_APPLICATION_CREDENTIALS` env var — the runbook must explain the correct placement. (4) Both WSGI files hardcode the PythonAnywhere username in `project_home` — the runbook must make this substitution explicit.

## Recommendation

Write `docs/DEPLOY.md` from scratch as a task-oriented runbook, not a reference doc. Structure it as a numbered sequence of deployment steps. Existing docs (`DEPLOYMENT_PYTHONANYHERE.md`, `DEPLOYMENT_GUIDE.md`) provide useful background but contain stale paths, wrong port conventions for PythonAnywhere WSGI, and do not reflect M002 changes (startup guards, health endpoints). Do not repurpose them — write fresh from the code audit below.

## Don't Hand-Roll

| Problem | Existing Solution | Why Use It |
|---------|------------------|------------|
| Env var audit | Already done in this research | Complete list with required/optional classification is in the table below |
| Health endpoint shape | Implemented in S03; verified by `scripts/verify-s03.sh` | Document the actual JSON fields, not the spec |
| WSGI config structure | `backend/dashboard/wsgi.py` and `backend/api/wsgi.py` | Runbook adapts these with `YOUR_USERNAME` substitution |
| Migration steps | `backend/migrate_transactions.py` | Document the actual migration entrypoint and what it does |

## Existing Code and Patterns

- `backend/dashboard/web_app.py` (lines 53–94) — three startup guards abort with `sys.exit(1)`: missing/insecure `FLASK_SECRET_KEY`, missing/insecure `JWT_SECRET`, missing/insecure `FINANCE_PASSWORD`. A fourth guard (WEB_CONCURRENCY > 1) is also at module level. All four must be satisfied before the app reaches `Flask(...)`.
- `backend/dashboard/admin_dashboard.py` (lines 68–78) — same WEB_CONCURRENCY guard; no FLASK_SECRET_KEY guard (different file, different code path). Used when deploying `admin_dashboard.py` directly rather than via `web_app.py`.
- `backend/dashboard/wsgi.py` — hardcodes `project_home = '/home/bankoseton/BANKONGSETON/backend/dashboard/'` and imports `from web_app import app as application`. Must replace `bankoseton` with actual username.
- `backend/api/wsgi.py` — hardcodes `project_home = "/home/juley2823/FinanceDashboard"` and a list of `sys.path` entries for `backend/` and `backend/api/`. `CORS_ORIGINS` defaults to `https://juley2823.pythonanywhere.com` — must override for the real domain. Imports `from api_server import app as application`.
- `backend/dashboard/dashboard_core.py` (`get_sheets_client`, line 131) — credentials lookup order: `config/credentials.json` → fallback `credentials.json` in cwd.
- `backend/api/api_server.py` (`get_sheets_client`, line 82) — same lookup order: `../../config/credentials.json` relative to `backend/api/` → fallback `credentials.json`.
- `backend/api/fcm_sender.py` (`_init_firebase`, line 19) — Firebase credentials looked up at `config/firebase-credentials.json` (relative to project root, via `os.path.dirname(__file__)/../..`). This is a file path, NOT `GOOGLE_APPLICATION_CREDENTIALS` env var. If the file is absent, FCM is silently disabled (returns False, logs WARNING).
- `backend/offline_queue.py` (`_DEFAULT_DB_PATH`, line 22) — SQLite file at `backend/offline_queue.db` (same directory as `offline_queue.py`). Created automatically by `_init_db()` on first import. On fresh deploy: file does not exist yet, is created empty with `CREATE TABLE IF NOT EXISTS write_queue`. No manual action required.
- `backend/migrate_transactions.py` — three migration functions: `migrate_transactions()` (adds ItemsJson column to Transactions Log), `migrate_users_schema()` (adds ParentEmail, FCMToken, Role columns to Users), `create_products_sheet()` (creates Products sheet with headers and seeds products.json data). Run with `python backend/migrate_transactions.py`.
- `backend/dashboard/dashboard_core.py:225` — `ensure_settings_sheet()` auto-creates Settings sheet on first access. Similarly `ensure_products_sheet()` and `_ensure_categories_sheet()` are lazy.
- `backend/dashboard/admin_dashboard.py` — `_ensure_cashier_accounts_sheet()` auto-creates Cashier Accounts with seeded default cashier.
- `backend/fraud_detection.py` — `_ensure_fraud_detection_sheets()` auto-creates Fraud Alerts and Suspended Cards worksheets on first fraud-page load (lazy init, D009).

## Environment Variables — Complete Audit

### Dashboard App (web_app.py / admin_dashboard.py)

| Variable | Required | Startup Hard-Fail? | Default | Description |
|----------|----------|-------------------|---------|-------------|
| `FLASK_SECRET_KEY` | **YES** | **YES — sys.exit(1)** | (none) | Flask session signing key. Must NOT equal `"bangko-admin-secret-key-change-in-production"`. Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_SECRET` | **YES** | **YES — sys.exit(1)** | (none) | JWT token signing key. Must NOT equal `"bangko-jwt-secret-2026"`. Same generation command. Must match the JWT_SECRET set in the API app. |
| `FINANCE_PASSWORD` | **YES** | **YES — sys.exit(1)** | (none) | Finance user password. Must NOT equal `"finance2025"`. |
| `GOOGLE_SHEETS_ID` | **YES** | no (raises on first Sheets call) | (none) | Google Sheets spreadsheet ID from the URL |
| `ADMIN_USERNAME` | **YES** | no | `""` (empty) | Admin username. Without this, admin login always fails. |
| `ADMIN_PASSWORD` | **YES** | no | `""` (empty) | Admin password. Without this, admin login always fails. |
| `FINANCE_USERNAME` | no | no | `"financedashboard"` | Finance username |
| `WEB_CONCURRENCY` | no | **YES if > 1** | `1` | Must be 1 or unset. Set by gunicorn; do not override to > 1. |
| `GUNICORN_WORKERS` | no | **YES if > 1** | `1` | Same constraint as WEB_CONCURRENCY. |
| `FLASK_ENV` | no | no | `"production"` | `"development"` expands CORS to localhost |
| `FLASK_DEBUG` | no | no | `"false"` | Never enable in production |
| `CORS_ORIGINS` | no | no | `""` → localhost only | Comma-separated allowed origins for the Android app |
| `LOW_BALANCE_THRESHOLD` | no | no | `50.0` | Float, PHP. SMS/FCM sent when balance drops below this. |
| `BATCH_EMAIL_HOUR` | no | no | `7` | Hour (0–23 PH time) for daily low-balance email batch |
| `BATCH_EMAIL_MINUTE` | no | no | `0` | Minute (0–59) for daily low-balance email batch |
| `ARDUINO_API_KEY` | no | no | `""` (disables endpoint) | Only needed if Arduino bridge is connected |
| `TWILIO_ACCOUNT_SID` | no | no | `""` | SMS disabled when empty |
| `TWILIO_AUTH_TOKEN` | no | no | `""` | All three Twilio vars must be set together |
| `TWILIO_FROM` | no | no | `""` | Twilio sender number in E.164 format (e.g. `+12015551234`) |
| `SMTP_SERVER` | no | no | `"smtp.gmail.com"` | Email notifications (requires all SMTP_* vars) |
| `SMTP_PORT` | no | no | `587` | |
| `SMTP_USER` | no | no | `""` | |
| `SMTP_PASSWORD` | no | no | `""` | |
| `FROM_EMAIL` | no | no | (= SMTP_USER) | Sender address for email notifications |
| `LARGE_TRANSACTION_THRESHOLD` | no | no | `100.0` | Float, PHP. Threshold for large-transaction SMS alert |

### API App (api_server.py)

| Variable | Required | Note |
|----------|----------|------|
| `GOOGLE_SHEETS_ID` | **YES** | Same sheet as dashboard |
| `JWT_SECRET` | **YES** | Must match dashboard app — tokens are shared |
| `FLASK_ENV` | no | Default `"production"` |
| `CORS_ORIGINS` | no | Must include Android app origin in production |
| `LOW_BALANCE_THRESHOLD` | no | Default `50.0` |
| `API_PORT` | no | Default `5001` (irrelevant under PythonAnywhere WSGI) |
| `API_DEBUG` | no | Default `False` |
| `TWILIO_ACCOUNT_SID` | no | SMS disabled when absent |
| `TWILIO_AUTH_TOKEN` | no | |
| `TWILIO_FROM` | no | |

## Credentials Files

| File | Purpose | Required? | Placement |
|------|---------|-----------|-----------|
| `config/credentials.json` | Google Sheets service account JSON key | **YES** | Project root `config/` directory |
| `config/firebase-credentials.json` | Firebase Admin SDK JSON key | No (FCM silently disabled if absent) | Project root `config/` directory |

Both apps look for credentials at `config/credentials.json` first, then fall back to `credentials.json` in cwd. Always place in `config/` to be safe.

## Google Sheets — Required vs Auto-Created

### Must exist before first app start

| Sheet Name | Columns required | Notes |
|-----------|-----------------|-------|
| `Users` | StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered, FCMToken | **ParentPhone must also be added** — used by all three apps for SMS (not in original schema doc). Can be empty but column must exist. |
| `Money Accounts` | MoneyCardNumber, StudentIDCard, Balance, Status, LastUpdated | Balance **must be column C**. Hardcoded as position 3 in cashier_routes.py and api_server.py |
| `Transactions Log` | Timestamp, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ItemsJson | `migrate_transactions.py` adds ItemsJson column if missing |
| `Lost Card Reports` | ReportID, ReportDate, StudentID, OldCardNumber, NewCardNumber, TransferredBalance, ReportedBy, Status | Must exist before any card report |
| `Settings` | Key, Value | Auto-created on first access. Manually adding `low_balance_threshold = 50` overrides the env var default. |

### Auto-created on first use (no manual action needed)

| Sheet Name | Created by | When |
|-----------|-----------|------|
| `Products` | `dashboard_core.py:ensure_products_sheet()` | First product management visit |
| `Categories` | `dashboard_core.py:_ensure_categories_sheet()` | First category action |
| `VirtualCards` | `nfc_payments.py:ensure_virtual_cards_sheet()` | First NFC registration |
| `Cashier Accounts` | `admin_dashboard.py:_ensure_cashier_accounts_sheet()` | First cashier login attempt with Sheets-auth |
| `Fraud Alerts` | `fraud_detection.py:_ensure_fraud_detection_sheets()` | First fraud page load |
| `Suspended Cards` | `fraud_detection.py:_ensure_fraud_detection_sheets()` | Same as Fraud Alerts |
| `Settings` | `dashboard_core.py:ensure_settings_sheet()` | First settings access |

## PythonAnywhere WSGI Configuration

Both apps are separate web apps on PythonAnywhere. Free tier supports one "always-on" web app; a second web app is possible on paid tier or using a "scheduled task" hack. The canonical setup:

**Dashboard app WSGI** (adapt from `backend/dashboard/wsgi.py`):
```python
import sys
import os
from dotenv import load_dotenv

project_home = '/home/YOUR_USERNAME/BANKONGSETON'
if project_home not in sys.path:
    sys.path.insert(0, project_home)
for _p in [
    os.path.join(project_home, 'backend'),
    os.path.join(project_home, 'backend', 'dashboard'),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(os.path.join(project_home, '.env'))
from web_app import app as application
```

Current `wsgi.py` has `project_home = '/home/bankoseton/BANKONGSETON/backend/dashboard/'` — this is wrong for sys.path (too deep; misses `backend/` level). The corrected version above is what the runbook should prescribe.

**API app WSGI** (adapt from `backend/api/wsgi.py`):
```python
import sys
import os

project_home = '/home/YOUR_USERNAME/BANKONGSETON'
for _p in [project_home, os.path.join(project_home, 'backend'), os.path.join(project_home, 'backend', 'api')]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('CORS_ORIGINS', 'https://YOUR_USERNAME.pythonanywhere.com')
from api_server import app as application
```

**Important:** Set secrets via the PythonAnywhere "Web" tab → "Environment variables" (or via `.env` file loaded by `load_dotenv()`). Never hardcode `FLASK_SECRET_KEY`, `JWT_SECRET`, or passwords in the WSGI file.

## Health Check Endpoints

Both apps expose `GET /api/health`. After deployment, verify:

```
# Dashboard app
curl https://YOUR_USERNAME.pythonanywhere.com/api/health
→ 200 {"status": "ok", "sheets_ok": true, "latency_ms": 123, "queue_pending": 0, "timestamp": "2026-03-15T...+08:00"}

# API app (if separate web app)
curl https://YOUR_API_USERNAME.pythonanywhere.com/api/health
→ 200 {"status": "ok", "sheets_ok": true, "latency_ms": 145, "queue_pending": 0, "timestamp": "2026-03-15T...+08:00"}
```

Failure interpretation:
- `sheets_ok: false, latency_ms: 0` → Sheets client never initialized; check `GOOGLE_SHEETS_ID` env var and `config/credentials.json`
- `sheets_ok: false, latency_ms: N` → Client initialized but connectivity probe failed; check network or Sheets API quota
- HTTP 503 → Sheets unreachable; check above + service account permission
- `queue_pending: N > 0` → Offline queue has unflushed transactions; Sheets write health degraded

## Known Operational Constraints to Document

1. **Single-worker only** — `WEB_CONCURRENCY=1` (or unset). Startup aborts with CRITICAL log if > 1. FraudDetector is a module-level singleton that splits across workers.

2. **E.164 phone format for SMS** — `ParentPhone` column in the Users sheet must contain numbers in `+639XXXXXXXXX` format. Malformed numbers cause Twilio to silently reject the SMS without raising an exception. The column is read defensively (falls back to `PhoneNumber` column), but both must be E.164 if populated.

3. **Offline queue on fresh deploy** — `backend/offline_queue.db` is created automatically on first import. On a fresh server it does not exist yet; the `SQLiteWriteQueue._init_db()` call creates it with `CREATE TABLE IF NOT EXISTS`. No manual setup needed. If the backend directory is read-only, the queue will fail to create the file — ensure PythonAnywhere has write access to `backend/`.

4. **Balance column position** — `Money Accounts` sheet Balance is hardcoded as **column C (position 3)** in both `cashier_routes.py` and `api_server.py`. Never reorder this column.

5. **JWT_SECRET must be stable** — `api_server.py` falls back to `secrets.token_urlsafe(32)` if `JWT_SECRET` is not set (no startup guard). This generates a new secret on every restart, invalidating all existing tokens. Always set JWT_SECRET explicitly and use the same value across both apps.

6. **Same Google Sheet ID for both apps** — Both apps read/write the same spreadsheet. `GOOGLE_SHEETS_ID` must be identical in both `.env` files.

7. **`config/credentials.json` placement** — Both `dashboard_core.py` and `api_server.py` look for `../../config/credentials.json` relative to their own file. The effective path from the project root is `config/credentials.json`. On PythonAnywhere, upload this file to `~/BANKONGSETON/config/credentials.json`.

8. **No CI pipeline** — There is no automated CI. Run `pytest tests/test_cashier_routes.py tests/test_admin_critical.py` locally before every deploy to verify the critical-path test suite passes.

## Migration Steps

Run once after initial deploy, before first real use:

```bash
cd ~/BANKONGSETON
source ~/.virtualenvs/bangko-env/bin/activate   # or however venv is activated on PA
python backend/migrate_transactions.py
```

What it does:
1. `migrate_transactions()` — adds `ItemsJson` column to Transactions Log header row
2. `migrate_users_schema()` — adds `ParentEmail`, `FCMToken`, `Role` columns to Users sheet header row
3. `create_products_sheet()` — creates Products sheet with headers; seeds from `backend/data/products.json` if file exists

All three functions are idempotent — safe to run multiple times (checks for existing column before adding).

**After migration, manually verify:**
- Users sheet has columns: StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered, FCMToken, **ParentPhone** (add this manually if needed for SMS)
- Money Accounts sheet has Balance in column C
- Transactions Log sheet has ItemsJson as the last column

## Startup Guard Quick Reference

The following will abort app startup with `sys.exit(1)`:

| App | Condition | Error logged |
|-----|-----------|-------------|
| web_app.py | `FLASK_SECRET_KEY` missing or equals `"bangko-admin-secret-key-change-in-production"` | CRITICAL event=startup_aborted reason=insecure_secret_key |
| web_app.py | `JWT_SECRET` missing or equals `"bangko-jwt-secret-2026"` | CRITICAL event=startup_aborted reason=insecure_jwt_secret |
| web_app.py | `FINANCE_PASSWORD` missing or equals `"finance2025"` | CRITICAL event=startup_aborted reason=insecure_finance_password |
| web_app.py | `WEB_CONCURRENCY > 1` or `GUNICORN_WORKERS > 1` | CRITICAL event=startup_aborted reason=multi_worker_forbidden |
| admin_dashboard.py | `WEB_CONCURRENCY > 1` or `GUNICORN_WORKERS > 1` | FATAL print (no logger) |

All PythonAnywhere-style errors appear in the app error log (Web tab → Log files → Error log).

## Test Suite — Pre-Deploy Verification

```bash
cd ~/BANKONGSETON
python -m pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short
```

Expected: 35 passed, ~2–4s, zero HTTP requests. Tests are fully hermetic — no credentials or network needed.

Verify structural invariants:
```bash
bash scripts/verify-s03.sh    # 18/18 checks for health and worker guard
bash scripts/verify-s02.sh    # 32/32 checks for cache wiring
```

## Skills Discovered

| Technology | Skill | Status |
|------------|-------|--------|
| PythonAnywhere WSGI | (none found) | n/a — documentation only slice |
| Flask deployment | (none found) | n/a |

## Open Risks

- **WSGI path correction** — The current `backend/dashboard/wsgi.py` sets `project_home` too deep (`backend/dashboard/`). The runbook should prescribe the corrected multi-path sys.path setup. If someone copies `wsgi.py` verbatim, `backend/` modules (cache.py, offline_queue.py, fraud_detection.py) will not import. The runbook must give the corrected WSGI template, not point to the existing file.
- **ParentPhone column gap** — The `Users` sheet documented schema (in `docs/google-sheets-schema.md`) does not include `ParentPhone`. If an operator follows only that schema doc and never reads the runbook, SMS will silently drop for all students. The runbook must add this column explicitly.
- **Dual-app PythonAnywhere setup** — Free tier has only one WSGI web app slot. The dashboard and API are separate apps. Operators on free tier must choose one, or use a paid account. The runbook should call this out rather than assuming both are always deployed together.
- **firebase-credentials.json optional** — FCM push is silently disabled if `config/firebase-credentials.json` is absent. Operators who want push notifications will need to set this up separately. The runbook should note this as an optional step with the correct file path.

## Sources

- `backend/dashboard/web_app.py` lines 53–94: startup guards, WEB_CONCURRENCY check
- `backend/dashboard/admin_dashboard.py` lines 68–78: WEB_CONCURRENCY guard
- `backend/api/api_server.py` lines 199–227: health check implementation
- `backend/dashboard/admin_dashboard.py` lines 452–482: health check implementation
- `backend/dashboard/dashboard_core.py` lines 113–128: CORS origins parsing
- `backend/dashboard/wsgi.py`, `backend/api/wsgi.py`: existing WSGI configs (both need path corrections)
- `backend/migrate_transactions.py`: migration entrypoint and function list
- `backend/offline_queue.py` line 22: `_DEFAULT_DB_PATH` and `_init_db()` auto-creation
- `backend/api/fcm_sender.py` lines 26–35: firebase-credentials.json lookup path
- `docs/google-sheets-schema.md`: sheet structure (missing ParentPhone — noted as gap)
- `.env.example`: existing env var template (outdated; missing JWT_SECRET, Twilio, startup guard context)
- `scripts/verify-s03.sh`: 18-check structural regression suite (runbook should reference this)
- S03 Summary: health endpoint response shape and observability surfaces
- S04 Summary: test suite run command and expected output
