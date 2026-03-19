---
id: T02
parent: S02
milestone: M006
provides:
  - Standalone POS frontend now fetches `/api/products` on load and renders dynamic category sidebar plus color-coded product cards with login/error handling.
key_files:
  - backend/cashier_app/templates/pos.html
  - tests/test_cashier_app_pos_route.py
  - .gsd/milestones/M006/slices/S02/tasks/T02-PLAN.md
  - .gsd/milestones/M006/slices/S02/S02-PLAN.md
key_decisions:
  - Frontend auth handling checks both `response.status === 401` and redirect-to-login fetch responses (`response.redirected && response.url.includes('/login')`) to match current backend redirect behavior.
patterns_established:
  - Product hydration pipeline: `fetchProducts()` → `hydrateProducts()` → `assignCategoryColors()` → `renderCategories()`/`renderProducts()` with centralized UI state.
observability_surfaces:
  - POS UI status/error surfaces (`#products-status`, `.error-state`), browser resource entries for `/api/products`, and frontend console event `event=products_fetch_failed_ui` on fetch failure.
duration: 1h 42m
verification_result: passed
completed_at: 2026-03-19T06:29:00+08:00
blocker_discovered: false
---

# T02: Implement frontend product fetching and rendering

**Implemented live product-fetch rendering in `pos.html` with dynamic categories, category-color product cards, and explicit login/error handling for `/api/products`.**

## What Happened

I first fixed the pre-flight planning gap by adding an `## Observability Impact` section to `.gsd/milestones/M006/slices/S02/tasks/T02-PLAN.md`.

Then I rewrote `backend/cashier_app/templates/pos.html` from skeleton placeholders into a modern POS layout with:
- dynamic product fetch on page load via `fetchProducts()` to `/api/products`,
- unauthorized handling that redirects to `/login`,
- category extraction + sidebar rendering,
- category-to-color mapping and product card rendering,
- a visible inline error state when products fail to load,
- visual treatment aligned to the slice target (white surfaces, clean cards, coral Charge button).

I also extended `tests/test_cashier_app_pos_route.py` with frontend-template coverage to verify the page includes the new fetch/render/auth-redirect hooks.

Finally, I executed runtime/browser verification for both real backend behavior (current environment returns 500 from `/api/products`) and mocked-success behavior (to verify category/card rendering and color mapping logic).

## Verification

- Python syntax and unit tests passed for updated route/template test coverage.
- Browser flow confirmed login → POS load, error-state rendering on real `/api/products` 500, and explicit 401 redirect behavior.
- Mocked `/api/products` payload confirmed categories appear in sidebar and product cards render with distinct category colors.
- Slice-level cart interaction check is still pending by design for T03 (clicking cards does not yet update totals).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile tests/test_cashier_app_pos_route.py backend/cashier_app/routes/pos.py backend/cashier_app/app.py` | 0 | ✅ pass | ~0.2s |
| 2 | `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` | 0 | ✅ pass | 0.83s |
| 3 | `bg_shell start "rtk proxy python backend/cashier_app/app.py" (ready_port=5010)` | 0 | ✅ pass | ~2s |
| 4 | Browser batch: `/login` → submit cashier credentials → assert `#category-list`, `#products-grid`, `.checkout-btn` | 0 | ✅ pass | ~8s |
| 5 | `browser_evaluate` fetch probe for real backend: `fetch('/api/products')` | 0 | ❌ fail (`status: 500` in current environment) | ~1s |
| 6 | Browser assert on failure visibility: `Unable to load products` + `.error-state` | 0 | ✅ pass | ~1s |
| 7 | Mocked success (`browser_mock_route **/api/products -> 200`) + reload + asserts for categories/cards/text | 0 | ✅ pass | ~7s |
| 8 | `browser_evaluate` computed card styles (`.product-card`) | 0 | ✅ pass (multiple unique background colors across categories) | ~1s |
| 9 | Slice check (pending T03): click product card and compare `.summary-total` before/after | 0 | ❌ fail (remains `₱0.00`, cart logic not implemented yet) | ~3s |
| 10 | `browser_evaluate` resource entries (`/api/products` present, no `:5003` entries) | 0 | ✅ pass | ~1s |
| 11 | Mocked unauthorized (`browser_mock_route **/api/products -> 401`) + reload + `url_contains('/login')` assert | 0 | ✅ pass | ~4s |
| 12 | `rtk proxy curl -s -i http://127.0.0.1:5010/api/products` | 0 | ✅ pass (unauthenticated redirect to `/login`) | ~0.2s |
| 13 | `rtk proxy curl -s -i -c tmp_cashier_cookie.txt -H "Content-Type: application/json" -d '{"username":"cashier","password":"cashier123"}' http://127.0.0.1:5010/api/login` | 0 | ✅ pass (login success + cookie issued) | ~0.3s |
| 14 | `rtk proxy curl -s -i -b tmp_cashier_cookie.txt http://127.0.0.1:5010/api/products` | 0 | ❌ fail (`500 {"error":"Failed to load products"}` in current env) | ~0.2s |

## Diagnostics

- Frontend runtime inspection:
  - `#products-status` shows loading/state text (`Loading products...`, `N items shown`, `Unable to load products`).
  - `.error-state` renders explicit user-facing failure copy when fetch fails.
  - `.product-card[data-category]` exposes per-card category for UI/debug inspection.
- Programmatic inspection surfaces:
  - `fetchProducts()` logs `event=products_fetch_failed_ui` on failure.
  - `performance.getEntriesByType('resource')` confirms `/api/products` requests and verifies no `:5003` calls.
- Backend error surface remains from T01:
  - `/api/products` returns `500 {"error":"Failed to load products"}` when Sheets is unavailable.

## Deviations

- Added focused template-level assertions to `tests/test_cashier_app_pos_route.py` to satisfy the task requirement to update tests alongside UI implementation.
- Added an execution knowledge note in `.gsd/KNOWLEDGE.md` about browser verification fallback when network log buffer is empty.

## Known Issues

- In this environment, live Google Sheets access is still unavailable; therefore `/api/products` returns HTTP 500 and real-data category/card rendering cannot be demonstrated without mocks.
- Slice-level cart behavior (product click updates order panel and totals) is intentionally still incomplete and scoped to T03.

## Files Created/Modified

- `backend/cashier_app/templates/pos.html` — Replaced placeholders with modern POS layout, dynamic product fetch, category rendering, color mapping, and UI error/login handling.
- `tests/test_cashier_app_pos_route.py` — Added tests asserting POS template includes fetch bootstrap, category/product rendering hooks, and unauthorized redirect logic.
- `.gsd/milestones/M006/slices/S02/tasks/T02-PLAN.md` — Added missing `## Observability Impact` section required by pre-flight checks.
- `.gsd/milestones/M006/slices/S02/S02-PLAN.md` — Marked T02 as complete (`[x]`).
- `.gsd/KNOWLEDGE.md` — Appended browser verification fallback pattern using `performance.getEntriesByType('resource')`.
