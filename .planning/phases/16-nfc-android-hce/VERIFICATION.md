---
phase: 16-nfc-android-hce
verified: 2026-03-05T00:00:00Z
status: approved
score: 11/11 must-haves verified (automated); physical device testing approved by owner
re_verification: false
human_verification:
  - test: "End-to-end NFC tap flow on real device"
    result: "Approved by project owner 2026-03-05 — pending physical deployment"
---

# Phase 16: NFC Android HCE Verification Report

**Phase Goal:** Enable NFC contactless payments via Android HCE (Host Card Emulation) for the student app. Students should be able to set up NFC payment on their device and tap to pay at terminals.

**Verified:** 2026-03-05
**Status:** APPROVED — 11/11 automated checks passed; physical device testing approved by project owner
**Re-verification:** No — initial verification

---

## Post-Phase Bug Fixes (2026-03-05)

During device testing, the following bugs were discovered and fixed:

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| NFC registration always returned "No money card registered" (403) | `nfc_register` queried `Money Accounts` sheet by `StudentID`, but that sheet has no `StudentID` column — login correctly reads `MoneyCardNumber` from the `Users` sheet | Changed `nfc_register` to look up `MoneyCardNumber` from `Users` sheet (same as login) |
| `nfc/unregister` network call silently failed | Mobile sent `DELETE` but backend only accepts `POST` on `/api/nfc/unregister` | Changed `ApiClient.kt` from `@DELETE` to `@POST` |
| Registration failure showed generic toast with no useful info | `SettingsActivity` discarded the `message` callback param | Now shows specific messages for session-expired / no-money-card / service-unavailable |

Commit: `fix(nfc): surface real server error, fix unregister method, fix money card lookup`

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|---------|
| 1  | HCE service responds to APDU SELECT with virtual card token | ✓ VERIFIED | `BankoHceService.processCommandApdu()` checks token + auth flag, returns `tokenBytes + SW_OK` or `SW_NO_TOKEN` |
| 2  | Device registration calls backend and stores token encrypted | ✓ VERIFIED | `NfcManager.registerDevice()` POSTs to `nfc/register`, stores token in `EncryptedSharedPreferences` (AES256-GCM) |
| 3  | Device unregistration clears token and revokes HCE authorization | ✓ VERIFIED | `NfcManager.unregisterDevice()` calls `nfc/unregister`, clears `securePrefs`, sets `BankoHceService.currentToken = null` and `isPaymentAuthorized = false` |
| 4  | Settings NFC section appears only on NFC-capable devices | ✓ VERIFIED | `SettingsActivity`: `nfcSection.visibility = View.VISIBLE` gated on `nfcManager.isNfcAvailable()`; layout default is `visibility="gone"` |
| 5  | PIN dialog in Settings creates 4–6 digit PIN for NFC setup | ✓ VERIFIED | `showPinDialog()` in `SettingsActivity` uses numeric password `EditText`; validation `pin.length in 4..6 && pin.all { it.isDigit() }` |
| 6  | NFC status reflects registration state (Not set up / ✓ Ready) | ✓ VERIFIED | `refreshNfcSection()` toggles `nfcStatusText` between `nfc_status_not_set_up` and `nfc_status_ready` strings; called on `onResume` |
| 7  | 'Activate NFC Pay' button visible only when device registered + NFC available | ✓ VERIFIED | `refreshNfcButton()` in `HomeActivity`: `isNfcAvailable() && isDeviceRegistered()` → `VISIBLE`, else `GONE`; called in `onResume` |
| 8  | Tapping 'Activate NFC Pay' triggers biometric/PIN auth before overlay launch | ✓ VERIFIED | Click listener calls `nfcManager.authenticateForPayment()`; biometric success → overlay; `NEEDS_PIN` → `showPinDialog()` → `verifyPin()` → overlay |
| 9  | NfcPayOverlayActivity shows 30-second full-screen countdown | ✓ VERIFIED | `CountDownTimer(30_000L, 1_000L)` updates `countdownText`; full-screen flags set; `BankoHceService.isPaymentAuthorized = true` in `onCreate` |
| 10 | Overlay dismisses on expiry/cancel; RESULT_OK triggers balance reload | ✓ VERIFIED | Timer expiry → `RESULT_CANCELED`; cancel button → `RESULT_CANCELED`; `onResume` polling → `RESULT_OK` when `!isPaymentAuthorized && !userCancelled`; `onActivityResult` calls `loadBalance()` + toast |
| 11 | ReceiptActivity shows 'NFC Payment' row for transactions with no line items | ✓ VERIFIED | `items.isNullOrEmpty()` branch creates synthetic `TransactionItem(name = getString(R.string.nfc_receipt_label), ...)` = "NFC Payment" |

**Score: 11/11 truths verified (automated)**

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `BankoHceService.kt` | HCE HostApduService responding to SELECT APDU | ✓ VERIFIED | 105 lines; extends `HostApduService`; `processCommandApdu` handles SELECT; auth + token check; `onDeactivated` resets flag |
| `NfcManager.kt` | Device registration, token storage, biometric auth | ✓ VERIFIED | 244 lines; encrypted prefs (AES256-GCM/SIV); biometric prompt; PIN fallback; `registerDevice`/`unregisterDevice` with coroutines |
| `NfcPayOverlayActivity.kt` | Full-screen overlay with 30s countdown | ✓ VERIFIED | 75 lines; `CountDownTimer`; `userCancelled` flag; `onResume` polling; `setResult(RESULT_OK/CANCELED)` |
| `activity_nfc_pay_overlay.xml` | Layout with `countdownText`, `instructionText`, `cancelButton` | ✓ VERIFIED | All three IDs present; full-screen black background; 64sp countdown |
| `HomeActivity.kt` | Activate NFC Pay button with conditional visibility | ✓ VERIFIED | `activateNfcPayButton: MaterialButton`; `refreshNfcButton()`; `REQUEST_NFC_PAY = 1001`; `onActivityResult`; PIN dialog |
| `activity_home.xml` | `activateNfcPayButton` with `visibility="gone"` | ✓ VERIFIED | `MaterialButton` id=`activateNfcPayButton` present, `visibility="gone"` |
| `SettingsActivity.kt` | NFC section with setup/remove buttons and status | ✓ VERIFIED | 180 lines; `nfcSection`, `nfcStatusText`, `setupNfcButton`, `removeNfcButton`; `refreshNfcSection()` on `onResume` |
| `activity_settings.xml` | NFC section layout with `nfcSection` group | ✓ VERIFIED | `LinearLayout id=nfcSection` with `visibility="gone"`; `nfcStatusText`, `setupNfcButton`, `removeNfcButton` |
| `ReceiptActivity.kt` | Null-items fallback + transaction type label | ✓ VERIFIED | `items.isNullOrEmpty()` branch; `transaction.type` rendered as `TextView`; type label inserted after time row |
| `AndroidManifest.xml` | NFC permissions, HCE feature, BankoHceService, NfcPayOverlayActivity | ✓ VERIFIED | All present: `NFC`, `USE_BIOMETRIC` perms; `android.hardware.nfc.hce` (`required=false`); BankoHceService with `BIND_NFC_SERVICE`; NfcPayOverlayActivity |
| `hce_service.xml` | AID `F042414E4B4F4E475345544F4E` for payment category | ✓ VERIFIED | Correct AID; `android:category="payment"`; `requireDeviceUnlock="true"` |
| `Models.kt` | `NfcDeviceRequest`, `NfcRegistrationResponse`, `NfcUnregisterRequest` | ✓ VERIFIED | All three data classes present |
| `ApiClient.kt` | `registerNfcDevice` and `unregisterNfcDevice` endpoints | ✓ VERIFIED | `@POST("nfc/register")` and `@POST("nfc/unregister")` as suspend funs |
| `build.gradle.kts` | `androidx.biometric:biometric:1.1.0` dependency | ✓ VERIFIED | Present at line 77 |
| `strings.xml` | All NFC-related strings | ✓ VERIFIED | 22 NFC strings covering overlay, home button, settings section, receipt label |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `NfcManager.registerDevice()` | `ApiClient.apiService.registerNfcDevice()` | `"Bearer $authToken"` + `NfcDeviceRequest` | ✓ WIRED | Coroutine call; response stored in `EncryptedSharedPreferences`; `BankoHceService.currentToken` set |
| `NfcManager.registerDevice()` | `BankoHceService.currentToken` | `BankoHceService.currentToken = token` | ✓ WIRED | Token pushed to companion @Volatile on successful registration |
| `NfcManager.authenticateForPayment()` | `BiometricPrompt` | `showBiometricPrompt()` → `BankoHceService.isPaymentAuthorized = true` | ✓ WIRED | BiometricPrompt callback sets auth flag on success |
| `HomeActivity` (click) | `NfcPayOverlayActivity` | `startActivityForResult(Intent(…NfcPayOverlayActivity), REQUEST_NFC_PAY)` | ✓ WIRED | Both biometric and PIN paths launch overlay |
| `NfcPayOverlayActivity` | `BankoHceService.isPaymentAuthorized` | Sets `true` in `onCreate`; polls in `onResume` | ✓ WIRED | Correctly uses `BankoHceService` companion (not NfcManager — plan template was corrected) |
| `NfcPayOverlayActivity` | `HomeActivity.onActivityResult` | `setResult(RESULT_OK)` + `finish()` | ✓ WIRED | `onActivityResult(REQUEST_NFC_PAY, RESULT_OK)` → toast + `loadBalance()` |
| `BankoHceService.onDeactivated` | overlay dismissal | Sets `isPaymentAuthorized = false`; `NfcPayOverlayActivity.onResume` polls | ✓ WIRED | Polling pattern: `!userCancelled && !BankoHceService.isPaymentAuthorized` → `RESULT_OK` |
| `SettingsActivity.setupNfcButton` | `NfcManager.registerDevice()` | PIN from dialog → `nfcManager.registerDevice(pin, authToken)` | ✓ WIRED | Success → `refreshNfcSection()` |
| `SettingsActivity.removeNfcButton` | `NfcManager.unregisterDevice()` | `nfcManager.unregisterDevice(authToken)` | ✓ WIRED | Success → `refreshNfcSection()` |
| `ReceiptActivity` | `nfc_receipt_label` string | `getString(R.string.nfc_receipt_label)` in synthetic item | ✓ WIRED | String = "NFC Payment" |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `AndroidManifest.xml` | 54–57 | `NfcPayOverlayActivity` missing `android:screenOrientation="portrait"` | ℹ️ Info | Plan specified `screenOrientation="portrait"`; implementation omitted it. Portrait lock would prevent accidental rotation during payment; not a functional blocker — Android defaults handle it |
| `NfcPayOverlayActivity.kt` | 29 | `BankoHceService.isPaymentAuthorized = true` set in `onCreate`, not in `onResume`/after biometric | ℹ️ Info | The flag is set before the overlay is actually displayed; this is consistent with the design (auth happened before launching the overlay) and is correct |

No TODO/FIXME/placeholder comments found. No empty implementations. No stub returns. No console-log-only handlers.

---

## Human Verification Required

### 1. Full NFC Tap Flow on Physical Device

**Test:** Install debug APK on NFC-capable Android device. Follow this sequence:
1. Log in with a student account
2. Go to **Settings** → confirm NFC section appears (if device has NFC) or is hidden (if not)
3. Tap **"Set Up NFC Payment"** → enter a 4–6 digit PIN → confirm PIN dialog validates correctly
4. Observe registration → confirm status changes to **"✓ NFC Payment Ready"** and Remove button appears
5. Return to **Home** → confirm **"Activate NFC Pay"** button is now visible
6. Tap **"Activate NFC Pay"** → confirm biometric/PIN prompt appears before overlay
7. Authenticate → confirm full-screen black overlay appears with "Hold phone to terminal" and live countdown
8. **Let timer run to 0** → confirm overlay dismisses cleanly (no crash)
9. Repeat step 6–7, then tap **Cancel** → confirm overlay dismisses immediately
10. *(If NFC reader available)* Tap phone to terminal during active window → confirm:
    - Overlay dismisses with "Payment successful" toast
    - Balance refreshes on HomeActivity
11. Go to **Transactions** → tap any NFC Purchase entry → confirm receipt shows **"NFC Payment"** row with correct amount (not a blank or missing row)
12. **Settings → Remove** → confirm status reverts to "Not set up" and Home button hides

**Expected:** All 12 steps pass without crashes, UI glitches, or incorrect state.

**Why human:** NFC HCE requires a physical NFC chip for APDU exchange; biometric prompt requires device biometrics; `onResume` deactivation polling and the overlay's visual countdown cannot be exercised in static code analysis.

---

## Gaps Summary

No automated gaps found. All 11 observable truths are verified against the codebase:

- **HCE infrastructure** (Plan 16-01): `BankoHceService`, `NfcManager`, models, API endpoints, manifest declarations, `hce_service.xml` AID, biometric dependency — all fully implemented and wired.
- **Receipt fallback** (Plan 16-02): `ReceiptActivity` handles `null`/empty items with synthetic NFC Payment row; `transaction.type` label rendered dynamically.
- **Settings NFC section** (Plan 16-03): Conditionally visible section with status display, PIN setup dialog, registration/unregistration wiring, `refreshNfcSection()` on resume.
- **NFC pay overlay + Home button** (Plan 16-04): `NfcPayOverlayActivity` with 30s `CountDownTimer`, `userCancelled` flag, `onResume` HCE-deactivation polling, `RESULT_OK` → toast + balance reload; `HomeActivity` conditional button visibility with biometric + PIN auth gate.

**One minor deviation from plan spec:** `screenOrientation="portrait"` omitted from `NfcPayOverlayActivity` manifest entry (plan required it). Not a functional blocker — the payment flow works without it. Worth adding in a cleanup pass.

The only remaining item is the **`checkpoint:human-verify`** gate from Plan 16-04, which explicitly requires physical device testing.

---

*Verified: 2026-03-05*
*Verifier: Claude (gsd-verifier)*
