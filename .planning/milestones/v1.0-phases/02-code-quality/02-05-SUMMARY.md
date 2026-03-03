---
phase: "02"
plan: "05"
subsystem: "backend-state-management"
tags: [refactor, global-state, thread-safety, utils-consolidation]
dependency_graph:
  requires: [02-01-SUMMARY.md]
  provides: [thread-safe-card-state, canonical-normalize-card-uid]
  affects: [admin_dashboard.py, cashier_routes.py, api_server.py]
tech_stack:
  added: []
  patterns: [singleton-state-object, centralized-utility-import]
key_files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/cashier/cashier_routes.py
    - backend/api/api_server.py
decisions:
  - "Use card_reader_state.update() for atomic multi-key writes (e.g. pending_student_id + card_reading_active together)"
  - "Keep get_sheets_client and get_philippines_time in admin_dashboard inline import in cashier_routes — only normalize_card_uid moved to utils"
metrics:
  duration: "~35 minutes (cross-session)"
  completed_date: "2026-02-26"
  tasks_completed: 2
  files_modified: 3
---

# Phase 02 Plan 05: Wire utils.py Into Dashboard and API Summary

**One-liner:** Thread-safe `CardReaderState` singleton replaces 4 module globals in `admin_dashboard.py`; `normalize_card_uid` consolidated to `utils.py` across all three backend files.

## What Was Built

### Task 1 — Migrate Global State to `CardReaderState` in `admin_dashboard.py`

Removed four module-scope globals (`arduino`, `arduino_bridge`, `card_reading_active`, `pending_student_id`) and the duplicate local `normalize_card_uid()` definition. Added `from utils import card_reader_state, normalize_card_uid` at the top.

All 8 affected functions now use `card_reader_state.get/set/update()`:

| Function | Changes |
|---|---|
| `connect_serial()` | `update(arduino=..., arduino_bridge=...)` |
| `disconnect_serial()` | `set('arduino', None)`, `set('card_reading_active', False)` |
| `start_register()` | `set('card_reading_active', True)`, `get('arduino')` |
| `link_money_card()` | `update(pending_student_id=..., card_reading_active=True)` |
| `read_card_thread()` | `get('arduino')`, `get/set('card_reading_active')` |
| `handle_money_card()` | `get('pending_student_id')` |
| `replace_lost_card()` | `update(pending_student_id=..., card_reading_active=True)` |
| `handle_replace_card()` | `get('pending_student_id')` |

**Commit:** `78ba53c`

### Task 2 — Migrate `normalize_card_uid` Import in `cashier_routes.py` and `api_server.py`

- **`cashier_routes.py`**: Added top-level `from utils import normalize_card_uid`; removed `normalize_card_uid` from the inline `from admin_dashboard import ...` statement inside `complete_sale()`. `get_sheets_client` and `get_philippines_time` remain in the inline import as they are still sourced from `admin_dashboard`.
- **`api_server.py`**: Added `from utils import normalize_card_uid` after the `sys.path.insert` block; removed the local `normalize_card_uid()` definition (which lacked None-safety — only did `str(uid).lstrip('0').upper()`). Now uses the canonical None-safe version from `utils.py`.

**Commit:** `8403983`

## Verification

Both tasks passed AST verification:

```
admin_dashboard.py: no global declarations for target vars, normalize_card_uid not defined locally, card_reader_state present — PASS
api_server.py: no local define, no admin_dashboard import, imports from utils — PASS
cashier_routes.py: no local define, no admin_dashboard import for normalize, imports from utils — PASS
```

## Decisions Made

1. **`card_reader_state.update()` for multi-key atomic writes** — When two state keys are set together (e.g., `pending_student_id` + `card_reading_active`), used `update(**kwargs)` to make it a single call.
2. **Keep `get_sheets_client` / `get_philippines_time` inline in cashier_routes** — These are not in scope for this plan; only `normalize_card_uid` was being de-duplicated.
3. **`api_server.py` gained None-safety** — The old local definition didn't guard against `None` input. The utils version does, making this a correctness improvement.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] `backend/dashboard/admin_dashboard.py` modified
- [x] `backend/dashboard/cashier/cashier_routes.py` modified
- [x] `backend/api/api_server.py` modified
- [x] Commit `78ba53c` exists
- [x] Commit `8403983` exists
