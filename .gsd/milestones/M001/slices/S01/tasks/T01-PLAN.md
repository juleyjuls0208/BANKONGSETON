# T01: Fraud Alert API Endpoints + Sheets Persistence

**Slice:** S01
**Milestone:** M001

## Goal
Add Google Sheets persistence to FraudDetector (load/save alerts to "Fraud Alerts" worksheet) and expose six /api/fraud/* endpoints in admin_dashboard.py.

## Must-Haves

### Truths
- GET /api/fraud/alerts returns JSON list with fields: id, money_card, fraud_type, risk_level, description, created_at, resolved
- GET /api/fraud/alerts?unresolved_only=true returns only unresolved alerts
- POST /api/fraud/alerts/<id>/resolve with {"notes": "..."} returns {"success": true}
- POST /api/fraud/cards/<uid>/suspend with {"reason": "..."} returns {"success": true}
- POST /api/fraud/cards/<uid>/unsuspend returns {"success": true}
- GET /api/fraud/suspended returns list of suspended cards
- GET /api/fraud/stats returns {"total_alerts", "unresolved_alerts", "today_alerts", "suspended_cards"}
- "Fraud Alerts" worksheet is created with header row if it doesn't exist

### Artifacts
- `backend/fraud_detection.py` — new methods: load_alerts_from_sheet(worksheet), save_alert_to_sheet(worksheet, alert), load_suspended_from_sheet(worksheet), save_suspended_to_sheet(worksheet, card, data)
- `backend/dashboard/admin_dashboard.py` — 6 new routes under /api/fraud/

### Key Links
- admin_dashboard.py → fraud_detection.get_fraud_detector() for all fraud routes
- admin_dashboard.py → get_worksheet_with_retry('Fraud Alerts') for persistence
- FraudDetector.analyze_transaction() already called nowhere — not wired to transactions in this task (that's a future enhancement)

## Steps
1. Add `load_alerts_from_sheet(ws)` to FraudDetector: read all rows, populate self.alerts list
2. Add `save_alert_to_sheet(ws, alert)` to FraudDetector: append one row to Fraud Alerts sheet
3. Add `load_suspended_from_sheet(ws)` and `save_suspended_to_sheet(ws, card, data)` for suspended cards persistence
4. Add `ensure_fraud_sheet(db)` helper in admin_dashboard.py: get or create "Fraud Alerts" worksheet with header row
5. Add `GET /api/fraud/alerts` route with optional query params: unresolved_only, risk_level, limit
6. Add `POST /api/fraud/alerts/<alert_id>/resolve` route
7. Add `POST /api/fraud/cards/<uid>/suspend` route — updates in-memory + sheet
8. Add `POST /api/fraud/cards/<uid>/unsuspend` route — updates in-memory + sheet
9. Add `GET /api/fraud/suspended` route
10. Add `GET /api/fraud/stats` route
11. Protect all routes with @login_required; suspend/unsuspend also @admin_only

## Observability Impact

### Signals Changed by This Task
- **event=fraud_alerts_loaded count=N** (INFO) — emitted by `load_from_sheets()` on first API request; confirms Sheets bootstrap succeeded.
- **event=suspended_cards_loaded count=N** (INFO) — same bootstrap call, suspended card side.
- **event=fraud_alerts_load_failed error=...** (WARNING) — sheet unreadable at startup; FraudDetector starts empty.
- **event=fraud_alert_save_failed** / **event=fraud_alert_update_failed** (WARNING) — write-back failed after in-memory op succeeded.
- **event=suspended_save_failed** / **event=suspended_remove_failed** (WARNING) — suspended card sheet write failed.
- Route ERROR logs with `exc_info=True` — full tracebacks on unexpected exceptions in any /api/fraud/* route.

### How a Future Agent Inspects This Task
- `grep "event=fraud" <log-file>` — shows all sheet-level events for this subsystem.
- `GET /api/fraud/stats` — live health check: confirms detector is alive, returns current counts.
- `GET /api/fraud/alerts` / `GET /api/fraud/suspended` — enumerate in-memory state.
- `_fraud_sheets_initialized` flag (module-level in admin_dashboard.py) — inspect to know if sheet bootstrap has run.

### Failure State Visibility
- If Sheets is unreachable: all six routes return HTTP 503 with `{"error": "Service temporarily unavailable"}`.
- If sheet load fails at startup: detector starts empty (no crash); WARNING logged; `_fraud_sheets_initialized` remains False so next request retries.
- In-memory FraudDetector is always the source of truth — sheet write failures are non-fatal by design (D010).

## Context
- FraudDetector instance: use get_fraud_detector() from fraud_detection.py — it's a module-level singleton
- Fraud Alerts sheet columns: AlertID, MoneyCard, FraudType, RiskLevel, Description, CreatedAt, Resolved, ResolvedAt, ResolutionNotes, AutoAction
- Suspended sheet: use a second sheet "Suspended Cards" — columns: MoneyCard, Reason, SuspendedAt, AutoSuspended
- Use @admin_only for suspend/unsuspend; @login_required for read-only routes
- Pattern for all routes: wrap in try/except with gspread errors returning 503, unexpected returning 500
