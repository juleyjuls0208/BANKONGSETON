---
estimated_steps: 4
estimated_files: 3
---

# T01: Create backend `/api/products` route

**Slice:** S02 — New POS UI — product grid and order panel
**Milestone:** M006

## Description

Create the `pos.py` route module to provide the `/api/products` endpoint for the standalone cashier POS. This route reads the product catalog from Google Sheets using the shared `get_sheets_client` function. It must implement the cache fallback pattern (as noted in D017) to degrade gracefully if `cache.py` is unavailable. It also needs to be secured by the `jwt_cookie_required` decorator established in S01. Finally, register this new blueprint with the Flask app in `app.py`.

## Steps

1. Create `backend/cashier_app/routes/pos.py` and set up the `pos_bp` Flask Blueprint.
2. Implement `GET /api/products` guarded by `@jwt_cookie_required`.
3. Inside the route, fetch the "Products" worksheet data using `get_sheets_client()`. Port the cache-fallback logic from `backend/dashboard/cashier/cashier_routes.py` to ensure it gracefully handles missing `cache.py`.
4. Return the products list as JSON.
5. In `backend/cashier_app/app.py`, import and register the `pos_bp`.

## Must-Haves

- [ ] New `pos_bp` blueprint created and registered.
- [ ] `/api/products` route implemented and returns JSON data from Google Sheets.
- [ ] Endpoint is protected with `jwt_cookie_required`.
- [ ] Cache fallback mechanism is in place for resilience.

## Verification

- Start the Flask app using `run_cashier.bat` (or `python backend/cashier_app/app.py`).
- Use a tool like curl or a browser network tab.
- Unauthenticated request to `/api/products` should fail or redirect.
- Authenticated request should return `[{"name": "...", "category": "...", "price": ...}, ...]`

## Observability Impact

- Signals added/changed: Logs any Google Sheets connection errors or cache failure warnings.
- How a future agent inspects this: Terminal output where the Flask app is running.
- Failure state exposed: HTTP 500 or empty list returned on Google Sheets failure.

## Inputs

- `backend/cashier_app/app.py` — Needs blueprint registration.
- `backend/dashboard/cashier/cashier_routes.py` — Reference for the cache-fallback Sheets query logic.
- `backend/cashier_app/routes/auth.py` — Contains the `jwt_cookie_required` decorator.

## Expected Output

- `backend/cashier_app/routes/pos.py` — New file with the `/api/products` route.
- `backend/cashier_app/app.py` — Modified to register `pos_bp`.