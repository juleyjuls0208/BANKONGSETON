# S03: Payment flows — RFID, QR, NFC — UAT

**Milestone:** M006
**Written:** 2026-03-19

## UAT Type

- UAT mode: mixed
- Why this mode is sufficient: This slice combines backend contract behavior (covered by route tests) and cashier UX state transitions (verified in live browser runtime). Hardware/student triggers were simulated where physical devices were unavailable, while standalone endpoint traffic and no-`:5003` isolation were verified live.

## Preconditions

1. Run standalone cashier app only (admin dashboard process off):
   - `SERVER_URL=http://localhost:5010 ARDUINO_API_KEY=uat-key rtk proxy python backend/cashier_app/app.py`
2. App is reachable at `http://localhost:5010`.
3. Cashier credentials available (e.g., seeded default account).
4. Browser tooling available for assertions and (if needed) SocketIO callback simulation.
5. For deterministic UI success-path checks in constrained environments, mock:
   - `**/api/complete-sale` → 200 `{success:true,...}`
   - `**/api/complete-sale-nfc` → 200 `{success:true,...}`

## Smoke Test

Login at `http://localhost:5010/login`, redirect to POS, add one item, and confirm the Charge button becomes actionable with payment controls/status panels visible.

## Test Cases

### 1. RFID checkout orchestration + cancellation

1. Log in as cashier and open POS.
2. Add one product to cart.
3. Select RFID payment method.
4. Click `#checkout-btn`.
5. **Expected:** `#payment-status` shows waiting-for-card state; cancel button enables.
6. Click `#cancel-sale-btn`.
7. **Expected:** `#payment-status` becomes cancelled, cancel button disables, cart remains intact for retry.
8. Click `#checkout-btn` again (RFID).
9. Simulate hardware callback:
   - `(window.cashierSocket._callbacks.$card_read||[]).forEach(fn => fn({success:true, uid:'5F6E7D8C'}))`
10. **Expected:** UI progresses through completion state and returns to ready state; cart clears after successful completion path.

### 2. QR generate + completion lifecycle

1. Add one product to cart.
2. Select QR payment method.
3. Click `#checkout-btn`.
4. **Expected:**
   - `#payment-status` shows waiting for student confirmation.
   - `#qr-token-status` shows active token.
   - `#qr-link` populated with `/api/qr/<token>` URL.
5. Simulate student completion callback:
   - `(window.cashierSocket._callbacks.$qr_payment||[]).forEach(fn => fn({success:true, new_balance:420}))`
6. **Expected:** Payment success text shown, cart clears, ready-to-charge state restored.

### 3. NFC-compatible checkout path

1. Add one product to cart.
2. Select NFC method (`#payment-method-nfc`).
3. Enter token in `#nfc-token-input`.
4. Click `#checkout-btn`.
5. **Expected:** NFC completion request path executes and UI returns to success/ready state with cleared cart.

### 4. Standalone isolation + required route traffic

1. Execute all three payment flows above in a single session.
2. Run browser assertions for request presence:
   - `/api/process-sale`
   - `/api/complete-sale`
   - `/api/qr-generate`
   - `/api/complete-sale-nfc`
   - `/api/cancel-sale`
   - `/api/queue/status`
   - `/api/arduino/wifi-status`
3. Evaluate resource entries:
   - `performance.getEntriesByType('resource').map(e => e.name)`
4. **Expected:** No resource URL contains `:5003`; API traffic stays on `localhost:5010`.

## Edge Cases

### Arduino WiFi status transition visibility

1. While POS is open, inspect `#wifi-status-badge` and `#wifi-status` (initially offline if no heartbeat).
2. Simulate heartbeat socket event:
   - `(window.cashierSocket._callbacks.$arduino_wifi_status||[]).forEach(fn => fn({online:true,state:'online',last_seen_s:0}))`
3. **Expected:** Badge/status flips to online with fresh heartbeat text.

### Queue observability when no pending writes

1. Inspect `#queue-status` after page load.
2. Click `#sync-queue-btn` when enabled (or observe disabled state when queue empty).
3. **Expected:** Queue counters are visible and coherent (`pending/failed/synced`), with no fatal UI errors.

## Failure Signals

- Login succeeds but POS fetches redirect/loop to `/login` unexpectedly.
- `#checkout-btn` does not transition payment status for selected method.
- Missing SocketIO handlers cause stuck states (waiting-card/waiting-qr never resolves/cancels).
- `/api/process-sale` or method-specific routes are absent from runtime request log.
- Any resource request points to `:5003` (breaks standalone isolation).
- WiFi/queue diagnostic surfaces are missing or static despite status events.

## Not Proven By This UAT

- Fully live non-mocked successful RFID and NFC debits against production-like Sheets data.
- Physical Arduino R4 card-read POST + API-key path execution in this harness (requires hardware-inclusive operator run).
- Student mobile QR scanner UX itself (Android/iOS camera scan journey is outside this cashier-focused UAT script).

## Notes for Tester

- If hardware is unavailable, use callback simulation for deterministic SocketIO phase checks; this is an accepted fallback pattern for standalone cashier UAT.
- Keep admin dashboard process off during all checks; this UAT specifically proves standalone behavior.
- If product loading fails due Sheets outage, capture failure evidence, then run deterministic route mocks to continue validating POS orchestration wiring.
