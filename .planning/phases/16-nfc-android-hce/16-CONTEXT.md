# Phase 16: NFC Android HCE - Context

**Gathered:** 2026-03-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Integrate Android HCE into `student_app_v2` so students can tap their phone at the cashier terminal to pay. Includes card registration flow, payment authorization UI, and fixing the NFC Purchase receipt in the transactions list. Out of scope: NFC hardware on the cashier/Arduino side.

</domain>

<decisions>
## Implementation Decisions

### App consolidation
- **Target app is `student_app_v2`** (`com.bankongseton.student`) — port NFC code INTO this app, not mobile/android
- Port `BankoHceService.kt` and `NfcManager.kt` from `mobile/android` as-is; update package declaration to `com.bankongseton.student`
- `mobile/android` is archived (kept in repo, receives no further updates)
- NFC hardware is **optional** (`android:required="false"`) — non-NFC devices can still install the app

### Registration entry point
- NFC card setup lives in **SettingsActivity**, added as a new section below dark mode
- On non-NFC devices: **hide the NFC section entirely** (no unavailable message, no dead UI)
- NFC section states:
  - Not registered → show status + "Set Up NFC Payment" button
  - Registered → show "✓ NFC Payment Ready" + "Remove" button (no activate-payment button here)
- Auth method: **PIN set during registration** (4–6 digits); biometric used automatically if device supports it; PIN is the fallback

### Payment authorization UX
- **"Activate NFC Pay" button on HomeActivity** — only shown if device is registered and NFC is enabled
- App must be **open/foreground** for biometric prompt to trigger (standard Android HCE constraint)
- Auth flow: tap button → biometric (or PIN if biometric unavailable) → **30-second active window**
- During active window: **full-screen overlay** showing "Hold phone to terminal" with a live countdown timer
- After HCE deactivation (terminal tap detected): overlay dismisses, **toast "Payment successful" + auto-reload balance**

### NFC Purchase receipt
- Root cause is likely **null items from `/api/nfc/pay`** (not a navigation bug — the adapter already handles NFC Purchase clicks correctly)
- When `items` is null or empty: show a **single synthetic line item row** reading "NFC Payment" with the total amount
- **One shared `ReceiptActivity`** with a null-items fallback — no separate activity
- ReceiptActivity shows the **transaction type label** ("NFC Purchase" vs "Purchase") so students can distinguish payment methods

### Claude's Discretion
- Exact layout/styling of the NFC section in SettingsActivity
- Overlay countdown visual design
- Error handling for registration network failures
- How `NfcManager`'s `ApiClient` usage is reconciled with `student_app_v2`'s singleton `ApiClient`

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `mobile/android/BankoHceService.kt`: Complete HCE service — port as-is, rename package. Handles SELECT APDU, token response, auth flag, 30s reset on deactivation.
- `mobile/android/NfcManager.kt`: Complete token storage (EncryptedSharedPreferences) + biometric prompt + registerDevice/unregisterDevice API calls. Needs package rename + `ApiClient` wiring updated for student_app_v2's API client.
- `mobile/android/AndroidManifest.xml`: Has exact NFC permissions and HCE service declaration to copy into student_app_v2's manifest.
- `student_app_v2/TransactionsAdapter.kt`: Already handles `NFC Purchase` type — color-codes it red and navigates to ReceiptActivity on click. No changes needed.
- `student_app_v2/ReceiptActivity.kt`: Already iterates `transaction.items` for line items. Needs null-items fallback + transaction type label.

### Established Patterns
- `student_app_v2` uses a singleton `ApiClient` object (not the `ApiClient.getInstance(context)` pattern from `mobile/android`) — `NfcManager` must be adapted to use student_app_v2's API pattern
- `SecureStorage` in student_app_v2 uses its own encrypted storage — NfcManager can keep its own `EncryptedSharedPreferences` instance for NFC-specific data
- `HomeActivity` already has `transactionsButton` and `settingsButton` — "Activate NFC Pay" button follows same pattern
- `SettingsActivity` uses `SwitchMaterial` and `Button` from Material Design — NFC section should match that component style

### Integration Points
- `student_app_v2/AndroidManifest.xml`: Add `<uses-permission android:name="android.permission.NFC" />`, `<uses-permission android:name="android.permission.USE_BIOMETRIC" />`, `<uses-feature android:name="android.hardware.nfc.hce" android:required="false" />`, and `BankoHceService` service declaration
- `student_app_v2/ApiClient.kt` (`BangkoApiService` interface): Add `registerNfcDevice` and `unregisterNfcDevice` endpoints
- `student_app_v2/Models.kt`: Add `NfcRegistrationResponse(virtual_card_token: String)` and `NfcDeviceRequest` models
- `student_app_v2/HomeActivity.kt`: Add "Activate NFC Pay" button (conditionally visible when registered + NFC enabled)
- `student_app_v2/SettingsActivity.kt`: Add NFC section (visibility controlled by `NfcManager.isNfcAvailable()`)

</code_context>

<specifics>
## Specific Ideas

- Full-screen overlay during the 30-second active window ("Hold phone to terminal" + countdown) — similar to contactless payment apps like Apple Pay / Google Pay ready state
- Biometric prompt title: "Bangko ng Seton Payment" + subtitle "Authenticate to enable NFC payment" (already in mobile/android's NfcManager — keep it)
- PIN fallback dialog reuses mobile/android's existing `showPinDialog` logic

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 16-nfc-android-hce*
*Context gathered: 2026-03-04*
