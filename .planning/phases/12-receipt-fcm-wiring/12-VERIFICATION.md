# Phase 12: Receipt & FCM Wiring — Verification Report

**Date:** 2026-03-02  
**Phase:** 12 — Receipt & FCM Wiring  
**Method:** Static code inspection only (per CONTEXT.md locked decision)  
**Inspector:** Phase 12 planner/executor

---

## Summary

All three requirements (APP-03, NOTF-01, and `migrate_users_schema` startup) are **VERIFIED** by direct code inspection. Phase 7 already fixed all three items. The Integration Audit (dated 2026-03-01) predates Phase 7 and accurately described the state *at that time*. Phase 11 (cashier security hardening) introduced a ~220-line shift in `cashier_routes.py`, moving route handlers from ~line 307 to ~line 527, but all features survived intact.

The only code change required for this phase was updating `backend/config_validator.py` to add `ItemsJson` as the 11th expected column in the Transactions Log schema (it had 10 columns; runtime writes 11).

---

## Requirement Status

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| APP-03 | Itemized receipt — BalanceBefore and ItemsJson present in cashier transaction row | ✅ VERIFIED | `cashier_routes.py:520-532` — 11-column row with `BalanceBefore` at col 7 and `ItemsJson` at col 11 |
| NOTF-01 | Low-balance push notification fires from cashier POS path | ✅ VERIFIED | `cashier_routes.py:570-612` — both `send_purchase_push()` and `send_low_balance_push()` called; FCM block is non-blocking |
| migrate startup | `migrate_users_schema()` called at `api_server.py` startup | ✅ VERIFIED | `api_server.py:109-115` — called unconditionally at startup in non-fatal try/except |

---

## Detailed Evidence

### APP-03 — Transaction Row Schema

**File:** `backend/dashboard/cashier/cashier_routes.py`  
**Lines:** 520–532

```python
transaction_row = [
    transaction_id,       # col 1:  TransactionID
    timestamp,            # col 2:  Timestamp
    resolved_student_id,  # col 3:  StudentID
    normalized_card,      # col 4:  MoneyCardNumber
    transaction_type,     # col 5:  TransactionType ('Manual' or 'Purchase')
    total,                # col 6:  Amount
    current_balance,      # col 7:  BalanceBefore   ← APP-03 requires this
    new_balance,          # col 8:  BalanceAfter
    "Completed",          # col 9:  Status
    "",                   # col 10: ErrorMessage
    json.dumps(items),    # col 11: ItemsJson        ← APP-03 requires this
]
```

**Result:** All 11 columns present in correct order. BalanceBefore at position 7 (1-indexed). ItemsJson at position 11.

**Note on line shift:** Phase 7 VERIFICATION referenced `cashier_routes.py:307-316`. Current code is at lines 520-532. The ~220-line shift was introduced by Phase 11 (cashier security hardening), which inserted the following functions at the top of the file before the route handlers:
- `_init_cashier_credentials()` — blueprint `record_once` callback
- `_get_parent_app_module()` — helper to resolve sibling module paths
- `get_worksheet_with_retry()` — Sheets API retry wrapper
- `ensure_products_sheet()` — Products sheet auto-create helper

The features themselves are intact; only the line numbers changed.

---

### NOTF-01 — FCM Calls from complete_sale

**File:** `backend/dashboard/cashier/cashier_routes.py`  
**Lines:** 570–612 (approximate; exact lines vary by minor edits)

```python
# FCM block — AFTER session.pop() and BEFORE return jsonify()
# Sale is already committed at this point; FCM is a non-transactional side effect
try:
    threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
    try:
        # Read threshold from Settings sheet (fresh per-request, not cached)
        settings_sheet = db.worksheet("Settings")
        settings_records = settings_sheet.get_all_records()
        for row in settings_records:
            if str(row.get("Key", "")).strip().lower() == "low_balance_threshold":
                threshold = float(row.get("Value", threshold))
                break
    except Exception as settings_err:
        logger.warning("event=settings_read_failed ...")

    users_sheet2 = db.worksheet("Users")
    user_records2 = users_sheet2.get_all_records()
    for user in user_records2:
        if normalize_card_uid(user.get("MoneyCardNumber", "")) == normalized_card:
            fcm_token = str(user.get("FCMToken", "")).strip()
            if fcm_token:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))
                from fcm_sender import send_purchase_push
                send_purchase_push(fcm_token, total, new_balance)     # purchase push (every sale)
                if new_balance < threshold:
                    from fcm_sender import send_low_balance_push
                    send_low_balance_push(fcm_token, new_balance)     # low-balance push (conditional)
            break
except Exception as notif_error:
    logger.warning("event=low_balance_notify_failed error=%s", notif_error)
# Transaction response follows — always reached regardless of FCM outcome:
return jsonify({"success": True, "new_balance": new_balance, "timestamp": timestamp})
```

**Result:**
- `send_low_balance_push()` called when `new_balance < threshold` ✅
- `send_purchase_push()` called on every successful sale ✅ (beneficial addition beyond NOTF-01 scope — per CONTEXT.md: keep it)
- Entire FCM block wrapped in outer `try/except Exception` — failures log a warning but never prevent `return jsonify(...)` ✅
- `return jsonify(...)` is outside and after the FCM block — non-blocking confirmed ✅

**FCM import path:** `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))` followed by `from fcm_sender import send_purchase_push`. This resolves to `backend/api/fcm_sender.py` which is the correct file.

**Additional FCM paths (noted for completeness — not required for NOTF-01):**
- `api_server.py` `process_cashier_transaction` endpoint also calls `send_low_balance_push()` — a separate API path (port 5001)
- `admin_dashboard.py` has FCM calls for money-load events
Both are intact and follow the same non-blocking pattern. NOTF-01 specifies cashier POS (`cashier_routes.py`); these are additional coverage.

---

### migrate_users_schema Startup

**File:** `backend/api/api_server.py`  
**Lines:** 109–115

```python
# Run schema migration at startup (idempotent — skips if all columns exist)
try:
    from migrate_transactions import migrate_users_schema
    migrate_users_schema()
except Exception as _mig_err:
    logger.warning("event=migrate_users_startup_failed error=%s", _mig_err)
```

**Result:**
- Called unconditionally at module load time after `db = get_sheets_client()` ✅
- Non-fatal try/except: Sheets API outage at startup logs a warning but never crashes the server ✅
- This resolves the Integration Audit's claim that "migrate_users_schema() is never called at startup" — it was already fixed in Phase 7

---

## Integration Audit Contradiction — Origin Explained

The Integration Audit (2026-03-01) reported:
- APP-03: `🔴 BROKEN` — "Timestamp format mismatch; BalanceBefore ₱0.00 for all cashier POS rows"
- NOTF-01: `🔴 BROKEN` — "FCM never called from cashier_routes.py; also blocked on fresh deploy by missing FCMToken column"
- TD-02: `migrate_users_schema()` not called at startup
- TD-03: "cashier writes 7 cols, schema expects 8 (`BalanceBefore` missing)"

Phase 7 fixed all three issues. The audit was written from a code snapshot that predated Phase 7's changes. The Phase 7 VERIFICATION report (which cited lines 307-316) documents the fixes. This is a documentation lag, not a regression.

The only remaining gap the audit did not know about was `config_validator.py` having 10 columns instead of 11 — this was addressed in Phase 12 (see below).

---

## Code Change Made This Phase

### config_validator.py — Added ItemsJson to Transactions Log Schema

**File:** `backend/config_validator.py`  
**Lines:** 235–237

**Before:**
```python
'Transactions Log': ['TransactionID', 'Timestamp', 'StudentID',
                     'MoneyCardNumber', 'TransactionType', 'Amount',
                     'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage'],
```

**After:**
```python
'Transactions Log': ['TransactionID', 'Timestamp', 'StudentID',
                     'MoneyCardNumber', 'TransactionType', 'Amount',
                     'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage',
                     'ItemsJson'],
```

**Why:** The runtime transaction row (`cashier_routes.py:520-532`) writes 11 columns. The validator's expected schema had only 10. Without this fix, running `python config_validator.py` would pass silently even if the Transactions Log sheet was missing the `ItemsJson` header — it would not warn the operator. After the fix, the validator correctly flags a missing `ItemsJson` column.

**Note on CONTEXT.md:** CONTEXT.md stated "currently hardcoded as 8 columns". Direct inspection found 10 columns (BalanceBefore, BalanceAfter, Status, and ErrorMessage were added at prior phases). Only `ItemsJson` was missing. One column added, not three.

---

## Google Sheet Header Row

Per CONTEXT.md locked decision: "Verify the Transactions Google Sheet header row matches the 11-column structure."

**Assessment:** Cannot be verified by static code inspection. The Google Sheet lives in Google Drive and is not accessible without a live Sheets API call. **Recommended action:** Run `python backend/config_validator.py` after deployment — the validator will now correctly check for all 11 columns including `ItemsJson` and report any missing header.

---

## Phase 12 Outcome

| Item | Before Phase 12 | After Phase 12 |
|------|-----------------|----------------|
| APP-03 code | Already VERIFIED (Phase 7 fix) | VERIFIED — documented with line numbers |
| NOTF-01 code | Already VERIFIED (Phase 7 fix) | VERIFIED — documented with line numbers |
| migrate_users_schema startup | Already VERIFIED (Phase 7 fix) | VERIFIED — documented with line numbers |
| config_validator.py schema | 10 columns (missing ItemsJson) | 11 columns — matches runtime |
| INTEGRATION_AUDIT.md | APP-03 and NOTF-01 marked 🔴 BROKEN | Updated to ✅ VERIFIED with Phase 12 reference |
