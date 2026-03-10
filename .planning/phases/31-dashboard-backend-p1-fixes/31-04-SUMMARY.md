---
phase: 31-dashboard-backend-p1-fixes
plan: "04"
subsystem: backend-auth
tags: [jwt, auth, student-login, api]
dependency_graph:
  requires: [31-02]
  provides: [jwt-student-auth]
  affects: [backend/api/api_server.py]
tech_stack:
  added: []
  patterns: [JWT as active_sessions key, opaque token preserved but unused at login]
key_files:
  modified: [backend/api/api_server.py]
  created: []
decisions:
  - "active_sessions dict remains source of truth for student auth — JWT is the key, not the auth mechanism"
  - "generate_token() preserved in file — not deleted — in case of other callers"
  - "One-line change: generate_token() → generate_jwt_token(student[\"StudentID\"]) at line 310"
metrics:
  duration: 5min
  completed: "2026-03-10"
  tasks_completed: 2
  files_changed: 1
requirements_satisfied: [REQ-QUAL-01]
---

# Phase 31 Plan 04: Wire JWT Token into Student Login Summary

**One-liner:** Wired existing `generate_jwt_token(student_id)` into student login — JWT string replaces opaque `secrets.token_urlsafe(32)` as the `active_sessions` key.

## What Was Built

Student login in `backend/api/api_server.py` now generates a proper JWT token (with `user_id`, `role="student"`, `exp`, `iat` claims) instead of an opaque random string. The `active_sessions` dict is still used as the session store with the JWT as its key — this is consistent with the 8-hour TTL eviction added in plan 31-02.

### Change Summary

| File | Change |
|------|--------|
| `backend/api/api_server.py:310` | `generate_token()` → `generate_jwt_token(student["StudentID"])` |
| `backend/api/api_server.py:310` | Comment: `# Generate session token` → `# Generate JWT session token` |

### Architecture Notes

- `generate_jwt_token(user_id, role="student")` existed at line 172 but was never called (dead code before this plan)
- `generate_token()` (opaque `secrets.token_urlsafe(32)`) is still defined but no longer called at student login
- `active_sessions[token]` dict still populated with same keys: `student_id`, `card_number`, `login_time` (float)
- All downstream student endpoints use `_check_session(token)` to read from `active_sessions` — no changes needed there
- Android API contract unchanged: login response still returns `{"token": "...", ...}`

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Read generate_jwt_token() and require_auth before wiring | (read-only, no commit) | backend/api/api_server.py |
| 2 | Wire generate_jwt_token() into student login | 30703a1 | backend/api/api_server.py |

## Deviations from Plan

None — plan executed exactly as written. The one-line change was precisely as specified.

## Verification Results

```
PASS: student login uses generate_jwt_token()
PASS: generate_token() still present (not deleted)
PASS: active_sessions dict still used as session store
```

## Self-Check: PASSED

- [x] `backend/api/api_server.py` modified — confirmed present
- [x] Commit `30703a1` exists — confirmed via `git log`
- [x] `generate_jwt_token(student["StudentID"])` in source — verified
- [x] `generate_token()` still defined — verified
- [x] `active_sessions[token]` still used — verified
