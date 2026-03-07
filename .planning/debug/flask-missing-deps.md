---
status: resolved
trigger: "ModuleNotFoundError: No module named 'flask' when running python backend/dashboard/admin_dashboard.py"
created: 2026-02-26T00:00:00Z
updated: 2026-02-26T00:00:00Z
---

## Current Focus

hypothesis: Flask and runtime web-server dependencies were never installed system-wide; only test/auth packages were bootstrapped
test: Compare pip list vs requirements.txt
expecting: Flask, Flask-CORS, Flask-SocketIO, gunicorn, pyjwt, psutil, openpyxl, pyserial, gspread all absent
next_action: RESOLVED - diagnosis complete

## Symptoms

expected: `python backend/dashboard/admin_dashboard.py` starts the Flask dashboard server
actual: Crashes immediately with `ModuleNotFoundError: No module named 'flask'`
errors: ModuleNotFoundError: No module named 'flask'
reproduction: Run `python backend/dashboard/admin_dashboard.py` in project root
started: Always — Flask was never installed in this environment

## Eliminated

- hypothesis: venv exists and is not activated
  evidence: STATE.md decision [02-01] explicitly states "pytest + python-dotenv installed system-wide (no venv present in this project)"
  timestamp: 2026-02-26

- hypothesis: requirements.txt is missing or malformed
  evidence: backend/dashboard/requirements.txt exists and is complete with all 45 dependencies
  timestamp: 2026-02-26

## Evidence

- timestamp: 2026-02-26
  checked: backend/dashboard/requirements.txt
  found: 45 dependencies listed; Flask>=3.0.0, Flask-CORS>=4.0.0, Flask-SocketIO>=5.3.0, gunicorn, pyjwt, psutil, openpyxl, pyserial, gspread required
  implication: All runtime dependencies are documented but not installed

- timestamp: 2026-02-26
  checked: pip list (system-wide, no venv)
  found: Only 28 packages installed — google-auth, pytest, pytest-cov, python-dotenv, pytz, cryptography, requests, urllib3, and transitive deps; NO Flask, NO pyserial, NO gspread, NO gunicorn, NO psutil, NO openpyxl, NO pyjwt
  implication: Environment was bootstrapped only for test-running (pytest/dotenv) and auth packages (google-auth stack); runtime app packages were never installed

- timestamp: 2026-02-26
  checked: STATE.md decisions section
  found: "[02-01]: pytest + python-dotenv installed system-wide (no venv present in this project)"
  implication: The project intentionally runs system-wide with no venv; only the minimum test packages were installed ad-hoc during Phase 2

- timestamp: 2026-02-26
  checked: backend/api/requirements_api.txt
  found: File does not exist; no backend/api directory
  implication: Single requirements file at backend/dashboard/requirements.txt covers all backend dependencies

- timestamp: 2026-02-26
  checked: setup.py, pyproject.toml
  found: Neither file exists in the project root
  implication: No automated install mechanism exists; manual pip install -r is required

## Resolution

root_cause: Flask and all runtime web-server packages (Flask, Flask-CORS, Flask-SocketIO, gunicorn, pyjwt, psutil, openpyxl, pyserial, gspread) are listed in backend/dashboard/requirements.txt but were never installed; only test/auth packages were bootstrapped system-wide during Phase 2 development
fix: N/A — developer setup step, not a code fix; run: pip install -r backend/dashboard/requirements.txt
verification: N/A — diagnosis-only mode
files_changed: []
