---
phase: 24-admin-cashier-improvements
plan: "04"
subsystem: admin-dashboard
tags: [transactions, void, balance-reversal, admin-ui]
dependency_graph:
  requires: [24-01]
  provides: [transaction-void-endpoint, void-ui]
  affects: [admin_dashboard.py, web_app.py, transactions.html]
tech_stack:
  added: []
  patterns: [admin_only-decorator, Google-Sheets-row-update, Bootstrap-modal-confirmation]
key_files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/web_app.py
    - backend/dashboard/templates/transactions.html
decisions:
  - "void_transaction only allows voiding TransactionType='Purchase' (returns 400 for others) — conscious design choice already in codebase"
  - "Balance reversal uses card number lookup against Money Accounts sheet — no StudentID fallback needed since MoneyCardNumber is always present"
  - "Confirmation modal (not window.confirm) used for void — consistent with Bootstrap UI patterns in other admin dialogs"
metrics:
  duration: "~5min"
  completed: "2026-03-09T07:26:24Z"
  tasks_completed: 3
  files_modified: 1
---

# Phase 24 Plan 04: Transaction Void Feature — Summary

## One-liner

Transaction void: admin confirms modal → POST `/api/transactions/<id>/void` → Sheets row marked Voided + student balance restored.

## What Was Built

### Task 1 & 2: `void_transaction` API route (admin_dashboard.py + web_app.py)

Both backend files already contained a production-quality `void_transaction` route under `@app.route('/api/transactions/<transaction_id>/void', methods=['POST'])` protected by `@admin_only`. The implementation:

- Dynamically resolves column indices from sheet headers (robust against column reordering)
- Returns **404** if TransactionID not found
- Returns **409** if transaction is already voided
- Returns **400** if transaction type is not 'Purchase' (design guard against voiding top-ups)
- Updates `TransactionType` → `'Voided'` in Transactions Log
- Looks up `MoneyCardNumber` in Money Accounts sheet and reverses the amount
- Balance reversal: `new_balance = current_balance + (-amount)` (amount is negative for purchases, so this adds back the deduction)
- Uses `normalize_card_uid()` for card number matching
- Logs errors with `exc_info=True`; balance reversal failures are non-fatal (transaction still marked voided)

### Task 3: Void button in transactions.html

Added to the transactions table:
- New **Actions** column header
- Per-row **Void** button (`.void-btn`) — only shown for non-voided transactions
- Bootstrap confirmation modal (`#voidConfirmModal`) with transaction ID displayed
- Async `fetch` POST to `/api/transactions/<txn_id>/void`
- On success: button replaced with grey `Voided` badge; row's type cell updated inline
- Button disabled + text changed to `...` during in-flight request (prevents double-submit)
- Error handling with `alert()` on failure + button re-enabled

## Deviations from Plan

### Pre-implemented Tasks

**Tasks 1 & 2 already existed in codebase**
- **Found during:** Initial inspection
- **Issue:** Both `admin_dashboard.py` and `web_app.py` already contained complete `void_transaction` implementations from prior work
- **Action:** Verified correctness against plan spec, confirmed syntax clean, treated as done
- **Difference from plan spec:** Existing code restricts voiding to `TransactionType == 'Purchase'` only (plan proposed allowing any non-voided type). This is a stricter, safer default — kept as-is.

## Self-Check

- [x] `backend/dashboard/admin_dashboard.py` — `void_transaction` route present at line 921
- [x] `backend/dashboard/web_app.py` — `void_transaction` route present at line 756
- [x] `backend/dashboard/templates/transactions.html` — `voidConfirmModal`, `void-btn` present
- [x] Python syntax OK (both py files)
- [x] HTML parses OK (transactions.html)
- [x] Task 3 commit: `663cb66`
