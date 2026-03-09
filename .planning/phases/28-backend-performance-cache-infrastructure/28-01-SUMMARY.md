---
phase: 28-backend-performance-cache-infrastructure
plan: "01"
subsystem: backend/api
tags: [cache, nfc, performance, google-sheets]
dependency_graph:
  requires: []
  provides: [transactions_all-cache, virtual_cards_all-invalidation]
  affects: [nfc_pay, nfc_register, get_transactions]
tech_stack:
  added: []
  patterns: [cache-first read, post-write invalidation]
key_files:
  created: []
  modified:
    - backend/api/api_server.py
key_decisions:
  - "Cache transactions_all with 30s TTL in get_transactions() — matches pattern established for users_all in plan 28-02"
  - "Invalidate transactions_all immediately after append_row() in nfc_pay() to prevent stale history"
  - "Invalidate virtual_cards_all in nfc_register() to ensure fresh VirtualCards data on next NFC payment"
metrics:
  duration: "~10 minutes"
  completed: "2026-03-09"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 28 Plan 01: NFC Pay Cache Invalidations + Transactions Cache Summary

**One-liner:** Added `transactions_all` cache (30s TTL) to `get_transactions()` and two missing post-write `invalidate_cached()` calls in `nfc_pay()` and `nfc_register()` to complete the cache coherency layer.

## Tasks Completed

| # | Task | Commit | Status |
|---|------|--------|--------|
| 1 | Add missing invalidations (`transactions_all` + `virtual_cards_all`) | `0737c37` | ✅ Done |
| 2 | Cache Transactions Log in `get_transactions()` | `0737c37` | ✅ Done |

Both tasks committed together as they were tightly coupled and independently unshippable (T2 needs T1's invalidation to be safe).

## What Was Done

### Task 1: Cache invalidations

**`nfc_pay()` — after `trans_sheet.append_row()`** (line ~1162):
```python
invalidate_cached("transactions_all")
```
Ensures the next call to `get_transactions()` re-fetches from Sheets rather than serving a stale history that excludes the just-completed purchase.

**`nfc_register()` — after `nfc_service.register_virtual_card()`** (line ~908):
```python
invalidate_cached("users_all")
invalidate_cached("virtual_cards_all")   # ← added
```
Ensures the `virtual_cards_all` cache is cleared when a new card is registered, so `nfc_pay()` on the next payment reads fresh VirtualCards data.

### Task 2: Transactions cache

**`get_transactions()`** (line ~539):
```python
trans_sheet = get_worksheet_with_retry("Transactions Log")
trans_records = get_cached("transactions_all")
if trans_records is None:
    trans_records = trans_sheet.get_all_records()
    set_cached("transactions_all", trans_records, ttl=30)
```
Reduces per-user transaction history fetch from 1 Google Sheets API call per request to ≤1 call per 30-second window (shared across all users, invalidated on every NFC purchase).

## Deviations from Plan

### Partial prior completion

**Found during:** Pre-execution inspection  
**Issue:** The `virtual_cards_all` cache in `nfc_pay()` (Task 1 step 1) and the `money_sheet.row_values(1)` elimination (Task 1 step 2) were already applied in a prior session (commit `d3a6aa3`).  
**Action:** Skipped those sub-steps; executed only the two missing `invalidate_cached` calls and the `get_transactions()` cache wrap.  
**Impact:** None — correct outcome achieved.

## Verification

```
PASS — all patterns correct
syntax OK
```

All 6 required cache patterns confirmed present; both forbidden patterns (`nfc_service.get_virtual_card_by_token`, `money_sheet.row_values(1)`) confirmed absent.

## Self-Check: PASSED

- ✅ `backend/api/api_server.py` modified
- ✅ Commit `0737c37` exists
- ✅ All 6 cache patterns present in source
- ✅ Python syntax valid
