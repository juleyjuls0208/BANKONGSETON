# M004: NFC Phone Payment Fix — Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

## Project Description

Bangko ng Seton is an RFID-based school money management system. Students pay at the cashier by tapping a physical RFID card or an Android phone (NFC HCE virtual card). The cashier runs a Flask web app on the school LAN; the Arduino UNO R4 WiFi reads cards and posts over WiFi to the backend.

## Why This Milestone

Phone NFC payments are broken 100% of the time. The root cause is confirmed from two independent diagnostic signals:

1. **Serial Monitor**: `APDU ok=NO rspLen=60 lastBytes=34 8` — `inDataExchange` gets no response from the phone's HCE service. `rspLen=60` = unchanged initial buffer size = no bytes received. Arduino falls back to `deliver("087EC8BE", "CARD")`.

2. **Server log**: `[NFC DEBUG] >>> complete_sale CALLED <<<` — NOT `complete_sale_nfc CALLED`. The backend received a `card_read` event with the phone's hardware UID (`087EC8BE`), which is not registered in Money Accounts → 404 "Card not found".

The fix is a firmware retry loop. `inDataExchange` fails on the first attempt because the Android HCE service needs more time after RF field reconnect than the single 150ms pre-delay provides. Retrying up to 3 times with 150ms between each attempt gives HCE up to ~450ms total to initialize after the RF cycle — enough for all known Android HCE implementations.

The backend NFC path (`complete_sale_nfc`) has never been exercised on real hardware. M004/S02 validates it for the first time.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Tap an Android phone at the payment terminal → cashier sees "NFC Payment received! New Balance: ₱X.XX" success modal → Sheets balance row updated with "NFC Purchase" label
- Physical RFID card taps continue working without regression

### Entry point / environment

- Entry point: Cashier initiates a sale; student taps phone at Arduino (powerbank, WiFi, standalone)
- Environment: School LAN; Arduino flashed with updated firmware; Flask backend running
- Live dependencies involved: Arduino UNO R4 WiFi, PN532 NFC module, Android HCE app (student_app_v2), Flask backend (web_app.py, cashier_routes.py), Google Sheets (VirtualCards, Money Accounts, Transactions Log)

## Completion Class

- Contract complete means: `python -m py_compile backend/dashboard/cashier/cashier_routes.py` exits 0; `bash scripts/verify-m004.sh` exits 0 (APDU_MAX_RETRIES constant in firmware, retry loop structure confirmed, py_compile pass)
- Integration complete means: Arduino flashed; phone tap → `APDU ok=YES attempt N/3` in Serial Monitor; Flask log shows `POST /api/nfc/tap 200`; `event=nfc_sale_complete` in server log
- Operational complete means: physical card tap still produces `POST /api/arduino/card-read 200` after firmware change (no regression); phone tap consistently succeeds across ≥2 consecutive attempts

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- Phone tap at standalone Arduino → Serial Monitor shows `APDU ok=YES attempt N/3` → Flask log shows `POST /api/nfc/tap 200` → `[NFC DEBUG] >>> complete_sale_nfc CALLED <<<` in server log → cashier sees "NFC Payment received!" → Sheets balance decremented → Transactions Log row with "NFC Purchase" written
- Physical RFID card tap → Serial Monitor shows `Card detected ... HTTP: delivered — CARD|<uid>` → Flask log shows `POST /api/arduino/card-read 200` → `complete_sale CALLED` → success (no regression)

## Risks and Unknowns

- 3 retries × 150ms = 450ms total budget — sufficient for all tested phones; untested on extremely slow HCE implementations or devices that reinitialize HCE very slowly
- `complete_sale_nfc()` has never been run on real hardware — MoneyCardNumber in VirtualCards might not match Money Accounts for some students; the debug prints (`[NFC DEBUG] raw_money_card=...`) and the D032 alignment fix in S02 address this

## Existing Codebase / Prior Art

- `arduino/bankongseton_rfid/bankongseton_rfid.ino` — APDU exchange at the `inDataExchange` call (~line 621); constants at top of file (HEARTBEAT_INTERVAL_MS pattern to follow); diagnostic Serial prints already present; `deliver()` dispatch by prefix unchanged
- `backend/dashboard/cashier/cashier_routes.py` — `complete_sale_nfc()` function; currently uses `normalize_card_uid()` for Money Accounts lookup (deviates from D032); `[NFC DEBUG]` prints useful during S02 validation, can be cleaned up after
- `backend/dashboard/web_app.py` — `POST /api/nfc/tap` endpoint; emits `nfc_payment` socket event; unchanged in M004
- `scripts/verify-s01.sh`, `verify-s02.sh`, `verify-m003-s03.sh`, `verify-m003-s04.sh` — verify script pattern to follow for new `scripts/verify-m004.sh`

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

- R025 — APDU Retry for Phone NFC Payments (new, owned by M004/S01)
- R021 — Phone NFC Payment at Cashier (advancing from contract-verified to validated in M004/S02)

## Scope

### In Scope

- Add `APDU_MAX_RETRIES=3` and `APDU_RETRY_DELAY_MS=150` constants to firmware
- Wrap `inDataExchange` in a retry loop (reset `responseLength=60` before each attempt; break on success)
- Update Serial diagnostic output to show `attempt N/3` on each try
- Align `complete_sale_nfc()` Money Accounts lookup to D032 (direct string comparison, not normalize_card_uid)
- Write `scripts/verify-m004.sh` (structural verification of firmware constants + py_compile)
- End-to-end hardware validation: phone tap → `complete_sale_nfc` → Sheets debit

### Out of Scope

- Android app changes — HCE service is already correct; issue is entirely firmware-side
- SAK buffer offset investigation — SAK=0x78 triggers APDU attempt correctly; fixing offset is not needed for the bug
- Additional phone models — fix is model-agnostic (retry handles timing variance across all phones)
- `web_app.py` changes — `/api/nfc/tap` endpoint is already correct

## Implementation Decisions

### APDU Retry Loop

- Constants at top of .ino file: `APDU_MAX_RETRIES 3`, `APDU_RETRY_DELAY_MS 150`
- Reset `responseLength = 60` before each `inDataExchange` call (prevents stale length from failed attempt contaminating the nfcTokenOk check)
- Delay fires between attempts only (not before attempt 1 — the existing 150ms pre-delay already handles that)
- Serial output: `"APDU attempt N/3 ok=YES/NO rspLen=N"` — shows exactly which attempt succeeded
- On all attempts exhausted (`apduOk` still false): existing CARD fallback path unchanged

### Backend Alignment (D032)

- `complete_sale_nfc()` Money Accounts lookup: change from `normalize_card_uid()` comparison to direct `str(...).strip() == money_card_number` — matches D032 and mirrors `api_server.py nfc_pay()` reference
- `[NFC DEBUG]` prints in `complete_sale_nfc()`: retain during S02 validation; remove the verbose first-10-records loop once end-to-end is confirmed
