# Phase 23: iPhone App Version - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a native iOS app for BankongSeton students. The app covers: login, balance display, transaction history, receipt detail, budget tracker, lost card report, and settings. No payment capability on iOS — students use their physical RFID card to pay at the cashier. No cashier-side changes required.

</domain>

<decisions>
## Implementation Decisions

### Framework & Platform
- **SwiftUI** — native iOS, no cross-platform framework
- **Minimum iOS 16** — covers ~85%+ of active devices; modern SwiftUI API support
- **Distribution: ad hoc / direct install** — no App Store; installed via Xcode or AltStore on student devices; free Apple Developer account supports up to 100 devices (paid $99/year for 10,000)
- Mac with Xcode is available for development

### Payment on iOS
- **No payment capability in this phase** — iOS cannot emulate NFC/RFID cards (HCE is blocked by Apple; Apple Pay controls the Secure Element)
- Students use their physical RFID card to pay at the cashier terminal as normal
- The iOS app is informational only: balance, history, budget tracking, card management

### iOS Screens (7 screens)
1. **Login** — student ID + PIN
2. **Home / Balance** — current balance display
3. **Transaction History** — paginated list
4. **Receipt Detail** — line items per transaction
5. **Settings** — profile, logout
6. **Lost Card Report** — freeze/report physical RFID card
7. **Budget Tracker** — spending categories

### Push Notifications
- **Skipped for iOS v1** — no APNs/FCM setup required in this phase
- Can be added in a future phase (FCM supports iOS via APNs with an Apple Developer certificate)

### Backend
- **Zero new endpoints** — all required student endpoints already exist
- `/api/student/login`, `/api/student/balance`, `/api/student/transactions`, `/api/student/report_lost_card` all reused as-is
- No changes to cashier routes, NFC routes, or any existing backend code

### Android App Relation
- Android app is unchanged by this phase
- No shared code — iOS is a clean SwiftUI rewrite of the same feature set
- API contract is the same; iOS app is a new API client

### Claude's Discretion
- SwiftUI navigation pattern (NavigationStack vs NavigationView — suggest NavigationStack for iOS 16+)
- Keychain vs UserDefaults for token storage (suggest Keychain for auth token)
- Loading/skeleton states design
- Error handling UX (suggest toast-style alerts consistent with Android app feel)
- Budget tracker category definitions (can mirror Android)
- Project folder structure inside Xcode project

</decisions>

<specifics>
## Specific Ideas

- iOS app should be visually comparable to the Android `student_app_v2` in terms of features and feel, even though it's a SwiftUI rewrite.
- NFC on iPhone: confirmed technically impossible on iOS (HCE blocked by Apple). No payment workaround in this phase.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Backend API** (`backend/api_server.py`): All student endpoints already exist — `/api/student/login`, `/api/student/balance`, `/api/student/transactions`, `/api/student/report_lost_card`. iOS app calls these directly.
- **Android app screens** (`mobile/student_app_v2/`): HomeActivity, TransactionsActivity, ReceiptActivity, SettingsActivity — use as functional reference for what each iOS screen should do.
- **Transaction schema**: 11-column Transactions Log in Google Sheets (Timestamp, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, ...) — iOS receipt view needs to parse this format.

### Established Patterns
- **Auth**: JWT stored in EncryptedSharedPreferences (Android) → use iOS Keychain. Token passed as `Authorization: Bearer <token>` header.
- **Session**: `active_sessions` dict on backend keyed by student_id — iOS app must maintain this same session-based auth pattern.
- **Thai Baht**: currency symbol is `฿` (not `₱`) — confirmed in Phase 04-05 decision.
- **Transaction types**: `Purchase`, `NFC Purchase`, `Top-up` — iOS transaction list must filter/label these.

### Integration Points
- **Lost card report**: existing endpoint at `/api/student/report_lost_card` — iOS screen calls this directly.
- **Budget tracker**: no backend endpoint — Android does this client-side from transaction history. iOS should do the same.

</code_context>

<deferred>
## Deferred Ideas

- **QR code payment** — considered and dropped for v1. Would require new `/api/qr/generate` + `/api/qr/pay` backend endpoints and a cashier UI "Pay with QR" button. May revisit in a future phase.
- **Push notifications on iOS** — APNs + FCM certificate setup. Deferred to a future phase after iOS v1 ships.
- **App Store distribution** — requires $99/year Apple Developer account and App Store review. Out of scope for school deployment; may revisit if scale grows.
- **iPad-optimized layout** — iPhone only for v1; iPad support deferred.
- **NFC on iOS** — confirmed impossible (HCE blocked by Apple). Not revisitable without Apple Pay integration, which is out of scope.

</deferred>

---

*Phase: 23-iphone-app-version*
*Context gathered: 2026-03-09*
