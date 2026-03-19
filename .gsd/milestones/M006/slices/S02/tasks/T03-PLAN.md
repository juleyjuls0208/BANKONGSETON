---
estimated_steps: 4
estimated_files: 1
---

# T03: Build interactive cart and order panel logic

**Slice:** S02 — New POS UI — product grid and order panel
**Milestone:** M006

## Description

Complete the right-side order panel of the POS UI. Build the JavaScript logic to maintain a `cart` array. Wire up click listeners on the product cards to add items to the cart or increment their quantity if already present. Render the cart contents in the right sidebar, including controls to adjust quantities or remove items entirely. Calculate the running grand total dynamically and display it prominently on a coral-colored "Charge" button, matching the specific design requirements for R054.

## Steps

1. In `pos.html`, define a global JavaScript `cart` array and an `addToCart(product)` function attached to the click event of the product grid cards.
2. Build a `renderCart()` function that takes the `cart` array and injects HTML into the right-side order panel, listing item names, quantities, individual prices, and subotals.
3. Add increment `(+)`, decrement `(-)`, and remove `(x)` buttons for each line item in the cart, and wire them to update the `cart` state and trigger a re-render.
4. Calculate the grand total during `renderCart()` and update the main checkout button. Style this button prominently with a coral background color.

## Must-Haves

- [ ] Clicking a product adds it to the right-side cart.
- [ ] Cart allows modifying item quantities and removing items.
- [ ] Cart total mathematically matches the items.
- [ ] Checkout button is styled prominently with a coral color.

## Verification

- Click multiple products in the grid.
- Verify they appear in the cart panel.
- Verify the total updates accurately.
- Click `+` and `-` on a cart item and verify the quantity and total adjust correctly.
- Verify the Charge button reflects the total and has the required coral color.

## Inputs

- `backend/cashier_app/templates/pos.html` — Contains the product grid from T02.

## Expected Output

- `backend/cashier_app/templates/pos.html` — Updated with cart state management, DOM rendering for the order panel, and the coral Charge button.

## Observability Impact

- **Signals changed:** Frontend now emits deterministic cart UI state via `.order-item` rows, quantity controls, and a `Charge • ₱X.XX` button label that mirrors computed total.
- **How to inspect:** Use browser DOM inspection (`.order-items`, `.order-item-qty`, `.order-item-subtotal`, `#checkout-btn`) and runtime checks after click events on `.product-card` and cart controls.
- **Failure visibility:** Quantity/total mismatches become visible immediately in the order panel and charge button value; cart-action errors are surfaced via `console.error('event=cart_render_failed_ui', ...)` if render/update fails.