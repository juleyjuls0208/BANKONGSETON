# Bangko ng Seton — School RFID Money Management System

RFID-based canteen money system for Seton School. A student taps an ID/money
card (or an NFC phone) at a terminal; the Flask backend records the
transaction, updates the balance, and emails the parent.

> **Status:** actively deployed. The backend runs on an Oracle Cloud VM, the
> database is **Supabase Postgres**, and the physical RFID reader stays
> **on-prem** (Arduino + serial bridge).

## What's in this repo

| Path | What it is |
|------|------------|
| `backend/api/` | REST API + JWT auth (Flask, port `5001`) |
| `backend/dashboard/` | Admin / finance web dashboard (Flask-SocketIO, port `5003`) |
| `backend/cashier_app/` | Cashier POS app (port `5010`) |
| `backend/kiosk/`, `backend/tech/` | On-prem terminals driven by the Arduino reader |
| `backend/sheets_adapter.py` | **The data layer** — Supabase/Postgres via `psycopg2`. This is the live DB, not Google Sheets. |
| `arduino/` | RFID reader sketches (R4, NFC-R3, kiosk) |
| `mobile/android/`, `mobile/ios/` | Student apps |
| `deploy/oracle/` | Cloud deployment (nginx + gunicorn + systemd) |
| `docs/` | Detailed guides (deploy, email, NFC, API, troubleshooting) |

Data is stored in Supabase Postgres. Some modules still import `gspread`, but
the running system goes through `sheets_adapter` (reads `DATABASE_URL`). The
Google Sheets path is legacy — don't stand up a new deployment on it.

## Requirements
- **Python 3.11+** (local dev runs 3.11)
- A **Supabase** project (set `DATABASE_URL`)
- Arduino Uno/Nano/R4 + MFRC522 for on-prem card taps
- Node, for the mobile apps

## Install (local dev)

Dependencies are split per component — **there is no root `requirements.txt`**:

```bash
python -m venv .venv && .venv/Scripts/activate   # Windows; source venv/bin/activate on Linux/Mac
pip install -r backend/api/requirements_api.txt
pip install -r backend/dashboard/requirements.txt
pip install -r backend/cashier_app/requirements.txt
pip install -r requirements-test.txt
```

Copy `.env.example` → `.env` and set at minimum `DATABASE_URL` (your Supabase
Postgres connection string). The legacy `GOOGLE_SHEETS_ID` is ignored by the
live path.

## Run

```bash
python backend/api/api_server.py            # API,        port 5001
python backend/dashboard/admin_dashboard.py # Dashboard,  port 5003
python backend/cashier_app/app.py           # Cashier POS, port 5010
```

The on-prem RFID reader connects over `SERIAL_PORT`; the API and dashboard boot
fine without it. For cloud serving, `deploy/oracle/` runs the same apps behind
nginx (web on `:5000`, api on `:5001`).

## Tests

~450 test functions across `tests/` (47 files). Run the suite with:

```bash
pytest
```

DB-backed tests need `DATABASE_URL`; test-only deps are in `requirements-test.txt`.

## Deploy

See [`deploy/oracle/README.md`](deploy/oracle/README.md) — it provisions an
always-free ARM VM with nginx + two gunicorn workers + systemd units, using
Supabase as the source of truth. The Arduino reader is **not** deployed to the
cloud: run `arduino_bridge.py` + the R4 on a school machine that has the USB
reader and network access to the API.

## Docs

Start in `docs/`: `DEPLOY.md`, `EMAIL_SETUP.md`, `NFC_IMPLEMENTATION.md`,
`ARCHITECTURE.md`, `api-reference.md`, `TROUBLESHOOTING.md`.

## License

Educational use for Seton School.
