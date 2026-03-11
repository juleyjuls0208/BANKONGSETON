# T02: Fraud Alerts Admin Dashboard Page

**Slice:** S01
**Milestone:** M001

## Goal
Add a Fraud Alerts page to the admin dashboard with alerts table, resolve button, and card suspend/unsuspend UI.

## Must-Haves

### Truths
- "Fraud Alerts" nav item appears in the sidebar with an unresolved alert count badge
- Navigating to /fraud-alerts renders the page (returns 200)
- Alerts table renders rows with: card UID, fraud type, risk badge (color-coded), description, created time, Resolve button
- Clicking Resolve opens a modal for optional notes, then POSTs to /api/fraud/alerts/<id>/resolve and refreshes the table
- Suspended Cards section shows card, reason, suspended time, and Unsuspend button
- Manual suspend form lets admin enter a card UID and reason, then POSTs to /api/fraud/cards/<uid>/suspend
- Risk badge colors: CRITICAL=red, HIGH=orange, MEDIUM=yellow, LOW=gray

### Artifacts
- `backend/dashboard/templates/fraud_alerts.html` — new page (min 150 lines, full Bootstrap 5 layout matching existing pages)
- `backend/dashboard/templates/base.html` — updated nav entry for Fraud Alerts with badge
- `backend/dashboard/admin_dashboard.py` — new route GET /fraud-alerts returning render_template

### Key Links
- fraud_alerts.html JS → /api/fraud/alerts for table data
- fraud_alerts.html JS → /api/fraud/alerts/<id>/resolve for resolve action
- fraud_alerts.html JS → /api/fraud/suspended for suspended cards section
- fraud_alerts.html JS → /api/fraud/cards/<uid>/suspend and /unsuspend
- base.html badge → /api/fraud/stats for unresolved count

## Steps
1. Add GET /fraud-alerts route to admin_dashboard.py (login_required)
2. Read base.html to understand nav structure
3. Add "Fraud Alerts" nav item to base.html sidebar with badge span (id="fraudAlertBadge")
4. Write fraud_alerts.html: Bootstrap 5, sidebar from base, two sections (Alerts and Suspended Cards)
5. JS: on page load, fetch /api/fraud/alerts?unresolved_only=true and render table
6. JS: Resolve button opens modal with notes textarea, on confirm POST to /api/fraud/alerts/<id>/resolve, reload table
7. JS: render suspended cards section from /api/fraud/suspended
8. JS: Unsuspend button POSTs to /api/fraud/cards/<uid>/unsuspend, reloads section
9. JS: Manual suspend form — card UID input + reason input + Submit, POSTs to /api/fraud/cards/<uid>/suspend
10. JS: base.html badge update — fetch /api/fraud/stats on page load, set badge text to unresolved_alerts

## Context
- Look at backend/dashboard/templates/students.html for the pattern: sidebar, table, modal
- base.html nav items follow pattern: <a href="/route" class="...">icon + text</a>
- All existing pages use Bootstrap 5.3 + Bootstrap Icons
- Match the indigo/purple color scheme of the existing dashboard
