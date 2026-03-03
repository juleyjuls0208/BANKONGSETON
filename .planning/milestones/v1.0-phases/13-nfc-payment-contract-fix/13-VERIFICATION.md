---
phase: 13-nfc-payment-contract-fix
verified: 2026-03-02T14:45:00Z
status: passed
score: 8/8 must-haves verified
re_verification: false
---

# Phase 13: NFC Payment Contract Fix — Verification Report

**Phase Goal:** The Android HCE service can complete an NFC payment end-to-end — the registration response uses the field name the app expects, and the payment endpoint does not require the app to supply a device token it cannot obtain
**Verified:** 2026-03-02T14:45:00Z
**Status:** ✅ PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|---------|
| 1  | Python `/api/nfc/register` response body key is `virtual_card_token` | ✓ VERIFIED | `nfc_payments.py:137` returns `"virtual_card_token": virtual_card_token`; `api_server.py:652` exposes `"virtual_card_token": result["virtual_card_token"]` |
| 2  | `NfcRegistrationResponse` data class has field `virtual_card_token` (not `virtual_token`) | ✓ VERIFIED | `ApiClient.kt:50` — `val virtual_card_token: String`; zero occurrences of `virtual_token` in file |
| 3  | `NfcManager` stores and reads `virtual_card_token` via `KEY_VIRTUAL_CARD_TOKEN` constant | ✓ VERIFIED | `NfcManager.kt:33` declares `KEY_VIRTUAL_CARD_TOKEN = "virtual_card_token"`; used at lines 86, 91, 114 |
| 4  | `NfcManager.KEY_VIRTUAL_TOKEN` constant is renamed to `KEY_VIRTUAL_CARD_TOKEN` | ✓ VERIFIED | Zero occurrences of `KEY_VIRTUAL_TOKEN` anywhere in Android source |
| 5  | `/api/nfc/pay` accepts a request with only `virtual_card_token` (no `X-Device-Token`) and returns 200 on success | ✓ VERIFIED | `api_server.py` nfc_pay() handler: no header extraction, no 401 guard on `X-Device-Token`; Step 1 is body validation only |
| 6  | Server looks up device_token internally from VirtualCards sheet using `virtual_card_token` alone | ✓ VERIFIED | `api_server.py:799` calls `nfc_service.get_virtual_card_by_token(virtual_card_token, db)`; method matches on `VirtualCardToken` + `IsActive` only |
| 7  | `X-Device-Token` header is no longer required (absence does not cause 401) | ✓ VERIFIED | Zero occurrences of `X-Device-Token` in `api_server.py`; CORS `allow_headers` is `["Authorization", "Content-Type"]` only (line 82) |
| 8  | Existing active VirtualCard rows (with VirtualCardToken + IsActive) are still found correctly | ✓ VERIFIED | `get_virtual_card_by_token()` queries `VirtualCardToken` + `IsActive == 'TRUE'` (nfc_payments.py:187–188); both conditions match existing sheet schema |

**Score:** 8/8 truths verified

---

### Required Artifacts

| Artifact | Provides | Contains (required) | Status | Details |
|----------|----------|---------------------|--------|---------|
| `mobile/android/app/src/main/java/com/juls/bankongsetonandroid/ApiClient.kt` | NfcRegistrationResponse Retrofit response model | `val virtual_card_token: String` | ✓ VERIFIED | Line 50 — correct field name; zero `virtual_token` occurrences |
| `mobile/android/app/src/main/java/com/juls/bankongsetonandroid/NfcManager.kt` | NFC device registration and token storage | `KEY_VIRTUAL_CARD_TOKEN` | ✓ VERIFIED | Line 33 — constant declaration; 4 usages (declaration, isDeviceRegistered, getVirtualToken, registerDevice put) |
| `backend/nfc_payments.py` | NFCService with single-token lookup method | `get_virtual_card_by_token` | ✓ VERIFIED | Lines 170–192 — single-token method present; both `get_virtual_card_by_tokens` (two-param) and `get_virtual_card_by_token` (one-param) exist |
| `backend/api/api_server.py` | `/api/nfc/pay` handler without X-Device-Token requirement | `get_virtual_card_by_token` | ✓ VERIFIED | Line 799 — single-token call; X-Device-Token fully absent |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `NfcManager.registerDevice()` | `NfcRegistrationResponse.virtual_card_token` | `response.body()!!.virtual_card_token` | ✓ WIRED | NfcManager.kt:110 — field access correct; result stored via `KEY_VIRTUAL_CARD_TOKEN` at line 114 |
| `NfcManager EncryptedSharedPreferences` | `BankoHceService APDU response` | `KEY_VIRTUAL_CARD_TOKEN` constant in put/getString | ✓ WIRED | Lines 86 (isDeviceRegistered), 91 (getVirtualToken), 114 (registerDevice put) all use `KEY_VIRTUAL_CARD_TOKEN`; `getVirtualToken()` feeds `BankoHceService.currentToken` at line 173 |
| `api_server.py nfc_pay()` | `NFCService.get_virtual_card_by_token()` | `nfc_service.get_virtual_card_by_token(virtual_card_token, db)` | ✓ WIRED | api_server.py:799 — exact call present; old `get_virtual_card_by_tokens` call absent (zero occurrences) |
| `NFCService.get_virtual_card_by_token()` | VirtualCards Google Sheet | `ensure_virtual_cards_sheet(db).get_all_records()` | ✓ WIRED | nfc_payments.py:182–189 — sheet fetched, records scanned on `VirtualCardToken` + `IsActive == 'TRUE'` |

---

### Requirements Coverage

| Requirement | Source Plan | Description (from REQUIREMENTS.md) | Status | Evidence |
|-------------|-------------|-------------------------------------|--------|---------|
| NFC-03 | 13-01-PLAN.md | Transaction flow accepts both RFID card UID and NFC virtual card token as payment sources | ✓ SATISFIED | `NfcRegistrationResponse.virtual_card_token` now correctly deserializes the backend's JSON key; token chain from register → EncryptedSharedPreferences → HCE APDU is intact |
| NFC-04 | 13-02-PLAN.md | API authentication supports NFC device token alongside JWT (ready for Android HCE integration) | ✓ SATISFIED | `/api/nfc/pay` no longer requires X-Device-Token; Android HCE can complete payment with `virtual_card_token` + JWT only |

**Orphaned requirements check:** REQUIREMENTS.md maps only NFC-03 and NFC-04 to Phase 13 (lines 136–137). Both are covered by plan frontmatter. No orphaned requirements.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `ApiClient.kt` | 101 | `// TODO: Replace with your actual server URL` | ℹ️ Info | Pre-existing TODO, not introduced by this phase; no impact on NFC-03/NFC-04 goal |

No blockers or warnings introduced by this phase.

---

### Human Verification Required

#### 1. End-to-End NFC Payment Flow

**Test:** On a physical Android device with NFC enabled:
1. Launch app, log in as a student
2. Navigate to NFC Settings → Register Device (enter a PIN)
3. Tap device to a payment terminal (or simulate via NFC reader)
4. Confirm payment terminal receives the virtual_card_token via APDU and calls `/api/nfc/pay`
5. Check response: 200 with `new_balance` and `timestamp`

**Expected:** Payment succeeds without any X-Device-Token header; balance is debited; transaction logged
**Why human:** Real NFC APDU exchange and live Google Sheets balance debit require a physical device and running server

#### 2. Re-registration After Token Invalidation

**Test:** If a device previously stored the old `"virtual_token"` key in EncryptedSharedPreferences, verify `isDeviceRegistered()` returns `false` on first launch (key mismatch), and the user can re-register successfully
**Expected:** App prompts re-registration; after registering, `virtual_card_token` is stored under the new key; NFC payments work
**Why human:** Requires a device that ran the old code and had the old SharedPreferences key written

---

### Gaps Summary

No gaps found. All must-haves are fully implemented and wired.

**Plan 01 (NFC-03):**
- `NfcRegistrationResponse.virtual_card_token` correctly declared (ApiClient.kt:50)
- `KEY_VIRTUAL_CARD_TOKEN` constant declared and used in all 4 SharedPreferences operations (NfcManager.kt:33, 86, 91, 114)
- Field access `response.body()!!.virtual_card_token` correct (NfcManager.kt:110)
- Zero occurrences of old `virtual_token` / `KEY_VIRTUAL_TOKEN` in entire Android source tree

**Plan 02 (NFC-04):**
- `NFCService.get_virtual_card_by_token()` added as new method; backward-compatible `get_virtual_card_by_tokens()` retained (nfc_payments.py:146, 170)
- `nfc_pay()` handler calls single-token method (api_server.py:799); X-Device-Token block fully removed
- CORS `allow_headers` no longer lists `X-Device-Token` (api_server.py:82)
- All 4 commits verified against git log (748338d, e1e6e08, 62ed1cc, dc788bd)

---

_Verified: 2026-03-02T14:45:00Z_
_Verifier: Claude (gsd-verifier)_
