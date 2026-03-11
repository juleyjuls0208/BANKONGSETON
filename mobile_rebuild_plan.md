# Mobile Rebuild & Cashier System Plan

## 1. Goal Description
Rebuild the student mobile app from scratch in a new directory (`mobile/student_app_v2`) using **Jetpack Compose** for a modern, minimalist (Apple/Google style) design. Implement a comprehensive Cashier System that tracks individual products, categories, and sends email receipts to parents. Update the backend and web dashboard to support detailed transaction viewing.

## 2. Technical Decisions
> [!NOTE]
> **New Folder**: The new app will be created in `mobile/student_app_v2` to preserve the old structure if needed.
> **Tech Stack**: We will use **Kotlin + Jetpack Compose** for the Android app to achieve the "Modern/Minimalist" look naturally.
> **Email Service**: SMTP with retry logic (3 attempts, 5s delay). Transactions proceed regardless of email status.
> **RFID Hardware**: RC522 module via Arduino serial communication (9600 baud, 5s timeout).
> **Push Notifications**: Firebase Cloud Messaging (FCM) for transaction/balance alerts.
> **Design System**: Material You Dynamic Color + System Dark/Light mode preference.
> **Cashier Security**: JWT-based authentication. Only users with `role=cashier` or `role=admin` can access.

## 3. Proposed Features & Changes

### A. Mobile App (Student V2)
**Directory**: `mobile/student_app_v2`
**Design Philosophy**: "Material You" (Google) meets "Human Interface" (Apple). Large whitespace, bold typography, smooth transitions.
- **[NEW] Balancer & Dashboard**: Minimal card showing current balance.
- **[NEW] Transaction History**: List of transactions. Clicking one expands to show *Itemized Receipts* (e.g., "Burger - ₱50", "Coke - ₱30").
- **[NEW] Settings**: Toggle Dark/Light mode manually (persisted in DataStore).
- **[RESTORE] Report Lost Card**: Feature to immediately deactivate the current card if lost.
- **[RESTORE] Notifications**: Push notifications for transactions and low balance alerts.

### B. Cashier System (Web-Based)
**Architecture**: Web Frontend (HTML/JS) + Flask Backend (Python) + Arduino RC522 (Serial Bridge).
- **[NEW] Cashier Web Interface**:
    - Login page with JWT authentication (requires `role=cashier` or `role=admin`).
    - Product Catalog with search/filter (Grid/List view).
    - "Cart" sidebar showing selected items and total.
    - **Payment Flow**:
        1. Cashier selects items -> Click "Pay".
        2. Web UI shows modal: "Tap Student Card" (20s timeout indicator).
        3. Backend signals Arduino RC522 to read via serial.
        4. User taps card -> Arduino sends UID (or timeout after 20s).
        5. **Balance Check**: Backend checks if `Balance >= Total`.
            - If YES: Deduct balance, Log transaction (commit to DB first), Queue email (async retry 3x), Send FCM notification, Return "Success".
            - If NO: Return "Insufficient Funds", Web UI shows error.
    - **Product Management**: Admins can add/edit/disable products via dashboard.

### C. Backend & Database
- **[Modify] Google Sheets**:
    - `Users`: Add `ParentEmail`, `FCMToken`, `Role` columns.
    - `Transactions Log`: Add `ItemsJson` column (JSON array of `{name, price, qty}`).
    - `Products`: New sheet with columns: `ID`, `Name`, `Category`, `Price`, `ImageURL`, `Active`.
- **[NEW] Email Service** (`email_service.py`):
    - Trigger: After transaction commit.
    - Action: Async retry (3 attempts, 5s exponential backoff). Falls back to student email if `ParentEmail` is null.
    - Content: "Your child purchased: [List of Items]. New Balance: ₱XX.XX".
- **[NEW] Migration Script** (`migrate_transactions.py`):
    - Backfill existing transactions with empty `ItemsJson` field.
- **[NEW] API Endpoints**:
    - `POST /api/cashier/transaction` - Process purchase with items array
    - `GET /api/products` - List active products
    - `POST /api/products` - Create/update product (admin only)
    - `POST /api/users/fcm-token` - Register device for notifications

### D. Web Dashboard (Admin)
- **[MODIFY] Transactions Table**:
    - Make the 'Type' (or a detail button) clickable.
    - Modal popup showing the full breakdown of items for that transaction.

## 4. Implementation Stages

### Phase 1: Backend & Data Structure
1.  **Update Sheets Schema**: Add `ParentEmail`, `FCMToken`, `Role` to Users; `ItemsJson` to Transactions; Create `Products` sheet.
2.  **Migration Script**: Run `migrate_transactions.py` to prepare existing data.
3.  **Email Worker**: Implement `email_service.py` with async retry (3x, 5s backoff).
4.  **API Endpoints**: Define and implement 4 new endpoints (see Section 3.C).
5.  **JWT Auth**: Add middleware for cashier/admin role verification.
6.  **Testing Checkpoint**: 
    - Verify Sheets read/write with new columns.
    - Test email retry with intentional SMTP failure.
    - Validate JWT token generation and role checks.

### Phase 2: The New Mobile App
1.  **Setup**: Initialize new Android project in `mobile/student_app_v2` with Jetpack Compose + Material 3.
    - **Outcome**: Clean project structure with Firebase SDK integrated.
2.  **Build Configuration**: Configure `build.gradle` for signed APK generation + ProGuard rules.
3.  **Design System**: Implement Material You theme with dynamic color scheme (primaryContainer, surface, onSurface).
4.  **UI Implementation**: 
    - Login screen (Card UID + PIN)
    - Home (Balance card with pull-to-refresh)
    - History (LazyColumn with expandable items showing ItemsJson)
    - Settings (Dark/Light toggle, DataStore persistence)
5.  **API Integration**: Retrofit client with JWT interceptor.
6.  **FCM Integration**: Register device token on login, handle background notifications.
7.  **Testing Checkpoint**:
    - Build APK and install on physical device.
    - Test login flow and balance display.
    - Verify transaction history shows itemized receipts.


### Phase 3: Cashier & Web Updates
1.  **Cashier Web App**: 
    - Build `cashier` blueprint in Flask with JWT login.
    - Product Grid (search/filter by category) and Cart UI (responsive layout).
    - Payment modal with 20s timeout and loading states.
2.  **Arduino RC522 Integration**: 
    - Update `arduino_bridge.py` with 20s timeout handling.
    - Serial protocol: Send `READ_CARD`, receive `UID:<hex>` or `TIMEOUT`.
3.  **Product Management UI**: Admin page for CRUD operations on Products sheet.
4.  **Web Dashboard Enhancement**: Add "View Details" modal showing `ItemsJson` breakdown.
5.  **Testing Checkpoint**:
    - Test cashier login with valid/invalid credentials.
    - Perform purchase with RC522 card tap (success + timeout scenarios).
    - Verify email received and FCM notification on student device.
    - Check admin dashboard shows itemized receipt in modal.

## 5. Final Verification Plan
- **Build Test**: Run `./gradlew assembleRelease` and verify signed APK is generated and installable.
- **Email Test**: Perform transaction -> Verify email received (check retry logs if SMTP fails).
- **Security Test**: Attempt to access cashier page without JWT -> Verify redirect to login.
- **RC522 Test**: Test card tap with 3s response time -> Verify success. Simulate 6s timeout -> Verify error handling.
- **UI Test**: Toggle Dark/Light mode -> Verify Material You colors adapt instantly.
- **FCM Test**: Complete purchase on cashier -> Verify push notification on student device within 2s.
- **Receipt Test**: Buy 3 items -> Check Admin Dashboard -> Click transaction -> Verify all 3 items listed with prices.
- **Load Test**: Process 10 concurrent cashier transactions -> Verify no race conditions on balance deduction.
