# Phase 19-01 Summary — Parent Auth Backend

**Status:** Complete  
**Phase:** 19-parent-portal  
**Plan:** 01  
**Requirements covered:** PAR-01, PAR-02, PAR-04

---

## What Was Done

Added parent authentication infrastructure to `backend/dashboard/admin_dashboard.py`.

### Changes Made

**`backend/dashboard/admin_dashboard.py`**

1. **Import added** — `from werkzeug.security import generate_password_hash, check_password_hash` at top of file.

2. **`parent_only` decorator** — Added after `admin_only`. Requires `admin_logged_in` in session AND `session["role"] == "parent"`. Redirects to `url_for("login")` for both unauthenticated and wrong-role users.

3. **`index()` route** — Added parent redirect: if `session["role"] == "parent"`, redirects to `parent_portal` before the existing dashboard redirect.

4. **`login()` route** — Extended POST handler with a third credential check block (before the `else: 401`). Looks up username (treated as email) in Users sheet, matches `ParentEmail` column, verifies `ParentPasswordHash` with `check_password_hash`. On success, sets `session["role"] = "parent"`, `session["parent_student_id"]`, `session["parent_student_name"]`.

5. **`GET /parent` → `parent_portal()`** — Decorated with `@parent_only`. Renders `parent_dashboard.html`, passes `student_id` and `student_name` from session (template also fetches fresh data via JS).

6. **`POST /parent/logout` → `parent_logout()`** — Calls `session.clear()` and redirects to login.

7. **`POST /api/students/<student_id>/set-parent` → `set_parent_credentials()`** — Decorated with `@admin_only`. Accepts `{parent_email, parent_password}` JSON. Creates `ParentPasswordHash` column in Users sheet if missing. Writes email + password hash when email provided; clears both when email is blank.

---

## Key Decisions

- `parent_only` redirects to `login` (not `dashboard`) for wrong role — parent is a consumer, not an admin.
- Password hashing uses `werkzeug.security.generate_password_hash` (same library as Flask auth best practices; already a dependency).
- Blank `parent_email` = remove parent account (clears both email and hash columns).
- Parent login reuses the existing `/login` page; email is the username field.

---

## Artifacts Created / Modified

| File | Change |
|------|--------|
| `backend/dashboard/admin_dashboard.py` | Added import, decorator, 2 routes, login extension, set-parent API |

---

## Verification

```
python -c "import ast; c=open('backend/dashboard/admin_dashboard.py').read(); ast.parse(c); assert 'parent_only' in c; assert 'parent_portal' in c; assert 'parent_logout' in c; assert 'set_parent_credentials' in c; assert 'ParentPasswordHash' in c; assert 'check_password_hash' in c; print('ALL CHECKS PASSED')"
```
Result: `ALL CHECKS PASSED`
