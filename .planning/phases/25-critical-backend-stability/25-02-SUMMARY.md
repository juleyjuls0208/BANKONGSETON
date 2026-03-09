---
phase: 25-critical-backend-stability
plan: "02"
subsystem: backend-api
tags: [security, performance, cors, cache, google-sheets]
dependency_graph:
  requires: []
  provides: [cors-locked, users-sheet-ttl-cache]
  affects: [backend/api/wsgi.py, backend/api/api_server.py]
tech_stack:
  added: []
  patterns: [ttl-cache-aside, cors-origin-allowlist]
key_files:
  created: []
  modified:
    - backend/api/wsgi.py
    - backend/api/api_server.py
decisions:
  - "Used 'users_all' as the single cache key for all Users-sheet reads — all 14 call sites share the same 30s TTL window"
  - "invalidate_cached placed immediately after write operations in report_lost_card and nfc_register so next read always fetches fresh data"
  - "For the two inline for-loop patterns in nfc_pay(), introduced _cached_nfc/_cached_notif temp variables rather than restructuring the loops"
metrics:
  duration_minutes: 20
  completed: "2026-03-09"
  tasks_completed: 2
  tasks_total: 2
  files_changed: 2
requirements_satisfied: [REQ-SEC-01, REQ-PERF-01]
---

# Phase 25 Plan 02: CORS Fix + TTL Cache Wiring Summary

**One-liner:** Locked CORS from wildcard to production domain and wired existing TTL cache module into all 14 Users-sheet read paths with 30-second TTL and write-path invalidation.

---

## What Was Built

### Task 1 — CORS Wildcard Fix (`wsgi.py`)
- Removed misleading comment block ("Allow all origins for OkHttp/Retrofit Android")
- Changed `os.environ.setdefault('CORS_ORIGINS', '*')` → `os.environ.setdefault('CORS_ORIGINS', 'https://juley2823.pythonanywhere.com')`
- No other changes to the file

### Task 2 — TTL Cache Wiring (`api_server.py`)
- Added `from cache import get_cached, set_cached, invalidate_cached` import (line 35)
- Wrapped all 14 `users_sheet.get_all_records()` calls with cache-aside pattern:
  - 12 variable-assignment patterns (`records`, `user_records`, `users_records`, `user_records2`)
  - 2 inline for-loop patterns inside `nfc_pay()` using `_cached_nfc` / `_cached_notif` temp vars
- All use cache key `"users_all"` with `ttl=30`
- Added `invalidate_cached("users_all")` after the write in `report_lost_card()` (line 817)
- Added `invalidate_cached("users_all")` after the write in `nfc_register()` (line 904)

---

## Verification Results

```
wsgi SYNTAX OK
api_server SYNTAX OK
PASS: CORS domain locked
PASS: cache import
PASS: get_cached usage
PASS: set_cached usage
invalidate_cached count: 2 (need >= 2)
ALL PLAN ASSERTIONS PASSED
```

- `get_cached("users_all")` — 14 call sites ✅
- `set_cached("users_all", ...)` — 14 call sites ✅
- `invalidate_cached("users_all")` — 2 write paths ✅

---

## Commits

| Hash      | Message                                                         |
| --------- | --------------------------------------------------------------- |
| `28982e9` | `fix(25-02): restrict CORS wildcard to production domain`       |
| `c288060` | `feat(25-02): wire TTL cache into all 14 users_sheet.get_all_records() calls` |

---

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Notes

- Pre-existing LSP type errors throughout `api_server.py` (unrelated to `gspread` return types, `email_service` import, `request.user` etc.) were observed and left out of scope per deviation rules.
- Plan stated "12 occurrences" but actual count was 14 — two additional call sites were found and correctly patched. All 14 are now cached.

---

## Self-Check

- [x] `backend/api/wsgi.py` — exists, contains `juley2823.pythonanywhere.com`, no `'*'`
- [x] `backend/api/api_server.py` — exists, contains cache import and ≥14 get/set calls
- [x] Commit `28982e9` — exists in git log
- [x] Commit `c288060` — exists in git log
- [x] Both files pass `python -m py_compile`

## Self-Check: PASSED
