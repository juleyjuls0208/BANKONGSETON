---
status: diagnosed
phase: 02-code-quality
source: 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md, 02-05-SUMMARY.md, 02-06-SUMMARY.md
started: 2026-02-26T11:00:00Z
updated: 2026-02-26T11:15:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Structured log output when starting the server
expected: Run `python backend/dashboard/admin_dashboard.py` (Ctrl+C after it starts). Log lines appear with `level=INFO logger=bangko.admin_dashboard event=dashboard_starting ...` format — not raw text or bare print() output.
result: issue
reported: "ModuleNotFoundError: No module named 'flask' — server can't start, Flask not installed"
severity: blocker

### 2. No crash on import / startup error
expected: Running `python -c "import sys; sys.path.insert(0,'backend'); from errors import setup_logging, get_logger; setup_logging(); get_logger('test').info('event=test_ok')"` prints a log line with `event=test_ok` and exits with no error.
result: pass

### 3. Card UID normalization is consistent
expected: Running `python -c "import sys; sys.path.insert(0,'backend'); from utils import normalize_card_uid; print(normalize_card_uid('  0abc  '), normalize_card_uid(None), normalize_card_uid('ABC'))"` prints `ABC None ABC` — strips whitespace and leading zeros, uppercases, returns None for None input.
result: issue
reported: "Output is 'ABC  ABC' — None input returns empty string instead of None"
severity: major

### 4. All 19 unit tests pass
expected: Running `python -m pytest tests/test_utils.py -q` from the project root exits 0 with `19 passed` reported.
result: pass

### 5. No oauth2client import anywhere in active backend
expected: Running `grep -r "oauth2client" backend/` returns no matches (zero lines). The legacy dependency is fully replaced.
result: pass

### 6. Dead code archived (not deleted)
expected: The folder `_archive/` exists at the project root and contains `web_app_complete.py` and/or the `mobile/BankongSetonApp/` folder. The original `mobile/BankongSetonApp/` folder no longer exists at the root `mobile/` path (it's been moved).
result: pass

### 7. requirements.txt has google-auth (no oauth2client)
expected: Opening `backend/dashboard/requirements.txt` shows `google-auth==2.48.0` (or similar) and no `oauth2client` line.
result: pass

## Summary

total: 7
passed: 5
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "Running the backend server produces visible structured key=value log lines in the terminal"
  status: failed
  reason: "User reported: ModuleNotFoundError: No module named 'flask' — server can't start, Flask not installed"
  severity: blocker
  test: 1
  root_cause: "Flask and all runtime web-server packages are listed in backend/dashboard/requirements.txt but were never installed — only pytest/dotenv/google-auth were bootstrapped during Phase 2 development"
  artifacts:
    - path: "backend/dashboard/requirements.txt"
      issue: "Complete and correct but packages never installed (Flask>=3.0.0, gspread>=5.12.0, pyserial>=3.5, pyjwt, psutil, openpyxl, Flask-CORS, Flask-SocketIO, gunicorn)"
  missing:
    - "Run: pip install -r backend/dashboard/requirements.txt"
  debug_session: ".planning/debug/flask-missing-deps.md"

- truth: "normalize_card_uid(None) returns None"
  status: failed
  reason: "User reported: Output is 'ABC  ABC' — None input returns empty string instead of None"
  severity: major
  test: 3
  root_cause: "normalize_card_uid() was intentionally spec'd to return '' for None input (docstring line 7, line 34, test line 32) — both implementation and test are internally consistent but disagree with the QUAL-02 requirement that None should pass through as None"
  artifacts:
    - path: "backend/utils.py"
      issue: "Lines 50-51: if uid is None: return '' — should return None; return type -> str should be -> str | None"
    - path: "tests/test_utils.py"
      issue: "Line 32: asserts normalize_card_uid(None) == '' — needs updating to assert is None"
  missing:
    - "backend/utils.py line 51: change return '' to return None"
    - "backend/utils.py line 30: change -> str to -> str | None"
    - "backend/utils.py docstring line 7: update to 'Returns None for None input'"
    - "tests/test_utils.py line 32: change == '' to is None"
  debug_session: ""
