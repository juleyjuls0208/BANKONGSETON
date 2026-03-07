# Phase 19: Parent Portal - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Add a read-only parent role to the existing Flask web dashboard. Parents linked at student card registration can log in via web to view their student's current balance and full transaction history. Card registration form gains optional parent email + password fields. No new app, no new domain — everything runs inside the existing `admin_dashboard.py` Flask app.

Out of scope: parent push notifications, parent mobile app, parent top-up capability.

</domain>

<decisions>
## Implementation Decisions

### Portal entry point & layout
- Parents log in via the **existing `/login` page** (same as admin/finance) — no separate login URL
- After login, parent is redirected to `/parent` — a dedicated parent-only route
- The `/parent` page is **minimal**: student name + student ID at the top, then current balance, then full transaction list below
- **No admin dashboard shell** — no sidebar nav, no Bootstrap admin chrome. Clean and simple.
- Session behavior: **session-based, expires on idle/browser close** — consistent with existing admin session behavior

### Parent authentication
- Login method: **email + password**
- Password stored as a hash in a new **`ParentPasswordHash` column** in the Google Sheets Users sheet (alongside the already-existing `ParentEmail` column)
- **Admin sets the initial password** from the students management page — no self-service registration, no automated email of credentials
- **No self-service password reset** — admin resets parent password manually from the students management page (same action as setting it)
- Parent role key in session: `session["role"] = "parent"` — consistent with existing admin/finance role pattern

### Transaction history scope
- Parent sees **all-time transaction history** for their linked student, newest first
- Columns shown: **date, description/item, amount** (no cashier column, no transaction ID, no internal fields)
- A **monthly spending total** is shown near the balance: e.g., "Spent this month: ₱245.00" — a single number, no chart
- **No export** — view only. Parents can use browser print if needed.

### Card registration UX
- Parent email and password fields are added to the **existing student registration/edit form** on the students management page — same place admin manages all student info
- Both fields are **fully optional** — a student can be registered without a parent account; all existing functionality is unaffected
- The students list shows a **status indicator per student**: "Parent linked" or "No parent"
- To remove a parent account: admin **clears the email field** and saves — this unlinks the parent. No confirmation dialog needed.

### Claude's Discretion
- Exact visual layout of the parent dashboard page (balance card placement, table styling)
- Whether the existing `base.html` template is reused as a shell or a standalone `parent_dashboard.html` is created
- Password hashing library (bcrypt, werkzeug.security, or hashlib — whatever is already in use)
- Session expiry duration (recommend matching existing admin session timeout)
- How the login page distinguishes parent role from admin/finance after credential check (role detection logic)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/dashboard/admin_dashboard.py`: Flask app with `login_required` decorator, `session["admin_logged_in"]`/`session["role"]` pattern. New `parent_only` decorator follows same pattern.
- `backend/dashboard/templates/login.html`: Existing login page — reuse as-is; login route already handles multiple roles via `session["role"]`.
- `backend/dashboard/templates/students.html`: Existing student management page where parent email + password fields will be added.
- `backend/api/api_server.py` line 377: `parent_email = student.get("ParentEmail", "")` — ParentEmail column **already exists** in Users sheet. Only `ParentPasswordHash` is a new column.

### Established Patterns
- Session auth: `session["admin_logged_in"] = True` + `session["role"] = "admin|finance"` — parent adds `"parent"` to this role set
- Google Sheets access via `get_worksheet_with_retry("Users")` — parent auth reads same Users worksheet
- Role decorators: `login_required`, `admin_only`, `finance_or_admin` — new `parent_only` decorator follows the same pattern
- PythonAnywhere WSGI-compatible: no background workers, no websockets needed for parent portal

### Integration Points
- `admin_dashboard.py` `/login` route: After successful credential check, if `session["role"] == "parent"`, redirect to `/parent` instead of `/dashboard`
- New routes to add: `GET /parent` (parent dashboard), `POST /parent/logout`
- Google Sheets `Users` sheet: Add `ParentPasswordHash` column (ParentEmail already present)
- `students.html` form: Add parent email + password fields; add "Parent linked" / "No parent" badge to student list rows

</code_context>

<specifics>
## Specific Ideas

- Monthly spending summary near the balance: "Spent this month: ₱245.00" — one number, no chart, no date picker
- Student identity shown at top of parent page: student name + student ID number (so parent knows they're viewing the right account)
- The parent portal is intentionally minimal — no nav, no admin features, just balance + transactions

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 19-parent-portal*
*Context gathered: 2026-03-07*
