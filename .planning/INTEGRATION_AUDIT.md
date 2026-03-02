# BankongSeton v1.0 — Integration Audit Report

**Date:** 2026-03-01  
**Scope:** All 6 phases, all 41 v1 requirements  
**Auditor:** gsd-integration-checker  

---

## Executive Summary

The BankongSeton v1.0 milestone has **3 critical integration breaks** that prevent core user-facing features from working end-to-end, even though all 6 phases passed individual phase verification. The cashier RFID payment flow (the primary revenue path) is broken at the Arduino↔WebSocket boundary. Student receipt display is broken by a timestamp format mismatch. NFC receipt navigation is broken by a transaction type string mismatch. Additionally, 1 startup-time migration gap can silently block FCM notifications for all students.

| Severity | Count | Items |
|----------|-------|-------|
| 🔴 Critical | 3 | Cashier card-read wiring, BalanceBefore column schema, FCM migration not called at startup |
| 🟠 High | 3 | Timestamp format mismatch (receipt), NFC `mobile/android` schema mismatches, NFC Purchase receipt non-navigable |
| 🟡 Medium | 3 | cashier_routes direct sheet access, `card_error` exception leakage, JWT_SECRET random fallback |
| 🟢 Low | 2 | Cashier FCM gap undocumented, `mobile/android` orphaned endpoints |

---

## E2E Flow Status

| # | Flow | Status | Evidence |
|---|------|--------|----------|
| 1 | Card tap → payment → FCM notification | 🔴 **BROKEN** | cashier_routes.py:211 emits `cashier_request_card`; no handler listens for it anywhere |
| 2 | Admin product management → cashier POS display | 🟠 **PARTIAL** | Route wiring works; cashier uses `db.worksheet('Products')` directly, not `ensure_products_sheet()` |
| 3 | Student app login → balance → transaction history | 🟠 **PARTIAL** | Login/balance/list verified; ReceiptActivity timestamp parse always fails |
| 4 | NFC registration and payment | 🟠 **PARTIAL** | Backend endpoints verified; `mobile/android` has 3 schema mismatches and calls 2 non-existent routes |
| 5 | Documentation cross-reference integrity | 🟢 **VERIFIED** | All 8 docs linked from README; 2 minor content gaps (non-blocking) |

---

## Flow 1 — Card Tap → Payment → FCM Notification

**Status: 🔴 BROKEN**

### What should happen
1. Cashier clicks "Charge" on cashier_index.html
2. `process_sale` (cashier_routes.py) signals Arduino to read card
3. Arduino bridge reads card UID and emits `card_read` WebSocket event
4. `complete_sale` processes payment in Google Sheets and deducts balance
5. FCM push notification fires if balance < threshold

### Where it breaks

**Break 1 — WebSocket handler missing (cashier_routes.py:211)**
```
cashier_routes.py:211  socketio.emit('cashier_request_card', {'timeout': 10})
```
No SocketIO `@socketio.on('cashier_request_card')` handler exists anywhere in the codebase. The event fires into the void. `ArduinoBridge.read_card_with_timeout()` (arduino_bridge.py:28) is defined but never called in this code path.

**Break 2 — `app.arduino_bridge` attribute not set by cashier flow**  
```
cashier_routes.py:121  if hasattr(current_app, 'arduino_bridge'):
```
`current_app.arduino_bridge` is only set inside `admin_dashboard.py`'s `/connect_serial` route (line 1116). The cashier blueprint has no mechanism to set this attribute independently. If the admin hasn't connected serial first, the cashier's arduino check silently skips.

**Break 3 — ~~FCM never fires via cashier POS path~~ — RESOLVED in Phase 7, verified in Phase 12**  
~~`complete_sale` in cashier_routes.py deducts balance and records the transaction but never calls `send_low_balance_push()`. FCM is only triggered by `process_cashier_transaction` in api_server.py (the `/api/cashier/transaction` endpoint, port 5001), which is a separate path not used by the cashier web app.~~  
`cashier_routes.py:570-612` now calls `send_purchase_push()` on every sale and `send_low_balance_push()` when `new_balance < threshold`. Both calls are inside a non-blocking `try/except`. See `12-VERIFICATION.md`.

### Affected requirements
- **BUG-01** — Cashier POS is marked Complete but the actual card-read→payment E2E path is broken
- **NOTF-01** — Push notification never fires when a student pays via cashier POS

---

## Flow 2 — Admin Products → Cashier POS Display

**Status: 🟠 PARTIAL**

### What works ✅
- `products.html` calls `/api/products/list`, `/api/products/update`, `/api/products/toggle-status` — all exist in `admin_dashboard.py`
- All three admin product routes use `ensure_products_sheet()` (auto-creates sheet if missing)
- Cashier `/cashier/api/products` (cashier_routes.py:162) returns only active products
- `cashier_index.html:171` filters `data.products.filter(p => p.active)` correctly
- Dynamic category tabs and multi-item cart wiring verified

### What is partial ⚠️
**cashier_routes.py:162 calls `db.worksheet('Products')` directly** instead of `ensure_products_sheet()`. If the Products sheet does not yet exist (fresh deployment, or sheet accidentally deleted), the cashier returns HTTP 503 ("Products sheet not found") rather than auto-creating it. Admin panel would silently create it on next admin product load, but until then cashier is broken without a clear error message.

### Affected requirements
- **PROD-04** — Works only if Products sheet already exists (not self-healing from cashier side)
- **PROD-05** — Sheet persistence works; consistency of auto-create behavior is inconsistent across admin vs. cashier paths

---

## Flow 3 — Student App Login → Balance → Transaction History

**Status: 🟠 PARTIAL**

### What works ✅
- `LoginActivity` → `/api/auth/login` → JWT session token: verified
- FCM token buffered from `SharedPreferences` and sent to `/api/users/fcm-token` after login: verified
- `HomeActivity` → `/api/student/balance` with Snackbar error + `SecureStorage` persistence: verified
- `TransactionsActivity` → `/api/student/transactions` with `hasMore`/`currentOffset` offset pagination: verified

### Where it breaks

**Break 1 — Timestamp format mismatch (ReceiptActivity.kt)**
```kotlin
// ReceiptActivity.kt
SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss")  // expects ISO 8601 with 'T'
```
```python
# cashier_routes.py + api_server.py — both write:
datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # space, not 'T'
```
Every timestamp parsed in `ReceiptActivity` will fail silently and fall back to displaying the raw string. Date/time fields show as `"2026-02-28 14:32:00"` (verbatim string) instead of formatted date and time.

**Break 2 — BalanceBefore column missing from cashier_routes writes → balance shows ₱0.00**  
`cashier_routes.py` writes 7 columns to the Transactions sheet: `[timestamp, card_uid, student_name, type, amount, new_balance, 'Success']`. The schema has 8 columns where column index 5 is `BalanceBefore` and column 6 is `BalanceAfter`. When gspread maps by header name, cashier rows have `new_balance` in the `BalanceBefore` column and `'Success'` in the `BalanceAfter` column. `float('Success')` coercion fails → falls back to 0. Every cashier POS transaction displays **₱0.00 balance** in the student app's receipt view.

**Startup gap — FCM migration not called at startup**  
`migrate_users_schema()` in `backend/migrate_transactions.py` adds the `FCMToken` column to the Users sheet. It is **never called** at startup in `api_server.py`. On a fresh deployment or a Sheets environment without the column, `/api/users/fcm-token` returns HTTP 500 ("FCMToken column not found. Run migration first."), blocking FCM token registration for all students. This prevents `NOTF-01` from functioning even when the cashier FCM gap (Flow 1, Break 3) is fixed.

### Affected requirements
- **APP-02** — Transaction list displays correctly; receipt timestamps display raw string *(partial)*
- **APP-03** — Itemized receipt exists but timestamp fields are malformed; balance shown as ₱0.00 *(broken)*
- **APP-04** — Balance updates immediately on HomeActivity screen; but receipt balance history is ₱0.00 *(partial)*
- **NOTF-01** — FCM migration gap blocks token registration on fresh deployments *(partial)*

---

## Flow 4 — NFC Registration and Payment

**Status: 🟠 PARTIAL**

### What works ✅
- `/api/nfc/register` and `/api/nfc/pay` endpoints exist and are registered in `api_server.py`
- `NFCService` uses Sheets-backed `VirtualCards` (no in-memory state): verified
- Dual auth (cashier JWT + `X-Device-Token`) for `/api/nfc/pay`: verified
- CORS `allow_headers` includes `X-Device-Token`: verified
- NFC transactions logged to Transactions sheet: verified
- `student_app_v2` (Phase 4 primary deliverable) correctly identified as separate from `mobile/android`

### Where it breaks

**Break 1 — `mobile/android` calls 2 non-existent endpoints**
```kotlin
// mobile/android/ApiClient.kt
apiService.unregisterNfc(...)   // calls /api/nfc/unregister — does not exist
apiService.getNfcStatus(...)    // calls /api/nfc/status — does not exist
```
These routes are absent from `api_server.py`. Any attempt to unregister or check NFC status from `mobile/android` will return HTTP 404.

**Break 2 — `/api/nfc/register` request body schema mismatch**
```kotlin
// mobile/android: sends body { device_id, device_name, pin }
// api_server.py /api/nfc/register: takes no body, uses session JWT only
```
The registration call from `mobile/android` will silently succeed (the extra body is ignored) but the `pin` and `device_name` fields will never be stored or validated, contrary to what `mobile/android` expects.

**Break 3 — NFC Purchase receipt not navigable in student app**
```kotlin
// TransactionsAdapter.kt — only navigates to ReceiptActivity when:
if (transaction.type == "Purchase") { ... }
// NFC transactions are logged as type "NFC Purchase" — never matches
```
Students cannot tap NFC transactions to view their receipt. This affects any student who uses NFC to pay.

**Break 4 — `mobile/android` LoginResponse field mapping mismatch**
```kotlin
// mobile/android LoginResponse.kt
@SerializedName("student_id") val studentId: String
// api_server.py /api/auth/login returns:
{ "student": { "id": ..., ... } }  // key is "id", not "student_id"
```
`studentId` will always be null after login in `mobile/android`.

**Note:** `mobile/android` is an older, incomplete reference codebase. The Phase 4 deliverable is `mobile/student_app_v2`. The NFC integration guide points to `mobile/android/BankoHceService.kt` as the reference HCE implementation, which is appropriate since `student_app_v2` does not implement NFC (correctly deferred to v2).

### Affected requirements
- **NFC-01** — Backend endpoints exist and documented *(verified)*
- **NFC-02** — Sheets persistence verified *(verified)*
- **NFC-03** — Accepts both RFID and NFC token as payment source *(verified in backend)*; NFC receipts non-navigable in app *(partial)*
- **NFC-04** — Dual auth verified *(verified)*; `mobile/android` schema mismatches mean reference integration is broken *(partial)*
- **NFC-05** — NFC guide written; points to `mobile/android` which has broken API contracts *(partial)*

---

## Flow 5 — Documentation Cross-Reference Integrity

**Status: 🟢 VERIFIED (minor gaps)**

### What works ✅
- `docs/README.md` correctly links all 8 docs
- `google-sheets-schema.md` explicitly documents the 3-way write path discrepancy (7-col cashier, 8-col API, 7-col NFC)
- `api-reference.md` notes `balance_before` may be 0 for cashier rows with cross-link to schema doc
- `nfc-integration-guide.md` cross-links to `api-reference.md` and `google-sheets-schema.md`
- NFC receipt non-navigability (`NFC Purchase` type) is documented in `nfc-integration-guide.md:398` with link to `student-app.md`

### Minor gaps ⚠️
1. **`cashier-guide.md`** does not mention that FCM push notifications are **not** triggered by the cashier POS flow — only by `api_server.py`'s `/api/cashier/transaction` endpoint. Operational gap: admins and integrators would not know push notifications silently don't fire for cashier payments.
2. **`api-reference.md`** documents 12 endpoints but does not document any `cashier_routes.py` endpoints (`/cashier/api/products`, `/cashier/api/process_sale`, `/cashier/api/complete_sale`, etc.). These are live production endpoints with no documentation.

### Affected requirements
- **DOC-02** — `api-reference.md` missing cashier blueprint endpoints *(partial)*
- **DOC-04** — `cashier-guide.md` missing FCM gap explanation *(partial)*
- **DOC-05** — `student-app.md` and `nfc-integration-guide.md` internally consistent *(verified)*
- **DOC-06** — NFC guide accurate for backend; `mobile/android` schema mismatches not called out *(partial)*

---

## Cross-Phase Wiring Map

### Connected (working)

| Export / API | From Phase | Used By | Evidence |
|---|---|---|---|
| `normalize_card_uid()` | Phase 2 (utils.py) | Phase 1, Phase 5 (api_server, admin_dashboard, cashier_routes) | grep confirmed in all 3 files |
| `get_logger()` | Phase 2 (errors.py) | Phase 1, Phase 3, Phase 4, Phase 5 | grep confirmed across backend/ |
| `CardReaderState` singleton | Phase 2 (utils.py) | Phase 1 (admin_dashboard.py) | admin_dashboard.py import confirmed |
| `/api/auth/login` | Phase 1 (api_server.py) | Phase 4 (LoginActivity.kt) | ApiClient.kt call confirmed |
| `/api/student/balance` | Phase 4 (api_server.py) | Phase 4 (HomeActivity.kt) | ApiClient.kt call confirmed |
| `/api/student/transactions` | Phase 4 (api_server.py) | Phase 4 (TransactionsActivity.kt) | ApiClient.kt call confirmed |
| `/api/products/list` | Phase 3 (admin_dashboard.py) | Phase 3 (products.html) | fetch confirmed |
| `/api/products/update` | Phase 3 (admin_dashboard.py) | Phase 3 (products.html) | fetch confirmed |
| `/api/nfc/register`, `/api/nfc/pay` | Phase 5 (api_server.py) | Phase 6 (docs) | documented |
| `ensure_products_sheet()` | Phase 3 (admin_dashboard.py) | Phase 3 admin routes only | confirmed |

### Orphaned (exported but no consumer in primary path)

| Export | From | Reason |
|---|---|---|
| `ArduinoBridge.read_card_with_timeout()` | Phase 1 (arduino_bridge.py:28) | Defined, never called in cashier payment path |
| `migrate_users_schema()` | Phase 4 (migrate_transactions.py) | Must be run manually; not called at app startup |
| `mobile/android` codebase (NFC reference) | Phase 5 | Not the primary app deliverable; has broken contracts with current backend |

### Missing connections

| Expected Connection | From | To | Reason |
|---|---|---|---|
| `cashier_request_card` WebSocket handler | cashier_routes.py (emitter) | Any handler in codebase | Emitted at line 211, no listener exists |
| `send_low_balance_push()` call | Phase 4 (fcm_sender.py) | cashier_routes.py `complete_sale` | FCM is only called from api_server.py path |
| `ensure_products_sheet()` | Phase 3 (admin_dashboard.py) | cashier_routes.py `/cashier/api/products` | Cashier uses `db.worksheet()` directly |
| `migrate_users_schema()` call at startup | Phase 4 (migrate_transactions.py) | api_server.py startup | Not wired to app init |
| Timestamp format alignment | backend (both write `%Y-%m-%d %H:%M:%S`) | ReceiptActivity.kt (reads `'T'` format) | Format never aligned between phases |
| `BalanceBefore` column in cashier writes | Phase 1 cashier_routes.py | Phase 4 student app receipt | cashier writes 7 cols; schema expects 8 |

---

## Requirements Integration Map

| Requirement | Integration Path | Status | Issue |
|---|---|---|---|
| **BUG-01** | cashier_routes.py → arduino_bridge → card_read WebSocket → complete_sale | 🔴 BROKEN | `cashier_request_card` emitted with no handler; ArduinoBridge never invoked from cashier path |
| **BUG-02** | api_server.py input validation → normalize_card_uid() → Sheets query | ✅ WIRED | Regex guard + normalization confirmed |
| **BUG-03** | api_server.py + cashier_routes.py → try/except → HTTP error responses | ✅ WIRED | Graceful error handlers confirmed |
| **BUG-04** | admin_dashboard.py `/login` → credential validation | ✅ WIRED | Empty-string guard confirmed |
| **BUG-05** | api_server.py `process_cashier_transaction` → atomic deduction | ✅ WIRED | Row-level check confirmed |
| **SEC-01** | admin_dashboard.py startup → no credential log | ✅ WIRED | `get_logger()` used; no print statements |
| **SEC-02** | admin_dashboard.py startup → `FLASK_SECRET_KEY` guard | ⚠️ PARTIAL | Guard exists in admin_dashboard.py; **missing in api_server.py** (uses random fallback) |
| **SEC-03** | Both Flask apps → CORS config | ✅ WIRED | Origins allowlist confirmed |
| **SEC-04** | api_server.py + admin_dashboard.py → UID regex validation | ✅ WIRED | `normalize_card_uid()` used in all entry points |
| **SEC-05** | tests/ → env var usage | ✅ WIRED | No hardcoded secrets in test files |
| **QUAL-01** | backend/ → structured logging via `get_logger()` | ⚠️ PARTIAL | `card_error` exception text still emitted via WebSocket in 4 locations (admin_dashboard.py:1239, 1296, 1409, 1872) |
| **QUAL-02** | `normalize_card_uid()` → all 3 backend entry points | ✅ WIRED | Confirmed in api_server, admin_dashboard, cashier_routes |
| **QUAL-03** | `CardReaderState` singleton → thread-safe locking | ✅ WIRED | admin_dashboard.py uses singleton |
| **QUAL-04** | Dead code removed | ✅ WIRED | BankongSetonApp folder removed |
| **QUAL-05** | google-auth replaces oauth2client | ✅ WIRED | requirements files confirmed |
| **PROD-01** | products.html → `/api/products/update` (POST) → Products sheet | ✅ WIRED | Admin add route confirmed |
| **PROD-02** | products.html → `/api/products/update` (PUT) → Products sheet | ✅ WIRED | Admin edit route confirmed |
| **PROD-03** | products.html → `/api/products/toggle-status` → Products sheet | ✅ WIRED | Toggle route confirmed |
| **PROD-04** | cashier_routes.py `/cashier/api/products` → cashier_index.html grid | ⚠️ PARTIAL | Works if sheet exists; no auto-create from cashier side |
| **PROD-05** | Products sheet → `ensure_products_sheet()` (admin only) | ⚠️ PARTIAL | Only admin path auto-creates; cashier path uses direct `db.worksheet()` |
| **PROD-06** | cashier_index.html multi-item cart → `complete_sale` | ✅ WIRED | Multi-item cart and single transaction flow confirmed |
| **APP-01** | HomeActivity → `/api/student/balance` → balance display | ✅ WIRED | Verified with SecureStorage persistence |
| **APP-02** | TransactionsActivity → `/api/student/transactions` → RecyclerView | ⚠️ PARTIAL | List loads; receipt timestamps display as raw string |
| **APP-03** ✅ | TransactionsAdapter → ReceiptActivity → `/api/student/receipt/{id}` | ✅ VERIFIED | Fixed in Phase 7; verified in Phase 12. `cashier_routes.py:520-532` writes 11-col row with BalanceBefore (col 7) and ItemsJson (col 11). See `.planning/phases/12-receipt-fcm-wiring/12-VERIFICATION.md`. |
| **APP-04** | `complete_sale` → balance deduction → HomeActivity balance refresh | ⚠️ PARTIAL | Balance updates on home screen; receipt shows ₱0.00 for past balance |
| **APP-05** | ApiClient.kt → error handling → Snackbar/error UI | ✅ WIRED | Error handling confirmed in all activities |
| **NOTF-01** ✅ | `complete_sale` → `send_low_balance_push()` → FCM → student device | ✅ VERIFIED | Fixed in Phase 7; verified in Phase 12. `cashier_routes.py:570-612` calls both `send_purchase_push()` and `send_low_balance_push()` in non-blocking try/except. `migrate_users_schema()` confirmed at `api_server.py:109-115`. See `.planning/phases/12-receipt-fcm-wiring/12-VERIFICATION.md`. |
| **NOTF-02** | Admin dashboard threshold config → `NOTF_THRESHOLD` env var | ✅ WIRED | Threshold configurable |
| **NFC-01** | `/api/nfc/register`, `/api/nfc/pay` → api_server.py | ✅ WIRED | Both endpoints exist and registered |
| **NFC-02** | NFCService → VirtualCards sheet (gspread) | ✅ WIRED | Sheets persistence confirmed, no in-memory state |
| **NFC-03** | `/api/nfc/pay` accepts token → Transactions sheet | ⚠️ PARTIAL | Backend accepts NFC token; `NFC Purchase` type not navigable to receipt in student app |
| **NFC-04** | `/api/nfc/pay` → dual auth (JWT + X-Device-Token) | ⚠️ PARTIAL | Backend verified; `mobile/android` has schema mismatches (body fields, missing endpoints) |
| **NFC-05** | docs/nfc-integration-guide.md → `mobile/android` reference | ⚠️ PARTIAL | Guide written; reference implementation (`mobile/android`) has broken API contracts |
| **DOC-01** | docs/architecture.md | ✅ VERIFIED | Accurate system overview |
| **DOC-02** | docs/api-reference.md | ⚠️ PARTIAL | 12 endpoints documented; cashier_routes blueprint endpoints undocumented |
| **DOC-03** | docs/google-sheets-schema.md | ✅ VERIFIED | 3-way write path discrepancy documented |
| **DOC-04** | docs/cashier-guide.md | ⚠️ PARTIAL | FCM not triggered by cashier POS path — not mentioned |
| **DOC-05** | docs/student-app.md | ✅ VERIFIED | Internally consistent |
| **DOC-06** | docs/nfc-integration-guide.md | ⚠️ PARTIAL | Accurate for backend; `mobile/android` broken contracts not called out |
| **DOC-07** | docs/admin-guide.md | ✅ VERIFIED | Product management accurately documented |
| **DOC-08** | docs/setup.md | ✅ VERIFIED | Setup steps accurate |

### Requirements with no cross-phase wiring (self-contained)

These requirements are fulfilled entirely within a single phase with no integration touchpoints to verify:

| Requirement | Phase | Notes |
|---|---|---|
| BUG-04 | Phase 1 | Admin login validation — self-contained in admin_dashboard.py |
| BUG-05 | Phase 1 | Atomic deduction — self-contained in api_server.py transaction handler |
| SEC-01 | Phase 1/2 | Logging hygiene — no external consumer |
| SEC-05 | Phase 1 | Test file secrets — no runtime integration |
| QUAL-04 | Phase 2 | Dead code removal — no integration to verify |
| QUAL-05 | Phase 2 | Library swap — no functional integration point |
| NOTF-02 | Phase 4 | Threshold config — read from env var, no cross-phase wiring |

---

## Tech Debt Table

| ID | Item | Severity | Affected Reqs | Fix |
|---|---|---|---|---|
| TD-01 | `cashier_request_card` WebSocket event emitted with no handler | 🔴 Critical | BUG-01 | Add `@socketio.on('cashier_request_card')` handler in cashier_routes.py that calls `arduino_bridge.read_card_with_timeout()` |
| TD-02 | ~~`migrate_users_schema()` not called at startup~~ **RESOLVED** (Phase 7 / verified Phase 12) | ✅ Resolved | NOTF-01 | `api_server.py:109-115` calls `migrate_users_schema()` at startup in non-fatal try/except |
| TD-03 | ~~Transactions sheet column mismatch — cashier writes 7 cols, schema expects 8 (`BalanceBefore` missing)~~ **RESOLVED** (Phase 7 / verified Phase 12) | ✅ Resolved | APP-03, APP-04 | `cashier_routes.py:520-532` writes 11-col row; `config_validator.py` updated to expect 11 cols (Phase 12) |
| TD-04 | Timestamp format mismatch — backend writes space, Android reads `'T'` | 🟠 High | APP-02, APP-03 | Either change backend to `datetime.isoformat()` or update `ReceiptActivity` to `"yyyy-MM-dd HH:mm:ss"` |
| TD-05 | `NFC Purchase` type not navigable to receipt | 🟠 High | NFC-03 | Add `"NFC Purchase"` to `TransactionsAdapter` navigation condition |
| TD-06 | `mobile/android` calls `/api/nfc/unregister` and `/api/nfc/status` (don't exist) | 🟠 High | NFC-04, NFC-05 | Add endpoints to api_server.py OR update nfc-integration-guide to note `mobile/android` is reference only for HCE, not API |
| TD-07 | `cashier_routes.py` uses `db.worksheet('Products')` instead of `ensure_products_sheet()` | 🟡 Medium | PROD-04, PROD-05 | Import and call `ensure_products_sheet()` in cashier_routes |
| TD-08 | 4× `socketio.emit('card_error', {'message': str(e)})` in admin_dashboard.py leak exception text | 🟡 Medium | QUAL-01 | Emit generic message; log full exception server-side only |
| TD-09 | `api_server.py` uses random `JWT_SECRET` fallback instead of requiring env var | 🟡 Medium | SEC-02 | Add startup guard matching admin_dashboard.py |
| TD-10 | `cashier-guide.md` doesn't document that FCM is not triggered by cashier POS path | 🟡 Medium | DOC-04 | Add operational note to cashier-guide.md |
| TD-11 | `api-reference.md` missing all cashier blueprint endpoints | 🟡 Medium | DOC-02 | Document `/cashier/api/*` routes |
| TD-12 | `mobile/android` LoginResponse maps `student_id` but backend returns `id` | 🟢 Low | NFC-04 | Fix SerializedName in mobile/android (low priority — not primary app) |

---

## Recommended Fix Priority Order

All fixes below are **needed before v1.0 can be called production-ready**.

### P0 — Immediate (blocks primary use case)

1. **TD-01** — Wire `cashier_request_card` → ArduinoBridge. Without this, no RFID card payment can complete.
2. **TD-03** — Add `balance_before` column to cashier_routes writes. Without this, every receipt shows ₱0.00 balance history.
3. **TD-02** — Call `migrate_users_schema()` at api_server startup. Without this, FCM registration fails silently on fresh deploys.

### P1 — High (breaks visible student features)

4. **TD-04** — Fix timestamp format mismatch (choose one side: backend ISO 8601 or Android space format).
5. **TD-05** — Add `"NFC Purchase"` to receipt navigation in `TransactionsAdapter`.

### P2 — Medium (integration consistency, documentation)

6. **TD-07** — Use `ensure_products_sheet()` in cashier_routes.
7. **TD-08** — Remove exception text from WebSocket `card_error` events.
8. **TD-09** — Add `JWT_SECRET` startup guard to api_server.py.
9. **TD-10** — Document FCM gap in cashier-guide.md.
10. **TD-11** — Document cashier blueprint endpoints in api-reference.md.

### P3 — Low (reference codebase cleanup)

11. **TD-06** — Add missing NFC endpoints OR clarify `mobile/android` scope in docs.
12. **TD-12** — Fix `LoginResponse` field mapping in `mobile/android`.

---

## Overall Integration Assessment

**The individual phases are well-implemented. The system does not yet work end-to-end.**

The Phase 1–2 quality work (centralized logging, UID normalization, singleton state) is correctly wired and consumed across all phases — this was done well. The Phase 3 product management admin UI is correctly connected. The Phase 4 student app is correctly wired for login, balance, and transaction list.

The failures are in the **handoff boundaries** between phases:
- Phase 1 (cashier POS) and Phase 2 (arduino_bridge) were built in the same phase but their runtime wiring was never completed in the cashier path
- Phase 4 (student app) and Phase 1 (cashier_routes transaction writes) never agreed on a Sheets column schema
- Phase 4 (FCM) and Phase 4 (migrate_transactions.py) were written in the same phase but the migration was not wired to startup
- Phase 5 (NFC types) and Phase 4 (TransactionsAdapter) were never aligned on the `"NFC Purchase"` string

**12 tech debt items identified. 3 are critical blockers. All 12 should be resolved before the v1.0 milestone is declared complete.**

---

*Integration audit produced: 2026-03-01*  
*Coverage: 6 phases, 41 requirements, 5 E2E flows*

---

---

# BankongSeton v1.0 — Cross-Phase Integration Audit (Part 2)

**Date:** 2026-03-02  
**Auditor:** gsd-integration-checker  
**Scope:** 11 completed phases — PROD, SEC, NFC, WEB requirement groups; deep read of all backend + both Android projects  
**Verdict:** ⚠️ PARTIAL — Core student app flows work; NFC payment is broken end-to-end; 2 security gaps

---

## Executive Summary

Three of the four primary E2E flows work correctly. The **NFC tap-to-pay flow** — the system's core differentiating feature — is broken at **two independent points** that each alone prevent any payment from completing. Both breaks are small and fixable. Two security gaps must be resolved before production deployment.

| Severity | Count | Items |
|----------|-------|-------|
| 🔴 Critical | 2 | NFC registration field mismatch (GAP-01), APDU ↔ `/api/nfc/pay` contract gap (GAP-02) |
| 🟠 High | 2 | Hardcoded cashier JWT fallback (GAP-03), hardcoded cashier credentials (GAP-04) |
| 🟡 Medium | 2 | WEB-02 NFC simulation not implemented (GAP-05), Transactions Log column count mismatch |
| 🟢 Low | 2 | Two Android projects — NFC capability not in primary app, orphaned `notifications.py` and `CardReaderState` |

---

## E2E Flow Status

| # | Flow | Status | Evidence |
|---|------|--------|----------|
| 1 | Student NFC payment: tap → balance deduct → receipt | 🔴 **BROKEN** | GAP-01: `currentToken` always null; GAP-02: `device_token` has no path to cashier HTTP header |
| 2 | Admin product management → cashier POS display | ✅ **COMPLETE** | `web_app.py /products` → Products Sheet ↔ `cashier_routes.py` reads same sheet |
| 3 | Student balance check + low-balance FCM notification | ✅ **COMPLETE** | `HomeActivity` → `/api/student/balance` → `fcm_sender.py` → Firebase → `FCMService.kt` all wired |
| 4 | Web dashboard real-time view (no Android dependency) | ✅ **COMPLETE** | `dashboard.html` socket.io + 8 event handlers + Flask-SocketIO emitters all verified |

---

## Detailed Findings

### GAP-01 — NFC Registration Response Field Mismatch 🔴 CRITICAL

**Break point:** `mobile/android/ApiClient.kt` `NfcRegistrationResponse`

Backend (`/api/nfc/register`) returns:
```json
{ "virtual_card_token": "...", "device_token": "...", "money_card": "...", "message": "..." }
```

Android model expects:
```kotlin
data class NfcRegistrationResponse(
    val virtual_token: String,   // WRONG — backend sends "virtual_card_token"
    val expires_at: String       // WRONG — backend doesn't send this field
)
```

`NfcManager.kt` line 110:
```kotlin
BankoHceService.currentToken = response.body()!!.virtual_token
// virtual_token is always null (Gson silently ignores unknown fields)
// → currentToken = null
// → every NFC tap returns SW_NO_TOKEN (0x6A82)
```

**Fix:**
```kotlin
// mobile/android/ApiClient.kt
data class NfcRegistrationResponse(
    val virtual_card_token: String,
    val device_token: String,
    val money_card: String,
    val message: String
)

// NfcManager.kt line 110
BankoHceService.currentToken = response.body()!!.virtual_card_token
```

**Affects:** NFC-01, NFC-02, NFC-03, NFC-04, NFC-05

---

### GAP-02 — APDU Protocol vs. `/api/nfc/pay` Two-Credential Contract 🔴 CRITICAL

**Break point:** `BankoHceService.kt` transmits only one value; `/api/nfc/pay` requires two.

`BankoHceService.processCommandApdu()` responds to a GET_TOKEN command with:
```kotlin
virtualToken.toByteArray(Charsets.UTF_8)   // sends virtual_card_token bytes only
```

`api_server.py /api/nfc/pay` requires:
- `virtual_card_token` — in request JSON body
- `X-Device-Token` — in HTTP request header

The cashier terminal receives only the `virtual_card_token` from the APDU exchange. There is no coded or documented path for `device_token` to reach the cashier terminal as an HTTP header.

**Recommended fix (minimal change — server-side lookup):**
Change `/api/nfc/pay` to accept only `virtual_card_token` and look up `device_token` server-side from the VirtualCards sheet. This removes the need to change the APDU protocol.

**Affects:** NFC-01, NFC-04

---

### GAP-03 — Cashier Blueprint JWT Insecure Fallback 🟠 HIGH (Security)

**File:** `backend/dashboard/cashier/cashier_routes.py` line ~95

```python
# cashier_routes.py
JWT_SECRET = os.getenv("JWT_SECRET", "bangko-jwt-secret-2026")   # ← hardcoded fallback

# api_server.py and web_app.py (Phase 1 fix already applied):
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET environment variable is required")
```

If `JWT_SECRET` is absent from the environment, cashier JWTs are signed with a publicly known key. Any attacker can forge a cashier JWT and access the cashier endpoints.

**Fix:** Remove the default; raise `RuntimeError` as the other two servers do.

**Affects:** SEC-02

---

### GAP-04 — Hardcoded Cashier Credentials 🟠 HIGH (Security)

**File:** `backend/dashboard/cashier/cashier_routes.py` line ~139

```python
if username == "cashier" and password == "cashier123":
```

Credentials are committed to source control. Cannot be rotated without a code change and redeployment.

**Fix:** Read from environment variables `CASHIER_USERNAME` / `CASHIER_PASSWORD`.

**Affects:** SEC-01

---

### GAP-05 — WEB-02 NFC Simulation Not Implemented 🟡 MEDIUM

WEB-02 requires: "NFC simulation UI for testing cashier payments without physical hardware."

Zero matches for `nfc_sim`, `simulate_nfc`, `nfc_simulation`, or `/api/nfc` across all 5 dashboard templates (`dashboard.html`, `products.html`, `transactions.html`, `login.html`, `students.html`). The feature was specified but not built.

**Affects:** WEB-02

---

### Transactions Log Column Count Mismatch 🟡 MEDIUM

`cashier_routes.py complete_sale()` writes **11 columns** to the Transactions sheet (including `ItemsJson`).  
`web_app.py load_balance()` writes **9 columns** (no `ItemsJson`).

If the sheet header row has 11 columns, rows written by `web_app.py` will have blank cells in columns 10–11. `get_all_records()` may misalign values in analytics queries.

**Affects:** PROD-06

---

### Orphaned Code (Low Risk)

| Item | Location | Reason |
|------|----------|--------|
| `EmailNotifier`, `NotificationManager` | `backend/notifications.py` | Never imported; FCM path via `fcm_sender.py` is active |
| `CardReaderState` singleton | `backend/utils.py` | Defined but never instantiated; `api_server.py` uses its own module-level Arduino globals |

---

## Cross-Phase Wiring — Connected (verified in this audit pass)

| API / Export | From | Used By | Status |
|---|---|---|---|
| `POST /api/auth/login` | `api_server.py` | `student_app_v2/LoginActivity.kt` | ✅ Fields match; session token returned and stored |
| `GET /api/student/balance` | `api_server.py` | `student_app_v2/HomeActivity.kt` | ✅ Balance displayed; SecureStorage persistence |
| `GET /api/student/transactions` | `api_server.py` | `student_app_v2/TransactionsActivity.kt` | ✅ Offset pagination wired |
| `POST /api/users/fcm-token` | `api_server.py` | `student_app_v2/LoginActivity.kt` | ✅ FCMService buffers token; sent after login |
| `POST /api/auth/logout` | `api_server.py` | `student_app_v2/SettingsActivity.kt` | ✅ Removes from `active_sessions{}` |
| `fcm_sender.send_low_balance_push()` | `backend/api/fcm_sender.py` | `api_server.py` post-transaction | ✅ Called after balance deduction |
| `FCMService.kt` | `student_app_v2` | Firebase → `onMessageReceived` | ✅ Notification displayed |
| WebSocket `new_transaction` / `balance_update` | `web_app.py` SocketIO emitters | `dashboard.html` JS handlers (8 confirmed) | ✅ Real-time updates wired |
| `POST /api/nfc/register` | `api_server.py` | `mobile/android/NfcManager.kt` | ❌ Response field names broken (GAP-01) |
| `POST /api/nfc/pay` | `api_server.py` | cashier terminal (expected) | ❌ Requires `device_token` header with no supply path (GAP-02) |

---

## Requirements Integration Map

| Requirement | Integration Path | Status | Issue |
|-------------|-----------------|--------|-------|
| PROD-01 Balance check | `HomeActivity` → `GET /api/student/balance` → Money Sheet | ✅ WIRED | — |
| PROD-02 Transaction history | `TransactionsActivity` → `GET /api/student/transactions` → Transactions Sheet | ✅ WIRED | Endpoint + model confirmed |
| PROD-03 Cashier NFC payment | `BankoHceService` → APDU → cashier → `POST /api/nfc/pay` | ❌ BROKEN | GAP-01 (null token) + GAP-02 (missing device_token path) |
| PROD-04 Product management | `web_app.py /products` → Products Sheet ↔ `cashier_routes.py` | ✅ WIRED | — |
| PROD-05 Low-balance FCM | `api_server.py` → `fcm_sender.py` → Firebase → `FCMService.kt` | ✅ WIRED | — |
| PROD-06 Transaction reports | `web_app.py` analytics → Transactions Sheet | ⚠️ PARTIAL | Column count mismatch (11 vs 9) may skew report data |
| SEC-01 Auth on endpoints | `require_auth` (student), JWT cookie (cashier/admin) | ⚠️ PARTIAL | Cashier credentials hardcoded in source (GAP-04) |
| SEC-02 Env vars, no secrets | `api_server.py` + `web_app.py` enforce correctly | ⚠️ PARTIAL | Cashier blueprint has known-public JWT fallback (GAP-03) |
| SEC-03 Input validation | Amount > 0, student_id checks in key endpoints | ✅ WIRED | Self-contained within `api_server.py` |
| SEC-04 Logout invalidation | `POST /api/auth/logout` removes from `active_sessions{}` | ✅ WIRED | Self-contained |
| NFC-01 HCE service | `BankoHceService.kt` registered in Manifest, correct AID | ⚠️ PARTIAL | Service exists; payment broken (GAP-01 + GAP-02) |
| NFC-02 Backend NFC endpoints | `POST /api/nfc/register`, `POST /api/nfc/pay` in `api_server.py` | ⚠️ PARTIAL | Register response contract broken (GAP-01) |
| NFC-03 Card emulation | AID matches `hce_service.xml` ↔ `BankoHceService.kt`; APDU SELECT handled | ⚠️ PARTIAL | Token always null after registration (GAP-01) |
| NFC-04 Non-breaking detection | `BankoHceService.onDeactivated()` resets `isPaymentAuthorized` | ✅ WIRED | Self-contained |
| NFC-05 Scaffolded routes | `/api/nfc/register`, `/api/nfc/pay` present | ⚠️ PARTIAL | Contract broken (GAP-01); unusable without GAP-02 fix |
| WEB-01 Standalone dashboard | `web_app.py` runs independently | ✅ WIRED | — |
| WEB-02 NFC simulation | Expected in dashboard templates | ❌ UNWIRED | GAP-05: feature not implemented |
| WEB-03 Responsive UI | Templates use Bootstrap/responsive CSS | ✅ WIRED | (sampled) |
| WEB-04 Real-time WebSocket | `dashboard.html` socket.io + 8 handlers + Flask-SocketIO emitters | ✅ WIRED | — |

**Requirements with no cross-phase wiring (self-contained):**
- **SEC-03** — Input validation within `api_server.py`; no cross-phase dependency
- **SEC-04** — `active_sessions{}` dict is module-scoped within `api_server.py`
- **NFC-04** — `BankoHceService.onDeactivated()` internal to HCE service
- **WEB-03** — CSS/layout; no backend wiring needed

---

## Prioritised Fix List

### P0 — NFC Payment Blockers (both required before any NFC payment can complete)

**Fix 1 (GAP-01):** Rename fields in `NfcRegistrationResponse` to match backend
- File: `mobile/android/ApiClient.kt`
- Fields: `virtual_card_token`, `device_token`, `money_card`, `message` (remove `virtual_token`, `expires_at`)
- Also update `NfcManager.kt` line 110: `BankoHceService.currentToken = response.body()!!.virtual_card_token`

**Fix 2 (GAP-02):** Remove `X-Device-Token` header requirement from `/api/nfc/pay`
- File: `backend/api/api_server.py`
- Change: Look up `device_token` server-side from VirtualCards sheet using `virtual_card_token` as key
- No APDU protocol change needed

### P1 — Security (before any production deployment)

**Fix 3 (GAP-03):** Remove cashier JWT hardcoded fallback
- File: `backend/dashboard/cashier/cashier_routes.py` line ~95
- Change: `os.getenv("JWT_SECRET", "bangko-jwt-secret-2026")` → raise `RuntimeError` if absent

**Fix 4 (GAP-04):** Externalize cashier login credentials
- File: `backend/dashboard/cashier/cashier_routes.py` line ~139
- Change: Read `CASHIER_USERNAME` / `CASHIER_PASSWORD` from environment variables

### P2 — Data Integrity

**Fix 5:** Align Transactions Log column counts between `cashier_routes.py` and `web_app.py`

### P3 — Feature Completeness

**Fix 6 (GAP-05):** Implement WEB-02 NFC simulation panel in dashboard template

**Fix 7 (optional):** Merge NFC capability (`BankoHceService` + `NfcManager`) into `student_app_v2`, or consolidate into one Android project

---

*Integration audit (Part 2) produced: 2026-03-02*  
*Coverage: 11 phases, PROD/SEC/NFC/WEB requirement groups, 4 E2E flows*  
*Files read: 21 source files across backend/ and both Android projects*
