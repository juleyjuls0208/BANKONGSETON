# S02: New POS UI — product grid and order panel

**Goal:** Implement the product grid and order panel components of the standalone cashier app, connecting to Google Sheets to load products dynamically.
**Demo:** Cashier opens `localhost:5010`, logs in, sees a fully styled POS UI matching the modern design (white background, category sidebar, color-coded product cards, coral Charge button). Clicking items adds them to the cart and updates the total.

## Must-Haves

- Fetch products from Google Sheets via a new `/api/products` route, utilizing cache fallback
- Protect the new API route with the `jwt_cookie_required` decorator
- Render a category sidebar dynamically based on loaded products
- Render color-coded product cards in a central grid
- Interactive cart on the right side: add items, update quantities, dynamic total calculation
- The "Charge" button must activate and reflect the total amount

## Proof Level

- This slice proves: integration
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- Start the standalone app: `python backend/cashier_app/app.py`
- Open `http://localhost:5010`, login, and observe the main POS UI loads products grouped by category.
- Verify clicking product cards adds them to the cart and updates the total correctly.
- Verify the network tab shows `/api/products` requests returning JSON and no calls to port 5003.

## Observability / Diagnostics

- Runtime signals: HTTP 200 for `/api/products`, error logging if Sheets fetch fails.
- Inspection surfaces: Browser Network tab, UI rendering state.
- Failure visibility: UI should show an error message if `/api/products` fails. `backend/cashier_app` logs exception details if Sheets are unreachable.

## Integration Closure

- Upstream surfaces consumed: `get_sheets_client` (Sheets DB), `jwt_cookie_required` (Auth)
- New wiring introduced in this slice: Frontend `fetch()` wired to `/api/products` backend route.
- What remains before the milestone is truly usable end-to-end: Real payment processing (S03).

## Tasks

- [x] **T01: Create backend `/api/products` route** `est:45m`
  - Why: The frontend needs to load the product list from Google Sheets dynamically without contacting the old admin dashboard (port 5003).
  - Files: `backend/cashier_app/routes/pos.py`, `backend/cashier_app/app.py`
  - Do: Create the `pos_bp` blueprint. Implement `GET /api/products` using `jwt_cookie_required`. Read from the "Products" sheet via `get_sheets_client`. Implement the cache fallback pattern (like `cashier_routes.py` D017). Register blueprint in `app.py`.
  - Verify: Start app, login, and access `http://localhost:5010/api/products` directly. Should return JSON list of products.
  - Done when: The `/api/products` endpoint successfully returns the Google Sheets product data as JSON.
- [x] **T02: Implement frontend product fetching and rendering** `est:1h`
  - Why: The POS UI needs to display the products in a modern grid categorized by item type.
  - Files: `backend/cashier_app/templates/pos.html`, `backend/cashier_app/static/css/pos.css` (or inline styles)
  - Do: Add JS to fetch `/api/products`. Parse unique categories for the sidebar. Render products into color-coded cards based on category. Apply "modern food-POS aesthetic" (white bg, clean cards).
  - Verify: Load the POS screen and observe categories in the sidebar and matching products in the main grid.
  - Done when: Products appear on the POS screen colored distinctly by their category, and the sidebar lists all available categories.
- [x] **T03: Build interactive cart and order panel logic** `est:1h`
  - Why: The cashier must be able to assemble an order before processing payment.
  - Files: `backend/cashier_app/templates/pos.html`
  - Do: Add JS click handlers to product cards to add them to a `cart` array. Render cart items in the right-side order panel. Implement quantity increment/decrement/remove. Calculate and display the grand total. Style the prominent coral "Charge" button.
  - Verify: Click multiple items, observe cart updates, modify quantities, and check that the total math is correct.
  - Done when: The cart visually updates with correct items, quantities, and a calculated grand total matching the clicked products.

## Files Likely Touched

- `backend/cashier_app/routes/pos.py`
- `backend/cashier_app/app.py`
- `backend/cashier_app/templates/pos.html`