---
phase: "31"
plan: "03"
subsystem: backend-dashboard-security
tags: [security, startup-guard, finance-password, hardcoded-credentials]
dependency_graph:
  requires: [31-01, 31-02]
  provides: [REQ-SEC-06]
  affects: [backend/dashboard/admin_dashboard.py, backend/dashboard/web_app.py]
tech_stack:
  added: []
  patterns: [startup-abort-guard, insecure-default-check]
key_files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/web_app.py
decisions:
  - "FINANCE_PASSWORD guard placed after JWT_SECRET guard in both files — consistent guard ordering (FLASK_SECRET_KEY → JWT_SECRET → FINANCE_PASSWORD)"
  - "Named constant _INSECURE_FINANCE_DEFAULT = 'finance2025' follows _INSECURE_DEFAULT/_JWT_INSECURE_DEFAULT naming pattern already in both files"
  - "Guard block reads and strips FINANCE_PASSWORD; module-level variable reused by login handlers (no second os.getenv call needed)"
metrics:
  duration: "5min"
  completed_date: "2026-03-10"
  tasks_completed: 2
  files_modified: 2
---

# Phase 31 Plan 03: Finance Password Startup Guard Summary

FINANCE_PASSWORD startup guard added to both dashboard backends; aborts process if env var is unset or equals the known-insecure default `"finance2025"`, and all 4 inline hardcoded defaults removed.

## What Was Built

Added an identical `FINANCE_PASSWORD` startup guard block to both `admin_dashboard.py` and `web_app.py`. If the server starts without a valid `FINANCE_PASSWORD` set in the environment, the process logs a `logger.critical` event at `reason=insecure_finance_password` and calls `sys.exit(1)`. This closes REQ-SEC-06.

Removed all 4 occurrences of the inline default `"finance2025"` in the fallback arguments to `os.getenv("FINANCE_PASSWORD", "finance2025")` — two per file (login handler + startup/health-check function). The guard at module load now acts as the single source of truth; the inline getenv calls no longer need fallbacks.

## Tasks

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add FINANCE_PASSWORD guard + remove inline defaults in admin_dashboard.py | `60ad324` | backend/dashboard/admin_dashboard.py |
| 2 | Add FINANCE_PASSWORD guard + remove inline defaults in web_app.py | `fe2eed8` | backend/dashboard/web_app.py |

## Deviations from Plan

None — plan executed exactly as written.

## Verification

Both files confirmed post-edit:
- `guard_present: True` — `insecure_finance_password` log event key present
- `insecure_const: True` — `_INSECURE_FINANCE_DEFAULT` named constant present
- `inline_defaults_remaining: 0` — no `os.getenv("FINANCE_PASSWORD", "finance2025")` calls remain
- `wsgi.py` `from web_app import app` import confirmed intact (untouched)

## Self-Check: PASSED

- `backend/dashboard/admin_dashboard.py` — modified, committed at `60ad324` ✓
- `backend/dashboard/web_app.py` — modified, committed at `fe2eed8` ✓
- Both commits verified in `git log` ✓
