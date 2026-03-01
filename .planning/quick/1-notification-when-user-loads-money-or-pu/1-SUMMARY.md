---
phase: quick-1
plan: 1
subsystem: notifications
tags: [fcm, push-notifications, purchase, load-balance, android]
dependency_graph:
  requires: [firebase_admin, FCMToken column in Users sheet]
  provides: [send_purchase_push, send_load_push in fcm_sender.py]
  affects: [nfc_pay, process_cashier_transaction, complete_sale, load_balance]
tech_stack:
  added: []
  patterns: [lazy-firebase-import, never-raise-push-pattern, try/except-never-block]
key_files:
  created: []
  modified:
    - backend/api/fcm_sender.py
    - backend/api/api_server.py
    - backend/dashboard/cashier/cashier_routes.py
    - backend/dashboard/admin_dashboard.py
decisions:
  - send_purchase_push always fires regardless of balance (not gated on threshold)
  - cashier_routes.py user lookup moved outside the threshold gate so purchase push always fires
  - send_load_push uses import sys as _sys to avoid shadowing module-level sys in admin_dashboard.py
  - Path resolution uses os.path.dirname(__file__) + '../api' (dashboard/ → backend/api/)
metrics:
  duration: ~5min
  completed: "2026-03-02"
  tasks_completed: 3
  files_modified: 4
---

# Quick Task 1: FCM Push Notifications on Balance Change — Summary

**One-liner:** FCM push notifications added to all four transaction paths — purchase (NFC, cashier RFID, process_cashier_transaction) and load — using never-raise wrapper functions in fcm_sender.py.

## What Was Built

Two new helper functions in `backend/api/fcm_sender.py`, wired into all four transaction entry points:

### New Functions in fcm_sender.py

| Function | Title | Body |
|---|---|---|
| `send_purchase_push(fcm_token, amount, new_balance)` | "Purchase Confirmed" | "฿{amount} deducted. New balance: ฿{new_balance}" |
| `send_load_push(fcm_token, amount, new_balance)` | "Money Loaded" | "฿{amount} added to your account. Balance: ฿{new_balance}" |

Both follow the identical pattern as `send_low_balance_push()`: lazy `firebase_admin` import, guard against uninitialized app, never raise, return `bool`.

### Transaction Path Wiring

| Path | File | Trigger | Push Sent |
|---|---|---|---|
| NFC tap payment | `api_server.py:nfc_pay()` | After `trans_sheet.append_row` | `send_purchase_push` |
| Android app purchase | `api_server.py:process_cashier_transaction()` | After `trans_sheet.append_row` | `send_purchase_push` always + `send_low_balance_push` if below threshold |
| Cashier RFID | `cashier_routes.py:complete_sale()` | After balance committed | `send_purchase_push` always + `send_low_balance_push` if below threshold |
| Admin loads money | `admin_dashboard.py:load_balance()` | After `transactions_sheet.append_row` | `send_load_push` |

### Key Design Decisions

- **Purchase push is always sent** — not gated on balance threshold. Every purchase generates a notification regardless of remaining balance.
- **Low-balance push still fires separately** when `new_balance < threshold` after a purchase.
- **All four notification blocks are wrapped in `try/except`** — push failures never block or roll back transactions.
- **cashier_routes.py user lookup restructured** — previously only looked up user when `new_balance < threshold`; now looks up unconditionally so purchase push can always fire.
- **No Android changes needed** — `FCMService.kt` already handles any notification by title/body (confirmed by plan context).

## Commits

| # | Hash | Description |
|---|---|---|
| T1 | `64cef70` | feat(quick-1-1): add send_purchase_push() and send_load_push() to fcm_sender.py |
| T2 | `cf70867` | feat(quick-1-2): wire send_purchase_push into all three purchase paths |
| T3 | `7cfcc35` | feat(quick-1-3): wire send_load_push into load_balance() in admin_dashboard.py |

## Verification

All four files parse with no syntax errors:
```
ALL OK
```

`send_purchase_push` and `send_load_push` confirmed present in all expected locations:
- `backend/api/api_server.py` — lines 893, 895 (nfc_pay), 1149, 1151 (process_cashier_transaction)
- `backend/dashboard/cashier/cashier_routes.py` — lines 567, 569 (complete_sale)
- `backend/dashboard/admin_dashboard.py` — lines 1229, 1231 (load_balance)
- `backend/api/fcm_sender.py` — lines 83, 118 (function definitions)

## Deviations from Plan

### Auto-restructured: cashier_routes.py notification block

**Found during:** Task 2
**Issue:** The existing low-balance block in `complete_sale()` only entered the user lookup loop when `new_balance < threshold`. Inserting `send_purchase_push` inside the `if new_balance < threshold:` block would have meant purchase push was NOT sent when balance stayed above threshold — contrary to the plan's "always send" requirement.
**Fix:** Moved the Users sheet lookup and the `fcm_token` extraction outside the threshold gate. Purchase push fires unconditionally; low-balance push is nested inside `if new_balance < threshold:` as before.
**Files modified:** `backend/dashboard/cashier/cashier_routes.py`
**Commit:** `cf70867`
