# Phase 23: iPhone App Version - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a native iOS app for BankongSeton students. The app covers: login, balance display, transaction history, receipt detail, QR code payment (student scans cashier's QR), budget tracker, lost card report, and settings. The cashier POS web UI also needs a "Pay with QR" button that generates a per-transaction QR code.

</domain>

<decisions>
## Implementation Decisions

### Framework & Platform
- **SwiftUI** — native iOS, no cross-platform framework
- **Minimum iOS 16** — covers ~85%+ of active devices; modern SwiftUI API support
- **Distribution: ad hoc / direct install** — no App Store; installed via Xcode or AltStore on student devices; free Apple Developer account supports up to 100 devices (paid $99/year for 10,000)
- Mac with Xcode is available for development

### Payment Method: QR Code (not NFC)
- iPhone **cannot emulate NFC/RFID cards** — iOS blocks HCE; Apple Pay controls the Secure Element
- Payment flow: **cashier generates QR → student scans with iOS app → app confirms payment**
- QR encodes a **per-transaction token** (not just a cashier ID) — one QR per sale, contains transaction token + basket total
- Student sees the basket total in-app before confirming

### QR Backend Architecture
- **New `/api/qr/generate`** endpoint — cashier calls this after building basket; returns a short-lived QR token + encoded total
- **New `/api/qr/pay`** endpoint — iOS app POSTs student auth + QR token; backend deducts balance and records transaction
- QR token is single-use and time-limited (Claude's discretion on TTL, suggest 90 seconds)
- Cashier UI: **"Pay with QR" button** added to existing cashier POS page — generates QR, displays overlay; SocketIO event confirms payment and clears overlay

### iOS Screens (Full MVP)
All 8 screens confirmed:
1. **Login** — student ID + PIN
2. **Home / Balance** — current balance display
3. **Transaction History** — paginated list
4. **Receipt Detail** — line items per transaction
5. **QR Payment Scanner** — camera scanner, shows basket total, confirm button
6. **Settings** — profile, logout
7. **Lost Card Report** — freeze/report physical RFID card
8. **Budget Tracker** — spending categories

### Push Notifications
- **Skipped for iOS v1** — no APNs/FCM setup required in this phase
- Can be added in a future phase (FCM supports iOS via APNs with an Apple Developer certificate)

### Backend Auth
- iOS uses the same **JWT-based auth** as Android — no new auth scheme
- `/api/student/login`, `/api/student/balance`, `/api/student/transactions` all reused as-is
- QR pay endpoints are new additions; no changes to existing NFC or cashier endpoints

### Android App Relation
- Android app is unchanged by this phase
- No shared code — iOS is a clean SwiftUI rewrite of the same feature set
- API contract is the same; iOS app is a new API client

### Claude's Discretion
- QR token TTL and invalidation strategy
- SwiftUI navigation pattern (NavigationStack vs NavigationView — suggest NavigationStack for iOS 16+)
- Keychain vs UserDefaults for token storage (suggest Keychain for auth token)
- Loading/skeleton states design
- Error handling UX (suggest toast-style alerts consistent with Android app feel)
- Budget tracker category definitions (can mirror Android)
- Project folder structure inside Xcode project

</decisions>

<specifics>
## Specific Ideas

- QR payment direction is **cashier shows QR, student scans** — not the other way around. This is important: the cashier's screen displays the QR code, the student opens the iOS app and points their camera at it.
- iOS app should be visually comparable to the Android `student_app_v2` in terms of features and feel, even though it's a SwiftUI rewrite.
- NFC on iPhone: user originally wanted NFC emulation, confirmed it is technically impossible on iOS. QR is the agreed alternative.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Backend API** (`backend/api_server.py`): All student endpoints already exist — `/api/student/login`, `/api/student/balance`, `/api/student/transactions`, `/api/student/report_lost_card`. iOS app calls these directly.
- **Android app screens** (`mobile/student_app_v2/`): HomeActivity, TransactionsActivity, ReceiptActivity, SettingsActivity, NfcPayOverlayActivity — use as functional reference for what each iOS screen should do.
- **Transaction schema**: 11-column Transactions Log in Google Sheets (Timestamp, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, ...) — iOS receipt view needs to parse this format.

### Established Patterns
- **Auth**: JWT stored in EncryptedSharedPreferences (Android) → use iOS Keychain. Token passed as `Authorization: Bearer <token>` header.
- **Session**: `active_sessions` dict on backend keyed by student_id — iOS app must maintain this same session-based auth pattern.
- **Thai Baht**: currency symbol is `฿` (not `₱`) — confirmed in Phase 04-05 decision.
- **Transaction types**: `Purchase`, `NFC Purchase`, `Top-up` — iOS transaction list must filter/label these.

### Integration Points
- **New QR endpoints** connect to: cashier POS UI (generate QR button + SocketIO confirm event), and iOS app (scan + pay).
- **Lost card report**: existing endpoint at `/api/student/report_lost_card` — iOS screen calls this directly.
- **Budget tracker**: no backend endpoint — Android does this client-side from transaction history. iOS should do the same.
- **Cashier POS** (`backend/cashier_routes.py`): "Pay with QR" button added to existing cashier HTML template. QR overlay uses SocketIO for real-time confirmation (same pattern as NFC payment modal from Phase 20.1).

</code_context>

<deferred>
## Deferred Ideas

- **Push notifications on iOS** — APNs + FCM certificate setup. Deferred to a future phase after iOS v1 ships.
- **App Store distribution** — requires $99/year Apple Developer account and App Store review. Out of scope for school deployment; may revisit if scale grows.
- **iPad-optimized layout** — iPhone only for v1; iPad support deferred.
- **NFC on iOS** — confirmed impossible (HCE blocked by Apple). Not revisitable without Apple Pay integration, which is out of scope.

</deferred>

---

*Phase: 23-iphone-app-version*
*Context gathered: 2026-03-09*
