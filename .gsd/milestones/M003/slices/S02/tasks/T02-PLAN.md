---
estimated_steps: 5
estimated_files: 2
---

# T02: Wire frontend NFC handler and write verify script

**Slice:** S02 — Phone NFC Cashier Payment
**Milestone:** M003

## Description

Add the two missing frontend pieces in `cashier_index.html` that make the `nfc_payment` socket event trigger a real sale: a `socket.on('nfc_payment', ...)` listener in `initWebSocket()` and an `async function completeNFCSale(token)` that calls the new backend endpoint. Then write `scripts/verify-s02.sh` — the slice's objective stopping condition — which runs 9 structural grep checks across both files.

The JS additions are modeled directly on the existing `card_read` handler and `completeSale()` function. `completeNFCSale()` must not check `arduinoConnected` (it is an inbound event, not an outbound action), and must open the payment modal if it isn't already open (phone tap can arrive before checkout is initiated).

## Steps

1. In `cashier_index.html`, locate `initWebSocket()` — specifically the `socket.on('card_error', ...)` handler at line ~299. Insert the new listener immediately after it, before the closing `}` of `initWebSocket()`:

   ```javascript
   socket.on('nfc_payment', function(data) {
       completeNFCSale(data.token);
   });
   ```

2. Locate `completeSale(cardUid)` at line ~344. Insert `completeNFCSale(token)` immediately after the closing `}` of `completeSale`:

   ```javascript
   async function completeNFCSale(token) {
       // Ensure modal is visible — NFC tap may arrive before cashier opens checkout
       var modal = document.getElementById('paymentModal');
       if (modal.style.display !== 'flex') {
           modal.style.display = 'flex';
           document.getElementById('modalTitle').textContent = 'NFC Payment';
           document.getElementById('modalMessage').textContent = 'Processing phone tap...';
       }
       try {
           const response = await fetch('/cashier/api/complete-sale-nfc', {
               method: 'POST',
               headers: {'Content-Type': 'application/json'},
               body: JSON.stringify({virtual_card_token: token})
           });
           const data = await response.json();
           if (data.error) {
               document.getElementById('modalTitle').textContent = 'Payment Failed';
               document.getElementById('modalMessage').textContent = data.error;
           } else {
               const offlineNote = data.offline ? ' (Offline \u2014 will sync)' : '';
               document.getElementById('modalTitle').textContent = 'Success!';
               document.getElementById('modalMessage').textContent =
                   'NFC Payment received!\nNew Balance: \u20B1' + data.new_balance.toFixed(2) + offlineNote;
               cart = [];
               renderCart();
               checkQueueStatus();
               setTimeout(function() { closeModal(); }, 2000);
           }
       } catch (error) {
           document.getElementById('modalTitle').textContent = 'Error';
           document.getElementById('modalMessage').textContent = error.message;
       }
   }
   ```

3. Confirm `completeNFCSale` does **not** reference `arduinoConnected` anywhere in its body (it is an inbound handler, not gated on connection state).

4. Write `scripts/verify-s02.sh` with 9 checks — follow the `check()` / `check_absent()` / summary pattern from `verify-s01.sh`:

   ```
   CASHIER_PY="backend/dashboard/cashier/cashier_routes.py"
   CASHIER_HTML="backend/dashboard/cashier/templates/cashier_index.html"
   
   (a) complete_sale_nfc function defined                   → grep "def complete_sale_nfc"     $CASHIER_PY
   (b) /api/complete-sale-nfc route registered              → grep "complete-sale-nfc"         $CASHIER_PY
   (c) VirtualCardToken field name present                  → grep "VirtualCardToken"           $CASHIER_PY
   (d) IsActive guard present                               → grep "IsActive"                   $CASHIER_PY
   (e) NFC Purchase transaction label present               → grep "NFC Purchase"               $CASHIER_PY
   (f) flask_session.pop('pending_transaction' present      → grep "pop.*pending_transaction"   $CASHIER_PY
   (g) socket.on('nfc_payment') in cashier UI               → grep "nfc_payment"                $CASHIER_HTML
   (h) completeNFCSale function defined in cashier UI       → grep "function completeNFCSale"   $CASHIER_HTML
   (i) /cashier/api/complete-sale-nfc URL in JS             → grep "complete-sale-nfc"          $CASHIER_HTML
   ```

5. Run verification:
   ```bash
   python -m py_compile backend/dashboard/cashier/cashier_routes.py
   bash scripts/verify-s02.sh
   ```

## Must-Haves

- [ ] `socket.on('nfc_payment', function(data) { completeNFCSale(data.token); });` added inside `initWebSocket()`
- [ ] `async function completeNFCSale(token)` defined immediately after `completeSale()`
- [ ] `completeNFCSale` opens modal if not already open (no silent-drop when called before checkout)
- [ ] `completeNFCSale` posts `{virtual_card_token: token}` to `/cashier/api/complete-sale-nfc`
- [ ] `completeNFCSale` shows `data.error` in modal on failure (not `alert()`, not silent)
- [ ] `completeNFCSale` clears cart and calls `checkQueueStatus()` on success
- [ ] `completeNFCSale` does NOT check `arduinoConnected`
- [ ] `scripts/verify-s02.sh` written; exits 0 (`bash scripts/verify-s02.sh` 9/9 pass)
- [ ] `python -m py_compile backend/dashboard/cashier/cashier_routes.py` still exits 0

## Verification

- `bash scripts/verify-s02.sh` — 9/9 checks must pass; script exits 0
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` — exits 0 (confirms T01 was not disturbed)

## Inputs

- `backend/dashboard/cashier/templates/cashier_index.html:287–303` — `initWebSocket()` block; insert `nfc_payment` handler after `card_error` handler
- `backend/dashboard/cashier/templates/cashier_index.html:344–373` — `completeSale(cardUid)` implementation template for `completeNFCSale(token)`
- `scripts/verify-s01.sh` — style template for verify-s02.sh (check/check_absent functions, exit code logic)
- T01 output: `complete_sale_nfc()` endpoint exists at `/cashier/api/complete-sale-nfc`

## Observability Impact

**Signals added by this task:**
- Browser console: `completeNFCSale` catch block surfaces JS errors (network failures, JSON parse) as visible modal text — not swallowed silently.
- Browser DevTools Network tab: `POST /cashier/api/complete-sale-nfc` XHR appears on every phone tap. Status 200 = success, 400 = no pending / missing token, 401 = bad token / no linked card, 503 = offline queued.
- Modal UI: success shows `New Balance: ₱X.XX`; failure shows `data.error` text (e.g. "Invalid or inactive virtual card token"); offline suffix ` (Offline — will sync)` appears when `data.offline` is true.
- No token value logged client-side — only the response fields are surfaced.

**How a future agent inspects this task:**
- `grep "nfc_payment\|completeNFCSale\|complete-sale-nfc" backend/dashboard/cashier/templates/cashier_index.html` — confirms all three wiring points are present.
- Open browser DevTools → Network → filter `/complete-sale-nfc` after a phone tap simulation.
- `bash scripts/verify-s02.sh` — 9/9 structural grep checks; exit 0 = wired correctly.

**Failure visibility:**
- Missing `socket.on('nfc_payment', ...)`: phone taps are silently dropped — no modal, no network request. Confirmed absent by verify-s02.sh check (g).
- `completeNFCSale` references `arduinoConnected`: phone taps rejected even when socket delivers the event. Guard absence confirmed by `grep "arduinoConnected" completeNFCSale` returning empty.
- Fetch throws (network down): catch block sets modal to `Error` / `error.message` — visible to cashier.

## Expected Output

- `backend/dashboard/cashier/templates/cashier_index.html` — `socket.on('nfc_payment', ...)` added in `initWebSocket()`; `completeNFCSale()` function added after `completeSale()`
- `scripts/verify-s02.sh` — new 9-check grep assertion script; exits 0 on pass
