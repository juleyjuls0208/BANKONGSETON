# S02: Phone NFC Cashier Payment — UAT

**Milestone:** M003
**Written:** 2026-03-15

## UAT Type

- UAT mode: mixed (artifact-driven contract checks already passed; runtime/human verification required for end-to-end proof)
- Why this mode is sufficient: Contract and structural verification are complete (`py_compile` + `verify-s02.sh` 9/9). Runtime end-to-end proof requires a deployed Arduino + Flask backend + VirtualCards data in Sheets — that is the human UAT gate before R021 is marked validated.

## Preconditions

1. Arduino UNO R4 WiFi flashed with S01 firmware (`httpPostNFC` routes to `/api/nfc/tap`)
2. Flask backend deployed and reachable from the Arduino's LAN IP (same school network)
3. `ARDUINO_API_KEY` in backend `.env` matches the `API_KEY` constant in `secrets.h`
4. Google Sheets has at least one active VirtualCards row: `VirtualCardToken` = a known token string, `IsActive` = `TRUE`, `MoneyCardNumber` = a valid card number linked to a Money Accounts row with sufficient balance
5. A student Android phone with the HCE NFC app installed and provisioned with the above token
6. Cashier logged in at the cashier UI; at least one product in the cart with a non-zero total (so `pending_transaction` is set in session)
7. Browser DevTools Network tab open; filter set to `complete-sale-nfc`

## Smoke Test

Tap the provisioned Android phone at the Arduino PN532 reader → the cashier UI payment modal should open (or update if already open) within 2 seconds and display "NFC Payment received!" with a balance figure. No manual steps between tap and modal — end-to-end is fully automatic.

## Test Cases

### 1. Happy Path — Phone Tap Completes Sale

**Setup:** Cart has one product (e.g., ₱25.00 rice). Student phone token is active and linked to a card with ≥ ₱25.00 balance.

1. Cashier adds product to cart; total shows ₱25.00.
2. Student taps Android phone at Arduino PN532 reader.
3. Arduino firmware POSTs `{"token": "<token>"}` to `/api/nfc/tap` (verify in Flask access log).
4. Backend emits `nfc_payment` SocketIO event to cashier UI.
5. Cashier UI `socket.on('nfc_payment')` fires → calls `completeNFCSale(token)`.
6. `completeNFCSale` POSTs `{"virtual_card_token": "<token>"}` to `/cashier/api/complete-sale-nfc`.
7. **Expected:** Modal shows "Processing phone tap…" then "NFC Payment received!" with `New Balance: ₱<old_balance - 25.00>`.
8. **Expected:** Google Sheets Transactions Log has a new row with transaction type `NFC Purchase`, amount ₱25.00, correct card number.
9. **Expected:** Student's Money Accounts balance reduced by ₱25.00.
10. **Expected:** Parent receives email/SMS notification (if SMTP/Twilio configured).
11. **Expected:** Flask access log shows `POST /cashier/api/complete-sale-nfc 200`.

---

### 2. No Pending Transaction — Phone Tap Arrives Before Cart

**Setup:** Cashier UI is open but no product has been added to the cart (no `pending_transaction` in session).

1. Student taps Android phone at Arduino.
2. `nfc_payment` event fires → `completeNFCSale(token)` called.
3. POST to `/cashier/api/complete-sale-nfc` reaches backend with empty/missing session.
4. **Expected:** Backend returns `{"error": "No pending transaction"}` (HTTP 400).
5. **Expected:** Cashier UI opens payment modal (if not already open) and displays "Payment Failed" with "No pending transaction" error text.
6. **Expected:** No Sheets debit; no transaction row written.
7. **Expected:** Server log contains `event=nfc_sale_no_pending`.

---

### 3. Invalid or Inactive Virtual Card Token

**Setup:** Tap with a token that either doesn't exist in VirtualCards or has `IsActive` = `FALSE`.

1. Cart has a product loaded (pending_transaction in session).
2. Tap phone with an inactive/unknown token at Arduino.
3. **Expected:** Backend returns HTTP 401 `{"error": "Invalid or inactive virtual card token"}`.
4. **Expected:** Modal shows "Payment Failed" with the error text.
5. **Expected:** No balance debit, no Sheets row.
6. **Expected:** Flask log shows `POST /cashier/api/complete-sale-nfc 401`.

---

### 4. Virtual Card Has No Linked Money Card

**Setup:** A VirtualCards row has a valid, active `VirtualCardToken` but `MoneyCardNumber` is blank or not found in Money Accounts.

1. Cart loaded. Tap phone provisioned with this orphaned token.
2. **Expected:** Backend returns HTTP 401 `{"error": "Virtual card has no linked money card"}` (or "Account not found" depending on which guard fires first).
3. **Expected:** Modal shows the error; no debit.

---

### 5. Offline Fallback — Sheets Unreachable

**Setup:** Simulate Sheets unavailable (revoke service account credentials temporarily, or block outbound HTTPS on the test machine). Cart loaded. Phone token is valid.

1. Tap phone at Arduino while Sheets is unreachable.
2. Backend exhausts 3 retry attempts.
3. **Expected:** Response contains `{"offline": true, "new_balance": <last_known>, ...}` — sale queued to SQLite.
4. **Expected:** Modal shows balance with " (Offline — will sync)" suffix.
5. **Expected:** `GET /cashier/api/queue/status` returns `pending_count ≥ 1`.
6. Restore Sheets connectivity.
7. **Expected:** Queue syncs automatically; Sheets transaction row appears; `queue/status` returns `pending_count = 0`.

---

### 6. Replay Prevention — Double Tap

**Setup:** Cart loaded with ₱25.00. Student taps phone once — sale completes.

1. First tap: sale completes. Modal shows "NFC Payment received!" Balance debited.
2. Within the same session, attempt a second POST to `/cashier/api/complete-sale-nfc` with the same token (e.g., repeat the tap or replay the XHR in DevTools).
3. **Expected:** Backend returns HTTP 400 `{"error": "No pending transaction"}` — `flask_session.pop` removed the pending_transaction after the first successful debit.
4. **Expected:** Balance not debited a second time.

---

### 7. Transaction Appears as "NFC Purchase" in Transactions Log (Admin Verification)

1. Complete a successful phone tap sale (Test Case 1).
2. Admin navigates to the Transactions page in the admin dashboard.
3. **Expected:** The new row shows transaction type `NFC Purchase` (not `Card Purchase`, not `NFC Tap`, not blank).
4. **Expected:** All 7 columns are populated (date, type, amount, card number, student name, cashier, station).

## Edge Cases

### Phone Tap Arrives While Modal Is Already Open from a Previous Action

1. Cashier has the payment modal open from a prior card tap result.
2. Student taps phone at Arduino.
3. **Expected:** `completeNFCSale` posts to the endpoint; the modal content updates in-place. No second modal opens. No JS error in console.

### Token Contains Special Characters

1. If a VirtualCardToken was provisioned with base64 characters (`+`, `/`, `=`), tap that phone.
2. **Expected:** Backend receives and looks up the token exactly as-is; no URL-encoding issues in the POST body (payload is JSON, not form-encoded).

### Cashier Not Logged In (JWT Expired)

1. JWT session expires mid-shift.
2. Phone tap arrives → `completeNFCSale` POSTs to endpoint.
3. **Expected:** Backend returns 401/redirect (JWT protection). Modal shows "Payment Failed" with an auth error or network error — NOT a crash.

## Failure Signals

- Modal never opens after phone tap → `nfc_payment` event not reaching cashier UI; check SocketIO connection in browser console
- Modal shows "Payment Failed / No pending transaction" on first tap → cart not loaded before tapping; cashier must add items first
- `POST /cashier/api/complete-sale-nfc 404` → blueprint not registered or route URL typo; run `bash scripts/verify-s02.sh`
- `grep "complete_sale_nfc" server.log` returns nothing → event wiring is broken upstream (check `dashboard_core.py` `/api/nfc/tap` handler)
- Sheets balance not updated but modal shows success → offline queue active; check `GET /cashier/api/queue/status` and wait for sync
- `bash scripts/verify-s02.sh` failure after any edit → structural regression in cashier_routes.py or cashier_index.html

## Requirements Proved By This UAT

- R021 — Phone NFC Payment at Cashier: Test Cases 1–7 together prove the full lifecycle (happy path + failure paths + replay prevention + audit trail)

## Not Proven By This UAT

- R020 (WiFi routing fix) — proved in S01 UAT; S02 consumes S01's output
- R022 (WiFi status badge) — S03 scope; `arduinoConnected` flag for WiFi is not part of this slice
- R023 (powerbank stability) — S04 scope; 30-minute idle + auto-reconnect test deferred
- R024 (wireless deployment docs) — S04 scope
- Sheets service account rotation / credential expiry behavior
- Concurrent phone taps from multiple students at the same station (race condition in session `pending_transaction`)

## Notes for Tester

- **Token value** is never printed in server logs by design — log `token_len` only. If you need to verify the token, check the VirtualCards sheet directly.
- The `IsActive` column must contain exactly `TRUE` (case-insensitive in code, but Sheets checkbox stores `TRUE`/`FALSE` as string when the column is a plain text column, and as boolean when it's a checkbox column). If lookup fails with a valid token, check what `str(IsActive_value).upper()` evaluates to in a quick Python shell.
- Test Case 5 (offline fallback) is the hardest to simulate cleanly — blocking DNS or HTTPS outbound is more reliable than revoking credentials (which takes time to propagate). Alternatively, temporarily set `GOOGLE_SHEETS_CREDENTIALS_FILE` to a nonexistent path and restart Flask.
- The payment modal opens automatically if not already visible when a phone tap arrives. This is intentional — the cashier doesn't need to click anything before handing the phone to the student.
