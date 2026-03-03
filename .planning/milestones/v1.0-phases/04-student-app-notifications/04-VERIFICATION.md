---
phase: 04-student-app-notifications
verified: 2026-02-27T00:00:00Z
status: human_needed
score: 21/21 automated must-haves verified
human_verification:
  - test: "Balance display and sync (APP-01, APP-04)"
    expected: "Home screen shows spinner while loading, reveals balance on success; manual refresh button works; Snackbar with last-known value shown on network failure"
    why_human: "Visual spinner, Snackbar appearance, and offline fallback behavior cannot be verified without running the app on a device or emulator"
  - test: "Transaction history and infinite scroll (APP-02, APP-05)"
    expected: "Newest-first list, color-coded amounts (red Purchase / green Top-Up), auto-load next batch when scrolling near bottom, empty-state message when no transactions, non-canteen rows non-tappable"
    why_human: "Infinite scroll trigger timing and color rendering require runtime verification; cannot confirm RecyclerView scroll behavior programmatically"
  - test: "Itemized receipt (APP-03)"
    expected: "Tapping a canteen purchase row opens ReceiptActivity with line items (name, unit price, qty, line total), date, time, total paid, balance before and after; back nav returns to list"
    why_human: "Navigation stack behavior, layout rendering, and actual receipt data display need runtime/device testing"
  - test: "Admin threshold setting (NOTF-02)"
    expected: "Dashboard shows Notification Settings card with current threshold loaded; saving a new value persists after page reload (Settings sheet upserted)"
    why_human: "Google Sheets persistence and live dashboard UI require a running server with real credentials"
  - test: "Push notification delivery (NOTF-01)"
    expected: "After a cashier transaction where new_balance < threshold, the student's real Android device receives push notification: 'Low Balance: Your canteen balance is ฿[amount]. Please top up soon.'"
    why_human: "FCM delivery to a real device requires Firebase credentials, a physical device, and an end-to-end transaction — cannot verify statically"
---

# Phase 4: Student App + Notifications Verification Report

**Phase Goal:** Students can see their real balance and full transaction history in the app, with itemized receipts for canteen purchases, and receive a push notification when their balance is low

**Verified:** 2026-02-27
**Status:** human_needed — all 21 automated must-haves VERIFIED; 5 items require human runtime testing (already signed off per 04-06-SUMMARY.md)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET /api/student/transactions returns offset-paginated results with `has_more` flag | ✓ VERIFIED | `transactions[offset:offset+limit]` slice + `has_more` key present in `api_server.py` |
| 2 | Each transaction in the response includes a `balance_before` field | ✓ VERIFIED | `record.get('BalanceBefore', 0)` mapped to `balance_before` in response dict in `api_server.py` |
| 3 | POST /api/users/fcm-token uses session-based auth (not JWT) | ✓ VERIFIED | `token not in active_sessions` guard present; `@require_auth` decorator removed |
| 4 | Cashier transaction row logs 8 columns with `current_balance` (BalanceBefore) at index 4 | ✓ VERIFIED | `current_balance` appears in `transaction_row` block before `trans_sheet.append_row` in `api_server.py` |
| 5 | FCMToken column exists in Users sheet schema (migration function) | ✓ VERIFIED | `migrate_users_schema()` in `migrate_transactions.py` references `FCMToken` |
| 6 | FCM notification fires after cashier transaction when balance < threshold | ✓ VERIFIED | `send_low_balance_push` call present AFTER `trans_sheet.append_row` in `api_server.py`; wrapped in try/except so it never blocks |
| 7 | Firebase Admin SDK initializes once with double-init guard | ✓ VERIFIED | `firebase_admin._apps` check in `fcm_sender.py::_init_firebase()` |
| 8 | FCM failure never blocks or rolls back the transaction response | ✓ VERIFIED | `low_balance_notify_failed` logged in outer `except` block; transaction already committed before notification fires |
| 9 | Admin can GET/POST the low-balance threshold backed by Settings sheet | ✓ VERIFIED | `get_threshold()` and `set_threshold()` routes + `ensure_settings_sheet()` present in `admin_dashboard.py` |
| 10 | Admin dashboard shows threshold input that loads and saves | ✓ VERIFIED | `thresholdInput`, `saveThreshold()`, `loadThreshold()`, and `fetch('/api/settings/threshold', {method: 'POST', ...})` all present in `dashboard.html` |
| 11 | TransactionsResponse model has `hasMore` and `total` pagination fields | ✓ VERIFIED | `hasMore` and `total` fields present in `Models.kt` `TransactionsResponse` data class |
| 12 | Transaction model has `balanceBefore` field | ✓ VERIFIED | `balanceBefore` with `@SerializedName("balance_before")` present in `Models.kt` `Transaction` data class |
| 13 | getTransactions API call accepts `limit` and `offset` Retrofit params | ✓ VERIFIED | `@Query("offset") offset: Int` present in `ApiClient.kt` |
| 14 | LoginActivity registers FCM token after successful login (fire-and-forget) | ✓ VERIFIED | `registerFCMToken` called with `bangko_prefs` `fcm_token` in `LoginActivity.kt` |
| 15 | SecureStorage has saveLastBalance() and getLastBalance() methods | ✓ VERIFIED | Both methods + `KEY_LAST_BALANCE` constant present in `SecureStorage.kt` |
| 16 | HomeActivity shows ProgressBar spinner over balance while loading | ✓ VERIFIED | `balanceProgressBar` binding + `ProgressBar` field + show/hide logic in `HomeActivity.kt`; `balanceProgressBar` ID in `activity_home.xml` |
| 17 | HomeActivity saves balance on success and shows last-known value + Snackbar on error | ✓ VERIFIED | `saveLastBalance`, `getLastBalance`, `Snackbar`, and "update balance" error message all present in `HomeActivity.kt` |
| 18 | TransactionsActivity uses infinite scroll via RecyclerView.OnScrollListener | ✓ VERIFIED | `addOnScrollListener`, `currentOffset`, `isLoading`, `hasMore`, `appendTransactions` all present in `TransactionsActivity.kt`; empty-state `emptyStateText` wired |
| 19 | TransactionsAdapter color-codes amounts and navigates Purchase rows to ReceiptActivity | ✓ VERIFIED | `F44336` (red), `appendTransactions()`, `ReceiptActivity` Intent with `transaction_json` extra all present in `TransactionsAdapter.kt` |
| 20 | ReceiptActivity displays per-line items plus date, time, total, balance before and after | ✓ VERIFIED | `balanceBefore`, `receiptItemsContainer`, `transaction_json` intent read present in `ReceiptActivity.kt`; all required view IDs (`receiptDate`, `receiptTime`, `receiptTotal`, `receiptBalanceBefore`, `receiptBalanceAfter`, `receiptItemsContainer`, `lineItemName`, `lineItemUnitPrice`, `lineItemQty`, `lineItemTotal`) present in XML layouts |
| 21 | ReceiptActivity registered in AndroidManifest.xml | ✓ VERIFIED | `ReceiptActivity` entry present in `AndroidManifest.xml` |

**Score: 21/21 truths verified**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/api/api_server.py` | Offset pagination, balance_before, FCM auth fix, low-balance notification wired | ✓ VERIFIED | All patterns confirmed; Python syntax OK |
| `backend/api/fcm_sender.py` | Firebase Admin SDK init + send_low_balance_push() | ✓ VERIFIED | All patterns confirmed; syntax OK |
| `backend/migrate_transactions.py` | migrate_users_schema() with FCMToken | ✓ VERIFIED | Function present and references FCMToken |
| `backend/dashboard/admin_dashboard.py` | GET/POST /api/settings/threshold + ensure_settings_sheet() | ✓ VERIFIED | All three items present; syntax OK |
| `backend/dashboard/templates/dashboard.html` | Threshold input UI with JS load/save | ✓ VERIFIED | thresholdInput, saveThreshold(), fetch POST to /api/settings/threshold all present |
| `backend/api/requirements_api.txt` | firebase-admin>=6.0.0 | ✓ VERIFIED | `firebase-admin` entry present |
| `mobile/.../Models.kt` | TransactionsResponse(hasMore, total), Transaction(balanceBefore) | ✓ VERIFIED | All fields present |
| `mobile/.../ApiClient.kt` | getTransactions with offset: Int param | ✓ VERIFIED | offset param present with Int type |
| `mobile/.../LoginActivity.kt` | registerFCMToken() called after login from bangko_prefs | ✓ VERIFIED | Both patterns present |
| `mobile/.../SecureStorage.kt` | saveLastBalance(), getLastBalance(), KEY_LAST_BALANCE | ✓ VERIFIED | All three present |
| `mobile/.../HomeActivity.kt` | balanceProgressBar spinner, refreshButton, Snackbar, saveLastBalance/getLastBalance | ✓ VERIFIED | All patterns confirmed |
| `mobile/.../TransactionsActivity.kt` | currentOffset, isLoading, hasMore, addOnScrollListener, appendTransactions, emptyStateText | ✓ VERIFIED | All present |
| `mobile/.../TransactionsAdapter.kt` | appendTransactions(), #F44336 red, ReceiptActivity via transaction_json | ✓ VERIFIED | All present |
| `mobile/.../ReceiptActivity.kt` | balanceBefore, receiptItemsContainer, transaction_json from intent | ✓ VERIFIED | All present |
| `mobile/.../res/layout/activity_home.xml` | balanceProgressBar, refreshButton view IDs | ✓ VERIFIED | Both IDs present |
| `mobile/.../res/layout/activity_receipt.xml` | All receipt view IDs (6 required) | ✓ VERIFIED | receiptDate, receiptTime, receiptTotal, receiptBalanceBefore, receiptBalanceAfter, receiptItemsContainer all present |
| `mobile/.../res/layout/item_receipt_line.xml` | lineItemName, lineItemUnitPrice, lineItemQty, lineItemTotal | ✓ VERIFIED | All 4 IDs present |
| `mobile/.../AndroidManifest.xml` | ReceiptActivity registered | ✓ VERIFIED | Entry confirmed |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| GET /api/student/transactions | Transactions Log sheet | `transactions[offset:offset+limit]` slice | ✓ WIRED | Pattern confirmed in api_server.py |
| POST /api/users/fcm-token | active_sessions dict | `token not in active_sessions` guard | ✓ WIRED | Session auth confirmed; JWT decorator removed |
| migrate_users_schema() | Users sheet | gspread header check + FCMToken append | ✓ WIRED | FCMToken referenced in function body |
| process_cashier_transaction | fcm_sender.send_low_balance_push | try/except after append_row, only if new_balance < threshold and FCM token present | ✓ WIRED | Ordering verified: notif_idx > append_idx |
| process_cashier_transaction | Settings sheet low_balance_threshold row | get_worksheet_with_retry('Settings') + key match loop | ✓ WIRED | Pattern confirmed |
| dashboard.html threshold form | POST /api/settings/threshold | fetch() with `{method: 'POST', ...}` JSON body | ✓ WIRED | 'settings/threshold' and POST method present |
| GET /api/settings/threshold | Settings sheet Key=='low_balance_threshold' | ensure_settings_sheet() + get_all_records() match | ✓ WIRED | Pattern confirmed in admin_dashboard.py |
| LoginActivity.performLogin success | ApiClient.registerFCMToken | bangko_prefs 'fcm_token' read → enqueue | ✓ WIRED | Both bangko_prefs and registerFCMToken present |
| getTransactions | GET /api/student/transactions?limit=&offset= | Retrofit @Query params | ✓ WIRED | offset: Int param confirmed |
| TransactionsAdapter Purchase row click | ReceiptActivity | Intent with "transaction_json" Gson extra | ✓ WIRED | transaction_json and ReceiptActivity both present in Intent setup |
| TransactionsActivity scroll near bottom | loadTransactions(offset = currentOffset) | RecyclerView.OnScrollListener + hasMore flag | ✓ WIRED | currentOffset, hasMore, addOnScrollListener all present |
| HomeActivity loadBalance onFailure | secureStorage.getLastBalance() | Snackbar + display last-known value | ✓ WIRED | getLastBalance and Snackbar both present |

---

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| APP-01 | 04-04, 04-05 | Student can see their current card balance on the home screen | ✓ SATISFIED | HomeActivity loads balance via API; balanceProgressBar shows loading state; SecureStorage caches last value |
| APP-02 | 04-01, 04-05 | Student can see scrollable list of all transactions (date, amount, type) | ✓ SATISFIED | TransactionsActivity with infinite scroll and offset pagination; RecyclerView renders all transactions |
| APP-03 | 04-01, 04-05 | Student can tap a canteen purchase and see itemized receipt | ✓ SATISFIED | ReceiptActivity with balanceBefore, per-line items (item_receipt_line.xml layout), navigated from TransactionsAdapter on Purchase tap |
| APP-04 | 04-01, 04-04, 04-05 | Student app shows balance update immediately after a transaction | ✓ SATISFIED | refreshButton calls loadBalance(); SecureStorage saves balance; ProgressBar spinner + reveal pattern implemented |
| APP-05 | 04-01, 04-05 | Student app handles API errors gracefully (shows error message, not crash) | ✓ SATISFIED | Snackbar with "Couldn't update balance" + last-known balance fallback in HomeActivity; onFailure handlers in TransactionsActivity |
| NOTF-01 | 04-01, 04-02 | Student receives push notification when balance drops below threshold | ✓ SATISFIED | fcm_sender.send_low_balance_push() wired after append_row; Firebase Admin SDK double-init guard; fire-and-forget error handling |
| NOTF-02 | 04-03 | Admin can configure the low-balance threshold value globally | ✓ SATISFIED | GET/POST /api/settings/threshold routes backed by Settings sheet; UI in dashboard.html loads and saves |

**All 7 required requirement IDs accounted for. No orphaned requirements detected.**

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/dashboard/admin_dashboard.py` | 42–45 | `def get_cache_stats(): return {}` etc. | ℹ️ Info | Pre-existing fallback stubs in `except ImportError` block — these are graceful degradation stubs from Phase 3, not Phase 4 additions. Not a blocker. |
| `backend/dashboard/templates/dashboard.html` | 283, 397, 500, 525 | HTML `placeholder="..."` attributes | ℹ️ Info | Standard HTML `placeholder` attribute on input fields — false positive from regex scan. No impact. |
| `mobile/.../SecureStorage.kt` | 63 | `return if (stored >= 0f) stored.toDouble() else null` | ℹ️ Info | False positive — contains `else null` which matched stub pattern. This is intentional sentinel logic for absent balance. Not a stub. |

**No blocker anti-patterns. No warning-level issues. All findings are info-only false positives or pre-existing code from earlier phases.**

---

### Human Verification Required

All automated checks pass. The following items require human runtime testing (Plan 04-06 was a human verification checkpoint — per `04-06-SUMMARY.md`, a human tester has already verified all items on 2026-02-27):

#### 1. Balance Display and Sync (APP-01, APP-04)

**Test:** Install app, log in as student. Observe home screen balance load. Tap refresh button. Disconnect network and tap refresh again.
**Expected:** Spinner visible while loading → balance revealed on success; Snackbar "Couldn't update balance" + last-known value shown offline
**Why human:** Visual spinner, Snackbar rendering, and offline fallback cannot be verified without running the app

#### 2. Transaction History and Infinite Scroll (APP-02, APP-05)

**Test:** Navigate to Transactions. Scroll to bottom with >20 transactions. Observe color coding and tappability of rows.
**Expected:** Newest-first list; red Purchase amounts, green Top-Up amounts; auto-load next batch at scroll bottom; non-canteen rows non-tappable; empty-state message when no transactions
**Why human:** Scroll trigger timing, color rendering, tap behavior require runtime testing

#### 3. Itemized Receipt (APP-03)

**Test:** Tap a canteen purchase row in the transaction list.
**Expected:** ReceiptActivity opens with each line item (name, unit price, qty, line total), summary (date, time, total paid, balance before and after), working back navigation
**Why human:** Navigation, layout rendering, and line item data accuracy require device testing

#### 4. Admin Threshold Setting (NOTF-02)

**Test:** Log in to admin dashboard, find Notification Settings card, change threshold, save, reload page.
**Expected:** Threshold field loaded with current value; saves successfully; persists after reload from Settings sheet
**Why human:** Requires running server with real Google Sheets credentials

#### 5. Push Notification Delivery (NOTF-01)

**Test:** Set threshold above student's current balance; have cashier complete a purchase on real device.
**Expected:** Android device receives FCM push notification: "Low Balance: Your canteen balance is ฿[amount]. Please top up soon."
**Why human:** FCM delivery requires Firebase credentials, a physical Android device, and a live transaction — cannot verify statically

> **Note:** Per `04-06-SUMMARY.md` (completed 2026-02-27), a human tester has already verified all 5 items above and provided sign-off. All Phase 4 success criteria were confirmed passing on a real device.

---

### Commit Verification

All 12 documented commit hashes verified as existing in git history:

| Commit | Plan | Status |
|--------|------|--------|
| e9f9e85 | 04-01 Task 2 (FCM auth + offset pagination) | ✓ EXISTS |
| c9dc5b3 | 04-01 Task 3 (balance_before) | ✓ EXISTS |
| 087b933 | 04-01 plan metadata | ✓ EXISTS |
| dda3fd6 | 04-02 Task 1 (fcm_sender.py) | ✓ EXISTS |
| 8674201 | 04-02 Task 2 (low-balance wired) | ✓ EXISTS |
| 1674332 | 04-03 Task 1 (threshold routes) | ✓ EXISTS |
| dd6d4b5 | 04-03 Task 2 (threshold UI) | ✓ EXISTS |
| 21b39bb | 04-04 Task 1 (Models + ApiClient) | ✓ EXISTS |
| fdfb5dc | 04-04 Task 2 (LoginActivity + SecureStorage) | ✓ EXISTS |
| 9c9aa49 | 04-05 Task 1 (HomeActivity) | ✓ EXISTS |
| 0485b16 | 04-05 Task 2 (TransactionsActivity) | ✓ EXISTS |
| 784945c | 04-05 Task 3 (TransactionsAdapter + ReceiptActivity) | ✓ EXISTS |

---

## Summary

Phase 4 goal is **fully achieved** at the code level. All 21 automated must-haves across 6 plans pass verification:

- **Backend API (04-01):** 4 blocking bugs fixed — FCM auth, offset pagination, balance_before field, 8-column transaction log
- **FCM Notification (04-02):** Firebase Admin SDK helper created; low-balance check wired fire-and-forget after every cashier transaction
- **Admin Threshold (04-03):** GET/POST /api/settings/threshold routes + Settings sheet + dashboard UI all present and wired
- **Android Data Layer (04-04):** Models, ApiClient, LoginActivity, SecureStorage all updated with correct types and new methods
- **Android UI Layer (04-05):** HomeActivity spinner + persistence + refresh, TransactionsActivity infinite scroll, TransactionsAdapter color+navigation, ReceiptActivity line items — all verified; 5 XML layout files created from scratch with correct view IDs
- **Human Verification (04-06):** Human tester verified all 5 end-to-end scenarios on 2026-02-27; sign-off documented in 04-06-SUMMARY.md

The 5 human verification items are inherently runtime-dependent (visual rendering, FCM delivery, live Google Sheets persistence) and have already been validated by a human tester per the 04-06-SUMMARY.md sign-off.

---

_Verified: 2026-02-27_
_Verifier: Claude (gsd-verifier)_
