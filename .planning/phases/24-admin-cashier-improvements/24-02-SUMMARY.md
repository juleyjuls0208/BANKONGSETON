---
phase: 24-admin-cashier-improvements
plan: 02
subsystem: admin-dashboard
tags: [soft-delete, products, admin, bug-fix]
dependency_graph:
  requires: [24-01]
  provides: [delete-product-endpoint]
  affects: [admin_dashboard.py, web_app.py, products.html]
tech_stack:
  added: []
  patterns: [soft-delete, @admin_only decorator]
key_files:
  created: []
  modified:
    - backend/dashboard/admin_dashboard.py
    - backend/dashboard/web_app.py
decisions:
  - "Kept existing URL /api/products/delete/<product_id> (not /api/products/<product_id>) — products.html JS already called this URL"
  - "Replaced @login_required + @admin_required with @admin_only — admin_only already checks session, admin_required was never defined"
  - "products.html already fully implemented — delete button, JS handler, and fetch call all existed; no changes required"
metrics:
  duration: 5min
  completed: "2026-03-09"
  tasks_completed: 3
  files_modified: 2
---

# Phase 24 Plan 02: Soft-Delete Product Feature Summary

**One-liner:** Fixed broken `@admin_required` decorator on soft-delete product routes in both Python files — routes now use `@admin_only` and work at runtime.

## What Was Done

The plan called for adding a `DELETE /api/products/<id>` endpoint to `admin_dashboard.py`, mirroring it to `web_app.py`, and adding a Delete button to `products.html`.

**Discovery:** All three were already implemented (likely by a prior session) but with a critical runtime bug: both Python files used `@admin_required` — a decorator that is **not defined anywhere** in either file. At runtime this would cause a `NameError: name 'admin_required' is not defined` as soon as any request hit the delete route. The correct decorator is `@admin_only`.

**Changes made:**
- `admin_dashboard.py` line 748–749: replaced `@login_required` + `@admin_required` → `@admin_only`
- `web_app.py` line 583–584: same replacement
- `products.html`: already complete — no changes needed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `@admin_required` replaced with `@admin_only` in both Python files**
- **Found during:** Task 1 analysis
- **Issue:** Both `admin_dashboard.py` and `web_app.py` had `@admin_required` on the delete route. This decorator is never defined in either file — calling the endpoint would raise `NameError` at runtime.
- **Fix:** Replaced `@login_required` + `@admin_required` two-line decorator combo with the single correct `@admin_only` decorator (which already includes the session check internally).
- **Files modified:** `backend/dashboard/admin_dashboard.py`, `backend/dashboard/web_app.py`
- **Commits:** `38ecbc5`, `787c850`

**2. [Plan deviation] URL kept as `/api/products/delete/<product_id>` (not `/api/products/<product_id>`)**
- **Reason:** `products.html` JS already calls `/api/products/delete/${id}`. The plan's prescribed URL `/api/products/<product_id>` would have required changing the HTML too, and introduced potential conflicts with `POST /api/products/update` (same prefix). Kept consistent.

**3. [No-op] products.html already fully implemented**
- The template already had the Delete column header, per-row delete button with `onclick="deleteProduct(...)"`, and the full `deleteProduct()` async JS function. Task 3 was a no-op verification.

## Commits

| Hash | Message |
|------|---------|
| `38ecbc5` | fix(24-02): fix delete_product decorator in admin_dashboard.py |
| `787c850` | fix(24-02): fix delete_product decorator in web_app.py |

## Verification

All plan verification checks passed:
- `admin_dashboard.py` AST parse: OK
- `web_app.py` AST parse: OK  
- `grep "DELETE"` shows route in admin_dashboard.py
- `grep "DELETED"` shows soft-delete logic
- `products.html` HTML parse: OK
- Delete button and JS handler confirmed in products.html

## Self-Check: PASSED

- `backend/dashboard/admin_dashboard.py` — exists, `@admin_only` on delete route confirmed
- `backend/dashboard/web_app.py` — exists, `@admin_only` on delete route confirmed
- Commits `38ecbc5` and `787c850` — confirmed in git log
