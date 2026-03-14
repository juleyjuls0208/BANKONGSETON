# S01: Fraud Alerts Panel & Card Suspension

**Goal:** Wire FraudDetector to persistent Google Sheets storage and expose it via API endpoints and a new admin dashboard page.
**Demo:** Admin opens the Fraud Alerts page, sees alerts with risk levels and timestamps, resolves an alert, and manually suspends/unsuspends a card.

## Must-Haves

- GET /api/fraud/alerts returns a JSON list of alerts (filterable by unresolved_only, risk_level)
- POST /api/fraud/alerts/<id>/resolve marks an alert resolved with optional notes
- POST /api/fraud/cards/<uid>/suspend suspends a card (stored in Sheets + in-memory)
- POST /api/fraud/cards/<uid>/unsuspend unsuspends a card
- GET /api/fraud/suspended returns list of suspended cards
- GET /api/fraud/stats returns counts by type/risk
- Fraud Alerts worksheet created in Google Sheets with correct columns on first use
- Fraud alerts panel visible in admin nav with alert count badge
- Alerts table shows card, type, risk badge, description, created time, and Resolve button
- Suspended cards section shows card UID, reason, suspended time, and Unsuspend button

## Tasks

- [x] **T01: Fraud Alert API endpoints + Sheets persistence**
  Wire FraudDetector to Google Sheets "Fraud Alerts" worksheet. Add /api/fraud/* routes to admin_dashboard.py.

- [x] **T02: Fraud Alerts admin dashboard page**
  Add fraud_alerts.html template and nav entry. Alerts table with resolve/suspend/unsuspend UI.

## Observability / Diagnostics

### Runtime Signals
- Structured log events on sheet bootstrap: `event=fraud_alerts_loaded count=N` (INFO) and `event=suspended_cards_loaded count=N` (INFO) emitted by `load_from_sheets()` on first API request.
- Write failures are non-fatal WARNINGs: `event=fraud_alert_save_failed`, `event=fraud_alert_update_failed`, `event=suspended_save_failed`, `event=suspended_remove_failed` — all greppable by prefix.
- All route-level exceptions logged at ERROR with `exc_info=True` for full tracebacks.

### Inspection Surfaces
- `GET /api/fraud/stats` — live counts: total_alerts, unresolved_alerts, today_alerts, suspended_cards. Zero-config health check for the fraud subsystem.
- `GET /api/fraud/suspended` — enumerate all currently suspended cards with reason and timestamp.
- `GET /api/fraud/alerts?unresolved_only=true` — current alert queue without noise from resolved history.
- Browser Fraud Alerts page (`/fraud-alerts`) — human-readable view of the same data; sidebar badge shows unresolved count.

### Failure Visibility
- Google Sheets unavailable (gspread APIError / ConnectionError / TimeoutError): all six routes return HTTP 503 with `{"error": "Service temporarily unavailable"}`.
- Sheet load failures at startup: logged at WARNING; FraudDetector starts with empty in-memory state and continues operating — no crash.
- `_fraud_sheets_initialized` flag prevents repeated load attempts if the first fails.

### Redaction
- Card UIDs appear in logs at WARNING/ERROR level only — no sensitive financial amounts logged in fraud route handlers.

## Verification

- `pytest tests/test_fraud_api.py -v` → 33 tests pass (covers all 6 routes + all persistence methods + error paths)
- `GET /api/fraud/stats` returns JSON with keys: total_alerts, unresolved_alerts, today_alerts, suspended_cards ✅
- `GET /api/fraud/alerts` returns list with per-alert fields: id, money_card, fraud_type, risk_level, description, created_at, resolved ✅
- `GET /api/fraud/alerts?unresolved_only=true` returns only unresolved alerts ✅
- `POST /api/fraud/alerts/<id>/resolve` returns `{"success": true}` ✅
- `POST /api/fraud/cards/<uid>/suspend` requires @admin_only; returns `{"success": true}` ✅
- `POST /api/fraud/cards/<uid>/unsuspend` requires @admin_only; returns `{"success": true}` ✅
- "Fraud Alerts" worksheet created with header row on first use ✅
- Sheet write failure: route still returns success; WARNING logged with `event=` prefix ✅
- gspread timeout: route returns 503 ✅

## Files Likely Touched

- `backend/fraud_detection.py` — add sheet persistence methods
- `backend/dashboard/admin_dashboard.py` — add /api/fraud/* routes
- `backend/dashboard/templates/fraud_alerts.html` — new page
- `backend/dashboard/templates/base.html` — add nav entry
