# Phase 19-03 Summary — Students UI: Parent Badge + Set Parent Modal + Login Redirect

**Status:** Complete  
**Phase:** 19-parent-portal  
**Plan:** 03  
**Requirements covered:** PAR-06

---

## What Was Done

Updated `students.html` to show parent link status per student and allow admin to set/clear parent credentials. Updated `login.html` to redirect parent role to `/parent` instead of `/dashboard`.

### Changes Made

**`backend/dashboard/templates/students.html`**

1. **`<th>Parent</th>` column header** — Added after the Status `<th>`, before the admin Actions `<th>`.

2. **`colspan` updated** — The empty/loading row `<td>` colspan updated from `IS_ADMIN ? 7 : 6` to `IS_ADMIN ? 8 : 7` to account for the new Parent column.

3. **Parent badge cell** — Added in the `students.map()` template literal, after the Status cell. Renders:
   - `s.ParentEmail` truthy → `<span class="badge bg-info badge-status text-dark">Parent linked</span>`
   - falsy → `<span class="badge bg-light badge-status text-muted border">No parent</span>`

4. **"Set Parent" button** — Added inside the `${IS_ADMIN ? ...}` admin actions block after the History button. Calls `openSetParentModal(studentId, studentName, currentEmail)`.

5. **Set Parent modal HTML** — Added `id="setParentModal"` Bootstrap 5 modal inside the `{% if role == 'admin' %}` block (after topupModal). Contains: parent email input, parent password input (with "leave blank to keep existing" hint), feedback alert div, Save/Cancel buttons, spinner.

6. **Set Parent JS** — Added inside the `{% if role == 'admin' %}` script block:
   - `_setParentStudentId` module-level variable.
   - `openSetParentModal(studentId, studentName, currentEmail)` — populates modal fields and shows it via `new bootstrap.Modal(...)`.
   - `set-parent-confirm-btn` click handler — POSTs `{ parent_email, parent_password }` to `/api/students/${id}/set-parent`. On success: shows green alert + calls `loadStudents()` to refresh badge. On failure: shows red alert with `data.error`. Spinner + button disable/re-enable in try/finally.

**`backend/dashboard/templates/login.html`**

7. **Role-aware redirect** — The login success handler changed from:
   ```javascript
   if (data.success) {
       window.location.href = '/dashboard';
   ```
   to:
   ```javascript
   if (data.success) {
       if (data.role === 'parent') {
           window.location.href = '/parent';
       } else {
           window.location.href = '/dashboard';
       }
   ```
   Admin and finance users continue redirecting to `/dashboard`.

---

## Key Decisions

- Parent badge uses Bootstrap `bg-info` (blue) for linked, `bg-light border` (grey/outline) for unlinked — visually distinct without using red (which implies error/danger).
- `openSetParentModal` is called with 3 args (id, name, currentEmail) so the modal pre-fills the existing email — admin can see the current email and edit it rather than re-typing from scratch.
- Clearing the email field and saving removes the parent account (handled by `set_parent_credentials` backend from 19-01).
- After saving, `loadStudents()` is called (not a full page reload) to refresh the badge in-place.
- Login redirect checks `data.role === 'parent'` (exact string from backend session) before falling through to `/dashboard`.

---

## Artifacts Created / Modified

| File | Change |
|------|--------|
| `backend/dashboard/templates/students.html` | Added Parent column header, colspan update, parent badge cell, Set Parent button, setParentModal HTML, openSetParentModal JS, set-parent-confirm-btn click handler |
| `backend/dashboard/templates/login.html` | Role-aware redirect: `parent` → `/parent`, else → `/dashboard` |

---

## Verification

```
python -c "
c = open('backend/dashboard/templates/students.html').read()
assert 'setParentModal' in c, 'missing modal'
assert 'openSetParentModal' in c, 'missing JS function'
assert 'set-parent-confirm-btn' in c, 'missing confirm button'
assert 'set-parent' in c, 'missing API call'
print('students.html OK')
"
python -c "
c = open('backend/dashboard/templates/login.html').read()
assert \"data.role === 'parent'\" in c, 'missing parent role check'
assert \"'/parent'\" in c, 'missing /parent redirect'
print('login.html OK')
"
```
Result: `students.html OK` / `login.html OK`
