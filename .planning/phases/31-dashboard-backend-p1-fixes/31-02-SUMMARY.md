---
phase: 31-dashboard-backend-p1-fixes
plan: "02"
subsystem: backend/session-auth
tags: [session-ttl, security, memory-leak, currency-verification]
dependency_graph:
  requires: [31-01]
  provides: [session-ttl-enforcement]
  affects: [backend/api/api_server.py]
tech_stack:
  added: [time (stdlib)]
  patterns: [lazy-eviction, session-ttl]
key_files:
  modified: [backend/api/api_server.py]
  created: []
decisions:
  - "Used lazy eviction (_check_session) instead of background sweep thread to avoid dict-iteration race conditions"
  - "Stored login_time as time.time() float (not ISO string) for direct arithmetic comparison"
  - "Single helper _check_session() centralizes all TTL logic — 10 inline checks replaced"
metrics:
  duration: "5min"
  completed: "2026-03-10T06:03:34Z"
  tasks_completed: 2
  files_modified: 1
---

# Phase 31 Plan 02: Session TTL + Currency Symbol Verification Summary

**One-liner:** 8-hour session TTL via lazy eviction in `_check_session()` using `time.time()` float; REQ-CURR-01 ₱ symbol confirmed project-wide.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add 8-hour TTL to active_sessions with lazy eviction | 9552418 | backend/api/api_server.py |
| 2 | Verify REQ-CURR-01 currency symbol fix (no code changes) | bf8a0d2 | — |

## What Was Built

### Task 1: Session TTL Enforcement

Added 8-hour absolute TTL to `active_sessions` in `backend/api/api_server.py`:

- **`import time`** added to top-level imports (was missing)
- **`SESSION_TTL_SECONDS = 8 * 3600`** constant after `active_sessions = {}`
- **`_check_session(token)`** helper: checks `time.time() - session["login_time"] > SESSION_TTL_SECONDS`, performs lazy eviction (deletes entry), returns `None` on expiry
- **`login_time`** changed from `get_philippines_time().isoformat()` (ISO string) to `time.time()` (float) at login storage (~line 299)
- **10 inline auth patterns** replaced: all `if token not in active_sessions: return 401` + `session = active_sessions[token]` → `session = _check_session(token); if session is None: return 401 "Session expired, please log in again"`

**Security impact:** Stolen tokens now expire after 8 hours maximum. Previously, a token was valid indefinitely until the server restarted.

**Memory impact:** Stale sessions are evicted lazily on next access, preventing unbounded growth after a busy school day.

### Task 2: REQ-CURR-01 Verification

Project-wide search across all `.py`, `.html`, `.js`, `.ts`, `.jsx`, `.tsx` files (excluding `.git`, `node_modules`, `__pycache__`, `.planning`, `docs`, `venv`) found **zero occurrences** of the Thai Baht symbol `฿`. The fix from commit `64cef70` is confirmed in place. No code changes were required.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] One inline auth pattern had no blank line separator**
- **Found during:** Task 1
- **Issue:** The regex replacement matched 9 of 10 patterns (those with a blank line between `return 401` and `session = active_sessions[token]`). Line ~1581 had no blank line, so it wasn't caught by the batch regex.
- **Fix:** Applied a targeted literal replacement for the remaining occurrence.
- **Files modified:** backend/api/api_server.py
- **Commit:** 9552418 (included in same atomic commit)

**2. [Discrepancy] Plan's `<interfaces>` block described outdated `require_auth` decorator**
- **Found during:** Pre-execution analysis
- **Issue:** The plan showed `require_auth` as a session-based decorator. The actual code uses JWT for `require_auth`; session auth is entirely inline per-route.
- **Impact:** More replacements needed than plan implied — 10 inline patterns instead of 1 decorator.
- **Fix:** Replaced all 10 inline patterns. No architectural change required.

## Self-Check

### Files Verified
- `backend/api/api_server.py` — modified ✓
- Verification script confirms: `SESSION_TTL_SECONDS` ✓, `_check_session` ✓, `Session expired, please log in again` (10×) ✓, `time.time()` ✓, no `isoformat()` on `login_time` ✓, no remaining `token not in active_sessions` ✓

### Commits Verified
- `9552418` — fix(31-02): add 8-hour TTL to active_sessions with lazy eviction ✓
- `bf8a0d2` — chore(31-02): verify REQ-CURR-01 currency symbol fix confirmed ✓

## Self-Check: PASSED
