# M004: NFC Phone Payment Fix

**Vision:** Fix phone NFC payments at the cashier terminal. The APDU exchange fails 100% because Android HCE service initialization takes longer than the single 150ms pre-delay — `inDataExchange` times out, Arduino falls back to CARD delivery with the phone's hardware UID, and the cashier gets "Card not found." The fix is an APDU retry loop in firmware. Once the APDU succeeds, validate the full backend NFC path on real hardware for the first time.

## Success Criteria

- Student taps Android phone at payment terminal → `APDU ok=YES attempt N/3` in Serial Monitor → `complete_sale_nfc CALLED` in server log (NOT `complete_sale CALLED`) → cashier sees "NFC Payment received! New Balance: ₱X.XX"
- Physical RFID card tap after firmware change still produces success (no regression)
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0

## Key Risks / Unknowns

- APDU retry budget (3 × 150ms = 450ms) may not be enough for very slow HCE implementations — unlikely but unverified on all phone models
- `complete_sale_nfc()` has never been exercised on real hardware — MoneyCardNumber in VirtualCards vs Money Accounts alignment is unproven until S02

## Proof Strategy

- APDU timing → retire in S01 by flashing firmware and seeing `APDU ok=YES attempt N/3` in Serial Monitor on real phone tap
- complete_sale_nfc backend path → retire in S02 by seeing `event=nfc_sale_complete` in server log and success modal in cashier UI

## Verification Classes

- Contract verification: `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0; `bash scripts/verify-m004.sh` exits 0 (APDU_MAX_RETRIES + retry loop in firmware, py_compile pass)
- Integration verification: Arduino flashed; phone tap → `APDU ok=YES attempt N/3` in Serial Monitor; `POST /api/nfc/tap 200` in Flask log; `event=nfc_sale_complete` in server log
- Operational verification: physical RFID card tap after firmware flash → `POST /api/arduino/card-read 200` (regression check)
- UAT / human verification: cashier sees success modal with correct new balance; Sheets Transactions Log has new "NFC Purchase" row

## Milestone Definition of Done

This milestone is complete only when all are true:

- `APDU_MAX_RETRIES=3` and `APDU_RETRY_DELAY_MS=150` constants in firmware; retry loop wraps `inDataExchange`; `APDU attempt N/3 ok=YES/NO` visible in Serial Monitor on phone tap
- `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` appears in server log on phone tap (not `complete_sale CALLED`)
- Cashier UI shows "NFC Payment received! New Balance: ₱X.XX" success modal
- Physical card tap → `complete_sale CALLED` → success (no regression)
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0
- R021 advances to validated; R025 advances to validated

## Requirement Coverage

- Covers: R025 (APDU retry)
- Partially covers: R021 (phone NFC payment) — advances to validated after hardware test in S02
- Leaves for later: R020, R022, R023 (still pending same powerbank/WiFi hardware UAT from M003)
- Orphan risks: none

## Slices

- [x] **S01: Firmware APDU Retry** `risk:high` `depends:[]`
  > After this: flash the updated firmware, tap a phone at the Arduino — Serial Monitor shows `APDU attempt N/3 ok=YES ... HTTP: delivered — NFC|<token>`, confirming the retry loop works and the correct NFC path is taken.

- [ ] **S02: End-to-End Validation + Backend Cleanup** `risk:medium` `depends:[S01]`
  > After this: student taps Android phone at the payment terminal → `complete_sale_nfc CALLED` in server log → cashier sees "NFC Payment received! New Balance: ₱X.XX" → Sheets Transactions Log has a new "NFC Purchase" row.

## Boundary Map

### S01 → S02

Produces:
  `bankongseton_rfid.ino` → `APDU_MAX_RETRIES=3`, `APDU_RETRY_DELAY_MS=150` constants at top of file
  `bankongseton_rfid.ino` → retry loop wrapping `inDataExchange` (up to 3 attempts, 150ms between, reset responseLength=60 before each)
  `bankongseton_rfid.ino` → Serial diagnostic: `"APDU attempt N/3 ok=YES/NO rspLen=N"` on each try
  `scripts/verify-m004.sh` → structural grep: APDU_MAX_RETRIES present, retry loop present, py_compile exit 0

Consumes:
  nothing (root slice)

### S02 consumes from S01

  `bankongseton_rfid.ino` → delivers `NFC|<token>` to `/api/nfc/tap` when APDU succeeds (triggering `nfc_payment` socket event → `completeNFCSale` → `complete_sale_nfc`)
  `bankongseton_rfid.ino` → still delivers `CARD|<uid>` when all retries fail (physical card fallback unchanged — regression test)
