---
phase: 11
plan: 02
subsystem: security
tags: [security, jwt, startup-guard, cashier, admin-dashboard]
dependency_graph:
  requires: [11-01]
  provides: [SEC-02]
  affects: [cashier_routes.py, admin_dashboard.py, .env.example]
tech_stack:
  added: []
  patterns: [startup-guard, fail-fast, insecure-default-rejection]
key_files:
  created: []
  modified:
    - backend/dashboard/cashier/cashier_routes.py
    - backend/dashboard/admin_dashboard.py
    - .env.example
decisions:
  - JWT_SECRET validation moved into _init_cashier_credentials callback so it runs post-load_dotenv
  - JWT_SECRET = None placeholder at module level; set only after guard passes
  - Insecure default string kept as rejection constant (not as fallback)
metrics:
  duration: ~10 minutes
  completed: "2026-03-02"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 3
requirements: [SEC-02]
---

# Phase 11 Plan 02: JWT Secret Hardening Summary

## One-liner

Removed hardcoded `bangko-jwt-secret-2026` JWT fallback; both dashboards now abort startup if `JWT_SECRET` is missing or insecure.

## What Was Built

- **`cashier_routes.py`**: `JWT_SECRET = None` placeholder at module level; `_init_cashier_credentials` callback extended to read and validate `JWT_SECRET` — aborts with `sys.exit(1)` if missing or equal to the insecure default string.
- **`admin_dashboard.py`**: New `JWT_SECRET` startup guard block inserted between the `CASHIER_PASSWORD` guard and timezone config — same fail-fast pattern as the existing `FLASK_SECRET_KEY` guard.
- **`.env.example`**: New `JWT Secret (Cashier Dashboard)` section added with safe placeholder value and `python -c "import secrets; print(secrets.token_urlsafe(32))"` generation instructions.

## Verification Results

| Check | Result |
|---|---|
| No `os.getenv("JWT_SECRET", "bangko-...")` insecure fallback | ✅ Removed |
| Both files use `os.getenv("JWT_SECRET", "").strip()` with guard | ✅ Confirmed |
| `sys.exit(1)` fires on missing/insecure JWT_SECRET | ✅ In both files |
| `JWT_SECRET` documented in `.env.example` | ✅ Line 61 |

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Hash | Description |
|---|---|
| `34e0a3d` | feat(11-02): harden JWT_SECRET with startup guards and remove insecure fallback |

## Self-Check: PASSED

- ✅ `backend/dashboard/cashier/cashier_routes.py` exists
- ✅ `backend/dashboard/admin_dashboard.py` exists
- ✅ `.env.example` exists
- ✅ `11-02-SUMMARY.md` exists
- ✅ Commit `34e0a3d` verified in git log
