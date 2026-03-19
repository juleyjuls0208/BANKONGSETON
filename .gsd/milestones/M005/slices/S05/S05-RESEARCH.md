# S05: NFC/HCE Cleanup + Rename — Research

**Date:** 2026-03-18
**Slice:** S05 — NFC/HCE Cleanup + Rename
**Risk:** Low
**Depends on:** S01 (R3 firmware clean — confirmed), S03 (NFC routes replaced by QR), S04 (Android + iOS not importing NFC files)

## Summary

S05 is a pure deletion + dead-code cleanup slice. Every file to delete and every code block to remove has been catalogued below by reading the actual sources. No new code is written except the verify script. Both apps currently build with all NFC/HCE files still present (S04 passed its verify script while those files existed), so the dependency chain is: **delete the files → remove the call-sites → apps still build → py_compile exits 0 → verify script passes**.

The scope is wider than the roadmap bullet suggests. In addition to the named Kotlin files and Python files, `arduino_bridge.py` contains a significant NFC delivery path (`_post_nfc_payment`, `_enqueue_payment`, `_retry_loop`, `_drain_queue`, `_QueuedPayment`) that is dead once S03/S04 replace the NFC path with QR. The roadmap doesn't name `arduino_bridge.py` but it must be cleaned to remove the NFC socket event (`nfc_payment`) and associated delivery infrastructure.

Also wider: `HomeActivity.kt` contains NFC dead code (field declarations, `updateNfcButtonVisibility`, `onNfcPayClicked`, `showSetupPinDialog`, `showPinDialog`, `nfcPayLauncher`) that must be removed along with the NFC Kotlin files. `ApiClient.kt` and `Models.kt` have NFC API declarations. `activity_settings.xml` has an NFC section. `strings.xml` has NFC strings. These are all safe deletions — no live code references them.

The iOS changes are minimal: only comment text and display-string handling for the `"nfc"` transaction type needs updating.

## Recommendation

Decompose into three tasks:

1. **Python backend cleanup** — delete `nfc_payments.py`; remove 4 NFC routes from `api_server.py`; remove `complete_sale_nfc()` from `cashier_routes.py`; remove PhoneUID fallback block from `complete_sale()`; clean `arduino_bridge.py` NFC path; run `py_compile` to confirm.

2. **Android cleanup** — delete 3 Kotlin files + 2 XML resource files; remove dead NFC code from `HomeActivity.kt`; remove NFC API declarations from `ApiClient.kt` and `Models.kt`; remove NFC section from `activity_settings.xml`; remove NFC strings from `strings.xml`; remove NFC permission/feature declarations from `AndroidManifest.xml`; remove NFC activity + service declarations from `AndroidManifest.xml`.

3. **iOS + verify script** — update display-string handling for `"nfc"` type in `TransactionRowView.swift` and `ReceiptView.swift`; write `scripts/verify-m005-s05.sh`; confirm `py_compile` exits 0.

## Implementation Landscape

### Key Files

#### Delete entirely
- `backend/nfc_payments.py` — VirtualCard, NFCPaymentManager, NFCService classes; entire file
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` — HCE APDU service
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt` — virtual card registration, pin/biometric auth
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt` — NFC tap UI
- `mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml` — NFC tap layout
- `mobile/student_app_v2/app/src/main/res/xml/hce_service.xml` — HCE AID descriptor

#### backend/api/api_server.py
- **Lines 29, 34, 47** — `from nfc_payments import NFCService, ensure_virtual_cards_sheet` try/except block; `nfc_service = NFCService() if NFCService else None`. Remove all three.
- **Lines 572–929** — four complete route functions: `nfc_register()` (572–628), `nfc_status()` (629–682), `nfc_unregister()` (683–731), `nfc_pay()` (732–929). Remove all four. The next function after `nfc_pay` is `get_products()` at line 933 (preceded by `# ==================== NEW PHASE 1 ENDPOINTS ====================`).
- **Lines 647, 706** — inline `from nfc_payments import ensure_virtual_cards_sheet` inside `nfc_status` and `nfc_unregister` — removed as part of removing those functions.

#### backend/dashboard/cashier/cashier_routes.py
- **Lines 591–857** — entire `complete_sale_nfc()` route function. Route decorator at 591, function body ends at 857 just before `@cashier_bp.route('/api/queue/status')`.
- **Lines 376–404** — PhoneUID fallback block inside `complete_sale()`. The block is `if not account_row:` followed by `# ── PhoneUID fallback` comment block through the nested `if vc_match:` section. Remove from `if not account_row:` (line 376) through the closing `break` at line 404. The next `if not account_row:` (line 405 — Card not found 404) must remain.
- **Line 327** — `print("[NFC DEBUG] >>> complete_sale CALLED <<<", flush=True)` debug print — remove.

#### backend/dashboard/arduino_bridge.py
Full NFC delivery infrastructure must be removed:
- **Module docstring** (lines 1–11) — update to describe CARD/PONG-only protocol; remove NFC references
- **Module-level constants** (lines 30–34): `MAX_QUEUE_SIZE`, `RETRY_INTERVAL_SECONDS`, `MAX_RETRIES`, `REQUEST_TIMEOUT_SECONDS` — remove all four
- **`_QueuedPayment` class** (lines 37–48) — delete entirely
- **`ArduinoBridge.__init__`** — remove lines 59–65 (queue + retry thread init)
- **`_parse_line()`** (lines 107–143) — remove the `if line.startswith("NFC|"):` branch (lines 117–127) and the `elif line.startswith("ERROR|"):` branch (lines 139–143); update wire-format docstring comment to remove NFC/ERROR lines
- **`_post_nfc_payment()`** (lines 147–204) — delete entire method
- **`_enqueue_payment()`** (lines 206–239) — delete entire method
- **`_retry_loop()`** (lines 241–245) — delete entire method
- **`_drain_queue()`** (lines 247–302) — delete entire method
- **`queue_status()`** (lines 304–313) — delete entire method (only reports NFC queue depth; nothing calls it except dead code)

> **Note:** `import queue` and `import threading` at top of arduino_bridge.py — `threading` is still needed for `_serial_thread`. `queue` is only used for `_payment_queue`; remove it.

#### backend/dashboard/cashier/templates/cashier_index.html
- **Lines 338–340** — `socket.on('nfc_payment', function(data) { completeNFCSale(data.token); });` — remove entire 3-line block
- **Lines 428–460** — `async function completeNFCSale(token) { ... }` — remove entire function

#### mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt
Dead NFC members to remove (file stays; only dead code removed):
- **Line 39** — `private lateinit var activateNfcPayButton: LinearLayout` field declaration (never initialized via `findViewById`, `updateNfcButtonVisibility()` is never called)
- **Line 45** — `private lateinit var nfcManager: NfcManager` field declaration
- **Lines 53–59** — `private val nfcPayLauncher = registerForActivityResult(...)` block
- **Line 75** — `nfcManager = NfcManager.getInstance(this)` in `onCreate`
- **Lines 376–460** — entire NFC section: `updateNfcButtonVisibility()`, `onNfcPayClicked()`, `showSetupPinDialog()`, `showPinDialog()` — remove all four private functions and the `// ── NFC ─` section comment

Check if any of these imports become unused after removal: `android.app.Activity`, `android.widget.EditText`, `androidx.core.view.isVisible` — if no other usage remains, remove import.

#### mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt
- Remove `@POST("nfc/register") suspend fun registerNfcDevice(...)` (lines ~33–37)
- Remove `@POST("nfc/unregister") suspend fun unregisterNfcDevice(...)` (lines ~39–43)

#### mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt
- Remove `data class NfcDeviceRequest(...)` (lines ~62–65)
- Remove `data class NfcUnregisterRequest(...)` (lines ~67–70)
- Remove `data class NfcRegisterResponse(...)` (lines ~71–74)

#### mobile/student_app_v2/app/src/main/AndroidManifest.xml
- **Lines 9, 11–12** — remove `<uses-permission android:name="android.permission.NFC" />` and both `<uses-feature android:name="android.hardware.nfc*">` lines
- **Lines 58–62** — remove `<activity android:name=".NfcPayOverlayActivity" ...>` declaration
- **Lines 63–76** — remove `<service android:name=".BankoHceService" ...>` block including intent-filter and meta-data

#### mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml
- **Lines 120–193** — remove entire `<!-- ── Section: NFC Payment ── -->` `<LinearLayout android:id="@+id/nfcSection" ...>` block (it already has `android:visibility="gone"` and SettingsActivity.kt never wires any of its IDs)

#### mobile/student_app_v2/app/src/main/res/values/strings.xml
- **Lines 20, 43–53, 61–63, 66** — remove `action_nfc_pay`, all `nfc_*` strings, `<!-- NFC -->` section comment, `<!-- HCE Service -->` section, `hce_service_description`, `hce_aid_description`, `nfc_receipt_label`
- **EXCEPTION:** `nfc_cancel` (line 49) is used by `activity_qr_pay.xml` (Cancel button). **Do not remove it.** Rename it to `action_cancel` or leave as-is; simplest is leave it (it says "Cancel" — no semantic harm). Alternatively rename the string key to `action_cancel` and update the reference in `activity_qr_pay.xml`. Renaming is cleaner but optional.

#### mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt
- **Lines 251, 349, 363** — `"nfc"` in debit-type lists. Keep `"nfc"` in the filter lists for now (it's a historical transaction type in Sheets — existing `"NFC Purchase"` transactions would stop appearing in the budget/history if removed). **Leave these three lines unchanged** — they handle display of existing records, not dead code.
- **Line 116** — `"nfc" -> "NFC Payment"` in `formatTransactionType()` — same reasoning; leave unchanged.

#### iOS — TransactionRowView.swift, ReceiptView.swift, TransactionModels.swift
These files reference `"nfc"` for display/filtering of historical transaction records. The roadmap says "rename to 'QR Payment' display string". The right approach: replace `case "nfc purchase": return "NFC Purchase"` and `case "nfc": return "NFC Payment"` with `case "qr purchase", "nfc purchase": return "QR Purchase"` and `case "qr", "nfc": return "QR Payment"`. This keeps existing NFC transactions readable in the history while using the new terminology for new QR Purchase records.

Changes needed:
- `TransactionRowView.swift` lines 30–31: update `case "nfc purchase"` and `case "nfc"` labels
- `TransactionRowView.swift` line 13: `t == "nfc"` → keep (historical debit type detection; no change needed)
- `ReceiptView.swift` line 55: comment update only (line 4–5 are comments)
- `TransactionModels.swift` line 47: `t == "nfc"` — keep (navigability check; no functional change)

### Build Order

**T01 — Python backend cleanup (do first):** Delete `nfc_payments.py`, remove NFC routes from `api_server.py`, remove `complete_sale_nfc()` from `cashier_routes.py`, remove PhoneUID fallback from `complete_sale()`, clean `arduino_bridge.py`. Run `python -m py_compile` on all three .py files to confirm. This is the highest-value deletion (most dead code by line count) and confirms the Python contract.

**T02 — Android cleanup (do second):** Delete 3 Kotlin + 2 XML files. Edit `HomeActivity.kt`, `ApiClient.kt`, `Models.kt`, `AndroidManifest.xml`, `activity_settings.xml`, `strings.xml`. Android build verification is manual (Gradle build) but grep checks can confirm absence.

**T03 — iOS + verify script:** Update iOS display strings in `TransactionRowView.swift`. Write `scripts/verify-m005-s05.sh`. Run the script.

### Verification Approach

**`python -m py_compile`** on:
- `backend/nfc_payments.py` — should not exist (would fail pre-delete; verifier checks file absence)
- `backend/api/api_server.py` — exits 0 after removing NFC imports and routes
- `backend/dashboard/web_app.py` — exits 0 (no changes needed here)
- `backend/dashboard/cashier/cashier_routes.py` — exits 0 after `complete_sale_nfc` removal
- `backend/dashboard/arduino_bridge.py` — exits 0 after NFC delivery path removal

**Grep absence checks** (verify script):
- `nfc_payments.py` absent: `[ ! -f backend/nfc_payments.py ]`
- NFC Kotlin files absent: `[ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt ]` (same for NfcManager, NfcPayOverlayActivity)
- NFC XML files absent: `[ ! -f mobile/student_app_v2/app/src/main/res/xml/hce_service.xml ]` (same for activity_nfc_pay_overlay.xml)
- No `/api/nfc/` in api_server.py: `grep -qv '/api/nfc/' backend/api/api_server.py` or `! grep -q '/api/nfc/' backend/api/api_server.py`
- No `complete_sale_nfc` in cashier_routes.py
- No `nfc_payment` socket.on in cashier_index.html
- No `android.permission.NFC` in AndroidManifest.xml
- No `BankoHceService` in AndroidManifest.xml
- No `NfcManager` import in HomeActivity.kt
- `nfc_cancel` string still present (used by QR pay cancel button) — or `action_cancel` if renamed

## Constraints

- `nfc_cancel` string in `strings.xml` is referenced by `activity_qr_pay.xml` cancel button — must not be deleted. Either leave the key name as-is or rename it to `action_cancel` and update the XML reference in the same edit.
- Historical `"nfc"` transaction type strings in Android adapter and iOS row view must not remove the type from debit detection lists — existing historical transactions must still display with correct color/sign.
- `complete_sale()` (the main RFID card sale route, ~310 lines) must not be touched beyond removing the PhoneUID fallback block (lines 376–404). The surrounding logic (card UID lookup, balance debit, etc.) is live code.
- `import queue` removal from `arduino_bridge.py` — confirm no other use of `queue` module in that file before removing.

## Common Pitfalls

- **`nfc_cancel` string deletion** — `activity_qr_pay.xml` uses `@string/nfc_cancel` for its Cancel button. Deleting this string will cause an Android build error. Leave it or rename it to `action_cancel` with a matching reference update.
- **`complete_sale()` PhoneUID block scope** — the block starts at `if not account_row:` on line 376 and ends at `break` on line 404. The *next* `if not account_row:` on line 405 (returning 404 Card not found) must remain. Incorrect edit range will silently remove the 404 guard.
- **`arduino_bridge.py` import cleanup** — `queue` module is used only for `_payment_queue`; removing the queue infrastructure without removing `import queue` will leave a dead import (harmless but untidy). Removing `import queue` before verifying no other usages could break something if the module is used elsewhere — check first.
- **nfcPayLauncher in HomeActivity.kt** — `nfcPayLauncher` is used in `onNfcPayClicked()`, `showSetupPinDialog()`, and `showPinDialog()`. All four of those are being deleted together. `qrPayLauncher` (lines 61–67) must be preserved — it is used by `launchQrPay()` which is wired to `qrPayButton.setOnClickListener`.

## Skills Discovered

None required. This is deletion work in known Python, Kotlin, Swift, and XML — no new libraries or unfamiliar APIs.
