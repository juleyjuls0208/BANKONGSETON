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

<<<<<<< HEAD
- [ ] **T01: Fraud Alert API endpoints + Sheets persistence**
  Wire FraudDetector to Google Sheets "Fraud Alerts" worksheet. Add /api/fraud/* routes to admin_dashboard.py.

- [ ] **T02: Fraud Alerts admin dashboard page**
=======
- [x] **T01: Fraud Alert API endpoints + Sheets persistence**
  Wire FraudDetector to Google Sheets "Fraud Alerts" worksheet. Add /api/fraud/* routes to admin_dashboard.py.

- [x] **T02: Fraud Alerts admin dashboard page**
>>>>>>> gsd/M001/S01
  Add fraud_alerts.html template and nav entry. Alerts table with resolve/suspend/unsuspend UI.

## Files Likely Touched

- `backend/fraud_detection.py` — add sheet persistence methods
- `backend/dashboard/admin_dashboard.py` — add /api/fraud/* routes
- `backend/dashboard/templates/fraud_alerts.html` — new page
- `backend/dashboard/templates/base.html` — add nav entry
