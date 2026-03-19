---
estimated_steps: 4
estimated_files: 2
---

# T02: Implement frontend product fetching and rendering

**Slice:** S02 — New POS UI — product grid and order panel
**Milestone:** M006

## Description

Transform the skeleton POS UI from S01 into a modern layout with live data. Fetch the product list from the newly created `/api/products` endpoint. Extract unique categories to dynamically populate the left-hand sidebar. Render the products in a central grid, assigning distinct, appealing background colors to the product cards based on their category (fulfilling D058). Ensure the overall design matches the "modern food-POS aesthetic" (white background, clean fonts, color-coded cards).

## Steps

1. In `pos.html`, write a `fetchProducts()` JavaScript function that calls `/api/products` on page load. Handle 401s by redirecting to `/login`.
2. Process the returned product JSON to extract a list of unique categories and generate the left sidebar navigation items.
3. Map each category to a distinct background color.
4. Render the product cards into the main grid area, displaying product name, price, and using the category-mapped color as the card background.

## Must-Haves

- [ ] `/api/products` is fetched successfully when `pos.html` loads.
- [ ] Sidebar dynamically displays unique categories.
- [ ] Main grid displays product cards colored by their category.
- [ ] 401 Unauthorized responses trigger a redirect to `/login`.

## Verification

- Start the standalone app and log in.
- Open the POS interface.
- Visually verify that products from the spreadsheet appear in the central grid.
- Visually verify that product cards have different colors based on category.
- Visually verify the sidebar lists the categories accurately.

## Inputs

- `backend/cashier_app/templates/pos.html` — The skeleton layout to be populated.
- `backend/cashier_app/routes/pos.py` — The provider of `/api/products`.

## Expected Output

- `backend/cashier_app/templates/pos.html` — Updated with Javascript data fetching, DOM manipulation logic, and required inline CSS/classes for color coding.

## Observability Impact

- Runtime signals: Browser network should show `GET /api/products` with HTTP 200 on successful load; expired/invalid auth should produce 401 handling that redirects to `/login`.
- Inspection surfaces: Sidebar category nodes (`.category-item`) and product grid cards (`.product-card`) should be inspectable in DOM and reflect fetched API payload.
- Failure visibility: Non-401 `/api/products` failures should surface a user-visible error message in the products area, while backend logs remain the source for Sheets exception details.