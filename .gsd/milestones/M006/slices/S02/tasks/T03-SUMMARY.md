---
id: T03
parent: S02
milestone: M006
provides:
  - Standalone POS now supports full interactive cart behavior (add/increment/decrement/remove) with dynamic totals and a coral charge button that reflects computed order value.
key_files:
  - backend/cashier_app/templates/pos.html
  - tests/test_cashier_app_pos_route.py
  - .gsd/milestones/M006/slices/S02/tasks/T03-PLAN.md
  - .gsd/milestones/M006/slices/S02/S02-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - Render cart rows using DOM APIs (`createElement` + `textContent`) instead of string `innerHTML` because product data originates from operator-editable Google Sheets.
patterns_established:
  - Cart state pipeline: `addToCart()` / `updateCartQuantity()` / `removeFromCart()` mutate global `cart` array, then `renderCart()` is the single UI projection point for rows + totals + checkout state.
observability_surfaces:
  - `#order-items`, `.order-item-qty`, `.order-item-subtotal`, `#total-value`, and `#checkout-btn` expose deterministic cart state; render failures log `event=cart_render_failed_ui`; products-fetch failure still surfaces `event=products_fetch_failed_ui` plus `.error-state`.
duration: 1h 34m
verification_result: passed
completed_at: 2026-03-19T06:36:00+08:00
blocker_discovered: false
---

# T03: Build interactive cart and order panel logic

**Shipped interactive POS cart state/rendering in `pos.html` with quantity controls, mathematically correct running totals, and a prominent coral `Charge • ₱X.XX` button.**

## What Happened

I first completed the pre-flight requirement by adding `## Observability Impact` to `.gsd/milestones/M006/slices/S02/tasks/T03-PLAN.md`.

Then I implemented T03 directly in `backend/cashier_app/templates/pos.html`:
- added global `cart` state and cart helpers (`addToCart`, `updateCartQuantity`, `removeFromCart`, `getCartTotals`, `renderCart`),
- wired product cards to add-to-cart (click + keyboard Enter/Space),
- built dynamic order panel rendering with line-item subtotal, quantity controls (`+`, `−`, `×`), and event delegation,
- made subtotal/tax/total/charge-button text update from computed totals on every cart change,
- styled and preserved the coral checkout button as the primary CTA, with enabled/disabled behavior and numeric-stable display.

For safety and maintainability, cart rows are rendered with DOM APIs (`createElement`/`textContent`) rather than HTML string injection.

I also updated `tests/test_cashier_app_pos_route.py` with template-level assertions for the new cart interaction hooks and checkout total text update logic.

Finally, I ran runtime/browser checks for both:
- real backend behavior (current environment still returns `/api/products` 500 and shows error visibility), and
- mocked-success behavior (`/api/products` 200 JSON) to verify required cart interactions and total math end-to-end.

## Verification

- Python tests pass with added cart-template assertions.
- Browser flow confirms login to POS, product grid render (mocked products), and cart actions:
  - click products to add line items,
  - increment/decrement/remove controls update quantities and totals,
  - charge button text mirrors computed total and becomes enabled when cart is non-empty,
  - charge button computed color is coral (`rgb(255, 107, 87)`).
- Slice-level network check confirms `/api/products` requests occur on port 5010 and no `:5003` requests are present.
- Failure visibility remains intact on real backend fetch failure (`500 {"error":"Failed to load products"}` plus UI error state).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m py_compile tests/test_cashier_app_pos_route.py` | 0 | ✅ pass | ~0.2s |
| 2 | `rtk proxy python -m pytest tests/test_cashier_app_pos_route.py -q` | 0 | ✅ pass | 0.87s |
| 3 | `bg_shell start "rtk proxy python backend/cashier_app/app.py" (ready_port=5010)` | 0 | ✅ pass | ~2s |
| 4 | Browser batch: login (`/login` → credentials → Enter) + assert `#products-grid`, `#category-list`, `#checkout-btn` | 0 | ✅ pass | ~4s |
| 5 | `browser_mock_route **/api/products -> 200` + reload + assert products/categories visible | 0 | ✅ pass | ~3s |
| 6 | Browser batch: click Burger, Cola, Burger + assert `Charge • ₱205.50` and cart items visible | 0 | ✅ pass | ~4s |
| 7 | Browser batch: `+` then `−` then remove controls + assert totals (`₱290.50` → `₱205.50` → `₱170.00`) | 0 | ✅ pass | ~5s |
| 8 | `browser_evaluate` cart snapshot (`Burger x2`, subtotal/total `₱170.00`, `chargeDisabled=false`, `checkoutBg=rgb(255, 107, 87)`) | 0 | ✅ pass | ~1s |
| 9 | `browser_clear_routes` + reload + assert `.error-state` + network errors (`GET /api/products -> 500` with JSON error body) | 0 | ✅ pass | ~4s |
| 10 | `browser_evaluate` resource probe (`hasProductsRequest=true`, `hasLegacyPort5003=false`) | 0 | ✅ pass | ~1s |

## Diagnostics

- Cart state inspection surfaces:
  - line items: `.order-item`, `.order-item-name`, `.order-item-qty`, `.order-item-subtotal`
  - totals: `#subtotal-value`, `#tax-value`, `#total-value`
  - checkout state: `#checkout-btn` text + disabled state
- Cart render error telemetry:
  - frontend console event: `event=cart_render_failed_ui`
- Products fetch diagnostics retained from earlier tasks:
  - frontend console event: `event=products_fetch_failed_ui`
  - UI error surface: `.error-state`
  - backend failure shape: `500 {"error":"Failed to load products"}`

## Deviations

- Expanded coverage beyond the plan’s single-file estimate by updating `tests/test_cashier_app_pos_route.py` to include cart-specific template hooks.
- Added one decision record and one knowledge entry to capture the security/maintainability pattern for Sheets-driven cart rendering.

## Known Issues

- In this environment, live Sheets-backed `/api/products` still returns HTTP 500; therefore positive cart interaction verification was executed with a mocked `/api/products` 200 JSON response, while real failure visibility was verified separately.

## Files Created/Modified

- `backend/cashier_app/templates/pos.html` — Implemented interactive cart state + rendering, quantity controls, dynamic totals, and coral charge button behavior.
- `tests/test_cashier_app_pos_route.py` — Added assertions for cart state hooks and checkout total-label update logic in the POS template.
- `.gsd/milestones/M006/slices/S02/tasks/T03-PLAN.md` — Added required `## Observability Impact` section.
- `.gsd/milestones/M006/slices/S02/S02-PLAN.md` — Marked T03 done (`[x]`).
- `.gsd/DECISIONS.md` — Appended D059 (DOM-based cart row rendering for Sheets-driven data).
- `.gsd/KNOWLEDGE.md` — Added non-obvious rule about avoiding `innerHTML` for Sheets-sourced cart content.
