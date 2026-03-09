---
phase: 25-critical-backend-stability
plan: 25-01
subsystem: backend/api
tags: [concurrency, race-condition, email, reliability, threading]
dependency_graph:
  requires: []
  provides: [REQ-BUG-01, REQ-BUG-04]
  affects: [backend/api/api_server.py]
tech_stack:
  added: [threading (stdlib)]
  patterns: [per-resource mutex, fire-and-forget email with silent catch]
key_files:
  created: []
  modified: [backend/api/api_server.py]
decisions:
  - Per-card Lock keyed on normalized card UID, stored in module-level dict guarded by a meta-lock
  - Email block wrapped in try/except with logger.warning — no re-raise, success return remains outside
metrics:
  duration: ~12 minutes
  completed: 2026-03-09
  tasks_completed: 2
  tasks_total: 2
  files_changed: 1
---

# Phase 25 Plan 01: Race Condition & Email Crash Fixes Summary

**One-liner:** Per-card `threading.Lock()` guards both payment endpoints' read-check-write sequences; email block wrapped in silent `try/except` so a receipt failure can't return 500 after a completed debit.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add per-card threading locks to nfc_pay + process_cashier_transaction | d94fa41 | backend/api/api_server.py |
| 2 | Wrap email receipt block in silent try/except | 484cfee | backend/api/api_server.py |

## What Was Built

### Task 1 — Double-spend race condition fix (REQ-BUG-01)

Added module-level infrastructure:
```python
_card_locks: dict = {}
_card_locks_lock = threading.Lock()
```

In both `nfc_pay()` and `process_cashier_transaction()`, the full read-check-write sequence is now:
```python
with _card_locks_lock:
    card_lock = _card_locks.setdefault(normalized_card, threading.Lock())
with card_lock:
    # read balance from sheet
    # check sufficient funds
    # deduct and write back
```

This ensures two simultaneous requests for the same card are serialized, eliminating the silent balance loss that occurred when both threads read the same balance before either wrote back.

### Task 2 — Email crash after commit fix (REQ-BUG-04)

Wrapped the `if student_id:` email block in its own `try/except Exception as email_err:` with a `logger.warning("event=email_receipt_failed error=%s", email_err)` and **no re-raise**. The `return jsonify({"success": True, ...})` remains outside the try/except, unchanged. A receipt failure now produces a warning log entry instead of a 500 to the client whose money has already been deducted.

## Deviations from Plan

None — plan executed exactly as written. All exact line ranges and insertion points matched the plan specification.

## Self-Check

### Files exist:
- ✅ `backend/api/api_server.py` (modified)

### Commits exist:
- ✅ `d94fa41` — feat(25-01): add per-card threading locks
- ✅ `484cfee` — fix(25-01): wrap email receipt block in silent try/except

### Syntax check: PASS
```
python -m py_compile backend/api/api_server.py → SYNTAX OK
```

## Self-Check: PASSED
