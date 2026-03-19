# S04 Post-Slice Roadmap Assessment

**Verdict: Roadmap is fine. No changes needed.**

## What S04 Delivered

All four tasks completed and verified (12/12 verify-m005-s04.sh checks pass):

- **T01**: JWT token storage wired in both Android (EncryptedSharedPreferences) and iOS (Keychain); `getQrCart`/`confirmQrPayment` API methods added to both apps; CameraX 1.3.1 + ML Kit barcode-scanning 17.2.0 in Android build.gradle.kts.
- **T02**: Full `QRPayActivity.kt` with CameraX+ML Kit scanning, cart confirmation, error handling (402/404/410/401); `qrPayButton` always-visible in HomeActivity replacing hidden NFC button; balance refreshes on `RESULT_OK`.
- **T03**: `QRModels.swift`, `QRPayViewModel.swift`, `QRScannerView.swift` (AVFoundation), `QRPayView.swift`; `HomeView.swift` "Pay with QR" button; full `project.pbxproj` registration with camera usage description in both Debug and Release target configs.
- **T04**: `scripts/verify-m005-s04.sh` — 12/12 pass, exit 0.

## NFC Dead Code Status

NFC dead code was **intentionally retained** in Android per plan: `nfcManager`, `nfcPayLauncher`, `updateNfcButtonVisibility()`, `onNfcPayClicked()`, `showSetupPinDialog()`, `showPinDialog()` field/method declarations are still present but have no active call sites. The `activateNfcPayButton` layout binding was removed (the layout ID was replaced, so leaving the binding would cause NPE at runtime) — this is a minor simplification that reduces S05's cleanup work. `activity_nfc_pay_overlay.xml`, `BankoHceService.kt`, `NfcManager.kt`, `NfcPayOverlayActivity.kt`, `nfc_payments.py`, and all `/api/nfc/*` routes remain untouched, exactly as S05 expects.

## Success Criterion Coverage

All six milestone success criteria have a remaining owner or are already proven by a completed slice:

- Physical RFID card tap at R4 → sale completes → S01 ✓ done
- R4 OLED renders QR within ~1s → S02 ✓ done
- Android QR scan → cart → Confirm → balance debited → S04 ✓ done
- iOS QR scan → cart → Confirm → balance debited → S04 ✓ done
- All HCE/NFC code gone → **S05** (remaining, fully covers this)
- Both apps build clean; `python -m py_compile` exits 0 → **S05** (remaining, fully covers this)

## Requirement Coverage

All active requirements remain covered:

| Req | Status |
|-----|--------|
| R026 RC522 on R4 | S01 done |
| R027 OLED on R4 | S01/S02 done |
| R028 QR polling to OLED | S02 done |
| R029 Backend QR flow | S03 done |
| R030 Android QR scanner | S04 done |
| R031 RC522 on R3 | S01 done |
| R032 Dead NFC/HCE removed | S05 remaining — covered |
| R033 iOS QR scanner | S04 done |

## S05 Remains Unchanged

S05's scope, boundary contracts, and dependency list are exactly as planned. S04 confirmed that Android and iOS QR payment code is in place and not importing NFC/HCE code from active call paths — satisfying S05's stated precondition. S05 can proceed as written.
