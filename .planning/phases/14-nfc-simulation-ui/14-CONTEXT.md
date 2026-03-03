# Phase 14: NFC Simulation UI - Context

**Gathered:** 2026-03-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Add an NFC simulation panel to the admin dashboard that lets developers and testers simulate a card tap without physical Arduino hardware. The panel is only visible in web mode (`arduino_available=False`). Fulfills WEB-02 gap from the v1.0 audit.

The simulate endpoint verifies card registration status — it does NOT process payments or move money. Creating payments and the cashier POS are separate concerns.

</domain>

<decisions>
## Implementation Decisions

### Panel Placement
- Replace the existing "Web Dashboard Mode — Card management features require desktop installation with Arduino hardware." info alert with the simulation panel
- Stays within the existing `{% if role == 'admin' %}` Card Management section, `{% else %}` branch (web mode)
- Titled panel with subtitle explaining it is for testing without hardware
- Single-column layout, full width of the Card Management area
- Matches the existing `stat-card` visual style (white background, slight shadow) — no new visual patterns
- Button shows "Simulating..." and disables while the request is in-flight; re-enables on response

### Student Selection
- Dropdown `<select>` populated at page render via Jinja (no AJAX)
- Each option shows student name only (e.g., "Juan dela Cruz")
- Default state: placeholder "Select a student..." selected, Simulate Tap button disabled until a student is chosen
- Populated from `get_students()` in `web_app.py`

### What Simulate Does (Backend Endpoint)
- New endpoint in `web_app.py` — dashboard-local, no cross-server dependency
- Action: verify card registration only — check whether the selected student has an RFID card registered and return their info. No balance deduction, no transaction record.
- Success response: student name, card UID, current balance, and card registration status
- Distinct error cases handled:
  - Student not found (invalid or missing student ID)
  - Student has no card registered
  - Google Sheets unavailable (service error)

### Result Display
- Inline result area inside the panel, below the Simulate Tap button
- Hidden on initial page load; appears after the first simulate attempt
- Success: Bootstrap `alert-success` (green) showing student name, card UID, balance, and status ("Card registered — ready for payments")
- Error: Bootstrap `alert-danger` (red) showing the specific error message (not found / no card / service error)

### Claude's Discretion
- Exact card UID masking (show full UID or mask middle chars)
- Endpoint URL path (`/api/nfc/simulate` or similar)
- Exact balance formatting (₱ symbol, decimal places)
- Error message wording

</decisions>

<specifics>
## Specific Ideas

No specific UI references given — standard dashboard style is sufficient.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard.html` `{% if arduino_available %} / {% else %}` block: simulation panel goes in the `{% else %}` branch, replacing the bare info alert at line ~372
- `get_students()` in `web_app.py`: already returns student list from Google Sheets — use for Jinja-rendered dropdown
- Bootstrap `alert-success` / `alert-danger`: already used throughout the dashboard for feedback states
- Existing `stat-card` CSS class: used for all dashboard panels — reuse directly

### Established Patterns
- All dashboard routes in `web_app.py` use `@app.route` with JSON responses for API endpoints
- Auth guard: `@login_required` decorator (or session check) used on all protected routes
- Template rendering: `render_template('dashboard.html', ..., arduino_available=False)` is the pattern in `web_app.py`
- Google Sheets access: `get_sheets_client()` utility in `web_app.py` — use same pattern as other student endpoints

### Integration Points
- `backend/dashboard/web_app.py`: add new `/api/nfc/simulate` route (POST, JSON body with `student_name` or `student_id`)
- `backend/dashboard/templates/dashboard.html`: replace the `{% else %}` info alert block with simulation panel HTML + inline JS for fetch + result rendering
- `web_app.py` route for `/dashboard`: already passes `students` or can pass student list for the dropdown via Jinja context

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 14-nfc-simulation-ui*
*Context gathered: 2026-03-03*
