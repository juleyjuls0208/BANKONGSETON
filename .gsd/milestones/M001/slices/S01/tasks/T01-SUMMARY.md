---
id: T01
parent: S01
milestone: M001
provides:
  - GET /api/fraud/alerts (filterable by unresolved_only, risk_level, limit)
  - POST /api/fraud/alerts/<id>/resolve
  - POST /api/fraud/cards/<uid>/suspend
  - POST /api/fraud/cards/<uid>/unsuspend
  - GET /api/fraud/suspended
  - GET /api/fraud/stats
  - FraudDetector Google Sheets persistence (load + save + update + remove)
  - _ensure_fraud_sheets() helper — creates "Fraud Alerts" and "Suspended Cards" worksheets with headers on first use
key_files:
  - backend/fraud_detection.py
  - backend/dashboard/admin_dashboard.py
  - tests/test_fraud_api.py
key_decisions:
  - D009: Fraud Sheets lazy init — loads on first API request, not at app startup
  - D010: Sheet write failures are non-fatal WARNING; in-memory FraudDetector stays source of truth
  - D011: resolve requires @login_required only; suspend/unsuspend require @admin_only
  - D012: load_from_sheets(fraud_ws, suspended_ws) loads both worksheets in one call
patterns_established:
  - All fraud routes: try/except with gspread.exceptions.APIError|ConnectionError|TimeoutError -> 503, Exception -> 500
  - _get_fraud_detector_with_sheets() — singleton with lazy Sheets bootstrap; guarded by _fraud_sheets_initialized flag
  - Sheet persistence is best-effort: write failures logged at WARNING, operation still returns success
observability_surfaces:
  - event=fraud_alerts_loaded count=N (INFO log on startup load)
  - event=suspended_cards_loaded count=N (INFO log on startup load)
  - event=fraud_alerts_load_failed error=... (WARNING on load error)
  - event=fraud_alert_save_failed / event=fraud_alert_update_failed (WARNING on write error)
  - event=suspended_save_failed / event=suspended_remove_failed (WARNING on write error)
  - All route errors logged at ERROR with exc_info=True
duration: ~1h
verification_result: passed
completed_at: 2026-03-12
blocker_discovered: false
---

# T01: Fraud Alert API Endpoints + Sheets Persistence

**Added Google Sheets persistence to FraudDetector and exposed six /api/fraud/* routes in admin_dashboard.py — all 33 unit tests pass.**

## What Happened

The implementation was already substantially complete when execution began (both fraud_detection.py persistence methods and admin_dashboard.py routes existed). This task verified and hardened what was there:

1. **fraud_detection.py** — All required persistence methods were present:
   - `load_from_sheets(fraud_ws, suspended_ws)` — reads "Fraud Alerts" and "Suspended Cards" worksheets on first init
   - `save_alert_to_sheet(fraud_ws, alert)` — appends new alert row
   - `update_alert_in_sheet(fraud_ws, alert)` — updates Resolved/ResolvedAt/ResolutionNotes columns by AlertID
   - `save_suspended_card_to_sheet(suspended_ws, card, data)` — append or update suspended card row
   - `remove_suspended_card_from_sheet(suspended_ws, card)` — deletes row by MoneyCard
   - `FRAUD_ALERTS_HEADERS` and `SUSPENDED_CARDS_HEADERS` class constants with correct column definitions

2. **admin_dashboard.py** — All six routes present and functional:
   - `GET /api/fraud/alerts` — returns JSON list; supports `unresolved_only`, `risk_level`, `limit` query params
   - `POST /api/fraud/alerts/<alert_id>/resolve` — resolves alert + persists to sheet
   - `POST /api/fraud/cards/<uid>/suspend` — suspends card + persists; @admin_only
   - `POST /api/fraud/cards/<uid>/unsuspend` — unsuspends card + removes from sheet; @admin_only
   - `GET /api/fraud/suspended` — returns all suspended cards as list
   - `GET /api/fraud/stats` — returns total_alerts, unresolved_alerts, today_alerts, suspended_cards
   - `_ensure_fraud_sheets()` — creates "Fraud Alerts" and "Suspended Cards" worksheets with header rows if they don't exist
   - `_get_fraud_detector_with_sheets()` — lazy singleton init with one-time Sheets bootstrap

3. **503 error handling gap fixed** — Read-only routes (`get_fraud_alerts`, `resolve_fraud_alert`, `get_suspended_cards`, `get_fraud_stats`) were missing explicit `gspread.exceptions.APIError|ConnectionError|TimeoutError -> 503` handlers. Added to match the task plan pattern and the existing write routes.

## Verification

```
pytest tests/test_fraud_api.py -v
# 33 passed in 1.58s
```

Tests cover:
- `TestLoadFromSheets` — load_alerts_from_sheet populates list; load_suspended_cards; graceful error handling; skips empty AlertID rows
- `TestSaveAlertToSheet` — appends row; returns False on error
- `TestUpdateAlertInSheet` — updates resolved columns; returns False when not found
- `TestSaveSuspendedCard` — appends new; updates existing
- `TestRemoveSuspendedCard` — deletes row; returns False when not found
- `TestGetFraudAlertsRoute` — returns alert list; unresolved_only filter; risk_level filter; requires login
- `TestResolveAlertRoute` — resolves existing; 404 for unknown; requires login
- `TestSuspendCardRoute` — suspends card; requires admin role; requires login
- `TestUnsuspendCardRoute` — unsuspends card; 404 for non-suspended; requires admin role
- `TestGetSuspendedRoute` — returns suspended list; empty case; requires login
- `TestGetFraudStatsRoute` — returns required fields; accurate counts; requires login
- `TestEnsureFraudSheets` — creates sheet if missing; uses existing if present

Manual verification of Must-Have field presence:
- `FraudAlert.to_dict()` includes: id, money_card, fraud_type, risk_level, description, created_at, resolved ✅
- `get_stats()` includes: total_alerts, unresolved_alerts, today_alerts, suspended_cards ✅
- All 6 route decorators verified via regex against source ✅

## Diagnostics

- Structured log events on sheet load: `event=fraud_alerts_loaded count=N`, `event=suspended_cards_loaded count=N`
- Warning-level logs for all sheet write/read failures with `event=` prefix for grep-ability
- All route exceptions logged at ERROR level with `exc_info=True` for full tracebacks in logs
- To inspect: `grep "event=fraud" <logfile>` or check Flask error logs

## Deviations

- `load_from_sheets(fraud_ws, suspended_ws)` consolidates both worksheet loads into a single method (vs. the plan's separate `load_alerts_from_sheet(ws)` and `load_suspended_from_sheet(ws)`). This was a deliberate prior decision (D012) — fewer round-trips and both datasets are always needed together.
- 503 error handling was missing from 4 of the 6 read-only routes; added during this task to fully match the "gspread errors returning 503" requirement.

## Known Issues

None.

## Files Created/Modified

- `backend/fraud_detection.py` — Google Sheets persistence methods (load_from_sheets, save_alert_to_sheet, update_alert_in_sheet, save_suspended_card_to_sheet, remove_suspended_card_from_sheet) + header constants
- `backend/dashboard/admin_dashboard.py` — 6 /api/fraud/* routes, _ensure_fraud_sheets(), _get_fraud_detector_with_sheets(); added 503 error handling to read-only routes
- `tests/test_fraud_api.py` — 33 unit tests covering all routes and persistence methods
