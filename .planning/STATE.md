---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: completed
stopped_at: Completed 32.1-04-PLAN.md
last_updated: "2026-03-10T22:28:39.705Z"
last_activity: "2026-02-26 — Executed 02-03-PLAN.md: migrated all backend files from oauth2client to google-auth; pinned exact versions in requirements.txt; added smoke test"
progress:
  total_phases: 7
  completed_phases: 1
  total_plans: 10
  completed_plans: 8
  percent: 93
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app
**Current focus:** Phase 2 - Code Quality

## Current Position

Phase: 2 of 6 (Code Quality)
Plan: 3 of 5 completed in current phase
Status: Phase 2 plan 03 complete
Last activity: 2026-02-26 — Executed 02-03-PLAN.md: migrated all backend files from oauth2client to google-auth; pinned exact versions in requirements.txt; added smoke test

Progress: [█████████░] 93%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 1-2min
- Total execution time: 0.08 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-critical-fixes-security | 4 | 7min | 2min |
| 02-code-quality | 3 | 7min | 2min |

**Recent Trend:**
- Last 5 plans: 01-04 (2min), 02-01 (2min), 02-02 (2min), 02-03 (3min), —
- Trend: Stable
| Phase 32.1-nfc-fix P01 | 3min | 2 tasks | 1 files |
| Phase 32.1-nfc-fix P02 | 10 | 2 tasks | 1 files |
| Phase 32.1-nfc-fix P03 | 5 | 2 tasks | 1 files |
| Phase 32.1-nfc-fix P04 | 3 | 2 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: Fix backend first — cashier POS is broken; security holes must be closed before adding features
- [Init]: Keep Google Sheets as database — no SQL migration
- [Init]: NFC: architect backend now, Android implementation is v2
- [Init]: Documentation as Markdown in /docs/ so system can be explained to peers
- [01-01]: Startup guard at module level (not __main__) so it fires on import too
- [01-01]: CORS dev-mode auto-allows localhost origins when FLASK_ENV=development or CORS_ORIGINS is empty
- [01-01]: Used plain print() for redacted startup messages since get_logger import can fail
- [01-03]: Field-specific 400 errors for empty username/password (not a single generic error)
- [01-03]: and admin_user truthy check appended to credential comparison (not separate block)
- [01-03]: Test credentials use obviously-fake strings not env vars (tests run against live server)
- [01-03]: wsgi.py retains only GOOGLE_SHEETS_ID/GOOGLE_CREDENTIALS_FILE as non-secret defaults
- [Phase 01-02]: Used /cashier/api/products (JWT-protected) instead of /api/products/list (admin session required) to avoid auth mismatch
- [Phase 01-02]: Added /cashier/api/logout route (missing from cashier_routes.py, called by template logout button)
- [Phase 01-critical-fixes-security]: UID_PATTERN defined independently in each module to avoid cross-module import complexity given runtime sys.path.insert pattern in cashier_routes.py
- [01-05]: Serial/Arduino routes use ConnectionError/TimeoutError only (no gspread exceptions — they don't touch Sheets)
- [01-05]: timestamp set before retry loop to ensure consistent transaction time across retry attempts
- [01-05]: web_app_complete.py has 6 remaining bare str(e) — deferred (out-of-scope legacy file)
- [02-02]: Removed log_dir param from setup_logging() entirely (no callers used it; config_validator only passes log_level=)
- [02-02]: Kept get_logger() unchanged (returns getLogger(name) with default 'bangko') for downstream compatibility
- [02-02]: Unused imports in admin_dashboard.py/wsgi.py deferred (complex interdependencies, at-discretion scope)
- [02-01]: threading.Lock (not RLock) for CardReaderState — re-entrant locking not needed since get/set/update do not call each other
- [02-01]: No imports from errors.py in utils.py — avoids circular import risk given runtime sys.path.insert pattern
- [02-01]: pytest + python-dotenv installed system-wide (no venv present in this project)
- [02-03]: admin_dashboard.py and api_server.py were already migrated to google-auth before this plan — only config_validator.py and migrate_transactions.py required changes
- [02-03]: Option A (explicit Credentials.from_service_account_file) used for config_validator.py to match existing pattern in _validate_google_sheets_connection
- [02-03]: Option B (gspread.service_account shortcut) used for migrate_transactions.py — simplest migration, consistent with api_server.py
- [02-03]: credentials.json format unchanged — google-auth uses identical service account JSON format as oauth2client
- [Phase 32.1-nfc-fix]: autoRFCA=0 required for passive ISO14443A — autoRFCA=1 suppresses PN532 RF field during passive sensing (NTAG215 never powers up)
- [Phase 32.1-nfc-fix]: Remove setPassiveActivationRetries(0x0A) — 10 retries insufficient for NTAG215 7-byte double-cascade anticollision; PN532 default 0xFF bounded by NFC_TIMEOUT_MS is correct
- [Phase 32.1-nfc-fix]: UID-length dispatch: uidLen != 4 = physical card (CARD| path), == 4 = HCE phone (APDU path)
- [Phase 32.1-nfc-fix]: Named _start_serial_thread in ArduinoBridge constructor — required for test patchability via patch.object
- [Phase 32.1-nfc-fix]: UID_PATTERN widened to {8}|{14} in cashier_routes.py — NTAG215 7-byte UIDs (14 hex chars) accepted end-to-end

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Phase 1: Cashier POS products bug root cause not yet confirmed~~ RESOLVED in 01-02: added /cashier/api/products and /cashier/api/logout routes
- ~~Phase 1: Empty credential login (admin_dashboard.py line 221) appears intentional; needs user decision on replacement strategy~~ RESOLVED in 01-03
- ~~Phase 2: QUAL-05 (oauth2client -> google-auth) may require credential file format change — verify before executing~~ RESOLVED in 02-03: credentials.json format unchanged; google-auth uses identical service account JSON
- Phase 4: Push notifications require FCM setup; check if Android app already has FCM dependency before planning

## Session Continuity

Last session: 2026-03-10T22:22:05.756Z
Stopped at: Completed 32.1-04-PLAN.md
Resume file: None
