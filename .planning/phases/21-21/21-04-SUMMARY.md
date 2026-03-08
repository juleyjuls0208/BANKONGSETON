---
phase: "21"
plan: "04"
subsystem: backend-notifications
tags: [sms, twilio, nfc-pay, low-balance]
dependency_graph:
  requires: [21-03]
  provides: [twilio-sms-notifier, nfc-pay-sms-alerts]
  affects: [backend/notifications.py, backend/api/api_server.py]
tech_stack:
  added: [twilio (lazy import)]
  patterns: [lazy-import for optional dependency, non-blocking notification pattern]
key_files:
  created: []
  modified:
    - backend/notifications.py
    - backend/api/api_server.py
decisions:
  - "Twilio SDK imported lazily inside send_low_balance_sms() — keeps it optional; server still boots if twilio package absent"
  - "LOW_BALANCE_THRESHOLD read inline from env in nfc_pay handler (same pattern as cashier handler) — no new module-level constant"
  - "student_name + phone_number captured in same Users sheet loop as nfc_student_id — no extra Sheets API call"
  - "SMS block placed after FCM push block — consistent notification ordering; both are non-blocking try/except"
metrics:
  duration: "~10min"
  completed: "2026-03-08"
  tasks_completed: 2
  files_modified: 2
---

# Phase 21 Plan 04: Twilio SMS Low-Balance Notifications Summary

**One-liner:** Twilio SMS low-balance alerts via `TwilioSMSNotifier` class wired into the `/api/nfc/pay` handler with lazy SDK import and env-driven enable/disable.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add `TwilioSMSNotifier` class to `notifications.py` | `9f54595` | `backend/notifications.py` |
| 2 | Wire SMS notifier into `/api/nfc/pay` handler | `d99743e` | `backend/api/api_server.py` |

## What Was Built

### Task 1 — `TwilioSMSNotifier` (`notifications.py`)

Appended `TwilioSMSNotifier` class (lines 744–796) after the existing `EmailNotifier` class:

- Reads `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` from env (all default `""`)
- `self.enabled = bool(account_sid and auth_token and from_number)` — silent no-op when unconfigured
- `send_low_balance_sms(phone_number, student_name, new_balance, threshold)` → `bool`
  - Returns `False` early if `not self.enabled` or `not phone_number`
  - Lazy-imports `from twilio.rest import Client` inside the method body
  - Wraps Twilio API call in `try/except Exception` with `logger.warning` on failure
  - Returns `True` on success, `False` on any error

### Task 2 — Wire-in (`api_server.py`)

Three targeted changes:

**Module level (lines 33–36):**
```python
from notifications import TwilioSMSNotifier
...
sms_notifier = TwilioSMSNotifier()
```

**Users sheet loop in `nfc_pay` (lines 1067–1082):** Extended to also capture `student_name` and `phone_number` from the same record iteration — zero extra Sheets API calls.

**After FCM notification block (lines 1120–1129):**
```python
low_balance_threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
if new_balance < low_balance_threshold and phone_number:
    try:
        sms_notifier.send_low_balance_sms(...)
    except Exception as sms_err:
        logger.warning(f"Low balance SMS failed: {sms_err}")
```

## Deviations from Plan

### Plan Adjustments (Not Auto-fix)

**1. No `email_notifier` anchor point in `api_server.py`**
- **Found during:** Task 2 Step A
- **Plan said:** Place import + instantiation "below `email_notifier = EmailNotifier()`"
- **Reality:** No `email_notifier` instance exists at module level; file uses `from email_service import email_service` inside a handler body
- **Fix:** Placed `from notifications import TwilioSMSNotifier` and `sms_notifier = TwilioSMSNotifier()` after existing module-level service imports (after `nfc_service = NFCService()`)

**2. No existing low-balance email block in `nfc_pay`**
- **Plan said:** Add SMS block "after the low-balance email block" in `nfc_pay`
- **Reality:** `nfc_pay` has no email block — only FCM push notification block
- **Fix:** Placed SMS block immediately after the FCM notification try/except block (consistent with plan intent)

**3. `student_name` / `phone_number` not yet retrieved in `nfc_pay`**
- **Plan said:** "add `phone_number = student_record.get('PhoneNumber', '')`"
- **Reality:** No `student_record` variable; data comes from a loop over `users_sheet_nfc.get_all_records()`
- **Fix:** Extended the existing loop to also capture `student_name` and `phone_number` from matched record — same loop, no extra API call

## Self-Check: PASSED

- ✅ `.planning/phases/21-21/21-04-SUMMARY.md` — exists
- ✅ `9f54595` (feat(21-04): add TwilioSMSNotifier) — confirmed in git log
- ✅ `d99743e` (feat(21-04): wire TwilioSMSNotifier) — confirmed in git log
- ✅ `backend/notifications.py` — compiles cleanly (`py_compile` PASS)
- ✅ `backend/api/api_server.py` — compiles cleanly (`py_compile` PASS)
