---
id: S02
parent: M003
milestone: M003
provides:
  - POST /cashier/api/complete-sale-nfc endpoint (VirtualCards token → MoneyCardNumber → balance debit)
  - socket.on('nfc_payment') listener wired in cashier UI initWebSocket()
  - async function completeNFCSale(token) in cashier_index.html
  - scripts/verify-s02.sh — 9-check structural grep assertion script
requires:
  - slice: S01
    provides: httpPostNFC(token) in firmware routes "NFC" prefix to /api/nfc/tap which emits nfc_payment SocketIO event
affects:
  - S03 (WiFi badge / arduinoConnected flag — completeNFCSale already gate-free, no S03 changes needed to the NFC path)
  - S04 (powerbank hardening; nothing in S02 blocks it)
key_files:
  - backend/dashboard/cashier/cashier_routes.py
  - backend/dashboard/cashier/templates/cashier_index.html
  - scripts/verify-s02.sh
key_decisions:
  - Phone NFC token resolution runs inside cashier_routes.py — direct VirtualCards Sheets lookup, no cross-process call to api_server.py (D030)
  - Direct string match for MoneyCardNumber in Money Accounts loop — no normalize_card_uid(); VirtualCards stores the canonical card number; normalization would be wrong here
  - matched_user initialized before email try-block — SMS/FCM tail can reference it even when email lookup fails (mirrors complete_sale() pattern exactly)
  - completeNFCSale does NOT gate on arduinoConnected — it is an inbound socket event handler, not an outbound action; the Arduino's connection state is irrelevant when the phone tap already arrived
  - completeNFCSale opens the payment modal proactively if not already visible — phone tap can arrive before cashier initiates checkout; silent drop must be prevented
patterns_established:
  - Inbound socket event handlers (nfc_payment, card_read) delegate immediately to async fetch functions; no connection-state gating on inbound paths
  - VirtualCards token → MoneyCardNumber → Money Accounts debit: three-step chain, identical retry/rollback logic as physical card path
  - verify-s02.sh follows check()/summary pattern from verify-s01.sh; structural grep only, no runtime server needed
observability_surfaces:
  - "event=nfc_sale_complete token_len=N card=... total=..." logged at INFO on success; token value never logged
  - "event=nfc_sale_no_pending" logged at WARNING on 400 (missing session)
  - Flask access log POST /cashier/api/complete-sale-nfc 200/400/401/503
  - Browser DevTools Network: filter /complete-sale-nfc after phone tap
  - Modal UI: "NFC Payment received! New Balance: ₱X.XX" on success; error text on failure; " (Offline — will sync)" when data.offline is true
  - Diagnostic: grep "nfc_payment\|completeNFCSale\|complete-sale-nfc" backend/dashboard/cashier/templates/cashier_index.html
drill_down_paths:
  - .gsd/milestones/M003/slices/S02/tasks/T01-SUMMARY.md
  - .gsd/milestones/M003/slices/S02/tasks/T02-SUMMARY.md
duration: ~40m (T01: ~25m, T02: ~15m)
verification_result: passed
completed_at: 2026-03-15
---

# S02: Phone NFC Cashier Payment

**Phone NFC payment wired end-to-end at the cashier: `nfc_payment` socket event now calls `completeNFCSale(token)` in the UI, which POSTs to a new `POST /cashier/api/complete-sale-nfc` endpoint that resolves the virtual card token, debits the balance, and returns the same success payload as a physical card tap.**

## What Happened

**T01 — Backend endpoint:** Added `complete_sale_nfc()` (~235 lines) immediately after `complete_sale()` in `cashier_routes.py`. The function is a direct clone of `complete_sale()` with one difference in the lookup chain: instead of matching a physical card UID against Money Accounts directly, it first resolves the `virtual_card_token` through the VirtualCards worksheet (`VirtualCardToken` / `IsActive` / `MoneyCardNumber` field names, exact string match). The resolved `money_card_number` then passes through the identical three-step retry loop (3 attempts, 2s/4s backoff), rollback on exhaustion, offline-queue fallback, session pop for replay prevention, and email/SMS/FCM notification tail. Transaction row column 2 is `'NFC Purchase'`; all other columns match `complete_sale()`. Token value is never logged — only `token_len`.

**T02 — Frontend wiring and verify script:** Added `socket.on('nfc_payment', function(data) { completeNFCSale(data.token); });` inside `initWebSocket()` immediately after the `card_error` handler. Added `async function completeNFCSale(token)` immediately after `completeSale()` — mirrors the fetch/JSON/modal-update structure but POSTs `{virtual_card_token: token}` to `/cashier/api/complete-sale-nfc`, opens the payment modal proactively if not visible (phone tap can arrive before cashier initiates checkout), and never checks `arduinoConnected` (inbound event, not outbound action). Wrote `scripts/verify-s02.sh` with 9 structural grep assertions.

## Verification

```
python -m py_compile backend/dashboard/cashier/cashier_routes.py  → exit 0

bash scripts/verify-s02.sh
  PASS  (a) complete_sale_nfc function defined
  PASS  (b) /api/complete-sale-nfc route registered
  PASS  (c) VirtualCardToken field name present
  PASS  (d) IsActive guard present
  PASS  (e) NFC Purchase transaction label present
  PASS  (f) flask_session.pop('pending_transaction') present
  PASS  (g) socket.on('nfc_payment') in cashier UI
  PASS  (h) completeNFCSale function defined in cashier UI
  PASS  (i) /cashier/api/complete-sale-nfc URL in JS
  Results: 9 passed, 0 failed → exit 0
```

## Requirements Advanced

- R021 — Phone NFC Payment at Cashier: endpoint implemented, event wired, contract verified; advances from "active" toward validation pending live hardware test

## Requirements Validated

- none — R021 requires a live phone tap at real Arduino hardware; contract and structural proof are complete but the runtime proof is deferred to human UAT

## New Requirements Surfaced

- none

## Requirements Invalidated or Re-scoped

- none

## Deviations

none — implementation follows the task plan exactly across both tasks.

## Known Limitations

- Runtime end-to-end (phone tap at Arduino → sale complete → Sheets debit) cannot be verified without deployed hardware. Human UAT is required before R021 is marked validated.
- The `IsActive` check uses `str(row.get('IsActive', '')).upper() == 'TRUE'` — assumes Sheets stores `TRUE`/`FALSE` as a string; if Sheets returns a Python `bool`, the check still works because `str(True).upper() == 'TRUE'`.

## Follow-ups

- S03: WiFi status badge so cashier can see Arduino is online without needing to select a COM port (R022)
- S04: Powerbank hardening + `arduino/README-wireless.md` (R023, R024)
- After S03+S04 deploy: human UAT of phone tap → complete-sale-nfc to mark R021 validated

## Files Created/Modified

- `backend/dashboard/cashier/cashier_routes.py` — added `complete_sale_nfc()` (~235 lines) after `complete_sale()`; py_compile clean
- `backend/dashboard/cashier/templates/cashier_index.html` — added `socket.on('nfc_payment', ...)` in `initWebSocket()`; added `async function completeNFCSale(token)` after `completeSale()`
- `scripts/verify-s02.sh` — new 9-check structural grep assertion script for S02

## Forward Intelligence

### What the next slice should know
- The `nfc_payment` event is emitted by `dashboard_core.py` at line ~2051 — it carries `{token: <string>}`. `completeNFCSale(data.token)` extracts `.token` correctly; no `.uid` field on this event.
- `completeNFCSale` is deliberately gateless on `arduinoConnected`. S03's WiFi badge work should NOT add a guard here — the whole point is that the phone tap already arrived.
- The VirtualCards worksheet lookup uses `VirtualCardToken`, `IsActive`, `MoneyCardNumber` — any VirtualCards schema changes must update `complete_sale_nfc()` and `api_server.py:nfc_pay()` together.

### What's fragile
- VirtualCards sheet field names duplicated in two places (`cashier_routes.py:complete_sale_nfc` and `api_server.py:nfc_pay`) — if a column is renamed in Sheets, both files break; there is no shared constant.
- Offline-queue fallback in `complete_sale_nfc()` queues the debit but the token-to-card resolution result (money_card_number) is embedded in the queued payload — if the VirtualCards row changes between queue and sync, there is no re-resolution.

### Authoritative diagnostics
- `grep "event=nfc_sale" server.log` — finds both success (`nfc_sale_complete`) and no-pending (`nfc_sale_no_pending`) events; fastest first-look signal
- `bash scripts/verify-s02.sh` — confirms the structural wiring is intact after any future edit to cashier_routes.py or cashier_index.html
- Browser DevTools Network → filter `/complete-sale-nfc` — shows the exact request/response for each phone tap during testing

### What assumptions changed
- Original plan assumed the modal would always be open when a phone tap arrives. Actual: phone tap can arrive at any time, so `completeNFCSale` must open the modal proactively — added the `display !== 'flex'` guard.
