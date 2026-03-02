---
phase: 11
plan: "01"
subsystem: security
tags: [security, credentials, env-vars, startup-guard, cashier]
dependency_graph:
  requires: []
  provides: [SEC-01]
  affects: [cashier_routes, admin_dashboard]
tech_stack:
  added: []
  patterns: [startup-guard, record_once, env-var-credentials]
key_files:
  created: []
  modified:
    - backend/dashboard/cashier/cashier_routes.py
    - backend/dashboard/admin_dashboard.py
    - .env.example
decisions:
  - Used cashier_bp.record_once() instead of module-level os.getenv() because cashier_routes.py is imported before load_dotenv() runs in both web_app.py and admin_dashboard.py
  - Added separate startup guard in admin_dashboard.py to enforce the vars exist at server boot, independent of blueprint registration order
metrics:
  duration: "~10 minutes"
  completed: "2026-03-02"
  tasks_completed: 3
  files_modified: 3
---

# Phase 11 Plan 01: Cashier Security Hardening Summary

**One-liner:** Replace hardcoded cashier/cashier123 credentials with env-var-backed login using `record_once` guard and admin_dashboard startup check.

## What Was Built

Removed the last hardcoded credentials from the cashier login path. The `cashier_routes.py` blueprint now reads `CASHIER_USERNAME` and `CASHIER_PASSWORD` from the environment at app-registration time via `cashier_bp.record_once(_init_cashier_credentials)`, aborting startup with `sys.exit(1)` if either is missing. A second guard was added to `admin_dashboard.py` (after the existing `FLASK_SECRET_KEY` guard) that enforces the same constraint at server boot. Both `.env.example` and `.env` were updated with the new variables.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Replace hardcoded credentials in `cashier_routes.py` with env-var-backed login | `5f8a91d` |
| 2 | Add `CASHIER_USERNAME`/`CASHIER_PASSWORD` startup guard to `admin_dashboard.py` | `973d933` |
| 3 | Document new env vars in `.env.example` and `.env` | `c11846d` |

## Decisions Made

1. **`record_once` over module-level `os.getenv`:** `cashier_routes.py` is imported at the top of both `web_app.py` and `admin_dashboard.py` *before* `load_dotenv()` is called. Using `cashier_bp.record_once()` defers credential reading until the blueprint is registered on an app instance, ensuring `load_dotenv()` has already populated the environment.

2. **Dual guard pattern:** The `admin_dashboard.py` guard is redundant with the `record_once` guard but intentional — it enforces fail-fast behavior at the module level (server boot), not just at blueprint-registration time. This mirrors the existing `FLASK_SECRET_KEY` guard pattern already present in `admin_dashboard.py`.

## Deviations from Plan

None — plan executed exactly as written.

## Final Verification

```
grep -r "cashier123" backend/ --include="*.py"
→ zero matches
```

`cashier123` exists only in `.env` (gitignored) and nowhere in the committed Python source.

## Self-Check: PASSED

- `backend/dashboard/cashier/cashier_routes.py` — modified ✓
- `backend/dashboard/admin_dashboard.py` — modified ✓
- `.env.example` — modified ✓
- Commits `5f8a91d`, `973d933`, `c11846d` — verified ✓
- Zero `cashier123` in `backend/` Python files — verified ✓
