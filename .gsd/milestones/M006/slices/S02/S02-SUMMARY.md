---
id: S02
parent: M006
milestone: M006
provides:
  - Standalone cashier POS UI on port 5010 with dynamic category sidebar, color-coded product grid, and interactive order panel.
  - JWT-cookie-protected `/api/products` endpoint in `backend/cashier_app` backed by Google Sheets with cache import fallback.
requires:
  - slice: S01
    provides: Standalone Flask+SocketIO app shell, JWT cookie middleware, login/logout flow, and POS route scaffold on port 5010.
affects:
  - S03
key_files:
  - backend/cashier_app/routes/pos.py
  - backend/cashier_app/templates/pos.html
  - tests/test_cashier_app_pos_route.py
  - .gsd/REQUIREMENTS.md
  - .gsd/milestones/M006/M006-ROADMAP.md
key_decisions:
  - D059: Render cart rows with DOM APIs (`createElement` + `textContent`) instead of `innerHTML` for Sheets-sourced values.
  - D060: Treat both explicit 401 and redirected `/login` fetch responses as unauthenticated for POS product hydration.
patterns_established:
  - Product hydration pipeline: `fetchProducts()` → `hydrateProducts()` → `assignCategoryColors()` → `renderCategories()` + `renderProducts()`.
  - Cart state pipeline: mutate `cart` in `addToCart` / `updateCartQuantity` / `removeFromCart`, then project UI exclusively through `renderCart()`.
observability_surfaces:
  - API signal: `/api/products` returns 302 when unauthenticated, 500 with `{ "error": "Failed to load products" }` when Sheets is unavailable.
  - UI surfaces: `#products-status`, `.error-state`, `#order-items`, `#total-value`, `#checkout-btn`.
  - Frontend diagnostics: `event=products_fetch_failed_ui`, `event=cart_render_failed_ui` console events.
drill_down_paths:
  - .gsd/milestones/M006/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M006/slices/S02/tasks/T02-SUMMARY.md
  - .gsd/milestones/M006/slices/S02/tasks/T03-SUMMARY.md
duration: 4h 26m
verification_result: passed
completed_at: 2026-03-19T06:42:00+08:00
---

# S02: New POS UI — product grid and order panel

**Shipped the standalone cashier POS surface for M006: `/api/products` integration, dynamic category/product rendering, and a fully interactive order panel with live total-driven coral Charge CTA.**

## What Happened

S02 turned the S01 POS placeholder into an actual cashier workflow surface.

- **Backend contract (T01):** Added standalone `GET /api/products` in `backend/cashier_app/routes/pos.py`, protected by `@jwt_cookie_required`, reading the `Products` sheet via `get_sheets_client`, filtering inactive/empty rows, normalizing prices, and exposing explicit failure telemetry.
- **Frontend hydration + layout (T02):** Replaced static placeholder content in `backend/cashier_app/templates/pos.html` with a modern three-column POS layout (category rail, product grid, order panel), wired to `fetch('/api/products')`, dynamic category extraction, and per-category card colors.
- **Interactive order assembly (T03):** Implemented cart behavior end-to-end (add, increment, decrement, remove), deterministic total math, and `Charge • ₱X.XX` text/state updates.
- **Safety + robustness:** Cart row rendering uses DOM APIs (`textContent`) for Sheets-controlled values, and product-fetch auth handling supports both 401 and redirected-login responses.
- **Traceability updates:** R054 moved to validated with S02 runtime evidence; M006 roadmap now marks S02 complete.

## Verification

Executed verification across automated tests, runtime behavior, and browser UAT:

- `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` → **pass** (route auth/data/error paths + template hooks).
- Started app with `rtk proxy python backend/cashier_app/app.py` (ready on **port 5010**).
- Browser verification:
  - login flow works and POS shell renders expected regions (`#category-list`, `#products-grid`, `#checkout-btn`).
  - real `/api/products` failure path is visible (HTTP 500 + `.error-state` + user-facing message).
  - product fetch request observed on `:5010` with no `:5003` resources (`performance.getEntriesByType('resource')`).
  - mocked `/api/products` success confirms dynamic categories, color-coded cards, and cart math:
    - `Charge • ₱205.50` after Burger + Cola + Burger,
    - quantity controls update totals to `₱290.50` then `₱205.50` then `₱170.00`.
  - unauthorized product fetch behavior verified by mocking `/api/products` 401 and confirming redirect to `/login`.

## New Requirements Surfaced

- none

## Deviations

- Added/expanded template-level tests in `tests/test_cashier_app_pos_route.py` (not explicitly required by the task list, but necessary to lock behavior).
- Validation used a **mixed mode** for happy-path rendering because this environment could not reach live Google Sheets at execution time.

## Known Limitations

- Live Sheets-backed `/api/products` success (HTTP 200 from real sheet data) could not be proven in this environment; authenticated call currently returns 500 when Sheets credentials/connectivity are unavailable.
- Charge button currently reflects totals/state only; payment submission wiring remains for S03.

## Follow-ups

- S03 should bind `#checkout-btn` to payment flow routes (`/api/process-sale`, `/api/qr-generate`, etc.) without breaking cart projection and total semantics from S02.
- Re-run a live-data UAT in a credentialed environment to capture real `/api/products` 200 evidence and close the remaining integration gap.

## Files Created/Modified

- `backend/cashier_app/routes/pos.py` — Added standalone JWT-protected `/api/products` with Sheets read, active filtering, cache import fallback, and structured error logging.
- `backend/cashier_app/templates/pos.html` — Implemented full modern POS UI, dynamic product/category rendering, interactive cart controls, and live Charge button total updates.
- `tests/test_cashier_app_pos_route.py` — Added route behavior tests and POS template hook assertions for hydration/auth/cart logic.
- `.gsd/milestones/M006/M006-ROADMAP.md` — Marked S02 complete (`[x]`).
- `.gsd/REQUIREMENTS.md` — Updated R054 to validated with M006/S02 proof and adjusted coverage summary counts.
- `.gsd/DECISIONS.md` — Recorded D060 auth-response handling decision for frontend product fetch.
- `.gsd/PROJECT.md` — Refreshed M006 status to indicate S01+S02 complete.

## Forward Intelligence

### What the next slice should know
- S02 already establishes stable UI state boundaries: product fetch/hydration and cart projection are separated cleanly. S03 can attach payment actions to current cart totals without rewriting render architecture.

### What's fragile
- Live product hydration depends on external Sheets availability and credentials — when unavailable, UI correctly fails closed, but happy-path integration proof requires a credentialed runtime.

### Authoritative diagnostics
- `tests/test_cashier_app_pos_route.py` — fastest regression surface for `/api/products` auth/data/error contract and required POS JS hooks.
- Browser signals (`#products-status`, `.error-state`, `#total-value`, `#checkout-btn`) — deterministic runtime truth for hydration/cart state.

### What assumptions changed
- Assumption: runtime environment would provide reachable Sheets for direct happy-path proof.
- Reality: Sheets was unavailable, so S02 used mocked `/api/products` for positive UI/cart UAT while still proving real failure visibility and standalone port isolation.
