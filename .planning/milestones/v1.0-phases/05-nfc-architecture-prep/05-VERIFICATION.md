---
phase: 05-nfc-architecture-prep
verified: 2026-02-28T12:00:00Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 5: NFC Architecture Prep — Verification Report

**Phase Goal:** The backend exposes complete, documented NFC payment endpoints and persists VirtualCard state so the Android app can implement NFC in the next version without backend changes  
**Verified:** 2026-02-28  
**Status:** ✅ PASSED  
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A VirtualCard registered via the API is persisted to Google Sheets (VirtualCards tab) and survives a server restart | ✓ VERIFIED | `register_virtual_card()` calls `ensure_virtual_cards_sheet(db)` + `vc_sheet.append_row(...)` — no in-memory state (`nfc_payments.py:120–122`) |
| 2 | Re-registering a student silently deactivates their old VirtualCard row and appends a new one | ✓ VERIFIED | Loop `enumerate(records, start=2)` with `update_cell(idx, 6, 'FALSE')` before `append_row` (`nfc_payments.py:106–122`) |
| 3 | All VirtualCard lookups filter by IsActive == TRUE so deactivated rows are never matched | ✓ VERIFIED | `get_virtual_card_by_tokens()` checks `str(r.get('IsActive','')).upper() == 'TRUE'` (`nfc_payments.py:154`) |
| 4 | POST /api/nfc/register returns virtual_card_token (UUID v4), device_token, and money_card for a logged-in student | ✓ VERIFIED | Route present at `api_server.py:497`, returns all 3 fields (`api_server.py:535–540`) |
| 5 | POST /api/nfc/pay with valid cashier JWT + X-Device-Token + valid virtual_card_token debits the student account and returns new_balance | ✓ VERIFIED | Route at `api_server.py:547`, debits Money Accounts via `update_cell` (`api_server.py:618`), returns `new_balance` (`api_server.py:644`) |
| 6 | POST /api/nfc/pay with missing or wrong X-Device-Token returns 401 | ✓ VERIFIED | `if not device_token: return jsonify({'error': 'X-Device-Token header required'}), 401` (`api_server.py:566–567`); token mismatch returns 401 via `get_virtual_card_by_tokens` returning None (`api_server.py:584–585`) |
| 7 | POST /api/nfc/pay with invalid virtual_card_token (no match or inactive) returns 401 | ✓ VERIFIED | `if not matched: return jsonify({'error': 'Invalid virtual card token or device token'}), 401` (`api_server.py:584–585`) |
| 8 | X-Device-Token is listed in Flask-CORS allow_headers so Android clients are not blocked by preflight | ✓ VERIFIED | `CORS(app, origins=get_cors_origins(), allow_headers=['Authorization', 'Content-Type', 'X-Device-Token'])` (`api_server.py:61`) |
| 9 | docs/nfc-integration-guide.md exists and is self-contained — a future Android developer can implement NFC HCE v2 without asking the original author anything | ✓ VERIFIED | 373 lines; all 10 section checks pass (sequence diagram, Kotlin snippets, AID, error tables, schema) |
| 10 | NFC Purchase transaction type logged separately from RFID Purchase | ✓ VERIFIED | `trans_sheet.append_row([..., 'NFC Purchase', ...])` (`api_server.py:631–639`) |

**Score:** 10/10 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/nfc_payments.py` | NFCService class with register_virtual_card(), get_virtual_card_by_tokens() | ✓ VERIFIED | 158 lines; clean rewrite, `NFCPaymentManager` fully removed |
| `backend/nfc_payments.py` | VIRTUAL_CARDS_SHEET_NAME + VIRTUAL_CARDS_HEADERS constants | ✓ VERIFIED | `VIRTUAL_CARDS_SHEET_NAME = 'VirtualCards'`, `VIRTUAL_CARDS_HEADERS` = 6-element list |
| `backend/nfc_payments.py` | ensure_virtual_cards_sheet(db) function | ✓ VERIFIED | Mirrors `ensure_products_sheet()` pattern; creates sheet with 6 headers on first call |
| `backend/api/api_server.py` | POST /api/nfc/register endpoint | ✓ VERIFIED | `@app.route('/api/nfc/register', methods=['POST'])` at line 497 |
| `backend/api/api_server.py` | POST /api/nfc/pay endpoint | ✓ VERIFIED | `@app.route('/api/nfc/pay', methods=['POST'])` at line 547 |
| `backend/api/api_server.py` | CORS allow_headers includes X-Device-Token | ✓ VERIFIED | `allow_headers=['Authorization', 'Content-Type', 'X-Device-Token']` at line 61 |
| `docs/nfc-integration-guide.md` | Complete NFC HCE integration guide ≥150 lines | ✓ VERIFIED | 373 lines; all required sections and content present |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `nfc_payments.py` | Google Sheets VirtualCards tab | `db.worksheet(VIRTUAL_CARDS_SHEET_NAME)` + `append_row()` | ✓ WIRED | `ensure_virtual_cards_sheet` at line 61; `append_row` at line 120 |
| `NFCService.register_virtual_card()` | VirtualCards sheet upsert | `update_cell(idx, 6, 'FALSE')` + `append_row` | ✓ WIRED | Deactivate old rows loop (`nfc_payments.py:106–112`), then append new row (`nfc_payments.py:120–122`) |
| `POST /api/nfc/register` | active_sessions dict (not require_auth JWT) | `token = request.headers.get('Authorization','').replace('Bearer ','')` | ✓ WIRED | `active_sessions` check at `api_server.py:513`; NO `@require_auth` decorator on route |
| `POST /api/nfc/pay` | `@require_auth(roles=['admin','cashier'])` | decorator before handler | ✓ WIRED | `@require_auth(roles=['admin', 'cashier'])` at `api_server.py:548`, directly after `@app.route` |
| `nfc_pay handler` | `NFCService.get_virtual_card_by_tokens()` | import from nfc_payments | ✓ WIRED | `nfc_service.get_virtual_card_by_tokens(virtual_card_token, device_token, db)` (`api_server.py:583`) |
| `nfc_pay handler` | Transactions Log sheet | `append_row` with `TransactionType='NFC Purchase'` | ✓ WIRED | `trans_sheet.append_row([..., 'NFC Purchase', ...])` (`api_server.py:631–639`) |
| `docs/nfc-integration-guide.md` API section | Actual endpoint behavior | Request/response shapes from working implementation | ✓ WIRED | Guide documents exact response fields matching `api_server.py:535–540` and `api_server.py:643–647` |
| `docs/nfc-integration-guide.md` Kotlin section | Android HCE `processCommandApdu()` | `BankoHceService extends HostApduService` | ✓ WIRED | `BankoHceService : HostApduService()` with `processCommandApdu` in guide |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| NFC-01 | 05-02 | NFC payment API endpoints exist and are documented (`/api/nfc/register`, `/api/nfc/pay`) | ✓ SATISFIED | Both routes verified at `api_server.py:497` and `api_server.py:547`; guide documents both at `docs/nfc-integration-guide.md` |
| NFC-02 | 05-01 | VirtualCard model in nfc_payments.py is fully integrated with Google Sheets (persisted, not just in-memory) | ✓ SATISFIED | `NFCService` backed by Sheets via `ensure_virtual_cards_sheet(db)` + `append_row`; no in-memory dicts remain |
| NFC-03 | 05-02 | Transaction flow accepts both RFID card UID and NFC virtual card token as payment sources | ✓ SATISFIED | `nfc_pay` debits from `Money Accounts` via `MoneyCardNumber` obtained from `VirtualCard` lookup — same ledger as RFID path |
| NFC-04 | 05-02 | API authentication supports NFC device token alongside JWT (ready for Android HCE integration) | ✓ SATISFIED | Dual-auth: `@require_auth` JWT decorator + `X-Device-Token` header check inside handler; CORS allows `X-Device-Token` |
| NFC-05 | 05-03 | NFC integration guide written in docs/ explaining exactly what the Android app needs to implement for v2 | ✓ SATISFIED | `docs/nfc-integration-guide.md` (373 lines): sequence diagram, BankoHceService Kotlin, full error tables, VirtualCards schema |

**Orphaned requirements:** None — all 5 NFC-* IDs accounted for across plans 05-01, 05-02, 05-03.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | — | — | None found |

- `backend/nfc_payments.py`: No TODO/FIXME/placeholder comments; no empty returns; all old classes (`NFCPaymentManager`, PIN/biometric/expiry/multi-card) fully removed
- `backend/api/api_server.py`: No stubs; both NFC handlers have complete implementations including error paths
- `docs/nfc-integration-guide.md`: No placeholder sections; all code snippets are substantive copy-paste Kotlin

---

## Human Verification Required

### 1. Live Sheets Round-Trip

**Test:** With a running server and valid credentials, call `POST /api/nfc/register` with a valid student session token, then inspect the VirtualCards sheet.  
**Expected:** A new row appears with `IsActive=TRUE`, UUID v4 in VirtualCardToken, 44-char URL-safe string in DeviceToken.  
**Why human:** Cannot query live Google Sheets during static analysis.

### 2. NFC Pay Debit + Transaction Log

**Test:** With the tokens from step 1, call `POST /api/nfc/pay` with a valid cashier JWT, `X-Device-Token` header, and a small `total`. Check Money Accounts balance and Transactions Log sheet.  
**Expected:** Balance decremented by `total`; new row in Transactions Log with `TransactionType='NFC Purchase'` and negative `Amount`.  
**Why human:** End-to-end Sheets writes require live credentials.

### 3. Re-registration Upsert Behavior

**Test:** Call `POST /api/nfc/register` twice for the same student. Inspect VirtualCards sheet.  
**Expected:** First row's `IsActive` column set to `FALSE`; second row appended with `IsActive=TRUE`. Old tokens no longer work in `/api/nfc/pay`.  
**Why human:** Requires live Sheets state inspection.

---

## Commit Evidence

| Commit | Hash | Files Changed |
|--------|------|---------------|
| feat(05-01): rewrite nfc_payments.py | `90257cc` | `backend/nfc_payments.py` (+130/-374) |
| feat(05-02): add NFC endpoints + CORS | `9a58191` | `backend/api/api_server.py` (+160/-1) |
| docs(05-03): NFC integration guide | `8783ffd` | `docs/nfc-integration-guide.md` (+373) |

All 3 implementation commits verified present in git log.

---

## Summary

Phase 5 goal is **fully achieved**. All 10 observable truths verified, all 7 artifacts present and substantive, all 8 key links wired, all 5 requirements (NFC-01 through NFC-05) satisfied with direct code evidence.

The backend NFC layer is complete and self-contained:
- `backend/nfc_payments.py` — clean Sheets-backed `NFCService` (158 lines); old in-memory `NFCPaymentManager` fully removed
- `backend/api/api_server.py` — two NFC routes with correct auth patterns (active_sessions for register, dual JWT+device-token for pay); CORS updated
- `docs/nfc-integration-guide.md` — 373-line guide with BankoHceService Kotlin, sequence diagram, error tables, and VirtualCards schema

The Android app can implement NFC HCE in v2 from the guide alone, and the backend requires no further changes.

---

_Verified: 2026-02-28_  
_Verifier: Claude (gsd-verifier)_
