# Phase 8: Security + Reliability Fixes - Research

**Researched:** 2026-03-01
**Domain:** Python/Flask backend security hardening and resilience patterns
**Confidence:** HIGH

## Summary

Phase 8 is a narrow, surgical patch of three existing backend files. All three changes follow patterns already established in the codebase — no new libraries, no new concepts, and no architectural decisions remain open. The work is copy-and-adapt rather than design-and-build.

The JWT_SECRET startup guard in `api_server.py` is a direct port of the FLASK_SECRET_KEY guard in `admin_dashboard.py:58-63`. The WebSocket exception text leak fix is a find-and-replace of 4 specific lines in `admin_dashboard.py` (1239, 1296, 1409, 1872). The `ensure_products_sheet()` introduction to `cashier_routes.py` replicates the same function verbatim from `admin_dashboard.py:146-156` and `web_app.py:158-167`, with the only tricky part being providing `get_worksheet_with_retry` and a module-level `db` reference inside the locally-defined copy.

**Primary recommendation:** Copy existing patterns verbatim; the research reduces to confirming exact line numbers, scope of `db`/`get_worksheet_with_retry` availability in `cashier_routes.py`, and the exact `exc_info=True` status of the 4 log lines being changed.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**JWT Startup Guard (api_server.py)**
- Hard fail: call `sys.exit(1)` if `JWT_SECRET` env var is empty or missing
- Block empty/missing only — no list of known weak defaults to check
- Placement: module-level, before Flask app initialization (same pattern as admin_dashboard.py's FLASK_SECRET_KEY guard)
- Error message: mirror admin_dashboard.py's existing critical log message format, substituting `JWT_SECRET` for `FLASK_SECRET_KEY`

**WebSocket Exception Text Leak (admin_dashboard.py)**
- Replace all 4 `socketio.emit('card_error', {'message': str(e)})` with the same generic message everywhere: `"Card scan failed — please try again"`
- The 4 locations: lines 1239, 1296, 1409, 1872 in admin_dashboard.py
- Full exception must still be logged server-side with `exc_info=True` (most locations already have logger.error — ensure exc_info=True is present)

**ensure_products_sheet Placement (cashier_routes.py)**
- Define `ensure_products_sheet()` locally in cashier_routes.py — same pattern as admin_dashboard.py and web_app.py (each defines its own copy)
- Implementation must match admin_dashboard.py exactly: calls `get_worksheet_with_retry('Products')`, falls back to `add_worksheet` with correct headers if `WorksheetNotFound`
- Only fix line 176 (the `db.worksheet('Products')` call) — the success criteria is Products-only; leave other worksheet calls (Users, Money Accounts, Transactions Log, Settings) untouched

### Claude's Discretion
- Exact placement of the guard block relative to imports vs. config constants in api_server.py
- Whether to add a helper comment above the guard block
- Exact logger event= key names for the new JWT guard log messages

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SEC-02 | FLASK_SECRET_KEY is required non-empty (system refuses to start with default key) | Extended to cover JWT_SECRET in api_server.py using the existing guard pattern at admin_dashboard.py:58-63 |
| QUAL-01 | All 60+ debug print() statements replaced with structured logging (get_logger()) | Not a focus of this phase — this phase addresses WebSocket info-leak and resilience, not print→logger migration. Phase 8 scope is the 3 targeted fixes. QUAL-01 is listed in REQUIREMENTS.md as Pending/Phase 8 but the CONTEXT.md and phase description scope it to the 3 specific fixes only. |
| PROD-04 | Cashier POS displays all active products in a grid with name and price | Enabled by ensure_products_sheet() — /cashier/api/products no longer 503s when Products sheet is missing; it auto-creates the sheet instead |
| PROD-05 | Products are stored in Google Sheets (a dedicated Products sheet) | ensure_products_sheet() auto-creates the Products sheet with canonical headers ['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded'] if it does not exist |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`os`, `sys`) | stdlib | Env var reading, process exit | Already used throughout codebase |
| `gspread` | installed | Google Sheets worksheet operations | Already the DB layer |
| `flask-socketio` | installed | WebSocket emit | Already the real-time layer |
| `logging` / `get_logger()` | installed | Structured server-side logging | Already used project-wide |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `gspread.exceptions.WorksheetNotFound` | installed | Detect missing worksheet | In `ensure_products_sheet()` fallback |

**Installation:** No new dependencies required.

---

## Architecture Patterns

### Pattern 1: Module-Level Startup Guard

**What:** Read env var at module import time; log critical and `sys.exit(1)` if value is empty or missing.

**When to use:** Any secret required for the service to be secure; failure must be loud and immediate.

**Existing example (admin_dashboard.py:58-63):**
```python
# --- FLASK_SECRET_KEY startup guard (SEC-02) ---
_secret_key = os.getenv('FLASK_SECRET_KEY', '').strip()
_INSECURE_DEFAULT = 'bangko-admin-secret-key-change-in-production'
if not _secret_key or _secret_key == _INSECURE_DEFAULT:
    logger.critical("event=startup_aborted reason=insecure_secret_key message=\"...\"")
    sys.exit(1)
```

**Adaptation for api_server.py:**
- `JWT_SECRET` is currently set at `api_server.py:37`: `JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))`
- The guard replaces (or wraps) this line: strip the fallback default; test for empty string; call `logger.critical` then `sys.exit(1)`
- Placement: immediately after `load_dotenv()` at line 34, before `app = Flask(__name__)` at line 48
- The guard **replaces** the existing assignment; `JWT_SECRET` becomes the stripped env var value (no random fallback)
- The `_INSECURE_DEFAULT` check from admin_dashboard.py does not apply — CONTEXT.md specifies "Block empty/missing only"

**Concrete placement window:**
```
line 34: load_dotenv()
line 36: # JWT Configuration
line 37: JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))  ← REPLACE THIS
line 38: JWT_ALGORITHM = 'HS256'
```

Replacement:
```python
# --- JWT_SECRET startup guard ---
JWT_SECRET = os.getenv('JWT_SECRET', '').strip()
if not JWT_SECRET:
    logger.critical("event=startup_aborted reason=missing_jwt_secret message=\"JWT_SECRET is not set. Set a strong random key in your .env file. Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\"")
    sys.exit(1)
```

### Pattern 2: Generic WebSocket Error — Exception Logged, Not Emitted

**What:** Catch-all `except Exception as e` blocks that previously emitted `str(e)` to the client now emit a fixed user-facing string; the exception object goes only to the server log with `exc_info=True`.

**When to use:** Any `socketio.emit` in an exception handler where the message content comes from `str(e)`.

**Existing safe usage (admin_dashboard.py:1213, 1222):**
```python
socketio.emit('card_error', {'message': 'Card scan failed -- please try again', 'requires_ack': True})
```

Note: The CONTEXT.md message uses an em dash (`—`) while lines 1213/1222 use a double-hyphen (`--`). The CONTEXT.md decision text says `"Card scan failed — please try again"`. Use the em dash form to match the decision; the 4 lines being changed are new writes, not copies of 1213/1222.

**The 4 locations to fix (verified by grep):**

| Line | Handler | Current code | Fix needed |
|------|---------|-------------|------------|
| 1237-1239 | `read_card_loop` top-level loop | `logger.error("event=card_read_error error=%s", e)` then `socketio.emit('card_error', {'message': str(e)})` | Add `exc_info=True` to logger.error; replace message |
| 1293-1296 | `handle_id_card` except | `logger.error("event=id_card_check_error error=%s", e, exc_info=True)` then `socketio.emit(...)` | exc_info=True already present; replace message only |
| 1406-1409 | `handle_money_card` except | `logger.error("event=money_card_link_error error=%s", e, exc_info=True)` then `socketio.emit(...)` | exc_info=True already present; replace message only |
| 1869-1872 | `handle_replace_card` except | `logger.error("event=replace_card_error error=%s", e, exc_info=True)` then `socketio.emit(...)` | exc_info=True already present; replace message only |

**Confirmed:** Lines 1296, 1409, 1872 already have `exc_info=True`. Line 1239's logger.error at line 1238 does **not** have `exc_info=True` — it must be added.

### Pattern 3: Local ensure_products_sheet() Copy

**What:** Each module that needs the Products sheet defines its own `ensure_products_sheet()` that calls `get_worksheet_with_retry('Products')` and falls back to `add_worksheet` + header write on `WorksheetNotFound`. No shared utility module.

**When to use:** Consistent with the local-copy pattern confirmed in both admin_dashboard.py and web_app.py.

**Canonical implementation (identical in admin_dashboard.py:146-156 and web_app.py:158-167):**
```python
def ensure_products_sheet():
    """Get Products worksheet, creating it with correct headers if missing."""
    global db
    try:
        return get_worksheet_with_retry('Products')
    except gspread.exceptions.WorksheetNotFound:
        sheet = db.add_worksheet(title='Products', rows=100, cols=7)
        sheet.update('A1:G1', [['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']])
        logger.info("event=products_sheet_created message=Products sheet did not exist, created with headers")
        return sheet
```

**Key dependency verification for cashier_routes.py:**

`ensure_products_sheet()` requires two things in scope:
1. `get_worksheet_with_retry` — **NOT currently imported or defined in cashier_routes.py**. Must be defined locally or imported from parent module.
2. `db` (global) — **NOT a module-level global in cashier_routes.py**. The module uses `_get_parent_app_module().get_sheets_client()` inline within each route handler.

**Resolution:** cashier_routes.py must also define a local `get_worksheet_with_retry()` that wraps the parent module's `get_sheets_client()`. The cleanest approach consistent with the existing pattern is:

```python
def get_worksheet_with_retry(sheet_name, retries=2):
    """Get worksheet with retry logic — delegates to parent app's sheets client."""
    parent = _get_parent_app_module()
    db = parent.get_sheets_client()
    for attempt in range(retries + 1):
        try:
            return db.worksheet(sheet_name)
        except Exception as e:
            if attempt < retries:
                logger.warning("event=worksheet_retry attempt=%d retries=%d sheet=%s", attempt + 1, retries, sheet_name)
                import time as _time; _time.sleep(2)
                db = parent.get_sheets_client()
            else:
                raise e

def ensure_products_sheet():
    """Get Products worksheet, creating it with correct headers if missing."""
    try:
        return get_worksheet_with_retry('Products')
    except gspread.exceptions.WorksheetNotFound:
        db = _get_parent_app_module().get_sheets_client()
        sheet = db.add_worksheet(title='Products', rows=100, cols=7)
        sheet.update('A1:G1', [['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']])
        logger.info("event=products_sheet_created message=Products sheet did not exist, created with headers")
        return sheet
```

Note: the `global db` pattern from admin_dashboard.py/web_app.py doesn't apply directly in cashier_routes.py because `db` is not a module-level global there. The `get_worksheet_with_retry` helper must obtain `db` from the parent app module on each call. The `ensure_products_sheet` fallback also needs `db` — it can call `_get_parent_app_module().get_sheets_client()` directly (one fresh client call is acceptable on a fallback path).

**Then line 176 replacement:**
```python
# Before:
products_sheet = db.worksheet('Products')

# After:
products_sheet = ensure_products_sheet()
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Worksheet not-found fallback | Custom exception hierarchy | `gspread.exceptions.WorksheetNotFound` | Already the correct exception type; used in both admin_dashboard and web_app |
| Startup secrets validation | Env file parser / validator | `os.getenv()` + `sys.exit(1)` | Simplest correct pattern; already established in codebase |
| Generic error messages | Error code registry | Hardcoded string constant | 4 locations, same string; no abstraction needed |

---

## Common Pitfalls

### Pitfall 1: JWT_SECRET Random Fallback Left In Place
**What goes wrong:** Line 37 `JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))` generates a new random secret on every process start if the env var is unset. This breaks JWT verification across restarts and silently bypasses the security guard.
**Why it happens:** The original code was designed to "just work" without configuration.
**How to avoid:** The guard completely replaces the existing assignment — do not keep the `secrets.token_urlsafe(32)` fallback.
**Warning signs:** Tests pass even without JWT_SECRET set in env.

### Pitfall 2: exc_info=True Missing on Line 1238
**What goes wrong:** Line 1238 `logger.error("event=card_read_error error=%s", e)` does not have `exc_info=True`. If only the emit line (1239) is changed and the logger is not fixed, the full traceback is lost.
**Why it happens:** The other 3 locations already had `exc_info=True`; line 1238 was written without it.
**How to avoid:** When replacing line 1239's emit, also add `exc_info=True` to line 1238's logger call.
**Warning signs:** Grep for the pattern `logger.error.*card_read_error` without `exc_info=True`.

### Pitfall 3: ensure_products_sheet Uses global db That Doesn't Exist in cashier_routes
**What goes wrong:** Directly copying `global db` from admin_dashboard.py into cashier_routes.py will fail at runtime — there is no module-level `db` in cashier_routes.py.
**Why it happens:** admin_dashboard.py has `db = get_sheets_client()` at module level (line 130); cashier_routes.py obtains the client inside each route handler via `_get_parent_app_module().get_sheets_client()`.
**How to avoid:** Do not use `global db` in the cashier_routes versions of these helpers. Call `_get_parent_app_module().get_sheets_client()` inline.
**Warning signs:** `NameError: name 'db' is not defined` at runtime.

### Pitfall 4: Fixing Wrong Card_Error Lines
**What goes wrong:** `admin_dashboard.py` has many `socketio.emit('card_error', ...)` lines. Only 4 need changing (the `str(e)` ones at 1239, 1296, 1409, 1872). Other lines emit specific user-facing messages (duplicate card, no student ID, etc.) and must NOT be genericised.
**Why it happens:** There are 46 total `card_error` emits across the codebase; without anchoring to exact line numbers, wrong lines get changed.
**How to avoid:** Use exact line numbers from CONTEXT.md as anchors. The identifying pattern is `{'message': str(e)}` specifically.
**Warning signs:** Non-exception card_error messages (e.g., "This card is already registered...") become generic.

### Pitfall 5: Fixing card_error in web_app.py or arduino_bridge.py
**What goes wrong:** `web_app.py` and `arduino_bridge.py` also contain `str(e)` card_error emits (web_app.py:1252, 1365, 1807; arduino_bridge.py:95). These are **not** in scope for this phase.
**Why it happens:** grep results show many matches across files.
**How to avoid:** Changes are scoped to `admin_dashboard.py` only (4 specific lines).
**Warning signs:** Accidentally editing web_app.py or arduino_bridge.py.

---

## Code Examples

### SEC-02: JWT_SECRET guard (replaces api_server.py:36-37)
```python
# Source: mirrors admin_dashboard.py:58-63 pattern
# --- JWT_SECRET startup guard ---
JWT_SECRET = os.getenv('JWT_SECRET', '').strip()
if not JWT_SECRET:
    logger.critical(
        "event=startup_aborted reason=missing_jwt_secret "
        "message=\"JWT_SECRET is not set or is empty. Set a strong random key in your .env file. "
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\""
    )
    sys.exit(1)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24
```

### QUAL-01 / SEC pattern: Safe WebSocket emit (admin_dashboard.py line 1237-1239)
```python
# BEFORE:
        except Exception as e:
            logger.error("event=card_read_error error=%s", e)
            socketio.emit('card_error', {'message': str(e)})

# AFTER:
        except Exception as e:
            logger.error("event=card_read_error error=%s", e, exc_info=True)
            socketio.emit('card_error', {'message': 'Card scan failed \u2014 please try again'})
```

```python
# BEFORE (lines 1293-1296, 1406-1409, 1869-1872 — exc_info already present):
    except Exception as e:
        logger.error("event=..._error error=%s", e, exc_info=True)
        send_error("Error")
        socketio.emit('card_error', {'message': str(e)})

# AFTER:
    except Exception as e:
        logger.error("event=..._error error=%s", e, exc_info=True)
        send_error("Error")
        socketio.emit('card_error', {'message': 'Card scan failed \u2014 please try again'})
```

### PROD-04/05: ensure_products_sheet in cashier_routes.py
```python
# Define after _get_parent_app_module()

def get_worksheet_with_retry(sheet_name, retries=2):
    """Get worksheet with retry logic for the cashier blueprint."""
    import time as _time
    parent = _get_parent_app_module()
    _db = parent.get_sheets_client()
    for attempt in range(retries + 1):
        try:
            return _db.worksheet(sheet_name)
        except Exception as e:
            if attempt < retries:
                logger.warning("event=worksheet_retry attempt=%d retries=%d sheet=%s", attempt + 1, retries, sheet_name)
                _time.sleep(2)
                _db = parent.get_sheets_client()
            else:
                raise e

def ensure_products_sheet():
    """Get Products worksheet, creating it with correct headers if missing."""
    try:
        return get_worksheet_with_retry('Products')
    except gspread.exceptions.WorksheetNotFound:
        _db = _get_parent_app_module().get_sheets_client()
        sheet = _db.add_worksheet(title='Products', rows=100, cols=7)
        sheet.update('A1:G1', [['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']])
        logger.info("event=products_sheet_created message=Products sheet did not exist, created with headers")
        return sheet
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))` | Guard + hard fail | This phase | Server refuses to start insecurely |
| `socketio.emit('card_error', {'message': str(e)})` | Generic message, full traceback server-only | This phase | Exception details no longer leak to clients |
| `db.worksheet('Products')` in cashier_routes.py | `ensure_products_sheet()` | This phase | 503 becomes 200 + auto-create when sheet missing |

---

## Open Questions

1. **em dash vs double-hyphen in generic message**
   - What we know: CONTEXT.md specifies `"Card scan failed — please try again"` (em dash). Existing lines 1213/1222 use `--` (double-hyphen). The 4 lines being changed are exception paths, not copied from 1213/1222.
   - What's unclear: Whether to standardize all `card_error` messages to use the same punctuation.
   - Recommendation: Use the em dash as specified in CONTEXT.md for the 4 new lines. Do not alter 1213/1222 (out of scope).

2. **QUAL-01 scope ambiguity**
   - What we know: REQUIREMENTS.md maps QUAL-01 (print→logger migration) to Phase 8. But the phase description and CONTEXT.md describe only 3 targeted security/reliability fixes with no mention of print migration.
   - What's unclear: Whether the planner should include print→logger work or treat QUAL-01 as handled by prior phases.
   - Recommendation: The CONTEXT.md (user decisions document) takes precedence. Phase 8 scope is the 3 targeted fixes. QUAL-01's listing in REQUIREMENTS.md appears to be a stale mapping — Phase 2 (02-04) already addressed print→logger migration. The planner should note this mismatch but not add print-migration work to Phase 8 plans.

---

## Validation Architecture

> `workflow.nyquist_validation` is not present in `.planning/config.json` — skip this section.

*(nyquist_validation key absent from config.json; Validation Architecture section omitted.)*

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `admin_dashboard.py:58-63` — FLASK_SECRET_KEY guard pattern (verbatim copy target)
- Direct code inspection: `admin_dashboard.py:146-156` — ensure_products_sheet implementation
- Direct code inspection: `web_app.py:158-167` — second ensure_products_sheet copy (confirms convention)
- Direct code inspection: `api_server.py:34-48` — current JWT_SECRET assignment and Flask init ordering
- Direct code inspection: `cashier_routes.py:1-50, 169-192` — current db access pattern and products endpoint
- grep: `socketio.emit('card_error'` in admin_dashboard.py — confirmed 4 `str(e)` locations at lines 1239, 1296, 1409, 1872

### Secondary (MEDIUM confidence)
- `gspread.exceptions.WorksheetNotFound` — verified as the correct exception class already used in the codebase (admin_dashboard.py:151, web_app.py:163)

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; everything is already in the codebase
- Architecture: HIGH — all patterns are copies of existing verified code
- Pitfalls: HIGH — identified directly from code inspection (not from speculation)

**Research date:** 2026-03-01
**Valid until:** 2026-04-01 (stable Python/Flask patterns)
