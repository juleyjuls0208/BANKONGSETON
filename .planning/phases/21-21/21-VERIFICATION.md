---
phase: 21-v1.1-gap-closure-v1.2-features
verified: 2026-03-08T10:00:00Z
status: passed
score: 20/20 must-haves verified
re_verification: false
---

# Phase 21: v1.1 Gap Closure + v1.2 Features — Verification Report

**Phase Goal:** Close NFCA-01 and PAR-01–06 regressions from Phases 16/19, harden production config, and ship five v1.2 features: low-balance email, SMS notifications, multi-canteen station support, Arduino R3 auto-connect, and bulk CSV student import.
**Verified:** 2026-03-08T10:00:00Z
**Status:** ✅ PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | FCM token is sent to backend on registration and on login | ✓ VERIFIED | `FCMService.kt:28–30` — `CoroutineScope(Dispatchers.IO).launch { ApiClient.apiService.registerFCMToken(...)` in `onNewToken()`; commit `4897a91` |
| 2 | HCE virtual card token survives app restart / process kill | ✓ VERIFIED | `BankoHceService.kt:50–51` — `if (currentToken == null) { currentToken = NfcManager.getInstance(applicationContext).getVirtualToken() }`; commit `e383db3` |
| 3 | Parent login returns a 503 JSON error (not silent pass) when Sheets is unreachable | ✓ VERIFIED | `api_server.py:309–313`, `460–464`, `576–580` — `except (ConnectionError, TimeoutError)` → returns `503`; commit `62cac7e` |
| 4 | Only one google-services.json exists at the correct path (app/src/) | ✓ VERIFIED | `app/google-services.json` — ABSENT; `app/src/main/java/.../google-services.json` — ABSENT; `app/src/google-services.json` — EXISTS |
| 5 | No `[DEBUG]` console.log statements appear in dashboard.html | ✓ VERIFIED | `grep -c "console.log.*\[DEBUG\]" dashboard.html` → 0; 7 non-debug console.log calls preserved intentionally; commit `61f129a` |
| 6 | FLASK_DEBUG defaults to false in both admin_dashboard.py and web_app.py | ✓ VERIFIED | `admin_dashboard.py:3003` — `os.getenv("FLASK_DEBUG", "false")`; `web_app.py:2571` — same pattern; commit `db90fc8` |
| 7 | A low balance email is sent to the parent after every NFC tap-to-pay that drops balance below threshold | ✓ VERIFIED | `api_server.py:1119–1133` — `if new_balance < LOW_BALANCE_THRESHOLD: ... email_notifier.send_low_balance_alert(...)` guarded by try/except; `EmailNotifier` class at `notifications.py:34` |
| 8 | The payment transaction record includes the station_id of the physical device | ✓ VERIFIED | `api_server.py:1013` — `station_id = request.headers.get("X-Station-ID", "main")`; `api_server.py:1099` — station_id written into `append_row(...)` at position StationID |
| 9 | ArduinoBridge auto-connects to the serial port specified in STATION_SERIAL_PORT env var at startup | ✓ VERIFIED | `arduino_bridge.py:30,40–46` — `STATION_SERIAL_PORT = os.getenv("STATION_SERIAL_PORT", "")`; on `__init__`: `if self.arduino is None and STATION_SERIAL_PORT: ... Serial(STATION_SERIAL_PORT, 9600)` |
| 10 | An SMS is sent to the parent's phone number after every NFC tap-to-pay that drops balance below threshold | ✓ VERIFIED | `api_server.py:1139–1148` — `sms_notifier.send_low_balance_sms(...)` wrapped in try/except; `TwilioSMSNotifier` at `notifications.py:744` |
| 11 | SMS sending failure does not break or delay the payment flow | ✓ VERIFIED | `api_server.py:1141,1149` — SMS call in `try:` block; `except Exception as sms_err: logger.warning(...)` before the `return jsonify({...}), 200` |
| 12 | TwilioSMSNotifier class exists in notifications.py and is wired into the payment handler | ✓ VERIFIED | `notifications.py:744` — `class TwilioSMSNotifier`; `api_server.py:33,36` — `from notifications import TwilioSMSNotifier; sms_notifier = TwilioSMSNotifier()` |
| 13 | Admin can POST a CSV file to /api/students/import and receive a JSON summary of imported, skipped, and errored rows | ✓ VERIFIED | `admin_dashboard.py:2843–2895` and `web_app.py:2354–2406` — both return `jsonify({"imported": ..., "skipped": ..., "errors": ...})` |
| 14 | A single bad row does not abort the entire import | ✓ VERIFIED | `admin_dashboard.py:2870–2893` — per-row `try/except Exception` continues loop on error; `web_app.py` mirrors same pattern |
| 15 | CSV files exported from Excel (with BOM) are handled correctly | ✓ VERIFIED | `admin_dashboard.py:2854` — `file.read().decode("utf-8-sig")`; `web_app.py:2365` — identical |
| 16 | The /api/students/import endpoint exists in both admin_dashboard.py and web_app.py | ✓ VERIFIED | `admin_dashboard.py:2843` — `@app.route("/api/students/import", methods=["POST"])`; `web_app.py:2354` — same |
| 17 | NFCA-01 verification artifact exists with all sub-requirements audited | ✓ VERIFIED | `.planning/phases/21-21/21-NFCA01-VERIFICATION.md` — all 6 sub-requirements documented; 3 PASS, 3 GAP→FIXED; commit `36131e7` |
| 18 | PAR-01–06 verification artifact exists with all requirements audited | ✓ VERIFIED | `.planning/phases/21-21/21-PAR-VERIFICATION.md` — all 6 requirements documented; 5 PASS, 1 GAP→FIXED; commit `08ea774` |
| 19 | REQUIREMENTS.md, ROADMAP.md, STATE.md, PROJECT.md all updated to reflect Phase 21 | ✓ VERIFIED | All 8 requirement IDs in REQUIREMENTS.md; ROADMAP lists all 8 plans checked; STATE.md `status: complete`; PROJECT.md `v1.2`; commit `f333eb7`, `d2b478a` |
| 20 | CHANGELOG.md has a v1.2 section documenting all Phase 21 changes | ✓ VERIFIED | `CHANGELOG.md:7` — `## [v1.2] — 2026-03-08` with all 8 feature areas documented; commit `d2b478a` |

**Score:** 20/20 truths verified

---

## Required Artifacts

| Artifact | Requirement | Status | Key Evidence |
|----------|-------------|--------|--------------|
| `mobile/.../FCMService.kt` | V11-NFCA-01 | ✓ VERIFIED | `registerFCMToken` call at line 30 inside coroutine |
| `mobile/.../BankoHceService.kt` | V11-NFCA-01 | ✓ VERIFIED | `getVirtualToken()` null-restore at lines 50–51 |
| `mobile/.../app/src/google-services.json` | V11-NFCA-01 | ✓ VERIFIED | Only copy; stray copies absent |
| `backend/api/api_server.py` | V11-PAR-01-06, V12-EMAIL, V12-STATION, V12-SMS | ✓ VERIFIED | 503 handling at ~line 313; station_id:1013,1099; email:1119; SMS:1142 |
| `backend/dashboard/templates/dashboard.html` | PROD-HARDEN | ✓ VERIFIED | Zero `[DEBUG]` console.logs; 7 non-debug ones preserved correctly |
| `backend/dashboard/admin_dashboard.py` | PROD-HARDEN, V12-CSV | ✓ VERIFIED | `FLASK_DEBUG` default `"false"` at 3003; import endpoint at 2843 |
| `backend/dashboard/web_app.py` | PROD-HARDEN, V12-CSV | ✓ VERIFIED | `FLASK_DEBUG` default `"false"` at 2571; import endpoint at 2354 |
| `backend/notifications.py` | V12-EMAIL, V12-SMS | ✓ VERIFIED | `EmailNotifier` at line 34; `TwilioSMSNotifier` at line 744 |
| `backend/dashboard/arduino_bridge.py` | V12-STATION, V12-ARDUINO-R3 | ✓ VERIFIED | `STATION_SERIAL_PORT` auto-connect at 40–46; `X-Station-ID` header at 78 |
| `.planning/phases/21-21/21-NFCA01-VERIFICATION.md` | V11-NFCA-01 | ✓ VERIFIED | 6 sub-requirements, all resolved |
| `.planning/phases/21-21/21-PAR-VERIFICATION.md` | V11-PAR-01-06 | ✓ VERIFIED | 6 requirements, all resolved |
| `.planning/REQUIREMENTS.md` | All | ✓ VERIFIED | All 8 IDs present with full descriptions |
| `.planning/ROADMAP.md` | All | ✓ VERIFIED | Phase 21 entry with all 8 plans checked |
| `.planning/STATE.md` | All | ✓ VERIFIED | `status: complete`, Phase 21 noted |
| `.planning/PROJECT.md` | All | ✓ VERIFIED | References v1.2, updated 2026-03-08 |
| `CHANGELOG.md` | All | ✓ VERIFIED | `[v1.2] — 2026-03-08` with all feature areas |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `FCMService.onNewToken()` | `POST /api/fcm/register` | `ApiClient.apiService.registerFCMToken(...)` in CoroutineScope | ✓ WIRED | FCMService.kt:28–30 |
| `BankoHceService.processCommandApdu()` | NfcManager secure store | `NfcManager.getInstance(ctx).getVirtualToken()` on null check | ✓ WIRED | BankoHceService.kt:50–51 |
| `api_server.py` parent login handler | Google Sheets | `except (ConnectionError, TimeoutError) → return 503` | ✓ WIRED | api_server.py:309,460,576 |
| `arduino_bridge.py` startup | Serial port | `Serial(STATION_SERIAL_PORT, 9600)` in `__init__` | ✓ WIRED | arduino_bridge.py:40–46 |
| `arduino_bridge.py._post_nfc_payment()` | API headers | `headers["X-Station-ID"] = STATION_ID` | ✓ WIRED | arduino_bridge.py:78 |
| `api_server.py /api/nfc/pay` | `EmailNotifier.send_low_balance_alert()` | lazy import + call after `new_balance < LOW_BALANCE_THRESHOLD` | ✓ WIRED | api_server.py:1119–1132 |
| `api_server.py /api/nfc/pay` | `TwilioSMSNotifier.send_low_balance_sms()` | module-level `sms_notifier`; call at 1142; isolated try/except | ✓ WIRED | api_server.py:36,1139–1148 |
| `POST /api/students/import` | Sheets `append_row()` | per-row try/except; `utf-8-sig` decode; returns JSON summary | ✓ WIRED | admin_dashboard.py:2843–2895; web_app.py:2354–2406 |

---

## Requirements Coverage

| Requirement ID | Source Plan(s) | Description | Status | Evidence |
|----------------|----------------|-------------|--------|----------|
| V11-NFCA-01 | 21-01, 21-06, 21-08 | FCM token, HCE restore, google-services cleanup | ✓ SATISFIED | FCMService.kt:30; BankoHceService.kt:50–51; stray files absent; audit doc exists |
| V11-PAR-01-06 | 21-01, 21-07, 21-08 | Parent login 503 on Sheets failure | ✓ SATISFIED | api_server.py:309–313; audit doc exists |
| PROD-HARDEN | 21-02, 21-08 | Remove [DEBUG] console.logs; FLASK_DEBUG=false | ✓ SATISFIED | dashboard.html: 0 [DEBUG] logs; both server files: `"false"` default |
| V12-EMAIL | 21-03, 21-08 | Low-balance email alert to parent after NFC pay | ✓ SATISFIED | api_server.py:1119–1132; EmailNotifier class in notifications.py:34 |
| V12-STATION | 21-03, 21-08 | STATION_ID as X-Station-ID header + Transactions Log | ✓ SATISFIED | arduino_bridge.py:78; api_server.py:1013,1099 |
| V12-ARDUINO-R3 | 21-03, 21-08 | STATION_SERIAL_PORT auto-connect on startup | ✓ SATISFIED | arduino_bridge.py:30,40–46 |
| V12-SMS | 21-04, 21-08 | Twilio SMS on low-balance after NFC pay | ✓ SATISFIED | notifications.py:744; api_server.py:33,36,1142 |
| V12-CSV | 21-05, 21-08 | POST /api/students/import, BOM-safe, per-row errors | ✓ SATISFIED | admin_dashboard.py:2843–2895; web_app.py:2354–2406 |

All 8 requirement IDs accounted for. No orphaned requirements detected.

---

## Anti-Patterns Found

| File | Pattern | Severity | Notes |
|------|---------|----------|-------|
| `backend/dashboard/templates/dashboard.html` | 7 `console.log` calls remain | ℹ️ Info | These are non-debug logs (search, modal lifecycle) preserved intentionally. Plan 02 explicitly targeted only `[DEBUG]`-tagged calls. **Not a gap.** |
| `21-02-PLAN.md` artifact spec | `contains: "// console.log removed"` | ℹ️ Info | Marker comment was never written to dashboard.html (plan said to delete lines, not comment them). Spec was misleading but goal was achieved. **Not a gap.** |
| `21-01-SUMMARY.md` commit reference | `9f54595` cited as "Remove debug console.log" but actual commit message is "add TwilioSMSNotifier" | ℹ️ Info | Minor commit hash cross-reference error in summary; actual dashboard.html removal is `61f129a`. Both commits exist and contain correct changes. **Not a gap.** |

No blockers. No stubs. No empty implementations.

---

## Human Verification Required

### 1. SMS delivery end-to-end

**Test:** Configure `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` env vars; trigger a payment below threshold; confirm SMS received.
**Expected:** Parent/student phone receives low-balance SMS within 5 seconds.
**Why human:** Requires live Twilio credentials and real phone number; cannot verify from codebase.

### 2. Email delivery end-to-end

**Test:** Configure SMTP/email env vars; trigger NFC payment below `LOW_BALANCE_THRESHOLD`; confirm email received in parent inbox.
**Expected:** Parent receives low-balance alert email with student name, balance, and threshold.
**Why human:** Requires live email credentials; lazy-import pattern means `EmailNotifier` config env vars weren't inspected here.

### 3. Arduino R3 serial auto-connect on real hardware

**Test:** Set `STATION_SERIAL_PORT=/dev/ttyACM0` (or correct port); start ArduinoBridge; check logs for "Auto-connected to /dev/ttyACM0".
**Expected:** Log message confirms connection; subsequent NFC payments include station_id in Transactions Log.
**Why human:** Requires physical Arduino hardware; serial port path varies by OS/device.

### 4. CSV import UI flow in dashboard

**Test:** Navigate to admin dashboard; use bulk import UI; upload a CSV with one valid row, one row with missing fields, and one row with a duplicate StudentID.
**Expected:** Returns `{"imported": 1, "skipped": 2, "errors": [...]}` with per-row detail; no HTTP 500.
**Why human:** Verifies end-to-end UI wiring and response display, not just API existence.

---

## Summary

Phase 21 goal fully achieved. All 8 requirement IDs (V11-NFCA-01, V11-PAR-01-06, PROD-HARDEN, V12-EMAIL, V12-STATION, V12-ARDUINO-R3, V12-SMS, V12-CSV) are implemented, substantive, and wired. All 8 plans produced committed artifacts. The three informational notes (non-debug console.logs in dashboard, misleading plan marker comment, minor commit hash cross-reference in summary) are documentation quality observations — none affect functionality or goal achievement.

The project is correctly tagged as v1.2 in STATE.md, PROJECT.md, ROADMAP.md, and CHANGELOG.md.

---

_Verified: 2026-03-08T10:00:00Z_
_Verifier: Claude (gsd-verifier)_
