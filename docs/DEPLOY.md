# Bangko ng Seton — PythonAnywhere Deployment Runbook

> **Scope:** This runbook covers a fresh deploy of both the Dashboard app (`web_app.py`) and the API app (`api_server.py`) on PythonAnywhere, from zero to a passing `/api/health` call. Follow the steps in order.

---

## 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Python | 3.10 or higher |
| Git | Any recent version |
| PythonAnywhere account | Free tier supports **one** WSGI web app. Running Dashboard + API as separate always-on web apps requires a **paid tier** account (or a second free account for the second app). |
| Google Sheets spreadsheet | Must already exist with the sheets listed in [Section 5](#5-google-sheets-setup). |
| Google service account JSON | `config/credentials.json` — download from Google Cloud Console. |

---

## 2. Clone & Virtual Environment

```bash
# From your PythonAnywhere home directory
git clone https://github.com/YOUR_ORG/BANKONGSETON.git
cd BANKONGSETON

# Create virtualenv (PythonAnywhere built-in)
mkvirtualenv bangko-env --python=python3.10

# Install dependencies for both apps
pip install -r backend/dashboard/requirements.txt
pip install -r backend/api/requirements_api.txt
```

> **Note:** Both install steps are required even if you only deploy one app — shared modules in `backend/` are used by both.

---

## 3. Credentials Files

Two credential files live under `config/` in the project root. Upload them to `~/BANKONGSETON/config/` on PythonAnywhere.

| File | Purpose | Required? | Notes |
|------|---------|-----------|-------|
| `config/credentials.json` | Google Sheets service account JSON key | **YES** | Both apps fail without it. Lookup order: `config/credentials.json` → fallback `credentials.json` in cwd. |
| `config/firebase-credentials.json` | Firebase Admin SDK JSON key (for FCM push notifications) | No | FCM is **silently disabled** if this file is absent — no error is raised, push notifications simply do not fire. This is a file path lookup, NOT the `GOOGLE_APPLICATION_CREDENTIALS` env var. |

```bash
# Example upload from local machine (run on your local machine, not PythonAnywhere)
scp config/credentials.json YOUR_USERNAME@ssh.pythonanywhere.com:~/BANKONGSETON/config/
scp config/firebase-credentials.json YOUR_USERNAME@ssh.pythonanywhere.com:~/BANKONGSETON/config/
```

---

## 4. Environment Variables

Set these via the PythonAnywhere **Web** tab → **Environment variables**, or in a `.env` file at `~/BANKONGSETON/.env` loaded by `load_dotenv()` in the WSGI file. **Never hardcode secrets in the WSGI file itself.**

### 4a. Dashboard App (`web_app.py` / `admin_dashboard.py`)

| Variable | Required | Startup Hard-Fail? | Default | Description |
|----------|----------|--------------------|---------|-------------|
| `FLASK_SECRET_KEY` | **YES** | **YES — sys.exit(1)** | (none) | Flask session signing key. Must NOT equal `"bangko-admin-secret-key-change-in-production"`. Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_SECRET` | **YES** | **YES — sys.exit(1)** | (none) | JWT token signing key. Must NOT equal `"bangko-jwt-secret-2026"`. **Must match the JWT_SECRET set in the API app.** |
| `FINANCE_PASSWORD` | **YES** | **YES — sys.exit(1)** | (none) | Finance user password. Must NOT equal `"finance2025"`. |
| `GOOGLE_SHEETS_ID` | **YES** | no (raises on first Sheets call) | (none) | Google Sheets spreadsheet ID from the URL. Must be identical to the API app value. |
| `ADMIN_USERNAME` | **YES** | no | `""` (empty) | Admin login username. Without this, admin login always fails. |
| `ADMIN_PASSWORD` | **YES** | no | `""` (empty) | Admin login password. Without this, admin login always fails. |
| `FINANCE_USERNAME` | no | no | `"financedashboard"` | Finance login username. |
| `WEB_CONCURRENCY` | no | **YES if > 1** | `1` | Must be 1 or unset. Set by gunicorn; do not override above 1. |
| `GUNICORN_WORKERS` | no | **YES if > 1** | `1` | Same constraint as WEB_CONCURRENCY. |
| `FLASK_ENV` | no | no | `"production"` | Set to `"development"` only for local testing — expands CORS to localhost. |
| `FLASK_DEBUG` | no | no | `"false"` | Never enable in production. |
| `CORS_ORIGINS` | no | no | `""` → localhost only | Comma-separated allowed origins for the Android app. |
| `LOW_BALANCE_THRESHOLD` | no | no | `50.0` | PHP float. SMS/FCM alert sent when student balance drops below this. |
| `BATCH_EMAIL_HOUR` | no | no | `7` | Hour (0–23 PH time) for daily low-balance email batch. |
| `BATCH_EMAIL_MINUTE` | no | no | `0` | Minute (0–59) for daily low-balance email batch. |
| `ARDUINO_API_KEY` | no | no | `""` | Only needed if the Arduino card-reader bridge is connected. Empty = endpoint disabled. |
| `TWILIO_ACCOUNT_SID` | no | no | `""` | SMS disabled when empty. All three Twilio vars must be set together. |
| `TWILIO_AUTH_TOKEN` | no | no | `""` | Twilio auth token. |
| `TWILIO_FROM` | no | no | `""` | Twilio sender number in **E.164 format** (e.g. `+12015551234`). |
| `SMTP_SERVER` | no | no | `"smtp.gmail.com"` | Email notification SMTP host. All SMTP_* vars must be set together. |
| `SMTP_PORT` | no | no | `587` | SMTP port. |
| `SMTP_USER` | no | no | `""` | SMTP login username. |
| `SMTP_PASSWORD` | no | no | `""` | SMTP login password. |
| `FROM_EMAIL` | no | no | `= SMTP_USER` | Sender address for email notifications. |
| `LARGE_TRANSACTION_THRESHOLD` | no | no | `100.0` | PHP float. Threshold for large-transaction SMS alert. |

### 4b. API App (`api_server.py`)

| Variable | Required | Note |
|----------|----------|------|
| `GOOGLE_SHEETS_ID` | **YES** | Must be **the same spreadsheet ID** as the Dashboard app. |
| `JWT_SECRET` | **YES** | **Must match the Dashboard app JWT_SECRET exactly.** If unset, `api_server.py` falls back to `secrets.token_urlsafe(32)` — a new random secret generated on every restart, invalidating all existing tokens. Always set explicitly. |
| `FLASK_ENV` | no | Default `"production"`. |
| `CORS_ORIGINS` | no | Must include Android app origin in production. Defaults to `https://YOUR_USERNAME.pythonanywhere.com`. |
| `LOW_BALANCE_THRESHOLD` | no | Default `50.0`. |
| `API_PORT` | no | Default `5001`. Irrelevant under PythonAnywhere WSGI — port is managed by PA. |
| `API_DEBUG` | no | Default `False`. |
| `TWILIO_ACCOUNT_SID` | no | SMS disabled when absent. |
| `TWILIO_AUTH_TOKEN` | no | |
| `TWILIO_FROM` | no | E.164 format required. |

---

## 5. Google Sheets Setup

### Must exist before first app start

Create these sheets manually in your spreadsheet before starting the apps.

| Sheet Name | Required Columns | Notes |
|-----------|-----------------|-------|
| `Users` | StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered, FCMToken, **ParentPhone** | **ParentPhone is required for SMS** — add this column even if empty. All three apps use it. Not in earlier schema docs — add it manually. |
| `Money Accounts` | MoneyCardNumber, StudentIDCard, Balance, Status, LastUpdated | **Balance must be column C (position 3).** Hardcoded in `cashier_routes.py` and `api_server.py`. Never reorder. |
| `Transactions Log` | Timestamp, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ItemsJson | `migrate_transactions.py` adds ItemsJson column if it is missing. |
| `Lost Card Reports` | ReportID, ReportDate, StudentID, OldCardNumber, NewCardNumber, TransferredBalance, ReportedBy, Status | Must exist before any card-report operation. |

### Auto-created on first use (no manual action needed)

| Sheet Name | Created by | Trigger |
|-----------|-----------|---------|
| `Settings` | `dashboard_core.py:ensure_settings_sheet()` | First settings page visit |
| `Products` | `dashboard_core.py:ensure_products_sheet()` | First product management visit |
| `Categories` | `dashboard_core.py:_ensure_categories_sheet()` | First category action |
| `VirtualCards` | `nfc_payments.py:ensure_virtual_cards_sheet()` | First NFC registration |
| `Cashier Accounts` | `admin_dashboard.py:_ensure_cashier_accounts_sheet()` | First cashier login attempt |
| `Fraud Alerts` | `fraud_detection.py:_ensure_fraud_detection_sheets()` | First fraud page load |
| `Suspended Cards` | `fraud_detection.py:_ensure_fraud_detection_sheets()` | Same as Fraud Alerts |

---

## 6. PythonAnywhere WSGI Configuration

Each app is a separate PythonAnywhere web app. Go to **Web** tab → **Add a new web app** → **Manual configuration** → **Python 3.10**. Replace the generated WSGI file content with the template below. Replace `YOUR_USERNAME` with your actual PythonAnywhere username.

### Dashboard App WSGI

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

> **Why this matters:** The existing `backend/dashboard/wsgi.py` sets `project_home` to `backend/dashboard/` — too deep. That path misses `backend/` level modules (`cache.py`, `offline_queue.py`, `fraud_detection.py`). Use the corrected template above.

### API App WSGI

```python
import sys
import os

project_home = '/home/YOUR_USERNAME/BANKONGSETON'
for _p in [project_home,
           os.path.join(project_home, 'backend'),
           os.path.join(project_home, 'backend', 'api')]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('CORS_ORIGINS', 'https://YOUR_USERNAME.pythonanywhere.com')
from api_server import app as application
```

> **Important:** Set `FLASK_SECRET_KEY`, `JWT_SECRET`, `FINANCE_PASSWORD`, and other secrets via the PythonAnywhere **Web → Environment variables** panel or via `.env` file. Never hardcode secrets directly in the WSGI file.

---

## 7. Startup Guard Quick Reference

The following conditions abort app startup with `sys.exit(1)`. All PythonAnywhere-style aborts appear in the **Error log** (Web tab → Log files → Error log).

| App | Condition | Structured log event |
|-----|-----------|----------------------|
| `web_app.py` | `FLASK_SECRET_KEY` missing or equals the known-insecure default | `CRITICAL event=startup_aborted reason=insecure_secret_key` |
| `web_app.py` | `JWT_SECRET` missing or equals the known-insecure default | `CRITICAL event=startup_aborted reason=insecure_jwt_secret` |
| `web_app.py` | `FINANCE_PASSWORD` missing or equals `"finance2025"` | `CRITICAL event=startup_aborted reason=insecure_finance_password` |
| `web_app.py` | `WEB_CONCURRENCY > 1` or `GUNICORN_WORKERS > 1` | `CRITICAL event=startup_aborted reason=multi_worker_forbidden` |
| `admin_dashboard.py` | `WEB_CONCURRENCY > 1` or `GUNICORN_WORKERS > 1` | Fatal print (no structured logger) |

If the app returns HTTP 500 immediately on all routes, start here.

---

## 8. First-Run Migration

Run once after initial deploy, before first real use:

```bash
cd ~/BANKONGSETON
workon bangko-env
python backend/migrate_transactions.py
```

### What it does

| Function | Effect |
|----------|--------|
| `migrate_transactions()` | Adds `ItemsJson` column to Transactions Log header row (idempotent). |
| `migrate_users_schema()` | Adds `ParentEmail`, `FCMToken`, `Role` columns to Users sheet header row (idempotent). |
| `create_products_sheet()` | Creates Products sheet with headers; seeds from `backend/data/products.json` if the file exists (idempotent). |

All three functions are idempotent — safe to run multiple times.

### Post-migration verification checklist

After migration, open the Google Sheet and confirm:

- [ ] **Users** sheet has columns including `ParentPhone` (add this manually if not present — see [Section 5](#5-google-sheets-setup))
- [ ] **Money Accounts** sheet has `Balance` in **column C** (third column)
- [ ] **Transactions Log** sheet has `ItemsJson` as the last column

---

## 9. Health Check Sequence

After both apps are running, verify with:

```bash
# Dashboard app
curl https://YOUR_USERNAME.pythonanywhere.com/api/health

# API app (if deployed as a separate web app)
curl https://YOUR_API_USERNAME.pythonanywhere.com/api/health
```

**Expected response (HTTP 200):**

```json
{
  "status": "ok",
  "sheets_ok": true,
  "latency_ms": 123,
  "queue_pending": 0,
  "timestamp": "2026-03-15T06:00:00+08:00"
}
```

### Failure interpretation

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| `"sheets_ok": false, "latency_ms": 0` | Sheets client never initialized | Check `GOOGLE_SHEETS_ID` env var and `config/credentials.json` placement |
| `"sheets_ok": false, "latency_ms": N` (N > 0) | Client initialized but connectivity probe failed | Check network or Google Sheets API quota |
| HTTP 503 | Sheets unreachable at health check time | Check service account permissions and above |
| `"queue_pending": N` (N > 0) | Offline queue has unflushed transactions; Sheets write health degraded | Check Sheets connectivity; queue will auto-flush when Sheets recovers |

---

## 10. Known Operational Constraints

1. **Single-worker only** — `WEB_CONCURRENCY` must be `1` (or unset). Startup aborts with `CRITICAL event=startup_aborted reason=multi_worker_forbidden` if set above 1. `FraudDetector` is a module-level singleton that splits incorrectly across multiple workers.

2. **E.164 phone format for SMS** — The `ParentPhone` column in the Users sheet must contain numbers in `+639XXXXXXXXX` format (or any valid E.164 format). Malformed numbers cause Twilio to silently reject the SMS without raising an exception. The column is read defensively (falls back to `PhoneNumber` column), but both must be E.164 if populated.

3. **Offline queue auto-creation** — `backend/offline_queue.db` is created automatically on first import of `offline_queue.py`. On a fresh server it does not exist yet; `SQLiteWriteQueue._init_db()` creates it with `CREATE TABLE IF NOT EXISTS`. No manual setup needed. If the `backend/` directory is read-only, the queue will fail — ensure PythonAnywhere has write access to `backend/`.

4. **Balance column C position** — The `Money Accounts` sheet Balance column is hardcoded as **column C (position 3)** in both `cashier_routes.py` and `api_server.py`. Never reorder this column or insert columns before it.

5. **JWT_SECRET must be stable and shared** — `api_server.py` falls back to `secrets.token_urlsafe(32)` if `JWT_SECRET` is not set (no startup guard in the API app). This generates a new secret on every restart, invalidating all existing cashier tokens. Always set `JWT_SECRET` explicitly to the same value in both apps.

6. **Same Google Sheet ID for both apps** — Both apps read and write the same spreadsheet. `GOOGLE_SHEETS_ID` must be identical in both environment configurations.

7. **`config/credentials.json` placement** — Both `dashboard_core.py` and `api_server.py` resolve credentials relative to their own file location (`../../config/credentials.json`). The effective project-root path is `config/credentials.json`. On PythonAnywhere, upload to `~/BANKONGSETON/config/credentials.json`.

8. **No CI pipeline** — There is no automated CI. Run the pre-deploy test suite (see [Section 11](#11-pre-deploy-test-suite)) locally before every deploy to verify the critical-path test suite passes.

---

## 11. Pre-Deploy Test Suite

Run before every deploy from your local machine or a PythonAnywhere console:

```bash
cd ~/BANKONGSETON
workon bangko-env
python -m pytest tests/test_cashier_routes.py tests/test_admin_critical.py -v --tb=short
```

**Expected output:** `35 passed` in approximately 2–4 seconds with zero live HTTP requests. Tests are fully hermetic — no credentials, no network, no Google Sheets quota consumed.

### Structural regression checks

```bash
bash scripts/verify-s03.sh   # 18/18 checks: health endpoint and worker guard
bash scripts/verify-s02.sh   # 32/32 checks: cache wiring and schema invariants
```

Both scripts should print all `OK` lines with a final pass count. Any `FAIL` line must be resolved before deploying.

---

## Appendix: PythonAnywhere Free Tier Note

Free tier PythonAnywhere allows only **one always-on WSGI web app**. Options for running both Dashboard and API:

| Option | Cost | Notes |
|--------|------|-------|
| Deploy only Dashboard (recommended for testing) | Free | API routes are served through the dashboard WSGI. |
| Paid PythonAnywhere account | Paid | Allows multiple always-on web apps. |
| Second free account for API app | Free | API runs under a different `YOUR_API_USERNAME.pythonanywhere.com` subdomain. `CORS_ORIGINS` on Dashboard must include the API domain. |
