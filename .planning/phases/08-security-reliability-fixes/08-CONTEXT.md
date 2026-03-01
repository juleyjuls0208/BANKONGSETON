# Phase 8: Security + Reliability Fixes - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Three targeted gap-closure fixes in existing backend files:
1. `api_server.py` — JWT_SECRET startup guard (mirrors the FLASK_SECRET_KEY guard already in admin_dashboard.py)
2. `admin_dashboard.py` — 4 `socketio.emit('card_error', {'message': str(e)})` calls replaced with generic user-facing message; exception logged server-side only
3. `cashier_routes.py` — `db.worksheet('Products')` at line 176 replaced with `ensure_products_sheet()` defined locally

Creating new features, refactoring other worksheet calls, or extracting shared utilities are out of scope.

</domain>

<decisions>
## Implementation Decisions

### JWT Startup Guard (api_server.py)
- Hard fail: call `sys.exit(1)` if `JWT_SECRET` env var is empty or missing
- Block empty/missing only — no list of known weak defaults to check
- Placement: module-level, before Flask app initialization (same pattern as admin_dashboard.py's FLASK_SECRET_KEY guard)
- Error message: mirror admin_dashboard.py's existing critical log message format, substituting `JWT_SECRET` for `FLASK_SECRET_KEY`

### WebSocket Exception Text Leak (admin_dashboard.py)
- Replace all 4 `socketio.emit('card_error', {'message': str(e)})` with the same generic message everywhere: `"Card scan failed — please try again"`
- The 4 locations: lines 1239, 1296, 1409, 1872 in admin_dashboard.py
- Full exception must still be logged server-side with `exc_info=True` (most locations already have logger.error — ensure exc_info=True is present)

### ensure_products_sheet Placement (cashier_routes.py)
- Define `ensure_products_sheet()` locally in cashier_routes.py — same pattern as admin_dashboard.py and web_app.py (each defines its own copy)
- Implementation must match admin_dashboard.py exactly: calls `get_worksheet_with_retry('Products')`, falls back to `add_worksheet` with correct headers if `WorksheetNotFound`
- Only fix line 176 (the `db.worksheet('Products')` call) — the success criteria is Products-only; leave other worksheet calls (Users, Money Accounts, Transactions Log, Settings) untouched

### Claude's Discretion
- Exact placement of the guard block relative to imports vs. config constants in api_server.py
- Whether to add a helper comment above the guard block
- Exact logger event= key names for the new JWT guard log messages

</decisions>

<specifics>
## Specific Ideas

- The JWT guard should feel like a direct copy of the FLASK_SECRET_KEY block from admin_dashboard.py:58-63, not a reimagined version
- The "Card scan failed — please try again" message is already used at admin_dashboard.py:1213 and 1222 for non-exception card errors — reusing it keeps the error surface consistent

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `admin_dashboard.py:58-63`: Existing FLASK_SECRET_KEY startup guard — copy this pattern verbatim for JWT_SECRET in api_server.py
- `admin_dashboard.py:146-156`: `ensure_products_sheet()` definition — copy this into cashier_routes.py (it already calls `get_worksheet_with_retry` which must also be accessible)
- `web_app.py:158`: Second copy of `ensure_products_sheet()` — confirms the local-copy pattern is established convention in this codebase

### Established Patterns
- Startup guards: module-level, `logger.critical(...)` then `sys.exit(1)` — do not use `raise` or `warnings.warn`
- WebSocket errors: `socketio.emit('card_error', {'message': '...'})` — message field is the user-facing string, nothing else
- Logging: structured key=value format (`event=..., error=...`) with `exc_info=True` for unexpected exceptions

### Integration Points
- `api_server.py:37`: Current `JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))` — guard block should come immediately after this line or replace the fallback pattern
- `cashier_routes.py:176`: `products_sheet = db.worksheet('Products')` — single replacement point
- `cashier_routes.py` imports: must have access to `get_worksheet_with_retry` and `db` (global) for the locally-defined `ensure_products_sheet()` to work — verify these are already in scope

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-security-reliability-fixes*
*Context gathered: 2026-03-01*
