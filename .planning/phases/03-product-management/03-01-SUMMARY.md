# 03-01 Summary — Backend Product Endpoint Hardening

## Status: COMPLETE

## What was done

**Task 1: Added `ensure_products_sheet()` helper and fixed endpoint resilience**
- Added `ensure_products_sheet()` function after `get_worksheet_with_retry()` (line ~144)
- Auto-creates Products sheet with correct headers `[ID, Name, Category, Price, ImageURL, Active, DateAdded]` if missing
- All three product endpoints now call `ensure_products_sheet()` instead of `db.worksheet('Products')` directly
- All logger calls in product endpoints converted from f-strings to `%s` lazy formatting

**Task 2: Rewrote `update_product()` with merge-on-update logic**
- Old: overwrote all 7 fields with request payload (broke inline cell edits that send only 1 field)
- New: fetches existing record first, merges only fields present in request
- `active` field handled bidirectionally (present in request → use that value; absent → preserve existing)

**Task 3: Renamed `/api/products/delete` → `/api/products/toggle-status`**
- New route: `POST /api/products/toggle-status` with `{id, active}` payload
- Updates column F (Active) to `TRUE` or `FALSE` bidirectionally
- Function renamed to `toggle_product_status()`

## Verification results

- `python -c "import ast; ast.parse(...); print('syntax ok')"` → **syntax ok**
- No `db.worksheet('Products')` direct calls remain in product endpoints
- `ensure_products_sheet()` present in file
- `toggle-status` route present
- No f-string logger calls in product functions

## Files modified

- `backend/dashboard/admin_dashboard.py`
