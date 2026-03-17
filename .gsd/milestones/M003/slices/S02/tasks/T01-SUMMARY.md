---
id: T01
parent: S02
milestone: M003
provides:
  - POST /cashier/api/complete-sale-nfc endpoint with VirtualCards token resolution
key_files:
  - backend/dashboard/cashier/cashier_routes.py
key_decisions:
  - Direct string match for MoneyCardNumber in Money Accounts loop (no normalize_card_uid); VirtualCards stores the canonical form already
  - matched_user initialized before email try-block so SMS/FCM tail can reference it even when email fails — mirrors complete_sale() behaviour
patterns_established:
  - VirtualCards token → MoneyCardNumber → Money Accounts debit chain (three-step, same retry/rollback as physical card path)
observability_surfaces:
  - "event=nfc_sale_complete token_len=N card=... total=..." logged at INFO on success
  - "event=nfc_sale_no_pending" logged at WARNING on 400 (no session)
  - "event=offline_queued" / "event=offline_queue_failed" on Sheets exhaustion (inherited from complete_sale() pattern)
  - Flask access log POST /cashier/api/complete-sale-nfc 200/400/401/503
duration: ~25m
verification_result: passed
completed_at: 2026-03-15
blocker_discovered: false
---

# T01: Add `complete_sale_nfc()` backend endpoint

**Added `POST /cashier/api/complete-sale-nfc` — a direct clone of `complete_sale()` that resolves a phone NFC virtual-card token to a MoneyCardNumber via the VirtualCards sheet before debiting the balance.**

## What Happened

Inserted `complete_sale_nfc()` immediately after `complete_sale()` (~235 new lines). The function:

1. Validates `virtual_card_token` presence (400 if missing)
2. Guards against missing session `pending_transaction` (400 + `event=nfc_sale_no_pending`)
3. Looks up the VirtualCards worksheet with `VirtualCardToken` / `IsActive` / `MoneyCardNumber` field names — exact match, direct string compare (no UID normalization needed since VirtualCards stores canonical form)
4. Returns 401 for invalid/inactive token or missing linked card
5. Finds the Money Account row using direct `money_card_number` string match
6. Runs the identical 3-attempt retry loop with 2s/4s exponential backoff, rollback on exhaustion, and offline-queue fallback
7. Pops `pending_transaction` from session immediately after successful debit break (replay prevention)
8. Logs `event=nfc_sale_complete token_len=N card=... total=...` (token value never logged)
9. Runs email / SMS / FCM notification tail — all lookups use `money_card_number` not the token
10. Returns `{success, new_balance, timestamp}` (plus `offline: true` on queue fallback)

Transaction row column 2 is `'NFC Purchase'`, all other columns identical to `complete_sale()`.

## Verification

```
python -m py_compile backend/dashboard/cashier/cashier_routes.py  → OK (no output)

PASS: complete_sale_nfc
PASS: complete-sale-nfc
PASS: VirtualCardToken
PASS: IsActive
PASS: NFC Purchase
PASS: nfc_sale_no_pending
PASS: nfc_sale_complete
PASS: token_len
PASS: flask_session.pop pending_transaction
```

All 9 structural grep checks pass. py_compile exits 0.

## Diagnostics

- `grep "nfc_sale" server.log` — finds success and no-pending events
- `grep "complete_sale_nfc attempt" server.log` — Sheets retry warnings
- Response body on 400: `{"error": "No pending transaction"}` (missing session)
- Response body on 400: `{"error": "virtual_card_token required"}` (empty POST)
- Response body on 401: `{"error": "Invalid or inactive virtual card token"}`
- Response body on 401: `{"error": "Virtual card has no linked money card"}`
- Offline fallback: `offline: true` in JSON response + `event=offline_queued` in log

## Deviations

none — implementation follows the task plan exactly.

## Known Issues

none

## Files Created/Modified

- `backend/dashboard/cashier/cashier_routes.py` — added `complete_sale_nfc()` (~235 lines) after `complete_sale()`; py_compile clean
