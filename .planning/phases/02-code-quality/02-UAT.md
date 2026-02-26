---
status: complete
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
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "normalize_card_uid(None) returns None"
  status: failed
  reason: "User reported: Output is 'ABC  ABC' — None input returns empty string instead of None"
  severity: major
  test: 3
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""
