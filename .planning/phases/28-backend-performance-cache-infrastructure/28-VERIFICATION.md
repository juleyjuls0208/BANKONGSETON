---
phase: 28-backend-performance-cache-infrastructure
verified: 2026-03-09T21:30:00+08:00
status: passed
score: 4/4 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "Cashier transaction handler reads the Users sheet at most once per 30s TTL window — notification FCM block (line 629) and email block (line 655) now use get_cached('users_all') cache-first pattern"
  gaps_remaining: []
  regressions: []
---

# Phase 28: Backend Performance — Cache Infrastructure Verification Report

**Phase Goal:** NFC payment path drops from 7–9 sequential Sheets API calls to ≤3; cashier transaction reads the users sheet once (not thrice); per-user transaction query filters at the sheet level.  
**Verified:** 2026-03-09T21:30:00+08:00  
**Status:** passed  
**Re-verification:** Yes — after gap closure (notification FCM + email blocks now use `users_all` cache)

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | NFC payment path makes ≤3 Google Sheets API calls on warm cache | ✓ VERIFIED | Warm cache path: Money Accounts read (1) + update_cell (2) + append_row (3). VirtualCards and Users both use `get_cached()/set_cached()` → 0 API calls on cache hit. |
| 2 | Per-user transaction history fetches full Transactions Log at most once per 30s TTL, then filters in Python | ✓ VERIFIED | `get_transactions()` wraps `trans_sheet.get_all_records()` with `get_cached("transactions_all")` / `set_cached(..., ttl=30)`; Python-side filter unchanged. |
| 3 | Cashier transaction handler reads the Users sheet at most once per 30s TTL window | ✓ VERIFIED | All four `complete_sale()` Users reads now use `get_cached("users_all")` / `set_cached(...)` guards: manual lookup (line 455), RFID resolution (line 515), notification FCM block (line 629), email block (line 657). |
| 4 | `nfc_register()` invalidates `virtual_cards_all`; `nfc_pay()` invalidates `transactions_all` after append_row | ✓ VERIFIED | `invalidate_cached("virtual_cards_all")` at line 908 in `nfc_register()`; `invalidate_cached("transactions_all")` at line 1162 in `nfc_pay()`. Both confirmed present. |

**Score:** 4/4 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/api/api_server.py` | `virtual_cards_all` cache in `nfc_pay()` | ✓ VERIFIED | `get_cached("virtual_cards_all")` (1×) + `set_cached("virtual_cards_all"` (1×) present |
| `backend/api/api_server.py` | `transactions_all` cache in `get_transactions()` | ✓ VERIFIED | `get_cached("transactions_all")` (1×) + `set_cached("transactions_all"` (1×) present |
| `backend/api/api_server.py` | `invalidate_cached("transactions_all")` after `append_row` in `nfc_pay()` | ✓ VERIFIED | Present at line 1162, after `trans_sheet.append_row(...)` |
| `backend/api/api_server.py` | `invalidate_cached("virtual_cards_all")` in `nfc_register()` | ✓ VERIFIED | Present at line 908, after `register_virtual_card()` |
| `backend/dashboard/cashier/cashier_routes.py` | `from cache import get_cached, set_cached` with ImportError fallback | ✓ VERIFIED | Correct import with no-op fallback at lines 27–33 |
| `backend/dashboard/cashier/cashier_routes.py` | Both manual + RFID Users reads replaced with `users_all` cache | ✓ VERIFIED | Lines 455–458 (manual) and 515–518 (RFID) correctly wrapped in cache-miss guards |
| `backend/dashboard/cashier/cashier_routes.py` | Notification and email Users reads also cached | ✓ VERIFIED | Lines 629–632 (notification FCM block) and 657–660 (email block) now use `_users_notif = get_cached("users_all"); if None: fetch + set_cached(...)` pattern |

---

## Key Link Verification

### Plan 28-01 Key Links (api_server.py)

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `nfc_pay()` | `virtual_cards_all` cache | `get_cached("virtual_cards_all")` at call-site | ✓ WIRED | Pattern confirmed present; `nfc_service.get_virtual_card_by_token` is absent (removed) |
| `get_transactions()` | `transactions_all` cache | `get_cached("transactions_all")` wrapping `get_all_records()` | ✓ WIRED | Present at lines 541–544 |
| `nfc_pay()` after `append_row` | `invalidate_cached("transactions_all")` | Direct call | ✓ WIRED | Line 1162, immediately after `trans_sheet.append_row(...)` |
| `nfc_register()` after `register_virtual_card` | `invalidate_cached("virtual_cards_all")` | Direct call | ✓ WIRED | Line 908, alongside existing `invalidate_cached("users_all")` |

### Plan 28-02 Key Links (cashier_routes.py)

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| Manual lookup path (~line 455) | `users_all` cache | `get_cached("users_all")` replacing bare call | ✓ WIRED | Cache-miss guard confirmed: `_users = get_cached("users_all"); if _users is None: _users = _db.worksheet...` |
| RFID student-ID resolution (~line 515) | `users_all` cache | `get_cached("users_all")` replacing bare call | ✓ WIRED | Cache-miss guard confirmed: `_users_for_id = get_cached("users_all"); if _users_for_id is None:...` |
| Notification FCM block (~line 629) | `users_all` cache | `get_cached("users_all")` replacing bare call | ✓ WIRED | Cache-miss guard confirmed: `_users_notif = get_cached("users_all"); if _users_notif is None: db.worksheet...` |
| Email block (~line 657) | `users_all` cache | `get_cached("users_all")` replacing bare call | ✓ WIRED | Cache-miss guard confirmed: `_users_email = get_cached("users_all"); if _users_email is None: db.worksheet...` |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| REQ-PERF-02 | 28-01 | Reduce NFC payment path from 7–9 to ≤3 API calls | ✓ SATISFIED | Warm cache: 3 calls (Money read + update_cell + append_row). VirtualCards + Users cached. `nfc_service.get_virtual_card_by_token` removed. `money_sheet.row_values(1)` eliminated. |
| REQ-PERF-03 | 28-02 | Cache users sheet per request in cashier transaction — currently read 3× | ✓ SATISFIED | All four `complete_sale()` Users reads now use `users_all` cache: manual lookup (line 455), RFID resolution (line 515), notification FCM block (line 629), email block (line 657). On warm cache, 0 Users API calls per transaction. |
| REQ-PERF-04 | 28-01 | Add per-user transaction query — currently all-users fetch + Python filter | ✓ SATISFIED | `transactions_all` cache (30s TTL) wraps `trans_sheet.get_all_records()` in `get_transactions()`. Per-request API call eliminated; filter remains Python-side on cached data. Context explicitly accepted this approach as satisfying REQ-PERF-04 intent. |

**Note on REQ-PERF-04 interpretation:** The phase goal phrases this as "filters at the sheet level," but the implementation context and PLAN truth (28-01) explicitly chose caching + Python filter as the approach, stating: _"Satisfies REQ-PERF-04 intent: no all-users-fetch + Python filter on every API call."_ This is verified as delivered.

---

## Anti-Patterns Found

None — all previously identified anti-patterns resolved.

---

## Human Verification Required

None — all required verifications were performed via code review.

---

## Gaps Summary

No gaps — all phase goals achieved after gap closure.

**REQ-PERF-02** ✓ — NFC pay warm-cache path = exactly 3 API calls.  
**REQ-PERF-03** ✓ — All four `complete_sale()` Users reads now cache-first; 0 API calls per transaction on warm cache.  
**REQ-PERF-04** ✓ — `transactions_all` cache (30s TTL) eliminates per-request Transactions Log API calls.

---

_Initial verification: 2026-03-09T21:00:00+08:00 (gaps_found, 3/4)_  
_Re-verification: 2026-03-09T21:30:00+08:00 (passed, 4/4)_  
_Verifier: Claude (gsd-verifier)_
