# S02: New POS UI — product grid and order panel — UAT

**Milestone:** M006
**Written:** 2026-03-19

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: This slice combines backend contract behavior (`/api/products`) and cashier-facing UI interactions. Real runtime verified auth/failure/isolation behavior, while deterministic mocked payloads verified product/category/cart happy-path rendering and total math.

## Preconditions

- Standalone cashier app is running: `rtk proxy python backend/cashier_app/app.py`.
- Cashier credentials are available (`cashier` / `cashier123` in this environment).
- Browser can open `http://127.0.0.1:5010`.
- For happy-path UI checks when Sheets is unavailable, tester can mock `/api/products` to return stable sample JSON.

## Smoke Test

Open `http://127.0.0.1:5010/login`, sign in as cashier, and confirm POS shell loads with all three regions visible: category sidebar, product grid, and right-side order panel with coral Charge button.

## Test Cases

### 1. Standalone runtime + failure visibility (no admin dependency)

1. Navigate to `http://127.0.0.1:5010/login` and log in as cashier.
2. Let page load with real backend behavior (no route mock).
3. Confirm browser requests include `GET /api/products` on `127.0.0.1:5010`.
4. Confirm no resource requests to `:5003` are present.
5. **Expected:** If Sheets is unavailable, UI shows `Unable to load products` and an `.error-state` message, with response body `{ "error": "Failed to load products" }` and no crash.

### 2. Product hydration + modern visual structure

1. Mock `**/api/products` to return:
   - Burger / Meals / 85
   - Cola / Drinks / 35.5
   - Fries / Snacks / 50
2. Reload POS page.
3. Verify sidebar includes category options derived from payload (`Drinks`, `Meals`, `Snacks`) plus `All`.
4. Verify product cards render in the grid with category labels and prices.
5. **Expected:** Cards display distinct background colors by category, and status line shows item count (e.g., `3 items shown`).

### 3. Cart interactions + live total math + Charge state

1. With mocked products loaded, click Burger, Cola, then Burger again.
2. Verify order panel contains Burger and Cola line items with correct quantities.
3. Verify total and Charge button text become `₱205.50` and `Charge • ₱205.50`.
4. Click increment (`+`) on Burger once; verify total becomes `₱290.50`.
5. Click decrement (`−`) on Burger once; verify total returns to `₱205.50`.
6. Click remove (`×`) on Cola; verify total becomes `₱170.00` and Cola row is removed.
7. **Expected:** Cart controls mutate quantities deterministically, totals remain mathematically correct, and Charge button stays enabled when cart is non-empty.

## Edge Cases

### Unauthorized products API response

1. Mock `**/api/products` to return HTTP 401.
2. Reload POS page after login.
3. **Expected:** Client treats response as unauthenticated and redirects user to `/login`.

## Failure Signals

- POS page loads but category list remains empty without any status/error message.
- Product fetch calls go to `:5003` or any non-5010 backend.
- Clicking product cards does not create order rows or does not update totals.
- Charge button text does not mirror computed total, or remains disabled with non-empty cart.
- Unauthorized `/api/products` does not return cashier to login.

## Not Proven By This UAT

- Live Google Sheets happy-path fetch (HTTP 200 from real `Products` worksheet) in this environment.
- Payment completion flows (RFID/QR/NFC route wiring and sale finalization), which belong to S03.

## Notes for Tester

- In this environment, Sheets may be unreachable (`credentials.json` / connectivity issue), so expect 500 on real `/api/products` and use the mock for positive UI behavior checks.
- The coral Charge button in S02 is a stateful UI control only; clicking it is not yet wired to complete payments.
- If browser network buffer is sparse, use `performance.getEntriesByType('resource')` to confirm `/api/products` and absence of `:5003` requests.
