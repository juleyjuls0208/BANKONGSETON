# Phase 31: Dashboard & Backend P1 Fixes - Context

**Gathered:** 2026-03-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix 8 P1 requirements across backend and dashboard: socket event key mismatch, TXN ID collision, WriteQueue infinite retry, in-memory session leak, hardcoded FINANCE_PASSWORD default, dead JWT code (migrate to JWT), dashboard code duplication (~90% identical files), and wrong currency symbol in FCM push notifications.

</domain>

<decisions>
## Implementation Decisions

### REQ-BUG-05: card_error socket event key mismatch
- Backend emits `data.message`; dashboard.html line 768 reads `data.message` (appears correct)
- Planner must audit line 709 (modal path reads `data.error`) — one of these two paths is broken
- Fix whichever side is inconsistent; do not change the agreed key without confirming both sides

### REQ-BUG-06: TXN ID collision (same-second transactions)
- Current format: `TXN-{YYYYMMDDHHMMSS}` — collides if two transactions happen within the same second
- Fix: append a short UUID suffix (or microseconds) to guarantee uniqueness
- Affected locations: `backend/api/api_server.py:1122` and `:1447`

### REQ-BUG-07: WriteQueue infinite retry loop
- Cap retries at **3 attempts** before dropping the item permanently
- On drop: **log error only** — no socket alert, no health check surface
- Consistent with existing error-handling pattern in `resilience.py`

### REQ-BUG-08: active_sessions dict never expires
- Fix: **in-memory TTL only** — no Redis, no SQLite (PythonAnywhere single-worker WSGI, no multi-worker concern)
- TTL: **8-hour absolute** from login time (not sliding window)
- Expired token response: **401 Unauthorized** with message "Session expired, please log in again"

### REQ-SEC-06: Hardcoded FINANCE_PASSWORD default
- `FINANCE_PASSWORD` defaults to `finance2025` in both `admin_dashboard.py` and `web_app.py`
- Add a startup guard (same pattern as `FLASK_SECRET_KEY`): refuse to start if env var is not set or equals the known default
- Affected lines: `admin_dashboard.py:383`, `admin_dashboard.py:3293`, `web_app.py:355`, `web_app.py:2857`

### REQ-QUAL-01: Dead JWT code — migrate students to JWT
- **Do not just remove** `generate_jwt_token()` — migrate students from opaque tokens to JWT
- Reuse the existing JWT implementation already used for cashier auth
- Keep `active_sessions` dict as TTL enforcement layer; store JWT inside it instead of opaque token
- Android API response format unchanged (token still returned in login response body)

### REQ-QUAL-02: Dashboard code duplication
- Extract shared logic into **`dashboard_core.py`** in `backend/dashboard/`
- `admin_dashboard.py` (local/Arduino hardware mode) and `web_app.py` (PythonAnywhere web mode) remain as separate deployment entry points
- Both import from `dashboard_core.py` and keep only what is unique to their deployment mode
- `wsgi.py` and deployment configuration unchanged

### REQ-CURR-01: Wrong currency symbol in FCM push notifications
- FCM message construction uses ฿ (Thai Baht) instead of ₱ (Philippine Peso)
- Fix in `backend/api/api_server.py` FCM message construction
- Find and replace all occurrences of ฿ in FCM-related strings

### Claude's Discretion
- Exact UUID/microsecond format for TXN ID suffix (either is acceptable)
- How to structure `dashboard_core.py` internally (module layout, import style)
- Exact startup guard error message wording for FINANCE_PASSWORD

</decisions>

<specifics>
## Specific Ideas

- `active_sessions` TTL is 8 hours absolute — same session length as a typical school day; no need to refresh
- JWT migration for students reuses cashier's existing JWT path — no new JWT logic needed, just wire students through the same flow
- `dashboard_core.py` extraction should reduce both files from ~3000 lines to a small entry-point shim plus shared core

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generate_jwt_token()` at `api_server.py:155`: Already implemented but dead — wire student login through this instead of opaque token generation
- `active_sessions` dict at `api_server.py:143`: Kept as TTL layer; extend it to store JWT and expiry timestamp
- `WriteQueue` class at `resilience.py:126`: Add retry counter and drop logic here; `_write_queue` singleton at `resilience.py:277`

### Established Patterns
- `FLASK_SECRET_KEY` startup guard: Use same pattern for `FINANCE_PASSWORD` guard
- Cashier JWT auth: Reference implementation for student JWT migration
- Existing `resilience.py` error logging: Use same logger/format for WriteQueue drop logs

### Integration Points
- `dashboard.html:768` and `:709` — both handle `card_error` socket event; one path reads `data.message`, one reads `data.error` — planner must confirm which is canonical
- `api_server.py:1122` and `:1447` — both TXN ID generation sites; both need the same suffix fix
- `wsgi.py` — must remain untouched; imports from `web_app.py` which will delegate to `dashboard_core.py`

</code_context>

<deferred>
## Deferred Ideas

- Redis-backed sessions for multi-worker scaling — explicitly deferred; in-memory TTL is sufficient for PythonAnywhere single-worker
- Splitting `dashboard_core.py` into further sub-modules — planner's discretion if the file is still too large after extraction
- Any P2/P3 bugs found during audit — log separately, do not fix in this phase

</deferred>

---

*Phase: 31-dashboard-backend-p1-fixes*
*Context gathered: 2026-03-10*
