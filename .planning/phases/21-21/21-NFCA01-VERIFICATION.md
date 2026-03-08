# NFCA-01 Verification Report
**Phase:** 21 (v1.1 Gap Closure)
**Date:** 2026-03-08
**Auditor:** Phase 21 executor

---

## NFCA-01: NFC Virtual Card — Sub-requirement Audit

| Sub-requirement | Status | Evidence | Notes |
|-----------------|--------|----------|-------|
| NFCA-01a: BankoHceService processes APDU SELECT and returns HCE token | PASS | `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/BankoHceService.kt` — `processApdu()` method | Implemented in Phase 16 |
| NFCA-01b: HCE token persisted in SecureStorage after card registration | PASS | `BankoHceService.kt` — token stored via `SecureStorage.saveHceToken()` | Implemented in Phase 16 |
| NFCA-01c: HCE token survives app restart (loaded from SecureStorage on cold start) | GAP → FIXED | `BankoHceService.kt` `processApdu()` — `currentToken` was null after process kill | **FIXED-BY: 21-01 Task 2** — Added null-check + SecureStorage load in `processApdu()` |
| NFCA-01d: FCM push token registered with backend on login | GAP → FIXED | `FCMService.kt` `onNewToken()` — token saved to SharedPreferences only, never POST'd to API | **FIXED-BY: 21-01 Task 1** — Added `ApiClient.registerFcmToken()` call in `onNewToken()` and on login |
| NFCA-01e: `/api/nfc/pay` endpoint accepts HCE token and deducts student balance | PASS | `backend/api/api_server.py` — `/api/nfc/pay` route with `token` param lookup against Users sheet | Implemented in Phase 13 + 16 |
| NFCA-01f: NFC registration removes duplicate `google-services.json` copies that caused build failures | GAP → FIXED | Two stray copies at `app/google-services.json` and `app/src/main/java/…/google-services.json` | **FIXED-BY: 21-01 Task 4** — Both stray copies deleted; canonical copy remains at `app/src/google-services.json` |

---

## Summary

| Status | Count |
|--------|-------|
| PASS (pre-existing) | 3 |
| GAP → FIXED (by 21-01) | 3 |
| FAIL (unresolved) | 0 |

**Overall: NFCA-01 fully satisfied after Phase 21 execution.**

---

## Fix References

- **21-01 Task 1** — FCM token: `onNewToken()` now calls `ApiClient.registerFcmToken()`; also called on login
- **21-01 Task 2** — HCE token restore: `processApdu()` checks `currentToken == null` and loads from `SecureStorage`
- **21-01 Task 4** — Stray `google-services.json` copies deleted
