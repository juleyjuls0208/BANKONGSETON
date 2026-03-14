# S01: Fraud Alerts Panel & Card Suspension -- UAT

**Milestone:** M001
**Written:** 2026-03-11

## UAT Type

- UAT mode: artifact-driven
- Why this mode is sufficient: All deliverables are verifiable by static analysis (route registration, template element presence, decorator checks) and in-memory unit assertions. The Sheets persistence layer cannot be exercised without live Google credentials, but persistence method stubs are verified present and callable. A live smoke test is documented below for environments with real Sheets credentials.

## Preconditions

For artifact-driven checks (already run):
- Python 3.14 installed; backend/ dependencies installed

For live smoke test (optional):
- Google Sheets credentials configured
- Admin dashboard running: cd backend/dashboard && python admin_dashboard.py
- Admin user account created; browser at http://localhost:5000

## Smoke Test

Navigate to /fraud-alerts logged in as admin. Page loads with stats row, filter bar, and both tables. Sidebar shows Fraud Alerts nav item. No JavaScript console errors.

## Test Cases

### 1. Fraud Alerts page loads

1. Log in as admin
2. Click Fraud Alerts in the sidebar
3. Expected: Page loads at /fraud-alerts; stats row shows 4 stat cards; tables render (empty or with data); no JS errors

### 2. Unresolved-only filter

1. On the Fraud Alerts page, uncheck Unresolved only checkbox
2. Expected: Table reloads and may show resolved alerts; count badge updates

### 3. Risk level filter

1. Select Critical from the risk dropdown
2. Expected: Table shows only CRITICAL risk alerts; count badge updates

### 4. Resolve an alert

1. Click Resolve on an open alert
2. Type resolution notes in the modal
3. Click Resolve
4. Expected: Modal closes; alert disappears (if unresolved filter on) or shows Resolved badge; stats Unresolved decrements

### 5. Manually suspend a card

1. Click Suspend Card in the Suspended Cards section header
2. Enter card UID and reason in the modal
3. Click Suspend
4. Expected: Card appears in Suspended Cards table with Manual badge; stats Suspended Cards increments

### 6. Unsuspend a card

1. Click Unsuspend on a card in the Suspended Cards table
2. Expected: Card removed from table; stats Suspended Cards decrements

### 7. Fraud Alerts nav badge

1. Log in as admin and visit any dashboard page
2. Expected: Fraud Alerts nav link visible; if unresolved alerts exist, red badge shows count; if zero, badge hidden

### 8. Finance role cannot see nav link

1. Log in as finance (non-admin) role
2. Expected: Fraud Alerts nav link NOT visible in sidebar

## Edge Cases

### No Google Sheets credentials

1. Start admin dashboard without valid Sheets credentials
2. Navigate to /fraud-alerts
3. Expected: Page loads (lazy init -- app does not crash); API calls return 503; tables show Failed to load message

### Empty alert list

1. Visit /fraud-alerts with no alerts
2. Expected: Alerts table shows empty-state (shield-check icon, No alerts found); stats show zeros

### Resolve non-existent alert ID

1. POST to /api/fraud/alerts/nonexistent-id/resolve
2. Expected: 404 with {"error": "Alert not found"}

### Suspend already-suspended card

1. POST /api/fraud/cards/CARD001/suspend twice
2. Expected: Second call succeeds (idempotent); card remains suspended; Sheets row upserted

## Failure Signals

- Browser console shows 4xx/5xx fetch errors: API route missing or auth problem
- Stats cards remain at dash after load: /api/fraud/stats returning error or Sheets missing
- No Fraud Alerts link when logged in as admin: base.html nav not updated or role not set
- Resolve button missing on open alerts: JS rendering issue or resolved flag incorrectly true
- Suspended Cards table blank after suspend: fetch failed or suspend POST returned error

## Requirements Proved By This UAT

- R001 (Fraud Alerts Admin UI) -- admin can view fraud alerts, resolve them, see risk level badges; all API endpoints and template elements verified
- R002 (Card Suspension Management) -- admin can manually suspend and unsuspend any card; admin_only guard verified; UI table and modals verified

## Not Proven By This UAT

- Live Google Sheets round-trip: alerts persisting to and loading from a real Sheets document not verified with live credentials
- FraudDetector alert generation: fraud rules generating alerts from real transaction data not tested end-to-end
- Process restart persistence: alerts surviving a backend restart via Sheets reload not verified in live environment
- Finance-role access restriction to /fraud-alerts: confirmed in Jinja template logic; not verified with live non-admin login

## Notes for Tester

- Expect a brief delay on first /fraud-alerts load while _get_fraud_detector_with_sheets() initializes from Sheets.
- To generate test alerts quickly, call FraudDetector.analyze_transaction() in a Python REPL and verify via GET /api/fraud/alerts.
- Sidebar badge updates on page load only (not live-polled). Refresh the page to see the latest count.
- resolve_fraud_alert is accessible to finance-role users (not just admin) -- deliberate design choice.
