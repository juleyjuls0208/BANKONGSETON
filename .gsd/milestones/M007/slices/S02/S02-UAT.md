# M007 / S02 Manual UAT Checklist (Home + QR Flow, QR-Only)

Use this checklist on a real iOS device or simulator with camera controls. Mark each row **PASS** or **FAIL** and record short notes.

## Scope

- Home exposes a single QR payment path (no payment-method chooser).
- QR flow supports real scan outcomes (valid, invalid/expired, insufficient balance, camera denied).
- QR success returns to Home and refreshes visible balance/transactions.

## Preconditions

- App build is current (`BankongSetonStudent` scheme).
- Test account can sign in and reach Home.
- Cashier/backend can provide:
  - one **valid token-only** QR payload
  - one **expired/invalid** QR payload
  - one cart amount above student balance (for insufficient-balance path)
- If testing camera-denied path, reset camera permission state first.

## Pass/Fail Checklist

| # | Scenario | Steps | Expected Result | Result | Notes |
|---|----------|-------|-----------------|--------|-------|
| 1 | Home QR-only entry | Open Home screen. Inspect payment entry area. | Home shows **Pay with QR** CTA with `home-qr-pay-button` behavior. No payment-method chooser text/options appear. | ☐ PASS / ☐ FAIL | |
| 2 | Valid **token-only** scan happy path | Tap **Pay with QR** → scan token-only QR payload → wait for loading → tap **Confirm QR Payment**. | States progress `scanning → loading → confirming → success`. Success shows completion and dismisses back to Home. | ☐ PASS / ☐ FAIL | |
| 3 | Post-success continuity refresh | Immediately after row #2 dismisses, observe Home. Pull-to-refresh optional for confirmation. | Home balance/transactions reflect updated payment result without reopening app. | ☐ PASS / ☐ FAIL | |
| 4 | Invalid/expired QR path | Open QR flow again. Scan known invalid or expired payload. | App shows explicit error message (invalid/expired), with actionable controls (e.g., **Retry Scan**, **Close**, optional **Cancel** in flow). No silent scanner stall. | ☐ PASS / ☐ FAIL | |
| 5 | Insufficient balance path | Scan valid QR tied to cart amount above account balance → confirm payment. | App surfaces insufficient-balance error message and keeps user in actionable state (retry/close/cancel path). | ☐ PASS / ☐ FAIL | |
| 6 | Camera denied path | Deny camera permission in system settings (or simulator privacy), then open QR flow. | App surfaces camera-denied guidance (permission/settings language) with actionable controls (**Open Settings** when applicable, **Retry Scan**, **Close/Cancel**). | ☐ PASS / ☐ FAIL | |
| 7 | Retry from non-happy path | From an error state, tap **Retry Scan** and scan a valid token again. | Flow reliably returns to scanning and can complete a successful payment. | ☐ PASS / ☐ FAIL | |

## Exit Criteria

- All rows pass, especially rows **2, 4, 5, 6** (required non-happy-path coverage).
- Any fail includes reproducible notes (payload type, permission state, and visible error text).
- Do not record PIN/JWT/raw secret values in notes.
