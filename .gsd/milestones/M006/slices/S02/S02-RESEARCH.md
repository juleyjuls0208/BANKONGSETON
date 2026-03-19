# M006/S02 — Research

**Date:** 2026-03-18

## Summary

The S02 slice involves replacing the structural POS skeleton created in S01 with a functional product grid and order panel that matches the new modern UI design. We need to build the `routes/pos.py` module to fetch products from Google Sheets and build the frontend logic in `templates/pos.html` to render products by category, handle cart addition, and compute totals dynamically. The new UI will feature a category sidebar, a central product grid (color-coded by category), and a right-side order panel with a prominent checkout mechanism. 

S01 established the standalone app structure and auth middleware. S02 builds exclusively on this base, porting the Sheets data fetching logic from the existing dashboard while applying a much more polished visual presentation to the templates without dealing with actual payments just yet (which is reserved for S03).

## Recommendation

Create a new route file (`backend/cashier_app/routes/pos.py`) to serve the products API, migrating the `get_products` functionality from the existing `cashier_routes.py` blueprint but adapting it to standalone standards. Then, implement the full frontend JavaScript in `pos.html` to fetch the products, distinctively color-code them by category, populate the sidebar with unique categories, and construct the interactive cart.

## Implementation Landscape

### Key Files

- `backend/cashier_app/routes/pos.py` (New) — Will provide the `GET /api/products` endpoint. It needs to read from Google Sheets using the shared `get_sheets_client` and implement caching using `cache.py`.
- `backend/cashier_app/app.py` — Needs to register the new `pos_bp` blueprint.
- `backend/cashier_app/templates/pos.html` — Needs full JS logic to fetch `/api/products`, group by category, and render the DOM interactively. The CSS needs to be updated for category color-coding and the coral "Charge" button as mandated by the requirements.
- `backend/dashboard/cashier/cashier_routes.py` (Reference) — Source logic for `get_products` that we will port.

### Build Order

1. **Backend Route (`routes/pos.py`):** Create the blueprint and `GET /api/products` route using the `jwt_cookie_required` decorator from `routes.ui`. Ensure the cache fallback pattern is implemented.
2. **App Registration (`app.py`):** Register the new `pos_bp`.
3. **Frontend UI (`pos.html`):** 
   - Write the fetch routine for `/api/products`.
   - Build the sidebar category generation.
   - Build the color-coded product cards rendering logic.
   - Build the cart state management (add/remove/update qty, compute totals).

### Verification Approach

1. Start the server using `run_cashier.bat`.
2. Login to the POS dashboard.
3. Observe that products are fetched and rendered grouped by categories.
4. Verify clicking items adds them to the right-side cart.
5. Verify the cart totals update accurately.
6. Verify no API calls are made to the old port `5003`.

## Common Pitfalls

- **Missing JWT Auth on API:** The `GET /api/products` route must be protected by the `jwt_cookie_required` (or equivalent) decorator so unauthorized access is blocked, continuing the pattern from S01.
- **Cache Missing Import Fallback:** The Sheets `get_products` function in the old app uses a try/except for `cache.py`. The standalone app should implement the same graceful fallback (as noted in D017).

## Requirements Addressed

- **R053 — Standalone Cashier Web App:** Implements the product grid and order panel components of the standalone app.
- **R054 — Modern POS UI for Cashier:** Implements the white background, category sidebar, color-coded product cards, right-side order panel, and coral Charge button.