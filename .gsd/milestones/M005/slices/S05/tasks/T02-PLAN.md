---
estimated_steps: 8
estimated_files: 11
---

# T02: Delete NFC Android files and scrub dead code from Android sources

**Slice:** S05 — NFC/HCE Cleanup + Rename
**Milestone:** M005

## Description

Delete the five Android NFC/HCE files. Then remove dead NFC code from six Android source files. The single critical constraint is **`nfc_cancel` string in `strings.xml` must not be deleted** — it is used by `activity_qr_pay.xml` as the Cancel button string.

S04 T02 already removed the `activateNfcPayButton = findViewById(...)` binding and click listener from `HomeActivity.kt` (the layout ID was removed). What remains for S05 in `HomeActivity.kt` is:
- The field declaration `private lateinit var activateNfcPayButton: LinearLayout` (line 39)
- The field declaration `private lateinit var nfcManager: NfcManager` (line 45)
- The `nfcPayLauncher` block (lines 53–59)
- `nfcManager = NfcManager.getInstance(this)` in `onCreate` (line 75)
- Four dead NFC functions: `updateNfcButtonVisibility()`, `onNfcPayClicked()`, `showSetupPinDialog()`, `showPinDialog()` (lines 376–460)

Note: `qrPayLauncher` (lines 61–67) must be preserved — it is the live QR pay launcher wired to `qrPayButton`.

## Steps

1. **Delete the five NFC files:**
   ```bash
   rm mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt
   rm mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt
   rm mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt
   rm mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml
   rm mobile/student_app_v2/app/src/main/res/xml/hce_service.xml
   ```
   Verify: `[ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt ]` exits 0.

2. **Edit `HomeActivity.kt`** — Remove dead NFC members. Read the file first to confirm exact line numbers, then:
   - Remove line 39: `private lateinit var activateNfcPayButton: LinearLayout` (the field declaration)
   - Remove line 45: `private lateinit var nfcManager: NfcManager` (the field declaration)
   - Remove lines 53–59: the `nfcPayLauncher = registerForActivityResult(...)` block. **Do not remove `qrPayLauncher` (lines 61–67) — it is live code.**
   - Remove line 75: `nfcManager = NfcManager.getInstance(this)` from inside `onCreate`
   - Remove the entire NFC section: `updateNfcButtonVisibility()`, `onNfcPayClicked()`, `showSetupPinDialog()`, `showPinDialog()` and the `// ── NFC ─` section comment (lines 376–460)
   - After removal, check if `android.widget.EditText` and `androidx.core.view.isVisible` imports have any remaining usages. If not, remove those specific import lines. (`android.app.Activity` is still used by `qrPayLauncher`'s `registerForActivityResult` result type — leave it.)
   - Verify: `! grep -q 'nfcManager\|nfcPayLauncher\|NfcManager\|updateNfcButtonVisibility' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt`
   - Also confirm `qrPayLauncher` still present: `grep -q 'qrPayLauncher' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt`

3. **Edit `ApiClient.kt`** — Remove the two NFC API declarations from the `BangkoApiService` interface:
   - Remove `@POST("nfc/register") suspend fun registerNfcDevice(...)` (lines ~33–37)
   - Remove `@POST("nfc/unregister") suspend fun unregisterNfcDevice(...)` (lines ~39–43)
   - Verify: `! grep -q 'nfc/register\|nfc/unregister\|registerNfcDevice\|unregisterNfcDevice' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt`

4. **Edit `Models.kt`** — Remove the three NFC data class declarations:
   - Remove `data class NfcDeviceRequest(...)` (lines ~62–65)
   - Remove `data class NfcUnregisterRequest(...)` (lines ~67–70)
   - Remove `data class NfcRegisterResponse(...)` (lines ~71–74)
   - Verify: `! grep -q 'NfcDeviceRequest\|NfcUnregisterRequest\|NfcRegisterResponse' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt`

5. **Edit `AndroidManifest.xml`** — Remove NFC permissions, features, and component declarations:
   - Remove `<uses-permission android:name="android.permission.NFC" />`
   - Remove both `<uses-feature android:name="android.hardware.nfc` ... lines
   - Remove the `<activity android:name=".NfcPayOverlayActivity" ...>` block (lines 58–62)
   - Remove the `<service android:name=".BankoHceService" ...>` block with its intent-filter and meta-data (lines 63–76)
   - The `CAMERA` permission and `QRPayActivity` declaration added in S04 T02 must remain.
   - Verify: `! grep -q 'android.permission.NFC\|BankoHceService\|NfcPayOverlayActivity' mobile/student_app_v2/app/src/main/AndroidManifest.xml`

6. **Edit `activity_settings.xml`** — Remove the entire NFC section:
   - The section is marked with `<!-- ── Section: NFC Payment ── -->` and wraps a `<LinearLayout android:id="@+id/nfcSection" ...>` with `android:visibility="gone"` (lines 120–193)
   - Remove the entire block from the comment through the closing `</LinearLayout>`
   - Verify: `! grep -q 'nfcSection\|nfc_pay_setup_title' mobile/student_app_v2/app/src/main/res/layout/activity_settings.xml`

7. **Edit `strings.xml`** — Remove NFC strings. Critical constraint: **DO NOT remove `nfc_cancel`** — it is referenced by `activity_qr_pay.xml` Cancel button.
   - Read the file first to confirm current line numbers.
   - Remove `action_nfc_pay` string (line ~20)
   - Remove the `<!-- NFC -->` section comment and all `nfc_*` strings **except `nfc_cancel`**: specifically remove `nfc_setup_title`, `nfc_setup_message`, `nfc_pin_setup_title`, `nfc_pin_setup_message`, `nfc_pin_verify_title`, `nfc_pin_verify_message`, `nfc_pay_title`, `nfc_pay_scanning`, `nfc_pay_success`, `nfc_pay_error` (lines ~43–53)
   - Remove `<!-- HCE Service -->` section comment and `hce_service_description`, `hce_aid_description` strings (lines ~61–63)
   - Remove `nfc_receipt_label` string (line ~66)
   - After all removals, confirm `nfc_cancel` is still present: `grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml`
   - Verify removals: `! grep -q 'action_nfc_pay\|hce_service_description\|nfc_receipt_label' mobile/student_app_v2/app/src/main/res/values/strings.xml`

8. **Final verification sweep:**
   ```bash
   [ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt ] && echo "BankoHceService gone: OK"
   [ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt ] && echo "NfcManager gone: OK"
   [ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt ] && echo "NfcPayOverlayActivity gone: OK"
   [ ! -f mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml ] && echo "activity_nfc_pay_overlay gone: OK"
   [ ! -f mobile/student_app_v2/app/src/main/res/xml/hce_service.xml ] && echo "hce_service.xml gone: OK"
   ! grep -q 'android.permission.NFC' mobile/student_app_v2/app/src/main/AndroidManifest.xml && echo "NFC permission gone: OK"
   ! grep -q 'BankoHceService' mobile/student_app_v2/app/src/main/AndroidManifest.xml && echo "BankoHceService manifest gone: OK"
   ! grep -q 'nfcManager\|NfcManager' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt && echo "HomeActivity NFC gone: OK"
   grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml && echo "nfc_cancel preserved: OK"
   grep -q 'qrPayLauncher' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt && echo "qrPayLauncher preserved: OK"
   ```

## Must-Haves

- [ ] All 5 NFC files deleted (BankoHceService.kt, NfcManager.kt, NfcPayOverlayActivity.kt, activity_nfc_pay_overlay.xml, hce_service.xml)
- [ ] `android.permission.NFC` removed from AndroidManifest.xml
- [ ] `BankoHceService` service block removed from AndroidManifest.xml
- [ ] `NfcPayOverlayActivity` activity block removed from AndroidManifest.xml
- [ ] `nfcManager` field and `nfcPayLauncher` block removed from HomeActivity.kt
- [ ] `updateNfcButtonVisibility`, `onNfcPayClicked`, `showSetupPinDialog`, `showPinDialog` removed from HomeActivity.kt
- [ ] `qrPayLauncher` still present in HomeActivity.kt (live code — must not be removed)
- [ ] NFC API methods removed from ApiClient.kt; NFC data classes removed from Models.kt
- [ ] NFC section removed from activity_settings.xml
- [ ] NFC strings removed from strings.xml; **`nfc_cancel` string preserved**

## Verification

- `[ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt ]` exits 0
- `[ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt ]` exits 0
- `[ ! -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcPayOverlayActivity.kt ]` exits 0
- `[ ! -f mobile/student_app_v2/app/src/main/res/layout/activity_nfc_pay_overlay.xml ]` exits 0
- `[ ! -f mobile/student_app_v2/app/src/main/res/xml/hce_service.xml ]` exits 0
- `! grep -q 'android.permission.NFC' mobile/student_app_v2/app/src/main/AndroidManifest.xml` exits 0
- `! grep -q 'BankoHceService\|NfcPayOverlayActivity' mobile/student_app_v2/app/src/main/AndroidManifest.xml` exits 0
- `! grep -q 'nfcManager\|NfcManager' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` exits 0
- `grep -q 'nfc_cancel' mobile/student_app_v2/app/src/main/res/values/strings.xml` exits 0
- `grep -q 'qrPayLauncher' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` exits 0

## Observability Impact

### What signals change after this task
- **Android build**: Any `R.string.action_nfc_pay`, `R.string.nfc_receipt_label`, `R.id.activateNfcPayButton`, or NFC class references left behind would surface as Kotlin/Android compile errors (unresolved reference). The absence of errors after `./gradlew assembleDebug` confirms the cleanup is complete.
- **AndroidManifest**: `adb shell dumpsys package com.bankongseton.student | grep -i nfc` returns no output after deployment — no NFC intent-filters registered, no HCE service declared.
- **Grep sweep**: `grep -rn 'NfcManager\|BankoHceService\|nfc/register\|activateNfcPayButton' mobile/student_app_v2/app/src/main/` returns 0 lines — any hit means cleanup is incomplete.

### Failure visibility
- Unresolved `R.string.nfc_receipt_label` in `ReceiptActivity.kt` would produce a Kotlin compile error pointing to the exact line.
- Unresolved `R.string.action_nfc_pay` in `activity_home.xml` would cause a resource-linking error at Android build time (AAPT2 step).
- If `nfc_cancel` were accidentally deleted, AAPT2 would fail with `error: resource string/nfc_cancel not found` traced to any layout referencing it.

## Inputs

- S04 T02 summary: `activateNfcPayButton = findViewById(...)` and its click listener were already removed in S04 because the layout ID no longer exists. The *field declaration* `private lateinit var activateNfcPayButton: LinearLayout` and `updateNfcButtonVisibility()` function *body* remain for S05. `updateNfcButtonVisibility()` call sites (in onCreate and onResume) were also removed in S04.
- S04 T02 summary: `nfcPayLauncher` was left intact (declared and still registered). The `qrPayLauncher` (live code) must not be touched.
- Research doc: `nfc_cancel` is referenced by `activity_qr_pay.xml` Cancel button — deleting it causes an Android build error. Leave it.
- Research doc: Lines ~251, ~349, ~363 of `HomeActivity.kt` reference `"nfc"` in debit-type filter lists for displaying historical transactions — these are **not dead code** and must not be removed.
- Research doc: `activity_settings.xml` NFC section already has `android:visibility="gone"` — it was never live in the UI; safe to delete.

## Expected Output

- `BankoHceService.kt`, `NfcManager.kt`, `NfcPayOverlayActivity.kt`, `activity_nfc_pay_overlay.xml`, `hce_service.xml` — **deleted**
- `HomeActivity.kt` — NFC field declarations, `nfcPayLauncher`, NFC `onCreate` init, and four NFC private functions removed; `qrPayLauncher` and `"nfc"` historical-type filter references intact
- `ApiClient.kt` — `registerNfcDevice` and `unregisterNfcDevice` declarations removed
- `Models.kt` — `NfcDeviceRequest`, `NfcUnregisterRequest`, `NfcRegisterResponse` removed
- `AndroidManifest.xml` — NFC permission, features, activity, and service declarations removed; CAMERA permission and QRPayActivity intact
- `activity_settings.xml` — NFC section block removed
- `strings.xml` — NFC strings removed; `nfc_cancel` preserved
