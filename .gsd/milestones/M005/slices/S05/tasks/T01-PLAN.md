---
estimated_steps: 8
estimated_files: 5
---

# T01: Delete nfc_payments.py and scrub NFC dead code from Python backend

**Slice:** S05 — NFC/HCE Cleanup + Rename
**Milestone:** M005

## Description

Delete `backend/nfc_payments.py` entirely. Remove the four NFC route functions from `api_server.py` (lines 572–929: `nfc_register`, `nfc_status`, `nfc_unregister`, `nfc_pay`) along with the NFC import block at the top (lines 29, 34, 47). Remove `complete_sale_nfc()` from `cashier_routes.py` (lines 591–857) and the PhoneUID fallback block from inside `complete_sale()` (lines 376–404). Remove the `socket.on('nfc_payment')` handler and `completeNFCSale()` function from `cashier_index.html`. Clean `arduino_bridge.py` by removing the NFC queue infrastructure (`_QueuedPayment`, `_post_nfc_payment`, `_enqueue_payment`, `_retry_loop`, `_drain_queue`, `queue_status`) and the `NFC|` / `ERROR|` branches from `_parse_line()`, and remove `import queue`.

Run `python -m py_compile` on all three Python files to confirm syntax correctness.

## Steps

1. **Delete `backend/nfc_payments.py`** — `rm backend/nfc_payments.py`. Confirm with `[ ! -f backend/nfc_payments.py ]`.

2. **Remove NFC imports from `api_server.py`** — Remove the try/except block that imports `NFCService` and `ensure_virtual_cards_sheet` from `nfc_payments` (around lines 29–47). Remove the `nfc_service = NFCService() if NFCService else None` initialization line. Run `python -m py_compile backend/api/api_server.py` immediately to confirm the import removal is clean.

3. **Remove four NFC route functions from `api_server.py`** — Delete the entire bodies of `nfc_register()`, `nfc_status()`, `nfc_unregister()`, and `nfc_pay()` including their `@app.route` decorators (lines 572–929). The next function after `nfc_pay` is `get_products()` at line 933 preceded by `# ==================== NEW PHASE 1 ENDPOINTS ====================` — that comment and everything after it must remain. Run `python -m py_compile backend/api/api_server.py` again.

4. **Remove `complete_sale_nfc()` from `cashier_routes.py`** — Delete the entire function from the `@cashier_bp.route` decorator at line 591 through the closing line 857, just before `@cashier_bp.route('/api/queue/status')`. That next route must remain. Run `python -m py_compile backend/dashboard/cashier/cashier_routes.py`.

5. **Remove PhoneUID fallback block from `complete_sale()` in `cashier_routes.py`** — Inside `complete_sale()`, remove the block starting at `if not account_row:` with the `# ── PhoneUID fallback` comment (lines 376–404) through the closing `break`. The *next* `if not account_row:` (line 405 — Card not found 404) must remain — it is the guard that returns 404. Also remove the debug print at line 327: `print("[NFC DEBUG] >>> complete_sale CALLED <<<", flush=True)`. Run `python -m py_compile backend/dashboard/cashier/cashier_routes.py`.

6. **Remove NFC socket handler and function from `cashier_index.html`** — Delete the 3-line block `socket.on('nfc_payment', function(data) { completeNFCSale(data.token); });` (lines 338–340). Delete the entire `async function completeNFCSale(token) { ... }` function (lines 428–460). This is HTML/JS — no `py_compile` needed; confirm with `! grep -q 'completeNFCSale' backend/dashboard/cashier/templates/cashier_index.html`.

7. **Clean `arduino_bridge.py`** — Perform all of the following in a single careful read-then-edit pass:
   - Verify `queue` is only used by `_payment_queue` (no other usages) then remove `import queue` from the imports.
   - Remove module-level constants: `MAX_QUEUE_SIZE`, `RETRY_INTERVAL_SECONDS`, `MAX_RETRIES`, `REQUEST_TIMEOUT_SECONDS`.
   - Delete the `_QueuedPayment` dataclass.
   - In `ArduinoBridge.__init__`, remove the queue + retry thread init lines (the `self._payment_queue`, `self._retry_thread` assignments and the `threading.Thread` call that starts the retry thread).
   - In `_parse_line()`, remove the `if line.startswith("NFC|"):` branch and the `elif line.startswith("ERROR|"):` branch. Update the wire-format docstring to remove NFC/ERROR line descriptions.
   - Delete the four methods: `_post_nfc_payment()`, `_enqueue_payment()`, `_retry_loop()`, `_drain_queue()`, and `queue_status()`.
   - `threading` import must remain — it is still used for `_serial_thread`.
   - Run `python -m py_compile backend/dashboard/arduino_bridge.py`.

8. **Final verification sweep** — Run:
   ```bash
   python -m py_compile backend/api/api_server.py
   python -m py_compile backend/dashboard/cashier/cashier_routes.py
   python -m py_compile backend/dashboard/arduino_bridge.py
   [ ! -f backend/nfc_payments.py ] && echo "nfc_payments.py absent: OK"
   ! grep -q '/api/nfc/' backend/api/api_server.py && echo "no /api/nfc/ routes: OK"
   ! grep -q 'complete_sale_nfc' backend/dashboard/cashier/cashier_routes.py && echo "complete_sale_nfc gone: OK"
   ! grep -q 'nfc_payment' backend/dashboard/cashier/templates/cashier_index.html && echo "nfc_payment socket gone: OK"
   ! grep -q '_post_nfc_payment\|_enqueue_payment\|_drain_queue\|_QueuedPayment' backend/dashboard/arduino_bridge.py && echo "arduino_bridge NFC path gone: OK"
   ```

## Must-Haves

- [ ] `backend/nfc_payments.py` does not exist after this task
- [ ] No `/api/nfc/` routes remain in `api_server.py`
- [ ] No `nfc_payments` import in `api_server.py`
- [ ] `complete_sale_nfc` function is gone from `cashier_routes.py`
- [ ] PhoneUID fallback block (lines 376–404) removed from `complete_sale()` in `cashier_routes.py`; the next `if not account_row:` (404 guard) remains
- [ ] `socket.on('nfc_payment')` and `completeNFCSale()` gone from `cashier_index.html`
- [ ] `_QueuedPayment`, `_post_nfc_payment`, `_enqueue_payment`, `_retry_loop`, `_drain_queue`, `queue_status` all gone from `arduino_bridge.py`
- [ ] `import queue` removed from `arduino_bridge.py`; `import threading` retained
- [ ] `python -m py_compile` exits 0 on `api_server.py`, `cashier_routes.py`, `arduino_bridge.py`

## Verification

- `python -m py_compile backend/api/api_server.py` exits 0
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0
- `python -m py_compile backend/dashboard/arduino_bridge.py` exits 0
- `[ ! -f backend/nfc_payments.py ]` exits 0
- `! grep -q '/api/nfc/' backend/api/api_server.py` exits 0
- `! grep -q 'complete_sale_nfc' backend/dashboard/cashier/cashier_routes.py` exits 0
- `! grep -q 'nfc_payment' backend/dashboard/cashier/templates/cashier_index.html` exits 0
- `! grep -q '_post_nfc_payment\|_QueuedPayment' backend/dashboard/arduino_bridge.py` exits 0

## Observability Impact

- Signals added/changed: `arduino_bridge.py` `_parse_line()` no longer emits NFC-related log lines or socket events; only CARD|, PONG|, and unrecognized-prefix lines remain
- How a future agent inspects this: `bash scripts/verify-m005-s05.sh` checks (written in T03); `python -m py_compile` is the immediate syntax proof
- Failure state exposed: `py_compile` produces a `SyntaxError` with file+line if any edit accidentally removes a `:`, `def`, or closing bracket; grep checks pinpoint exactly which file still contains NFC identifiers

## Inputs

- `backend/nfc_payments.py` — file to delete (entire module)
- `backend/api/api_server.py` — NFC import block at ~lines 29–47; four route functions at ~lines 572–929
- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale_nfc()` at ~lines 591–857; PhoneUID block at ~lines 376–404; debug print at ~line 327
- `backend/dashboard/cashier/templates/cashier_index.html` — `socket.on('nfc_payment')` at ~lines 338–340; `completeNFCSale()` at ~lines 428–460
- `backend/dashboard/arduino_bridge.py` — `_QueuedPayment`, queue constants, NFC methods, `NFC|`/`ERROR|` parse branches

From S03 summary: `/api/nfc/*` routes are confirmed replaced by `/api/qr/*`; `socket.on('qr_payment')` was added to `cashier_index.html` after the `nfc_payment` handler — so the `nfc_payment` handler is definitively dead.

From S04 T02 summary: `updateNfcButtonVisibility()` call sites in `HomeActivity.kt` were removed in S04; the *function definition* was left for S05. The `complete_sale()` PhoneUID fallback block remains because S04 only touched Android/iOS.

## Expected Output

- `backend/nfc_payments.py` — **deleted**
- `backend/api/api_server.py` — NFC imports and four route functions removed; `python -m py_compile` exits 0
- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale_nfc()` and PhoneUID fallback block removed; debug print removed; `python -m py_compile` exits 0
- `backend/dashboard/cashier/templates/cashier_index.html` — NFC socket handler and `completeNFCSale()` removed
- `backend/dashboard/arduino_bridge.py` — NFC delivery infrastructure removed; `import queue` removed; `python -m py_compile` exits 0
