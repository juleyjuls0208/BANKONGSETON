---
id: T01
parent: S01
milestone: M001
provides:
  - Six /api/fraud/* endpoints in admin_dashboard.py
  - Google Sheets persistence methods in FraudDetector (load_from_sheets, save_alert_to_sheet, update_alert_in_sheet, save_suspended_card_to_sheet, remove_suspended_card_from_sheet)
  - _ensure_fraud_sheets() helper creating "Fraud Alerts" and "Suspended Cards" worksheets on first use
  - _get_fraud_detector_with_sheets() lazy-init singleton wiring Sheets to in-memory detector
key_files:
  - backend/fraud_detection.py
  - backend/dashboard/admin_dashboard.py
  - tests/test_fraud_api.py
key_decisions:
  - D009: Fraud Sheets lazy init — first API request, not app startup
  - D010: Sheet write failures non-fatal; in-memory FraudDetector is source of truth
  - D011: resolve_fraud_alert is @login_required only; suspend/unsuspend require @admin_only
  - D012: load_from_sheets() loads both worksheets in one call
patterns_established:
  - All six fraud routes wrap in try/except: gspread errors → 503, unexpected → 500 with exc_info=True
  - Sheet persistence is fire-and-forget; in-memory op always succeeds first, WARNING logged on sheet failure
  - _fraud_sheets_initialized module flag prevents repeated init attempts on Sheets failure
observability_surfaces:
  - GET /api/fraud/stats — live counts (total_alerts, unresolved_alerts, today_alerts, suspended_cards)
  - GET /api/fraud/alerts / GET /api/fraud/suspended — enumerate in-memory state
  - event=fraud_alerts_loaded / event=suspended_cards_loaded (INFO) — sheet bootstrap confirmed
  - event=fraud_alert_save_failed / event=fraud_alert_update_failed / event=suspended_save_failed / event=suspended_remove_failed (WARNING) — greppable write-back failures
duration: <1 session (implementation pre-existing; verified in this unit)
verification_result: passed
completed_at: 2026-03-14
blocker_discovered: false
---

# T01: Fraud Alert API Endpoints + Sheets Persistence

**Six /api/fraud/* routes wired to FraudDetector with lazy-loaded Google Sheets persistence; 33/33 tests pass.**

## What Happened

All implementation was already in place when this unit started:

- `backend/fraud_detection.py` already contained all five persistence methods (`load_from_sheets`, `save_alert_to_sheet`, `update_alert_in_sheet`, `save_suspended_card_to_sheet`, `remove_suspended_card_from_sheet`) plus the `FRAUD_ALERTS_HEADERS` and `SUSPENDED_CARDS_HEADERS` column-name constants.
- `backend/dashboard/admin_dashboard.py` already contained the `_ensure_fraud_sheets()` helper (creates both worksheets with header rows on first use), `_get_fraud_detector_with_sheets()` lazy init, and all six routes: `GET /api/fraud/alerts`, `POST /api/fraud/alerts/<id>/resolve`, `POST /api/fraud/cards/<uid>/suspend`, `POST /api/fraud/cards/<uid>/unsuspend`, `GET /api/fraud/suspended`, `GET /api/fraud/stats`.
- `tests/test_fraud_api.py` already contained 33 tests covering all routes, all persistence helpers, filter params, auth enforcement, and error paths.

This execution unit verified and confirmed the implementation, ran the full test suite, and confirmed all verification checks in the slice plan passed.

## Verification

```
pytest tests/test_fraud_api.py -v
33 passed in 2.01s
```

All 33 tests passed:
- `TestLoadFromSheets` (4 tests) — populates alerts list, loads suspended cards, handles API error gracefully, skips rows without AlertID ✅
- `TestSaveAlertToSheet` (2 tests) — appends row with correct columns, returns False on error ✅
- `TestUpdateAlertInSheet` (2 tests) — updates Resolved/ResolvedAt/Notes columns, returns False when not found ✅
- `TestSaveSuspendedCard` (2 tests) — appends new card, updates existing card ✅
- `TestRemoveSuspendedCard` (2 tests) — deletes row, returns False when not found ✅
- `TestGetFraudAlertsRoute` (4 tests) — returns alert list, unresolved_only filter, login required, risk_level filter ✅
- `TestResolveAlertRoute` (3 tests) — resolves existing alert, 404 for unknown alert, login required ✅
- `TestSuspendCardRoute` (3 tests) — suspends card, 403 for finance role, login required ✅
- `TestUnsuspendCardRoute` (3 tests) — unsuspends card, 404 for non-suspended, 403 for finance role ✅
- `TestGetSuspendedRoute` (3 tests) — returns list, empty when none, login required ✅
- `TestGetFraudStatsRoute` (3 tests) — required fields present, counts accurate, login required ✅
- `TestEnsureFraudSheets` (2 tests) — creates both sheets with header rows if missing, uses existing sheets ✅

All slice-level verification checks pass for T01 scope:
- `GET /api/fraud/stats` returns `total_alerts, unresolved_alerts, today_alerts, suspended_cards` ✅
- `GET /api/fraud/alerts` returns per-alert fields: id, money_card, fraud_type, risk_level, description, created_at, resolved ✅
- `GET /api/fraud/alerts?unresolved_only=true` returns only unresolved alerts ✅
- `POST /api/fraud/alerts/<id>/resolve` returns `{"success": true}` ✅
- `POST /api/fraud/cards/<uid>/suspend` requires @admin_only, returns `{"success": true}` ✅
- `POST /api/fraud/cards/<uid>/unsuspend` requires @admin_only, returns `{"success": true}` ✅
- "Fraud Alerts" worksheet created with header row on first use ✅
- Sheet write failure: route still returns success, WARNING logged with `event=` prefix ✅
- gspread timeout: route returns 503 ✅

## Diagnostics

- **Live counts:** `GET /api/fraud/stats` — returns `{total_alerts, unresolved_alerts, today_alerts, suspended_cards}` with no args. Zero-config health check.
- **Sheet bootstrap status:** `grep "event=fraud_alerts_loaded\|event=suspended_cards_loaded" <logfile>` — confirms Sheets init succeeded.
- **Write failures:** `grep "event=fraud_alert_save_failed\|event=suspended_save_failed" <logfile>` — non-fatal write-back issues.
- **Init flag:** `adm._fraud_sheets_initialized` (inspect at runtime) — True if sheet load succeeded at least once.
- **Error tracebacks:** All route exceptions logged at ERROR with `exc_info=True`.

## Deviations

- The 503 response body uses `{"error": "Service unavailable, please try again"}` rather than `{"error": "Service temporarily unavailable"}` as stated in the slice plan. The HTTP status code (503) and `error` key are correct; the message wording differs slightly. Not a blocker.

## Known Issues

None.

## Files Created/Modified

- `backend/fraud_detection.py` — FraudDetector persistence methods + FRAUD_ALERTS_HEADERS/SUSPENDED_CARDS_HEADERS constants + load_from_sheets() combined loader
- `backend/dashboard/admin_dashboard.py` — _ensure_fraud_sheets(), _get_fraud_detector_with_sheets(), _fraud_sheets_initialized flag, all 6 /api/fraud/* routes
- `tests/test_fraud_api.py` — 33-test verification suite covering all routes, persistence helpers, filter params, auth, and error paths
