# Phase 21: v1.1 Gap Closure + v1.2 Feature Implementation - Context

**Gathered:** 2026-03-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 21 has two distinct missions:

**Mission 1 — v1.1 Gap Closure:** Verify that NFCA-01 (NFC virtual card registration) and PAR-01–06 (parent portal) are actually working end-to-end. Both were implemented in Phases 16 and 19 respectively, but neither has been tested since implementation. REQUIREMENTS.md still shows both as `[ ] Pending`. Phase 21 produces formal VERIFICATION.md artifacts for both and marks them complete if they pass — or fixes them if they don't.

**Mission 2 — v1.2 Feature Implementation:** Implement the next wave of features, which includes: Arduino R3 NFC connectivity fix, web/local dashboard separation, background push notifications, low balance email to parent, SMS notifications, bulk student import, and multi-station canteen support.

**Production hardening** (remove debug artifacts, confirm env defaults) is a third, smaller deliverable bundled into this phase.

**Out of scope for Phase 21:** Flutter port (add to v1.2 roadmap but do not implement). Parent self-service password reset. Real-time WebSocket charts on PythonAnywhere.

</domain>

<decisions>
## Implementation Decisions

### NFCA-01: verification approach
- Phase 21 performs a **real verification pass** — do not simply close the checkbox based on Phase 16's VERIFICATION.md
- Rationale: the codebase has been modified since Phase 16 (Phases 17–20.1 all touched backend and mobile); NFCA-01 registration may have regressed
- Verification covers: `/api/nfc/register` endpoint contract, `virtual_card_token` round-trip, encrypted token storage in `EncryptedSharedPreferences`, `BankoHceService.currentToken` populated correctly, UI flow in `SettingsActivity` NFC section
- Produce a **new `21-NFCA01-VERIFICATION.md`** in `.planning/phases/21-21/` — do not modify Phase 16's existing VERIFICATION.md
- NFCA-01 is marked `[x]` in REQUIREMENTS.md **only if** the verification pass confirms it works (or after any fixes)

### PAR-01–06: verification approach
- Phase 21 performs a **full end-to-end verification pass** for all 6 parent portal requirements — Phase 19 never produced a VERIFICATION.md
- The parent portal has **never been tested since implementation** — treat it as unknown state; investigate before declaring it working
- Verification covers: parent login via `/login` with email+password, session scoped to correct student, `/api/parent/data` returns correct balance + transactions, `parent_dashboard.html` renders correctly, parent cannot access admin routes, card registration form accepts optional parent email + password
- Produce a **`21-PAR-VERIFICATION.md`** in `.planning/phases/21-21/`
- PAR-01–06 are marked `[x]` **only after** verification passes (or after any fixes)
- The shared `/login` route for admin and parent is **acceptable as-is** — no separate parent login URL needed

### Arduino R3 NFC fix
- The cashier terminal's ArduinoBridge either **cannot reach the R3** or the failure point is unknown — treat as an investigation task first
- Scope: diagnose why ArduinoBridge cannot connect to R3 (check IP configuration, serial detection, bridge startup, PN532/R3 firmware readiness), then fix
- Also verify admin dashboard can connect if it was previously affected
- This is a **bug fix**, not a feature — prioritize it early in planning since the core NFC payment flow is broken without it

### Web/local dashboard separation
- Currently `admin_dashboard.py` (local) and `web_app.py` (PythonAnywhere) are two separate files but are not cleanly maintained as separate codebases
- Decision: **PythonAnywhere web admin should work independently** of the local machine — credentials for the web version are already configured on PythonAnywhere
- The web version should **not require the local machine to be running** for parent portal, admin views, or student management
- Arduino controls (cashier UI, ArduinoBridge, serial/WiFi card reads) remain **local only** — these are hardware-dependent and cannot run on PythonAnywhere
- The planner should assess whether `admin_dashboard.py` and `web_app.py` need to be merged, diverged further, or feature-gated, and propose the cleanest approach given current duplication

### Background push notifications (FCM)
- Android app background notifications are **not working** — FCM push notifications do not arrive when the app is in the background or killed
- This is likely an FCM integration issue (missing `google-services.json` configuration, missing notification channel, or backend not sending FCM payloads correctly)
- Scope: diagnose the full FCM chain (backend sends → FCM delivers → Android receives → OS shows notification), then fix
- Relevant notification types: low balance alert, budget threshold alert, payment receipt

### Low balance email to parent
- When a student's balance drops below a threshold, send an **email to the linked parent email**
- Threshold: configurable per-student or a global default (planner to decide based on existing notification patterns)
- Backend already sends email notifications via `notifications.py` — reuse this infrastructure
- Only triggered if `ParentEmail` is set and valid for the student

### SMS notifications
- Add SMS as a notification channel for payment receipts and/or low balance alerts
- Deliver via a third-party SMS gateway (Twilio or equivalent — planner to recommend based on PythonAnywhere compatibility and Philippine carrier support)
- SMS is **optional** — if a student/parent has no phone number on file, no SMS is sent
- Scope: add `PhoneNumber` field to student record, backend sends SMS on relevant events, admin can input phone number at registration

### Bulk student import (CSV)
- Admin can upload a CSV file to register multiple students at once
- CSV format: at minimum `Name, StudentID, MoneyCardNumber` — additional optional columns for email, parent email, phone number
- Backend validates each row, skips duplicates, reports errors per row
- UI: a new "Import Students" button/modal on the students management page

### Multiple canteen stations
- Support more than one cashier terminal (Arduino reader) simultaneously
- Each station has a unique identifier; transactions are tagged with which station processed them
- Cashier UI can be opened on multiple machines without conflict
- Backend `/api/arduino/card-read` and `/api/nfc/pay` must handle concurrent requests from multiple stations gracefully
- Planner to assess whether the existing Google Sheets-backed transaction log can handle concurrent writes without race conditions

### Planning file updates
- REQUIREMENTS.md: fix **all** stale `[ ]` checkboxes and the traceability table — this is a deliverable of Phase 21
- ROADMAP.md: update Phase 21 with its real name and goal; mark ✓ Complete when done; add Flutter port as a v1.2 future phase placeholder
- STATE.md: update to reflect Phase 21 complete and all v1.1 requirements closed
- PROJECT.md: update key decisions log or project status section to reflect v1.1 completion and v1.2 start
- CHANGELOG.md: create a new CHANGELOG.md summarizing v1.1 completion and v1.2 scope

### Production hardening
- Remove the 6 `[DEBUG]` `console.log` statements from `backend/dashboard/templates/dashboard.html`
- Confirm `FLASK_DEBUG` defaults to `false` in production configuration (`backend/dashboard/admin_dashboard.py` and `web_app.py`)
- Confirm `API_DEBUG` defaults to `False` in `backend/api/api_server.py`
- This is a **light pass** — not a full security audit

### Flutter port
- **Do not implement in Phase 21**
- Add Flutter port as a future phase entry in ROADMAP.md under a v1.2 section
- Note the rationale: current Kotlin/Compose app is working; Flutter port is a rewrite, not a fix

### Claude's Discretion
- Exact SMS gateway selection (Twilio vs alternatives) — choose based on PythonAnywhere compatibility and Thai/Philippine carrier support
- Whether `admin_dashboard.py` and `web_app.py` are merged or kept separate — choose the approach with least duplication risk
- FCM notification channel IDs and payload structure
- CSV import error reporting UX (inline table errors vs summary modal)
- Whether multi-station support requires a schema migration or can be handled by tagging existing transaction records

</decisions>

<code_context>
## Existing Code Insights

### NFC (NFCA-01)
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/NfcManager.kt`: `registerDevice()` calls `ApiClient.apiService.registerNfcDevice()` → `POST /api/nfc/register`. Token stored in `EncryptedSharedPreferences` under key `virtual_card_token`. Sets `BankoHceService.currentToken` on success.
- `mobile/.../BankoHceService.kt`: `HostApduService` subclass; uses `currentToken` static field set by `NfcManager`
- `mobile/.../SettingsActivity.kt`: UI entry point for NFC registration/removal; uses `nfcManager.isDeviceRegistered()`
- `backend/api/api_server.py` line 832: `POST /api/nfc/register` route; delegates to `nfc_service.register_virtual_card()` in `backend/nfc_payments.py`
- `backend/nfc_payments.py` line 91: `register_virtual_card()` — writes to `Virtual Cards` sheet, returns `virtual_card_token` + `device_token`

### Parent Portal (PAR-01–06)
- `backend/dashboard/admin_dashboard.py` line 325: `parent_only` decorator — requires `session["role"] == "parent"`
- Line 438–446: `GET /parent` route renders `parent_dashboard.html` with student_id + student_name from session
- Line 456–507: `GET /api/parent/data` — fetches balance + transactions for session-linked student from Sheets
- Line 400–424: Parent login branch in `/login` route — looks up `ParentEmail` + `ParentPasswordHash` in Users sheet
- `backend/dashboard/templates/parent_dashboard.html`: Parent portal UI (balance + transaction history)
- `backend/dashboard/templates/students.html` line 408: "Set Parent" modal that posts `parent_email` + `parent_password`

### Arduino / ArduinoBridge
- `backend/dashboard/arduino_bridge.py`: `ArduinoBridge` class — parses `NFC|<token>` serial lines, emits `nfc_payment` SocketIO event, POSTs to `/api/nfc/pay` in daemon thread
- Connection target is R3 (UNO R3 at cashier) — investigate why ArduinoBridge cannot reach it
- `backend/dashboard/templates/cashier_index.html` lines 334, 345: SocketIO listeners for `nfc_payment` and `nfc_payment_result` events

### Notifications
- `backend/notifications.py`: Email notification infrastructure — `send_low_balance_email()` already checks `ParentEmail` (lines 652–660, 694–703); reuse for parent low balance trigger
- Backend already imports and calls `notifications.py` from `admin_dashboard.py` and `web_app.py`

### Dashboard duplication
- `backend/dashboard/admin_dashboard.py`: Local-first Flask app (has Arduino bridge, serial port support, cashier UI)
- `backend/dashboard/web_app.py`: PythonAnywhere-deployed version — credential differences only? Planner should diff the two files and propose the cleanest split
- `backend/api/api_server.py`: Separate Flask API server — deployed independently on PythonAnywhere

### Debug artifacts to remove
- `backend/dashboard/templates/dashboard.html` lines 448, 452, 786, 790, 807, 809: `console.log('[DEBUG] ...')` calls
- `backend/dashboard/admin_dashboard.py` line 2944: `debug = os.getenv("FLASK_DEBUG", "true")` — default is `"true"` (should be `"false"`)
- `backend/dashboard/web_app.py` line 2516: same pattern — `FLASK_DEBUG` default should be `"false"`
- `backend/api/api_server.py` line 1502: `API_DEBUG` default is `"False"` — already correct

</code_context>

<specifics>
## Specific Ideas

- Verification artifacts go in `.planning/phases/21-21/`: `21-NFCA01-VERIFICATION.md` and `21-PAR-VERIFICATION.md`
- Arduino R3 investigation: check `arduino_bridge.py` startup, port detection, IP/serial config — document findings before fixing
- Multi-station: tag each transaction with a `StationID` — cashier UI includes the station ID in card-read POSTs
- CSV import: show a preview table before committing, with per-row validation errors highlighted inline
- Low balance email: reuse the existing `send_low_balance_email()` in `notifications.py` — trigger from the same payment processing path that already calls it

</specifics>

<deferred>
## Deferred to Future Phases / Out of Scope

- **Flutter port**: add to ROADMAP.md as a future phase, do not implement in Phase 21
- **Parent self-service password reset**: admin resets parent password manually — no self-service flow
- **SQL database migration**: remains out of scope (Google Sheets still working at current scale)
- **iOS app**: Android-only
- **Real-time WebSocket charts on PythonAnywhere**: PythonAnywhere free tier limitation
- **OTA firmware updates for Arduino**: out of scope

</deferred>

---

*Phase: 21-21*
*Context gathered: 2026-03-08*
