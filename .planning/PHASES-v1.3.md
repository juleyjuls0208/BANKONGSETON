# BankongSeton v1.3 — Phase Index

**Milestone:** v1.3 Stability, Performance & Quality
**Created:** 2026-03-09
**Phases:** 25–34 (10 phases)
**Requirements:** 57 total across 7 categories

---

## Milestone Goal

Fix every known bug, close security holes, activate unused performance infrastructure (cache.py + resilience.py exist but are never imported), and clean up tech debt across all four components: Flask backend, dashboard/web app, Android app, iOS app.

---

## Phase Overview

| Phase | Name | Count | Priority | Component(s) |
|-------|------|-------|----------|--------------|
| **25** | Critical Backend Stability | 4 reqs | P0 | Backend |
| **26** | Critical Dashboard Stability | 3 reqs | P0/P1 | Dashboard |
| **27** | Critical Mobile Fixes | 5 reqs | P0 | Android + iOS |
| **28** | Backend Performance: Cache Infrastructure | 3 reqs | P1 | Backend |
| **29** | Android Security & P1 Bugs | 4 reqs | P1 | Android |
| **30** | iOS Bugs & UX | 7 reqs | P1/P2 | iOS |
| **31** | Dashboard & Backend P1 Fixes | 8 reqs | P1 | Backend + Dashboard |
| **32** | Mobile Budget Performance | 5 reqs | P2 | Backend + Android + iOS |
| **33** | Backend Code Quality | 7 reqs | P2 | Backend |
| **34** | Dashboard, Mobile Quality & Final Cleanup | 11 reqs | P2/P3 | Dashboard + Android + iOS |

---

## Phase Details

### Phase 25 — Critical Backend Stability
**Goal:** The backend cannot double-spend, crash on email failure after a committed transaction, serve to unauthorized origins, or skip its TTL cache.

**Requirements:**
- `REQ-SEC-01` (P0) — Restrict CORS wildcard in production wsgi.py
- `REQ-BUG-01` (P0) — Eliminate race condition on balance debit (double-spend risk)
- `REQ-BUG-04` (P0) — Guard email receipt block (unguarded → 500 on committed transaction)
- `REQ-PERF-01` (P0) — Wire up existing cache.py TTLCache in api_server.py

**Key success check:** Two concurrent payment requests to the same card → exactly one deduction.

---

### Phase 26 — Critical Dashboard Stability
**Goal:** No dashboard route crashes with NameErrors; Thai Baht ฿ is gone from every UI string.

**Requirements:**
- `REQ-BUG-02` (P0) — Fix `@admin_required` undefined on 3 routes → NameError
- `REQ-BUG-03` (P0) — Fix `get_db()` undefined in `_ensure_categories_sheet()` → NameError
- `REQ-CURR-02` (P1) — Replace ฿ with ₱ in cashier UI and dashboard templates

**Key success check:** All admin routes and /api/categories return 200 without crashing.

---

### Phase 27 — Critical Mobile Fixes
**Goal:** Lost card state persists across restarts on both apps; iOS never crashes via fatalError; Android release uses HTTPS only; NFC authorization is not publicly bypassable.

**Requirements:**
- `REQ-BUG-MOB-01` (P0) — Fix iOS handleCardLost immediately clearing itself
- `REQ-BUG-MOB-02` (P0) — Fix Android handleCardLost immediately clearing itself
- `REQ-BUG-MOB-03` (P0) — Remove fatalError() in iOS APIClient.swift
- `REQ-SEC-02` (P0) — Prevent Android NFC payment authorization bypass (public static fields)
- `REQ-SEC-03` (P0) — Remove usesCleartextTraffic="true" from Android release manifest

**Key success check:** Report lost card → kill app → relaunch → lost state visible on both platforms.

**Note:** Can run in parallel with phases 25/26 (independent mobile component).

---

### Phase 28 — Backend Performance: Cache Infrastructure
**Goal:** NFC payment path drops from 7–9 Sheets API calls to ≤3; cashier transaction reads users sheet once not thrice; per-user transaction query filters at sheet level.

**Requirements:**
- `REQ-PERF-02` (P1) — Reduce NFC payment path from 7–9 to ≤3 API calls
- `REQ-PERF-03` (P1) — Cache users sheet per request in cashier transaction (currently read 3×)
- `REQ-PERF-04` (P1) — Add per-user transaction query (currently all-users fetch + Python filter)

**Depends on:** Phase 25 (cache.py wired first)

**Key success check:** NFC tap-to-pay latency drops measurably; cashier transaction handler touches Sheets API ≤3× total.

---

### Phase 29 — Android Security & P1 Bugs
**Goal:** Android backup doesn't expose the NFC token; PIN stored as hash only; budget counts purchases only; RecyclerView taps always fire.

**Requirements:**
- `REQ-SEC-04` (P1) — Block NFC token from Android backup (Google Drive exposure)
- `REQ-SEC-05` (P1) — Replace PIN plaintext storage with one-way hash
- `REQ-BUG-MOB-06` (P1) — Fix Android budget calculation (top-ups counted as expenses)
- `REQ-BUG-MOB-07` (P1) — Fix RecyclerView isClickable not reset on recycled ViewHolders

**Depends on:** Phase 27 (mobile P0 fixes done)

---

### Phase 30 — iOS Bugs & UX
**Goal:** iOS correctly identifies lost card vs unauthorized; handles token expiry; and resolves 5 UX issues on the budget, transactions, and login screens.

**Requirements:**
- `REQ-BUG-MOB-04` (P1) — Fix CARD_LOST vs UNAUTHORIZED misclassification
- `REQ-BUG-MOB-05` (P1) — Handle 401 token expiry (stuck broken state)
- `REQ-UX-01` (P2) — Fix budget input overwritten by server load
- `REQ-UX-02` (P2) — Add empty state to iOS transactions list
- `REQ-UX-03` (P2) — Show cached balance while loading (not ₱0.00)
- `REQ-UX-04` (P2) — Fix PIN field content type (triggers password autofill)
- `REQ-UX-05` (P2) — Fix keyboard avoidance on login screen (iPhone SE)

**Depends on:** Phase 27 (mobile P0 fixes done)

---

### Phase 31 — Dashboard & Backend P1 Fixes
**Goal:** Socket errors show real messages; TXN IDs never collide; WriteQueue drops bad items; sessions expire in multi-worker deployment; Finance credential guarded; auth consolidated; dashboard code deduplicated; FCM uses ₱.

**Requirements:**
- `REQ-BUG-05` (P1) — Fix card_error socket event key mismatch (modal shows "undefined")
- `REQ-BUG-06` (P1) — Fix duplicate TXN IDs (same-second collision)
- `REQ-BUG-07` (P1) — Fix WriteQueue infinite retry loop
- `REQ-BUG-08` (P1) — Fix active_sessions never expiring / not multi-worker safe
- `REQ-SEC-06` (P1) — Remove hardcoded Finance credential default with startup guard
- `REQ-QUAL-01` (P1) — Consolidate dual auth systems (opaque tokens + JWT dead code)
- `REQ-QUAL-02` (P1) — Eliminate admin_dashboard.py / web_app.py ~90% code duplication
- `REQ-CURR-01` (P1) — Fix ฿ symbol in FCM push notification messages → ₱

**Depends on:** Phase 26 (dashboard P0 done), Phase 28 (backend perf done)

**Note:** Largest phase (8 items). May spawn 3–4 plans.

---

### Phase 32 — Mobile Budget Performance
**Goal:** Budget calculation no longer requires loading 200 transactions on either mobile platform; new server endpoint serves pre-aggregated spend; iOS DateFormatter is not re-allocated on every render.

**Requirements:**
- `REQ-PERF-06` (P2) — Fix Android budget: currently fetches all 200 transactions client-side
- `REQ-PERF-07` (P2) — Fix iOS BudgetViewModel: same full-fetch issue
- `REQ-PERF-08` (P2) — Add GET /api/budget-summary endpoint (pre-calculated monthly spend)
- `REQ-PERF-09` (P2) — Fix iOS DateFormatter re-allocation on every render pass
- `REQ-PERF-10` (P2) — Replace notifyDataSetChanged() with DiffUtil in Android TransactionsAdapter

**Depends on:** Phase 28 (backend perf groundwork), Phase 29, Phase 30 (mobile P1 done)

---

### Phase 33 — Backend Code Quality
**Goal:** Backend has one canonical time utility; no bare excepts; no null-body crashes; sys.path mutations at module level; ConnectionPool wired; Firebase initializes safely; balance column resolved by header name.

**Requirements:**
- `REQ-BUG-09` (P2) — Remove hardcoded column C for balance (use header-name lookup)
- `REQ-QUAL-03` (P2) — Deduplicate get_philippines_time() (defined in 4 files)
- `REQ-QUAL-04` (P2) — Remove bare except: clauses throughout backend
- `REQ-QUAL-05` (P2) — Fix null JSON body crashes on multiple endpoints
- `REQ-QUAL-06` (P2) — Fix sys.path mutation inside request handlers
- `REQ-QUAL-07` (P2) — Fix Firebase double-init race condition
- `REQ-PERF-05` (P2) — Wire up existing ConnectionPool in connection_pool.py

**Depends on:** Phase 31 (auth consolidation and duplication removal first)

---

### Phase 34 — Dashboard, Mobile Quality & Final Cleanup
**Goal:** Dashboard PWA installs cleanly; no phantom 404 polls; products page has no stacked listeners; login backgrounds load; server URLs environment-configurable on both platforms; Android coroutine and iOS Keychain papercuts resolved.

**Requirements:**
- `REQ-BUG-10` (P2) — Fix PWA service worker caching non-existent files
- `REQ-BUG-11` (P2) — Remove polling of non-existent /api/queue/status + /api/queue/process
- `REQ-BUG-12` (P2) — Fix duplicate event listeners in products.html renderTable()
- `REQ-QUAL-08` (P2) — Replace expiring Instagram CDN token URLs (dashboard backgrounds)
- `REQ-BUG-MOB-08` (P2) — Fix Android ReceiptActivity fragile unchecked cast
- `REQ-BUG-MOB-09` (P2) — Fix Android NFC success detection via onResume polling
- `REQ-QUAL-09` (P2) — Deduplicate isPurchaseType in iOS (defined in 2 files)
- `REQ-QUAL-10` (P2) — Move Android server URL out of hardcoded ApiClient.kt
- `REQ-QUAL-11` (P2) — Move iOS server URL out of hardcoded APIEndpoints.swift
- `REQ-QUAL-12` (P3) — Fix Android unscoped CoroutineScope in NfcManager (memory leak)
- `REQ-QUAL-13` (P3) — Move iOS theme preference from Keychain to UserDefaults

**Depends on:** Phase 31 (dashboard duplication removed), Phase 32 (mobile perf done)

---

## Dependency Graph

```
Phase 25 (Backend P0)
  │
  ├──► Phase 26 (Dashboard P0) ──► Phase 31 (Backend+Dashboard P1) ──► Phase 33 (Backend Quality) ──► Phase 34
  │                                                                                                        ▲
  └──► Phase 28 (Backend Perf) ──► Phase 31                                                               │
                                                                                                           │
Phase 27 (Mobile P0) [parallel to 25/26]                                                                  │
  │                                                                                                        │
  ├──► Phase 29 (Android P1) ──► Phase 32 (Mobile Perf) ──────────────────────────────────────────────────┤
  │                                                                                                        │
  └──► Phase 30 (iOS P1+UX) ──► Phase 32 ──────────────────────────────────────────────────────────────────┘
```

**Recommended execution order:** 25 → 26 → 27 → 28 → 29 → 30 → 31 → 32 → 33 → 34

Phases 25, 26, 27 can be started immediately. Phase 27 can run in parallel with 25/26.

---

## Requirements Coverage

| Category | P0 | P1 | P2 | P3 | Total | Phases |
|----------|----|----|----|----|-------|--------|
| Security (REQ-SEC) | 3 | 3 | 0 | 0 | 6 | 25, 27, 29, 31 |
| Backend Bugs (REQ-BUG) | 4 | 4 | 4 | 0 | 12 | 25, 26, 28, 31, 33 |
| Mobile Bugs (REQ-BUG-MOB) | 3 | 4 | 2 | 0 | 9 | 27, 29, 30, 34 |
| Performance (REQ-PERF) | 1 | 3 | 5 | 0 | 9 | 25, 28, 32, 33 |
| Currency (REQ-CURR) | 0 | 2 | 0 | 0 | 2 | 26, 31 |
| UX (REQ-UX) | 0 | 0 | 5 | 0 | 5 | 30 |
| Code Quality (REQ-QUAL) | 0 | 2 | 9 | 2 | 13 | 31, 33, 34 |
| **Total** | **11** | **18** | **25** | **2** | **57** | |

**57 / 57 requirements mapped. 0 unmapped.**

---

## Execution Checklist

- [ ] Phase 25 — Critical Backend Stability
- [ ] Phase 26 — Critical Dashboard Stability
- [ ] Phase 27 — Critical Mobile Fixes
- [ ] Phase 28 — Backend Performance: Cache Infrastructure
- [ ] Phase 29 — Android Security & P1 Bugs
- [ ] Phase 30 — iOS Bugs & UX
- [ ] Phase 31 — Dashboard & Backend P1 Fixes
- [ ] Phase 32 — Mobile Budget Performance
- [ ] Phase 33 — Backend Code Quality
- [ ] Phase 34 — Dashboard, Mobile Quality & Final Cleanup
