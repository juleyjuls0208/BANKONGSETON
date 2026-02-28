---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: unknown
last_updated: "2026-02-28T11:37:06.042Z"
progress:
  total_phases: 5
  completed_phases: 5
  total_plans: 26
  completed_plans: 26
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-22)

**Core value:** Students can pay for canteen food instantly by tapping their RFID card, with their balance always visible in the app
**Current focus:** Phase 5 - NFC Architecture Prep

## Current Position

Phase: 5 of 6 (NFC Architecture Prep)
Plan: 3 of 3 completed in current phase
Status: Phase complete
Last activity: 2026-02-28 — Executed 05-03-PLAN.md: Wrote docs/nfc-integration-guide.md (373 lines) — self-contained NFC HCE guide with BankoHceService Kotlin, sequence diagram, error tables, VirtualCards schema; closes NFC-05

Progress: [##########] 100%

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
| Phase 04-student-app-notifications P01 | 2min | 3 tasks | 1 files |
| Phase 04-student-app-notifications P03 | 30min | 2 tasks | 2 files |
| Phase 04-student-app-notifications P04 | 1min | 2 tasks | 4 files |
| Phase 04-student-app-notifications P02 | 1min | 2 tasks | 3 files |
| Phase 04-student-app-notifications P05 | 3min | 3 tasks | 10 files |
| Phase 05-nfc-architecture-prep P01 | 5min | 1 task | 1 file |
| Phase 05-nfc-architecture-prep P02 | 3min | 2 tasks | 1 file |
| Phase 05-nfc-architecture-prep P02 | 3min | 2 tasks | 1 files |
| Phase 05-nfc-architecture-prep P03 | 2min | 1 tasks | 1 files |

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
- [02-04]: arduino_bridge.py was at backend/dashboard/ not backend/adapters/ as plan stated — found and fixed as Rule 3 (blocking path error)
- [02-04]: email_service.py was out-of-scope but had 6 active print() calls — added as Rule 2 auto-fix to meet zero-print success criterion
  - [02-04]: test_phase1.py, test_phase3.py, generate_icons.py print() calls excluded (intentional test/utility output)
- [02-05]: Use card_reader_state.update() for atomic multi-key writes (pending_student_id + card_reading_active set together)
- [02-05]: Keep get_sheets_client/get_philippines_time in cashier_routes inline admin_dashboard import — only normalize_card_uid moved to utils
- [02-05]: api_server.py normalize_card_uid lacked None-safety; utils version adds None guard as correctness improvement
- [02-08]: No code changes required — requirements.txt was already complete; gap was uninstalled environment only
- [02-08]: System-wide pip install maintained (consistent with 02-01 decision; no venv in this project)
- [03-04]: Human verification gate required for visual/interactive UI concerns — toast notifications and inline edit state changes cannot be automated in CI
- [03-04]: Automated pre-checks (syntax + HTML parse + category assertions) run before human checkpoint to eliminate trivial failures early
- [Phase 04-01]: Use active_sessions auth (not JWT) for register_fcm_token — consistent with all other student endpoints
- [Phase 04-01]: Replace chr(64+fcm_col_idx) column-letter conversion with update_cell() to avoid off-by-one bug for columns > Z
- [Phase 04-01]: Insert BalanceBefore at transaction_row index 4 (before BalanceAfter) — matches Transactions Log sheet column spec
- [Phase 04-student-app-notifications]: Settings stored in Google Sheets Settings sheet with Key/Value columns — no new DB table needed
- [04-04]: FCM registration is fire-and-forget — login flow does not wait for FCM; both success and failure callbacks are silent no-ops
- [04-04]: getLastBalance() uses Float sentinel (-1f) in EncryptedSharedPreferences to distinguish stored zero from absent value
- [04-04]: Default page size for getTransactions changed 50→20 to match infinite scroll batch size in upcoming TransactionsActivity
- [Phase 04-student-app-notifications]: Lazy firebase_admin import inside functions prevents crash when credentials file absent
- [Phase 04-student-app-notifications]: Per-transaction Settings sheet read (not cached) allows admin threshold changes without restart
- [Phase 04-student-app-notifications]: Created 5 missing XML layout files from scratch (activity_home, activity_transactions, activity_receipt, item_transaction, item_receipt_line) — res/layout/ was empty before Plan 05
- [Phase 04-05]: Thai Baht symbol ฿ used throughout Android UI (fixed from ₱ in HomeActivity and TransactionsAdapter)
- [05-01]: Clean rewrite (not patch) of nfc_payments.py — NFCPaymentManager removed; NFCService is stateless with db parameter
- [05-01]: get_philippines_time() replicated locally in nfc_payments.py to avoid circular import from api_server.py
  - [05-02]: Used active_sessions (not @require_auth) for nfc_register — consistent with all student endpoints; critical correctness (not JWT-based)
  - [05-02]: X-Device-Token validated inside nfc_pay handler body (after JWT decorator) — clean separation of dual auth layers
  - [05-02]: TransactionType='NFC Purchase' distinct from 'Purchase' for Android transaction filtering
- [Phase 05-nfc-architecture-prep]: Guide written from actual api_server.py + nfc_payments.py source — not from plan descriptions

### Pending Todos

None yet.

### Blockers/Concerns

- ~~Phase 1: Cashier POS products bug root cause not yet confirmed~~ RESOLVED in 01-02: added /cashier/api/products and /cashier/api/logout routes
- ~~Phase 1: Empty credential login (admin_dashboard.py line 221) appears intentional; needs user decision on replacement strategy~~ RESOLVED in 01-03
- ~~Phase 2: QUAL-05 (oauth2client -> google-auth) may require credential file format change — verify before executing~~ RESOLVED in 02-03: credentials.json format unchanged; google-auth uses identical service account JSON
- Phase 4: Push notifications require FCM setup; check if Android app already has FCM dependency before planning

## Session Continuity

Last session: 2026-02-28
Stopped at: Completed 05-03-PLAN.md (NFC integration guide: 373-line self-contained HCE guide with BankoHceService Kotlin, error tables, VirtualCards schema; closes NFC-05)
Resume file: None
