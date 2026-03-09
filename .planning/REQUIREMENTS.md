# Requirements: BankongSeton v1.3 — Stability, Performance & Quality

**Defined:** 2026-03-09
**Milestone:** v1.3
**Core Value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app — reliably, quickly, and correctly.

**Source:** Full codebase audit across backend, dashboard, Android, and iOS (~197 issues found across all components)

---

## Priority Tiers

- **P0 — Critical:** Data integrity, security, or crash-level bugs that affect real users right now
- **P1 — High:** Broken features, severe performance, or UX blockers
- **P2 — Medium:** Correctness bugs that have workarounds, moderate performance, or code quality issues that cause maintenance drag
- **P3 — Low:** Polish, minor UX, cleanup

---

## REQ-SEC: Security

| ID | Priority | Requirement | Source |
|----|----------|-------------|--------|
| REQ-SEC-01 | P0 | Restrict CORS in production WSGI — `wsgi.py` currently allows `*` (all origins) | Backend WSGI-01 |
| REQ-SEC-02 | P0 | Prevent NFC payment authorization bypass — `BankoHceService.isPaymentAuthorized` and `currentToken` are public writable static fields; any code can authorize a payment without biometric/PIN | Android SEC-01 |
| REQ-SEC-03 | P0 | Remove `usesCleartextTraffic="true"` from Android release manifest — all API traffic must use HTTPS | Android SEC-02 |
| REQ-SEC-04 | P1 | Block NFC token from backup — Android backup rules expose the card token to Google Drive backup | Android SEC-03 |
| REQ-SEC-05 | P1 | Replace PIN plaintext storage — PIN stored in EncryptedSharedPreferences but is recoverable as plaintext; use a one-way hash | Android SEC-04 |
| REQ-SEC-06 | P1 | Remove hardcoded Finance dashboard credential default (`finance2025`) with no startup guard; apply same pattern as `FLASK_SECRET_KEY` guard | Dashboard SEC-01 |

---

## REQ-BUG: Critical Backend Bugs

| ID | Priority | Requirement | Source |
|----|----------|-------------|--------|
| REQ-BUG-01 | P0 | Eliminate race condition on balance debit — no atomic read-modify-write; concurrent requests can double-spend student balance | Backend BUG-01 |
| REQ-BUG-02 | P0 | Fix `@admin_required` decorator undefined on 3 dashboard routes (`add_category`, `delete_category`, `void_transaction`) — raises `NameError` on first call | Dashboard BUG-01 |
| REQ-BUG-03 | P0 | Fix `get_db()` undefined in `_ensure_categories_sheet()` — raises `NameError` on all `/api/categories` calls | Dashboard BUG-02 |
| REQ-BUG-04 | P0 | Guard email receipt block in cashier transaction — unguarded exception can return 500 on an already-committed transaction, corrupting client state | Backend BUG-12 |
| REQ-BUG-05 | P1 | Fix `card_error` socket event key mismatch — backend emits `data.message` but frontend listens for `data.error`; modal always shows `undefined` | Dashboard BUG-11 |
| REQ-BUG-06 | P1 | Fix duplicate TXN IDs — `TXNYYYYMMDDHHMMSS` format collides for concurrent transactions in the same second | Backend BUG-05 |
| REQ-BUG-07 | P1 | Fix `WriteQueue` infinite retry loop — a repeatedly-failing item loops forever instead of being dropped with an error log | Backend RES-03 |
| REQ-BUG-08 | P1 | Fix `active_sessions` dict never expiring and not multi-worker safe — breaks under gunicorn multi-process deployment | Backend BUG-04 |
| REQ-BUG-09 | P2 | Remove hardcoded column C for balance in cashier transaction — use column lookup by header name | Backend BUG-02 |
| REQ-BUG-10 | P2 | Fix PWA service worker caching non-existent files (`style.css`, `app.js`) — PWA install fails entirely | Dashboard BUG-22 |
| REQ-BUG-11 | P2 | Remove polling of non-existent `/api/queue/status` and `/api/queue/process` endpoints — `pwa.js` and `sync-status.js` generate constant 404s every 30 seconds | Dashboard BUG-24 |
| REQ-BUG-12 | P2 | Fix duplicate event listeners stacking in `products.html` `renderTable()` — causes multiple API calls per click | Dashboard BUG-17 |

---

## REQ-BUG-MOB: Mobile App Bugs

| ID | Priority | Requirement | Source |
|----|----------|-------------|--------|
| REQ-BUG-MOB-01 | P0 | Fix iOS `AuthManager.handleCardLost()` — saves `isCardLost` flag then immediately clears it via `clearAll()`; lost card state never persists across app restarts | iOS BUG-01 |
| REQ-BUG-MOB-02 | P0 | Fix Android `handleCardLost()` — same `isCardLost` flag deleted immediately after being set; never persists | Android BUG-09 |
| REQ-BUG-MOB-03 | P0 | Remove `fatalError()` calls in iOS `APIClient.swift` — two force-unwrap paths will crash production app on any URL construction error | iOS BUG-02 |
| REQ-BUG-MOB-04 | P1 | Fix iOS CARD_LOST vs UNAUTHORIZED misclassification — a blocked card shows "wrong PIN" to student instead of "card reported lost" | iOS BUG-03 |
| REQ-BUG-MOB-05 | P1 | Handle 401 token expiry in iOS — user is stuck in a broken authenticated state indefinitely with no re-auth prompt | iOS BUG-04 |
| REQ-BUG-MOB-06 | P1 | Fix Android budget calculation — spending sum counts top-ups as expenses; should only count Purchase/NFC Purchase transaction types | Android BUG-01 |
| REQ-BUG-MOB-07 | P1 | Fix Android RecyclerView `isClickable` not reset on recycled ViewHolders — taps silently ignored on reused cells | Android BUG-02 |
| REQ-BUG-MOB-08 | P2 | Fix Android `ReceiptActivity` fragile unchecked cast `parent.parent as LinearLayout` — crash risk if layout changes | Android BUG-03 |
| REQ-BUG-MOB-09 | P2 | Fix Android NFC payment success detection via `onResume` polling — unreliable; can produce false-positive payment completions | Android BUG-04 |

---

## REQ-PERF: Performance

| ID | Priority | Requirement | Source |
|----|----------|-------------|--------|
| REQ-PERF-01 | P0 | Wire up existing `cache.py` TTLCache in `api_server.py` — `users_sheet.get_all_records()` is called uncached on EVERY request; cache already exists but is never imported | Backend PERF-01, QUAL-02 |
| REQ-PERF-02 | P1 | Reduce NFC payment path from 7–9 sequential Google Sheets API calls to ≤3 — batch reads; estimated 1.4–4.5s latency improvement | Backend PERF-03 |
| REQ-PERF-03 | P1 | Cache users sheet per request in cashier transaction — currently read 3× per single cashier transaction | Backend PERF-04 |
| REQ-PERF-04 | P1 | Add per-user transaction query — currently all transactions for ALL users are fetched and filtered in Python | Backend PERF-02 |
| REQ-PERF-05 | P2 | Wire up existing `ConnectionPool` in `connection_pool.py` — fully implemented but never used | Backend QUAL-03 |
| REQ-PERF-06 | P2 | Fix Android budget load — currently fetches all 200 transactions client-side just to sum monthly spend | Android PERF-01 |
| REQ-PERF-07 | P2 | Fix iOS `BudgetViewModel` — same issue; fetches 200 transactions to calculate monthly spend client-side | iOS PERF-01 |
| REQ-PERF-08 | P2 | Add budget summary endpoint to API — serves pre-calculated monthly spend server-side to avoid full transaction fetch in both mobile apps | Backend PERF-05 |
| REQ-PERF-09 | P2 | Fix iOS `DateFormatter` allocation on every render pass in `ReceiptView` and `BudgetViewModel` — move to static/cached instance | iOS PERF-02 |
| REQ-PERF-10 | P2 | Replace `notifyDataSetChanged()` with `DiffUtil` in Android `TransactionsAdapter` | Android PERF-02 |

---

## REQ-CURR: Currency Symbol (₱ not ฿)

| ID | Priority | Requirement | Source |
|----|----------|-------------|--------|
| REQ-CURR-01 | P1 | Fix Thai Baht ฿ symbol in FCM push notification messages — should be Philippine Peso ₱ | Backend FCM-01 |
| REQ-CURR-02 | P1 | Fix Thai Baht ฿ symbol in cashier UI and dashboard templates — audit and replace all occurrences | Dashboard UI-01 |

---

## REQ-UX: User Experience

| ID | Priority | Requirement | Source |
|----|----------|-------------|--------|
| REQ-UX-01 | P2 | Fix iOS budget input overwritten by server load — if user types before load completes, value is replaced | iOS UX-01 |
| REQ-UX-02 | P2 | Add empty state to iOS transactions list — currently shows nothing with no message | iOS UX-02 |
| REQ-UX-03 | P2 | Show cached/last-known balance on iOS while loading instead of ₱0.00 | iOS UX-03 |
| REQ-UX-04 | P2 | Fix iOS login PIN field content type — `.textContentType(.password)` causes iOS to offer saved password autofill instead of numeric PIN | iOS UX-04 |
| REQ-UX-05 | P2 | Fix iOS keyboard avoidance on login screen — Sign In button hidden behind keyboard on iPhone SE | iOS UX-05 |

---

## REQ-QUAL: Code Quality & Tech Debt

| ID | Priority | Requirement | Source |
|----|----------|-------------|--------|
| REQ-QUAL-01 | P1 | Consolidate dual auth systems — `opaque_session_tokens` for students and JWT for cashier both active simultaneously; `generate_jwt_token()` is dead code | Backend BUG-03 |
| REQ-QUAL-02 | P1 | Eliminate `admin_dashboard.py` / `web_app.py` ~90% code duplication — fixes must currently be applied twice | Dashboard QUALITY-01 |
| REQ-QUAL-03 | P2 | Deduplicate `get_philippines_time()` — defined in 4 separate files; extract to shared utility | Backend QUAL-04 |
| REQ-QUAL-04 | P2 | Remove bare `except:` clauses throughout backend — replace with specific exception types | Backend QUAL-05 |
| REQ-QUAL-05 | P2 | Fix null JSON body crashes — multiple endpoints crash if `Content-Type: application/json` header is present but body is empty | Backend BUG-06 |
| REQ-QUAL-06 | P2 | Fix `sys.path` mutation inside request handler — move to module level or remove | Backend QUAL-06 |
| REQ-QUAL-07 | P2 | Fix Firebase double-init race condition in backend | Backend BUG-07 |
| REQ-QUAL-08 | P2 | Replace expiring Instagram CDN token URLs used as login background images in dashboard | Dashboard QUALITY-07 |
| REQ-QUAL-09 | P2 | Deduplicate `isPurchaseType` logic in iOS — defined in two files | iOS QUAL-01 |
| REQ-QUAL-10 | P2 | Move production server URL out of hardcoded `ApiClient.kt` into build config / environment | Android QUAL-01 |
| REQ-QUAL-11 | P2 | Move production server URL out of hardcoded `APIEndpoints.swift` into build config / environment | iOS QUAL-01 |
| REQ-QUAL-12 | P3 | Fix Android unscoped `CoroutineScope(Dispatchers.IO).launch` in `NfcManager` — causes memory leaks on Activity destroy | Android PERF-03 |
| REQ-QUAL-13 | P3 | Move iOS theme preference from Keychain to UserDefaults — Keychain is for secrets, not UI preferences | iOS QUAL-02 |

---

## Scope Summary

| Category | P0 | P1 | P2 | P3 | Total |
|----------|----|----|----|----|-------|
| Security | 3 | 3 | 0 | 0 | 6 |
| Backend Bugs | 4 | 4 | 4 | 0 | 12 |
| Mobile Bugs | 3 | 4 | 2 | 0 | 9 |
| Performance | 1 | 4 | 5 | 0 | 10 |
| Currency Fix | 0 | 2 | 0 | 0 | 2 |
| UX | 0 | 0 | 5 | 0 | 5 |
| Code Quality | 0 | 2 | 9 | 2 | 13 |
| **Total** | **11** | **19** | **25** | **2** | **57** |

**P0 items (11):** Must ship in v1.3 — data integrity, security, and crash-level bugs
**P1 items (19):** Should ship in v1.3 — broken features and severe performance
**P2 items (25):** Best-effort in v1.3 — correctness bugs with workarounds, code quality
**P3 items (2):** Can defer to v1.4
