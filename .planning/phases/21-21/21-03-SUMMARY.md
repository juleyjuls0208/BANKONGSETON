---
phase: "21"
plan: "03"
subsystem: "nfc-payments, arduino-bridge"
tags: ["low-balance-email", "station-tracking", "arduino-auto-connect", "nfc-pay"]
dependency_graph:
  requires: []
  provides: ["low-balance-email-on-nfc-pay", "station-id-in-transactions", "arduino-serial-auto-connect"]
  affects: ["backend/api/api_server.py", "backend/dashboard/arduino_bridge.py"]
tech_stack:
  added: []
  patterns: ["env-var-module-level-constant", "lazy-import-in-handler", "auto-connect-on-init"]
key_files:
  created: []
  modified:
    - "backend/api/api_server.py"
    - "backend/dashboard/arduino_bridge.py"
decisions:
  - "Used EmailNotifier.send_low_balance_alert(student_name, student_id, balance, to_email) signature from notifications.py — plan assumed different param names"
  - "Auto-connect implemented by creating serial.Serial in __init__ when arduino_serial is None — no separate connect() method exists in ArduinoBridge"
  - "Left existing inline LOW_BALANCE_THRESHOLD reads in other handlers (lines 1139, 1404) untouched — they have Settings sheet override logic and are out of scope"
metrics:
  duration: "~15 min"
  completed: "2026-03-08"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 21 Plan 03: Low-Balance Email Alert + Station Tracking + Arduino Auto-Connect Summary

**One-liner:** Low-balance email alerts via EmailNotifier wired into nfc_pay handler; X-Station-ID header tracking in transactions; STATION_SERIAL_PORT auto-connect in ArduinoBridge.__init__.

## Tasks Completed

| # | Task | Commit | Files Modified |
|---|------|--------|----------------|
| 1 | Wire low-balance email alert and station tracking in nfc_pay | 8cad199 | backend/api/api_server.py |
| 2 | Add station identity and serial auto-connect to ArduinoBridge | a79cecb | backend/dashboard/arduino_bridge.py |

## What Was Built

### Task 1 — `backend/api/api_server.py`

1. **Module-level `LOW_BALANCE_THRESHOLD`** (line 51): `LOW_BALANCE_THRESHOLD = float(os.getenv("LOW_BALANCE_THRESHOLD", "50"))` added after `JWT_EXPIRY_HOURS`, replacing ad-hoc env reads inside the `nfc_pay` handler.

2. **Station ID capture** (line 1013): `station_id = request.headers.get("X-Station-ID", "main")` — reads which canteen station sent the payment.

3. **Station ID in transaction row** (line 1099): `station_id` appended as last column (`StationID`) in the Transactions Log `append_row()` call; logger also updated to include `station=`.

4. **Low-balance email trigger** (lines 1119–1133): After the FCM push notification block, if `new_balance < LOW_BALANCE_THRESHOLD`, imports `EmailNotifier` from `notifications`, instantiates it, and calls `send_low_balance_alert(student_name, student_id, balance, to_email)`. Errors are caught with `logger.warning` and never block the response.

### Task 2 — `backend/dashboard/arduino_bridge.py`

1. **`STATION_ID` and `STATION_SERIAL_PORT` env vars** (lines 29–30): Added at module level after the existing `_CASHIER_JWT`/`_API_BASE_URL` block.

2. **`X-Station-ID` header injection** (line 78): `headers["X-Station-ID"] = STATION_ID` added in `_post_nfc_payment()` so the API server receives which station sent the payment.

3. **Auto-connect in `__init__`** (lines 40–48): If `self.arduino is None` and `STATION_SERIAL_PORT` is set, opens `serial.Serial(STATION_SERIAL_PORT, 9600, timeout=2)`, sleeps 2 s for Arduino bootloader, logs success or warning on failure.

## Deviations from Plan

### Auto-adapted Issues

**1. [Rule 1 - Adaptation] `send_low_balance_alert` parameter names differ from plan**
- **Found during:** Task 1, Step D
- **Issue:** Plan specified `(parent_email, student_name, new_balance, threshold)` but actual method signature in `notifications.py` is `(student_name, student_id, balance, to_email)`.
- **Fix:** Called with correct positional kwargs; retrieved `parent_email` and `student_name` from the same user record already in scope.
- **Files modified:** `backend/api/api_server.py`
- **Commit:** 8cad199

**2. [Rule 1 - Adaptation] `ArduinoBridge` has no `self.connect()` method**
- **Found during:** Task 2, Step C
- **Issue:** Plan's auto-connect snippet calls `self.connect(STATION_SERIAL_PORT)` but no such method exists — the class takes an already-opened `serial` object.
- **Fix:** Used `serial.Serial(STATION_SERIAL_PORT, 9600, timeout=2)` directly in `__init__` (same pattern as `web_app.py`), gated on `self.arduino is None`.
- **Files modified:** `backend/dashboard/arduino_bridge.py`
- **Commit:** a79cecb

## Self-Check

```
FOUND: backend/api/api_server.py
FOUND: backend/dashboard/arduino_bridge.py
FOUND commit: 8cad199
FOUND commit: a79cecb
```

## Self-Check: PASSED
