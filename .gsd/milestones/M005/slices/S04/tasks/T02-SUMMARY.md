---
id: T02
parent: S04
milestone: M005
provides:
  - QRPayActivity.kt with CameraX + ML Kit scanning, cart confirmation, and all error code handling (402/404/410/401)
  - activity_qr_pay.xml camera preview + confirmation panel layout
  - activity_home.xml qrPayButton (always-visible, replaces hidden activateNfcPayButton)
  - HomeActivity.kt qrPayLauncher wired to QRPayActivity; balance refreshes on RESULT_OK
  - AndroidManifest.xml CAMERA permission + QRPayActivity declaration
  - strings.xml 4 new QR strings
key_files:
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/QRPayActivity.kt
  - mobile/student_app_v2/app/src/main/res/layout/activity_qr_pay.xml
  - mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt
  - mobile/student_app_v2/app/src/main/res/layout/activity_home.xml
  - mobile/student_app_v2/app/src/main/AndroidManifest.xml
  - mobile/student_app_v2/app/src/main/res/values/strings.xml
key_decisions:
  - NFC dead code (nfcManager, nfcPayLauncher, updateNfcButtonVisibility(), onNfcPayClicked(), showSetupPinDialog(), showPinDialog()) kept as dead code per plan — removal deferred to S05
  - activateNfcPayButton field declaration retained but its findViewById() binding and click listener removed (layout ID gone; would cause NPE at runtime if left)
patterns_established:
  - QR token extraction uses substringAfterLast('/') on the full URL with a /api/qr/ guard to avoid false positives
  - scanning = false flag set synchronously before runOnUiThread to prevent double-scan race conditions
  - qrPayLauncher registered as ActivityResultLauncher; loadBalance() called only on RESULT_OK (not on cancel)
  - All error dialogs dismiss with finish() so the user returns to HomeActivity cleanly
observability_surfaces:
  - Toast "Payment successful!" — on-device confirmation of 200 from confirmQrPayment
  - AlertDialog title "Payment Error" — surfaces 402/401/404/410 as human-readable messages
  - qrPayLauncher.RESULT_OK → loadBalance() chain — updated hero-card balance confirms round-trip succeeded
  - grep 'QRPayActivity' AndroidManifest.xml — confirms activity registration
  - grep 'qrPayButton' HomeActivity.kt — confirms wiring
duration: 45m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T02: Build Android QRPayActivity — CameraX scanner, confirmation UI, HomeActivity wiring

**Created QRPayActivity with CameraX+ML Kit QR scanning, cart confirmation UI, and full error handling; wired always-visible "Scan QR" button in HomeActivity with balance refresh on success.**

## What Happened

Created all 6 files/modifications required by the plan:

1. **`activity_qr_pay.xml`** — FrameLayout with full-screen PreviewView for CameraX, scanning hint TextView overlay, and a NestedScrollView confirmation panel (hidden until QR is scanned) containing cashier name, itemsContainer LinearLayout, total row, Pay Now + Cancel buttons, and a progress indicator.

2. **`strings.xml`** — Added 4 new QR strings: `action_qr_pay` ("Scan QR"), `qr_pay_scanning`, `qr_pay_confirm_title`, `qr_pay_confirm_button` ("Pay Now").

3. **`QRPayActivity.kt`** — Full CameraX + ML Kit scanning activity. Key implementation details:
   - `scanning` boolean flag set to `false` before `runOnUiThread` call to prevent double-scan race
   - Token extracted with `rawValue.trimEnd('/').substringAfterLast('/')` guarded by `rawValue.contains("/api/qr/")`
   - `@OptIn(ExperimentalGetImage::class)` annotation on `processImage` for ML Kit
   - `fetchCart()` calls `secureStorage.getJwtToken()` and shows error dialog if null
   - `showConfirmation()` inflates `item_receipt_line.xml` rows into `itemsContainer`
   - `confirmPayment()` handles 200/402/404/410/401 with specific error messages
   - `setResult(RESULT_OK)` + `finish()` on success; `setResult(RESULT_CANCELED)` on Cancel
   - `cameraExecutor.shutdown()` in `onDestroy()`

4. **`activity_home.xml`** — Replaced `activateNfcPayButton` LinearLayout (was `visibility="gone"`, bluetooth icon, tertiary container color) with `qrPayButton` LinearLayout (always visible, camera icon, secondary container color).

5. **`HomeActivity.kt`** — Added `qrPayButton: LinearLayout` field, `qrPayLauncher` ActivityResultLauncher that calls `loadBalance()` on `RESULT_OK`, `launchQrPay()` method, wired the click listener. Removed the `activateNfcPayButton = findViewById(...)` binding and click listener (the layout ID no longer exists — would NPE at runtime). Removed both `updateNfcButtonVisibility()` call sites (onCreate and onResume). Left all other NFC dead code intact per plan instructions for S05 cleanup.

6. **`AndroidManifest.xml`** — Added `CAMERA` permission, `android.hardware.camera` uses-feature with `required="false"`, and `QRPayActivity` activity declaration with `screenOrientation="portrait"`.

Also applied pre-flight observability fixes: added `## Observability Impact` section to T02-PLAN.md and added failure-state diagnostic verification checks block to S04-PLAN.md.

## Verification

All 5 task verification checks passed:
```
OK: QRPayActivity in manifest
OK: CAMERA permission
OK: qrPayButton in HomeActivity
OK: QRPayActivity.kt exists
OK: activity_qr_pay.xml exists
```

All must-have checks passed:
- All 7 layout IDs present in activity_qr_pay.xml (previewView, confirmPanel, itemsContainer, tvTotal, btnConfirm, btnCancel, progressConfirm)
- scanning flag, substringAfterLast, 402, 410, RESULT_OK, RESULT_CANCELED all present in QRPayActivity.kt
- item_receipt_line.xml inflated in QRPayActivity
- qrPayButton in activity_home.xml; activateNfcPayButton removed from layout
- qrPayLauncher in HomeActivity; updateNfcButtonVisibility() has no call sites (definition only, dead code)
- All 4 QR strings in strings.xml
- No active references to activateNfcPayButton in onCreate/onResume (no NPE crash risk)

Slice-level partial verification: T01+T02 Android checks pass; T03/T04 pending as expected.

## Diagnostics

- **QRPayActivity crashes on launch** → CAMERA permission missing in manifest or CameraX/ML Kit not in build.gradle.kts (T01 incomplete)
- **401 on /api/qr/<token>** → `secureStorage.getJwtToken()` returned null → add `Log.d("JWT","jwt stored: ${secureStorage.getJwtToken() != null}")` in `HomeActivity.onCreate`
- **Blank confirmation panel** → item_receipt_line.xml IDs don't match (itemName/itemQty/itemPrice)
- **qrPayButton not visible** → check activity_home.xml for stale `android:visibility="gone"` (none present after this task)
- **Balance not refreshing** → confirm qrPayLauncher calls `loadBalance()` on `RESULT_OK` (registered before onCreate returns)

## Deviations

The plan stated to leave NFC code as dead code for S05. However, `activateNfcPayButton = findViewById(R.id.activateNfcPayButton)` and its click listener were also removed (not just the `updateNfcButtonVisibility()` calls) because the layout ID no longer exists after the button replacement — leaving the binding would have caused a `NullPointerException` at runtime. The field declaration (`private lateinit var activateNfcPayButton`) and the dead `updateNfcButtonVisibility()` function body are retained for S05 cleanup.

## Known Issues

None.

## Files Created/Modified

- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/QRPayActivity.kt` — NEW: full CameraX+ML Kit QR scanning activity with cart confirmation and error handling
- `mobile/student_app_v2/app/src/main/res/layout/activity_qr_pay.xml` — NEW: camera preview + confirmation panel layout
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt` — added qrPayButton/qrPayLauncher/launchQrPay; removed activateNfcPayButton binding and updateNfcButtonVisibility calls
- `mobile/student_app_v2/app/src/main/res/layout/activity_home.xml` — replaced activateNfcPayButton with qrPayButton (always visible)
- `mobile/student_app_v2/app/src/main/AndroidManifest.xml` — CAMERA permission + QRPayActivity declaration
- `mobile/student_app_v2/app/src/main/res/values/strings.xml` — 4 new QR strings
- `.gsd/milestones/M005/slices/S04/tasks/T02-PLAN.md` — added Observability Impact section (pre-flight fix)
- `.gsd/milestones/M005/slices/S04/S04-PLAN.md` — added failure-state diagnostic checks to Verification (pre-flight fix)
