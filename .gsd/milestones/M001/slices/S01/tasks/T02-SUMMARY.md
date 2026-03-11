---
id: T02
parent: S01
milestone: M001
provides:
  - fraud_alerts.html admin dashboard page
  - /fraud-alerts page route in admin_dashboard.py
  - Fraud Alerts nav item in base.html sidebar (admin-only, with live unresolved count badge)
  - Stats row: Unresolved, Today, Total Alerts, Suspended Cards
  - Filter bar: unresolved-only checkbox, risk-level dropdown
  - Alerts table: card UID, fraud type, RISK_BADGES, description, created time, status, Resolve button
  - Suspended Cards table: card UID, reason, suspended time, Auto/Manual badge, Unsuspend button
  - Resolve modal with notes textarea
  - Manually Suspend Card modal with UID and reason inputs
  - JS layer: loadStats(), loadAlerts(), loadSuspended(), openResolveModal(), confirmResolve(), unsuspendCard(), confirmSuspend()
key_files:
  - backend/dashboard/templates/fraud_alerts.html
  - backend/dashboard/templates/base.html
  - backend/dashboard/admin_dashboard.py
key_decisions:
  - Sidebar badge fetches /api/fraud/stats on every page load (not polled live)
  - Active page class set via active_page=fraud_alerts in render_template
  - Risk badges use inline Bootstrap variants for immediate visual triage
patterns_established:
  - fetch() to JSON to innerHTML pattern for alerts and suspended cards tables; fallback to error message on exception
  - All modals dismiss automatically on success and reload the relevant table
observability_surfaces:
  - GET /api/fraud/stats drives sidebar badge
  - alertCountBadge in alerts table header updates to current filtered count on every reload
duration: implemented together with T01 in commit 6e0721d; verified in this session
verification_result: passed
completed_at: 2026-03-11
blocker_discovered: false
---

# T02: Fraud Alerts Admin Dashboard Page

**Delivered fraud_alerts.html with stats row, filterable alerts table, suspended cards table, and two modals plus a Fraud Alerts sidebar nav link with live unresolved count badge in base.html.**

## What Happened

The implementation was already present in commit 6e0721d before this session started. This task session verified the implementation and wrote the slice artifacts.

fraud_alerts.html contains:
- Stats row (4 metric cards): Unresolved, Today, Total Alerts, Suspended Cards via loadStats() calling GET /api/fraud/stats
- Filter bar: unresolved-only checkbox (checked by default) and risk-level dropdown; both call loadAlerts() on change
- Alerts table: Card UID, Type (human-readable via FRAUD_TYPE_LABELS), Risk (colored badge via RISK_BADGES), Description, Created (formatted via fmtDate()), Status, Resolve button for open alerts
- Suspended Cards table: card UID, reason, suspended time, Auto/Manual badge, Unsuspend button; Suspend Card button in section header
- Resolve modal: notes textarea, Cancel/Resolve buttons; calls POST /api/fraud/alerts/<id>/resolve on confirm
- Manually Suspend Card modal: UID + reason inputs; calls POST /api/fraud/cards/<uid>/suspend on confirm
- JS: loadStats(), loadAlerts(), loadSuspended(), openResolveModal(), confirmResolve(), unsuspendCard(), confirmSuspend(); all three load functions called in parallel on page load

base.html changes:
- Fraud Alerts nav link (/fraud-alerts) inside the {% if role == admin %} block with active class support
- fraudAlertBadge span that fetches /api/fraud/stats on every page load and shows count when > 0

admin_dashboard.py changes:
- GET /fraud-alerts route rendering fraud_alerts.html with active_page=fraud_alerts

## Verification

Template element checks: 16/16 PASS
Existing test suite: 4/4 PASS

## Diagnostics

- GET /api/fraud/stats confirms fraud detector is alive and drives sidebar badge
- GET /api/fraud/alerts?unresolved_only=true shows current alert queue
- Browser JS console: all fetch calls try/caught; errors surface as inline table messages

## Deviations

None.

## Known Issues

None.

## Files Created/Modified

- backend/dashboard/templates/fraud_alerts.html -- new: full fraud alerts page
- backend/dashboard/templates/base.html -- added Fraud Alerts nav link with live badge
- backend/dashboard/admin_dashboard.py -- added GET /fraud-alerts page route
