# Phase 14: NFC Simulation UI - Research

**Researched:** 2026-03-03
**Domain:** Flask/Jinja2 HTML panel + JSON API endpoint (Python/Bootstrap)
**Confidence:** HIGH — codebase fully readable, all patterns directly verified from source

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Panel Placement**
- Replace the existing "Web Dashboard Mode — Card management features require desktop installation with Arduino hardware." info alert with the simulation panel
- Stays within the existing `{% if role == 'admin' %}` Card Management section, `{% else %}` branch (web mode)
- Titled panel with subtitle explaining it is for testing without hardware
- Single-column layout, full width of the Card Management area
- Matches the existing `stat-card` visual style (white background, slight shadow) — no new visual patterns
- Button shows "Simulating..." and disables while the request is in-flight; re-enables on response

**Student Selection**
- Dropdown `<select>` populated at page render via Jinja (no AJAX)
- Each option shows student name only (e.g., "Juan dela Cruz")
- Default state: placeholder "Select a student..." selected, Simulate Tap button disabled until a student is chosen
- Populated from `get_students()` in `web_app.py`

**What Simulate Does (Backend Endpoint)**
- New endpoint in `web_app.py` — dashboard-local, no cross-server dependency
- Action: verify card registration only — check whether the selected student has an RFID card registered and return their info. No balance deduction, no transaction record.
- Success response: student name, card UID, current balance, and card registration status
- Distinct error cases handled:
  - Student not found (invalid or missing student ID)
  - Student has no card registered
  - Google Sheets unavailable (service error)

**Result Display**
- Inline result area inside the panel, below the Simulate Tap button
- Hidden on initial page load; appears after the first simulate attempt
- Success: Bootstrap `alert-success` (green) showing student name, card UID, balance, and status ("Card registered — ready for payments")
- Error: Bootstrap `alert-danger` (red) showing the specific error message (not found / no card / service error)

### Claude's Discretion
- Exact card UID masking (show full UID or mask middle chars)
- Endpoint URL path (`/api/nfc/simulate` or similar)
- Exact balance formatting (₱ symbol, decimal places)
- Error message wording

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WEB-02 | NFC simulation panel in admin web dashboard for testing card tap without Arduino hardware | All patterns confirmed directly from source: `stat-card` CSS, `async/await fetch` JS, Bootstrap alert classes, `@admin_only` decorator, Sheets lookup logic, Jinja student dropdown |
</phase_requirements>

---

## Summary

Phase 14 adds a single NFC simulation panel to `dashboard.html` and a single POST endpoint to `web_app.py`. The work is entirely self-contained within the existing web dashboard stack — Flask + Jinja2 templates + vanilla JS `async/await fetch` + Bootstrap 5 — with zero new dependencies.

The panel replaces a 4-line info alert (lines 369–373 of `dashboard.html`) inside the `{% if role == 'admin' %}` / `{% else %}` block. The backend endpoint follows the same pattern as the dozen existing admin-only JSON endpoints in `web_app.py`. The Jinja dropdown requires adding a `students=` context variable to the `/dashboard` route, which is a one-line change.

The only non-trivial decision is how to fetch students for the Jinja context in the `/dashboard` route. `get_students()` is an API endpoint function, not a plain helper — the implementation must inline the same Sheets logic (Users + Money Accounts) or extract it into a reusable helper. Inlining is the simpler path; extracting is cleaner for future reuse. Either works.

**Primary recommendation:** Use `@admin_only` decorator on the new endpoint. Inline the student-fetch logic into the `/dashboard` route (copy from `get_students()`). Keep error handling identical to existing endpoints.

---

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|---|---|---|---|
| Flask | in use | Route registration, `jsonify`, `request.json` | Already the only web framework |
| Jinja2 | in use | Template rendering — student `<select>` options | Already used for all template context |
| Bootstrap 5 | in use (CDN) | `stat-card` CSS, `alert-success`, `alert-danger`, `d-none` | Already loaded in `dashboard.html` |
| gspread | in use | Google Sheets access — Users + Money Accounts lookup | All existing student endpoints use this |
| vanilla JS `fetch` | in use | `async/await` POST to `/api/nfc/simulate` | All existing dashboard JS uses this pattern |

### No New Dependencies
This phase installs nothing. All required tools are already present in the codebase.

---

## Architecture Patterns

### Recommended File Changes
```
backend/
└── dashboard/
    ├── web_app.py              # Two changes:
    │   ├── /dashboard route    #   1. Add students= to render_template call
    │   └── /api/nfc/simulate   #   2. New POST endpoint (admin_only)
    └── templates/
        └── dashboard.html      # One change: replace lines 369-373 with simulation panel
```

### Pattern 1: Admin-Only POST Endpoint

**What:** Protected JSON endpoint, reads `request.json`, validates input, queries Sheets, returns `jsonify`.
**When to use:** Any admin-gated write or lookup action.

```python
# Source: web_app.py lines 1468-1469, 1810 (existing @admin_only endpoints)
@app.route('/api/nfc/simulate', methods=['POST'])
@admin_only
def nfc_simulate():
    """Simulate NFC card tap — verify card registration, no payment"""
    try:
        data = request.json or {}
        student_id = str(data.get('student_id', '')).strip()
        if not student_id:
            return jsonify({'error': 'Student ID is required'}), 400

        users_sheet = get_worksheet_with_retry('Users')
        students = users_sheet.get_all_records()

        # Find student by StudentID
        student = next(
            (s for s in students if str(s.get('StudentID', '')) == student_id),
            None
        )
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        money_card = normalize_card_uid(str(student.get('MoneyCardNumber', '')))
        if not money_card:
            return jsonify({'error': 'No card registered for this student'}), 404

        # Fetch balance from Money Accounts
        money_sheet = get_worksheet_with_retry('Money Accounts')
        money_accounts = money_sheet.get_all_records()
        balance = 0.00
        for account in money_accounts:
            if normalize_card_uid(str(account.get('MoneyCardNumber', ''))) == money_card:
                balance = account.get('Balance', 0.00)
                break

        return jsonify({
            'student_name': student.get('Name'),
            'card_uid': student.get('MoneyCardNumber'),
            'balance': balance,
            'status': 'registered'
        })

    except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
            gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
        logger.error(f"Google Sheets unavailable in nfc_simulate: {e}")
        return jsonify({'error': 'Service unavailable, please try again'}), 503
    except Exception as e:
        logger.error(f"Unexpected error in nfc_simulate: {e}", exc_info=True)
        return jsonify({'error': 'An unexpected error occurred'}), 500
```

### Pattern 2: Passing Students to Jinja Template

**What:** Fetch all students in the route handler and pass as template context.
**When to use:** Dropdown needs data at render time, no AJAX.

```python
# Source: web_app.py line 300-307 (existing /dashboard route — extend this)
@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard page"""
    students = []
    if session.get('role') == 'admin':
        try:
            users_sheet = get_worksheet_with_retry('Users')
            students = users_sheet.get_all_records()
        except Exception:
            students = []  # Fail silently — dropdown will be empty, not a crash

    return render_template('dashboard.html',
                         username=session.get('admin_username'),
                         role=session.get('role', 'finance'),
                         arduino_available=False,
                         students=students)
```

> **Note:** Only fetch students when `role == 'admin'` to avoid an unnecessary Sheets call for finance users.

### Pattern 3: Simulation Panel HTML (Jinja + Bootstrap)

**What:** `stat-card` div replacing the info alert, with Jinja-rendered `<select>`, a submit button, and a hidden result div.
**When to use:** Admin web-mode panel with inline result feedback.

```html
<!-- Source: dashboard.html lines 369-373 (replace this block) -->
{% else %}
<!-- NFC Simulation Panel (Web Mode - Admin Only) -->
<div class="stat-card mb-4">
    <h5><i class="bi bi-wifi"></i> NFC Simulation</h5>
    <p class="text-muted small">Simulate a card tap for testing without Arduino hardware.</p>
    <div class="mb-3">
        <label for="nfcStudentSelect" class="form-label">Student</label>
        <select class="form-select" id="nfcStudentSelect" onchange="nfcSelectChanged()">
            <option value="" disabled selected>Select a student...</option>
            {% for student in students %}
            <option value="{{ student.StudentID }}">{{ student.Name }}</option>
            {% endfor %}
        </select>
    </div>
    <button class="btn btn-primary" id="nfcSimulateBtn" onclick="simulateNfcTap()" disabled>
        <i class="bi bi-wifi"></i> Simulate Tap
    </button>
    <div id="nfcResult" class="mt-3 d-none"></div>
</div>
{% endif %}
```

### Pattern 4: Async Fetch JS with Loading State

**What:** `async/await fetch` POST, button disabled during request, inline result via class swap.
**When to use:** All dashboard API calls — this is the only JS pattern used in the template.

```javascript
// Source: dashboard.html lines 851-901 (loadBalanceForm submit handler — canonical example)
function nfcSelectChanged() {
    const select = document.getElementById('nfcStudentSelect');
    document.getElementById('nfcSimulateBtn').disabled = !select.value;
}

async function simulateNfcTap() {
    const studentId = document.getElementById('nfcStudentSelect').value;
    const btn = document.getElementById('nfcSimulateBtn');
    const resultDiv = document.getElementById('nfcResult');

    btn.disabled = true;
    btn.innerHTML = '<i class="bi bi-hourglass-split"></i> Simulating...';
    resultDiv.classList.add('d-none');

    try {
        const response = await fetch('/api/nfc/simulate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: studentId })
        });
        const data = await response.json();

        if (response.ok) {
            resultDiv.className = 'alert alert-success mt-3';
            resultDiv.innerHTML = `
                <strong>${data.student_name}</strong><br>
                Card UID: <code>${data.card_uid}</code><br>
                Balance: ฿${parseFloat(data.balance).toFixed(2)}<br>
                <span class="badge bg-success">Card registered — ready for payments</span>
            `;
        } else {
            resultDiv.className = 'alert alert-danger mt-3';
            resultDiv.textContent = data.error;
        }
        resultDiv.classList.remove('d-none');
    } catch (error) {
        resultDiv.className = 'alert alert-danger mt-3';
        resultDiv.textContent = 'Network error: ' + error.message;
        resultDiv.classList.remove('d-none');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-wifi"></i> Simulate Tap';
    }
}
```

### Anti-Patterns to Avoid

- **Calling `/api/students` via AJAX to populate the dropdown:** Locked decision — use Jinja at render time.
- **Using `@login_required` instead of `@admin_only`:** Simulation is an admin tool; `@admin_only` enforces role check and returns 403 JSON (not a redirect) for non-admins.
- **Adding new CSS classes or visual styles:** Use `stat-card` exactly as-is — no new patterns.
- **Crashing `/dashboard` when Sheets is down:** Wrap the student fetch in `try/except` and pass `students=[]` gracefully.
- **Re-enabling the button inside the `if response.ok` branch only:** Always re-enable in `finally` — confirmed pattern from lines 898-900.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Card UID normalization | Custom string cleanup | `normalize_card_uid()` from `utils.py` (already imported at line 31) | Already handles all edge cases for this codebase |
| Bootstrap alert toggling | Custom CSS show/hide | `d-none` class add/remove + `className` reassignment | Already the pattern in the template (lines 858, 873, 890) |
| Auth guard on new endpoint | Inline `session.get('role')` check | `@admin_only` decorator (line 223) | Centralized, consistent, returns proper 403 JSON |
| Sheets retry logic | Direct `gspread` call | `get_worksheet_with_retry()` — already used everywhere | Handles transient Sheets API errors |

---

## Common Pitfalls

### Pitfall 1: `/dashboard` Route Crashes When Sheets Is Unavailable
**What goes wrong:** The student fetch added to the `/dashboard` route raises an exception, making the whole dashboard page return 500.
**Why it happens:** Sheets API calls can fail transiently; the route currently has no Sheets calls and no try/except.
**How to avoid:** Wrap the student fetch in `try/except Exception: students = []`. The dropdown will be empty but the page loads.
**Warning signs:** 500 on `/dashboard` in any environment without active Sheets connectivity.

### Pitfall 2: `students` Variable Undefined in Template
**What goes wrong:** `{% for student in students %}` throws a Jinja `UndefinedError` for finance users or when not passed.
**Why it happens:** `/dashboard` route currently passes only `username`, `role`, `arduino_available` — `students` is not in the context.
**How to avoid:** Always pass `students=students` (even as empty list `[]`) in the `render_template` call.
**Warning signs:** Jinja `UndefinedError` in server logs on dashboard load.

### Pitfall 3: Simulate Button Never Re-Enables After Network Error
**What goes wrong:** On a JS `catch` block, the button stays disabled forever.
**Why it happens:** `btn.disabled = false` placed only in the success branch.
**How to avoid:** Place `btn.disabled = false` and button text reset in the `finally` block — confirmed pattern from `loadBalanceForm` submit handler (line 898-900).

### Pitfall 4: `StudentID` Type Mismatch in Lookup
**What goes wrong:** Student lookup returns `None` even when the student exists.
**Why it happens:** Sheets returns numeric `StudentID` as int; `request.json` delivers it as a string; `==` fails across types.
**How to avoid:** Always `str(s.get('StudentID', '')) == student_id` where `student_id` is also `str(...)` — confirmed pattern from lines 827, 872.

### Pitfall 5: Finance Role Sees the Simulation Panel
**What goes wrong:** The simulation panel is visible to finance users.
**Why it happens:** The `{% else %}` branch is inside `{% if role == 'admin' %}` — but only if the outer block is correct.
**How to avoid:** Confirm the panel HTML sits inside the existing `{% if role == 'admin' %}` outer block (lines ~200–389 of `dashboard.html`), not outside it.

---

## Code Examples

### Verified: Existing `stat-card` CSS (dashboard.html lines 68-74)
```css
/* Source: dashboard.html lines 68-74 */
.stat-card {
    background: white;
    border-radius: 12px;
    padding: 25px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}
```

### Verified: Exception Hierarchy for Sheets Errors (web_app.py lines 793-799)
```python
# Source: web_app.py lines 793-799 — copy this exception tuple exactly
except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
    logger.error(f"Google Sheets unavailable in {func_name}: {e}")
    return jsonify({'error': 'Service unavailable, please try again'}), 503
except Exception as e:
    logger.error(f"Unexpected error in {func_name}: {e}", exc_info=True)
    return jsonify({'error': 'An unexpected error occurred'}), 500
```

### Verified: `normalize_card_uid` Import (web_app.py line 31)
```python
# Source: web_app.py line 31 — already imported, no change needed
from utils import card_reader_state, normalize_card_uid
```

### Verified: Exact Replacement Target (dashboard.html lines 369-373)
```html
<!-- Source: dashboard.html lines 369-373 — REPLACE THIS ENTIRE BLOCK -->
{% else %}
<!-- Web-Only Mode Notice -->
<div class="alert alert-info mb-4">
    <i class="bi bi-cloud"></i> <strong>Web Dashboard Mode</strong> - Card management features require desktop installation with Arduino hardware.
</div>
{% endif %}
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|---|---|---|
| Static info alert (lines 369-373) | Interactive simulation panel | Admin can verify card registration in web-only mode without hardware |
| No students context in `/dashboard` | `students=` passed from route | Enables Jinja-rendered dropdown with zero AJAX |

---

## Open Questions

1. **Where exactly to place the new JS functions in `dashboard.html`**
   - What we know: all JS is in a single `<script>` block near the bottom of the file
   - What's unclear: exact line number to insert `simulateNfcTap()` and `nfcSelectChanged()`
   - Recommendation: append to the existing `<script>` block — order doesn't matter since the functions are called via `onclick`

2. **Whether to extract a shared `fetch_students_for_context()` helper**
   - What we know: inlining is simpler; the logic is 5 lines
   - What's unclear: whether future phases will need the same helper
   - Recommendation: inline for now — YAGNI; the planner can decide to extract if desired

---

## Sources

### Primary (HIGH confidence)
- `backend/dashboard/web_app.py` — full read (1960 lines): decorators, route patterns, Sheets logic, error handling, `normalize_card_uid` import
- `backend/dashboard/templates/dashboard.html` — targeted reads (lines 55-440, 848-902): `stat-card` CSS, exact replacement target, `async/await fetch` JS pattern, Bootstrap alert pattern
- `.planning/phases/14-nfc-simulation-ui/14-CONTEXT.md` — locked decisions, discretion areas

### Secondary (MEDIUM confidence)
- `.planning/config.json` — `nyquist_validation` absent = disabled; `commit_docs: true`

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use, confirmed from imports and template
- Architecture: HIGH — all patterns copied directly from existing codebase; no new patterns
- Pitfalls: HIGH — all derived from direct code reading, not inference
- Validation Architecture: SKIPPED — `nyquist_validation` not present in config.json

**Research date:** 2026-03-03
**Valid until:** 2026-04-03 (stable stack; no external dependencies)
