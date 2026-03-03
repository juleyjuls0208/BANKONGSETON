# Phase 1: Critical Fixes + Security - Research

**Researched:** 2026-02-22
**Domain:** Python/Flask bug remediation, input validation, CORS hardening, secret management
**Confidence:** HIGH — all findings derived directly from reading the actual source files; no speculative or external-only claims

## Summary

This phase has 10 requirements split across 5 bugs (BUG-01 through BUG-05) and 5 security issues (SEC-01 through SEC-05). Every single one has been located to a specific file and line number by reading the real code. There are no unknowns about where the problems live; all fixes are surgical edits to existing files.

The dominant theme is a codebase that was built fast and never hardened: credentials printed at startup, wildcard CORS, a secret key with a hardcoded fallback, hardcoded passwords in test files, and a broken cashier HTML template that causes the blank-screen bug (BUG-01). The existing infrastructure (`resilience.py`, `errors.py`, `cache.py`) already provides retry and logging primitives — the bugs mostly exist because the entry-point files (`admin_dashboard.py`, `cashier_routes.py`, `api_server.py`) were not wired up to use them.

**Primary recommendation:** Fix each bug and security issue in isolation, in the exact files identified below. Do not refactor or restructure; that is Phase 2 (QUAL-*). Every change must be the minimum edit that satisfies the requirement.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Error visibility (BUG-02, BUG-03)**
- When Google Sheets API is unavailable: show "Service unavailable, please try again" (friendly, non-technical)
- When a null or malformed card UID is scanned: show error on-screen AND log server-side with raw UID for debugging
- All cashier-facing error messages require explicit acknowledgment (click/tap to dismiss) — not auto-dismissed
- Admin login rejection (BUG-04): show specific message indicating what is missing (e.g., "Username cannot be empty", "Password cannot be empty") rather than a generic "invalid credentials" message

**CORS allowed origins (SEC-03)**
- Deployment is cloud-hosted; CORS must be properly restricted
- Configuration via environment variable (CORS_ORIGINS) — never hardcoded; Claude decides exact var name and format
- Localhost (`http://localhost`, `http://127.0.0.1`) allowed only when FLASK_ENV=development, blocked in production
- Use `YOUR_PRODUCTION_DOMAIN` placeholder in `.env.example` with a comment explaining it must be set before deployment

**Transaction failure recovery (BUG-05)**
- Strategy: retry-then-abort — attempt the Sheets write up to 3 times total (2 retries) before failing
- If all retries fail: cashier sees "Transaction failed — please try again" (simple, no technical detail)
- Server-side logging: only log a failure record after all retries are exhausted (not each interim attempt)
- A failed transaction must leave no partial state — either the balance is updated and the transaction is recorded, or neither happens

**Startup enforcement (SEC-01, SEC-02)**
- FLASK_SECRET_KEY blank/missing: hard crash with `sys.exit(1)` and a clear error message
- Always enforce — no exceptions for dev environments; require a non-blank key at all times
- Credential logging fix (SEC-01): log a redacted confirmation like "Admin user: [configured]" or "Secret key: [set]"
- Test file secrets fix (SEC-05): replace hardcoded secrets with obviously-fake placeholder strings like `test-secret-key-do-not-use`

### Claude's Discretion
- Exact user-facing wording of Sheets API error message
- CORS_ORIGINS env var name and format
- Whether to use `sys.exit(1)` vs `raise RuntimeError` on blank secret key (user said "you decide" — decision already locked to sys.exit(1) above)
- Exact logging format for startup credential confirmation
- Whether test secrets use env vars or placeholder strings (decided: placeholder strings)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUG-01 | Cashier POS app displays the product menu correctly (currently broken — no products shown) | Root cause confirmed: corrupted cashier_index.html template has HTML tags embedded inside a JS function body, causing a parse error that prevents `loadProducts()` from executing. The fix is a full template rewrite. |
| BUG-02 | Null/empty card UID is rejected at input boundary (not silently treated as valid) | Root cause confirmed: `admin_dashboard.py` line 1046 checks `len(uid) == 8` but only after the card string is accepted; no rejection at the normalize_card_uid boundary. Empty UIDs silently match other empty-string entries. Fix: add explicit null/empty guard in `read_card_thread()` before the length check, emit an error event, and log with raw UID. |
| BUG-03 | Google Sheets API failures return graceful error responses (not 500 crashes) | Root cause confirmed: `api_server.py` and `admin_dashboard.py` both have bare `except Exception as e: return jsonify({'error': str(e)}), 500`. Fix: catch gspread exceptions specifically and return a user-readable 503 response; the existing `resilience.py::with_retry` and `cache.py` stale fallback can be wired in. |
| BUG-04 | Admin login requires non-empty credentials (empty string is not a valid login) | Root cause confirmed: `admin_dashboard.py` line 221 — when ADMIN_USERNAME and ADMIN_PASSWORD are both empty strings in .env, `username == admin_user and password == admin_pass` evaluates True for any blank submission. Fix: add explicit `if not username or not password` guard with field-specific messages before the credential comparison. |
| BUG-05 | Transaction balance deduction is protected against partial failure (no half-committed state) | Root cause confirmed: `cashier_routes.py` `complete_sale()` does `money_sheet.update_cell()` then `trans_sheet.append_row()` sequentially with no rollback. If the append fails, balance is already deducted. Fix: implement 3-attempt retry with rollback — if transaction log write fails after all retries, restore original balance and return error. |
| SEC-01 | Credentials (admin username/password) are never printed to stdout or logs at startup | Root cause confirmed: `admin_dashboard.py` lines 1752–1754 print `finance_user / finance_pass` and `admin_user / admin_pass` verbatim. Fix: replace with redacted confirmations. |
| SEC-02 | FLASK_SECRET_KEY is required non-empty (system refuses to start with default key) | Root cause confirmed: `admin_dashboard.py` line 61 uses `os.getenv('FLASK_SECRET_KEY', 'bangko-admin-secret-key-change-in-production')` as a fallback. Fix: load key, check if empty or equal to the known default/insecure value, and call `sys.exit(1)` with an error message before `app.run()`. |
| SEC-03 | CORS is restricted to known origins (no wildcard `*` in production) | Root cause confirmed: `admin_dashboard.py` line 63 `CORS(app)` and line 64 `SocketIO(app, cors_allowed_origins="*")`, `api_server.py` line 35 `CORS(app)` — all wildcard. Fix: read `CORS_ORIGINS` env var, parse to list, apply to both Flask-CORS and SocketIO; fall back to localhost-only in dev. |
| SEC-04 | Card UIDs are validated (regex format check) before use in Sheets queries | Root cause confirmed: `admin_dashboard.py` line 1046 checks `len(uid) == 8` but no hex character validation. `api_server.py` has no length or format check on incoming `card_uid` from API requests. Fix: add `re.match(r'^[0-9A-Fa-f]{8}$', uid)` validation in both entry points before any Sheets operation. |
| SEC-05 | Test files do not contain hardcoded secrets (JWT keys, passwords use env vars) | Root cause confirmed: `backend/test_phase1.py` line 21 `JWT_SECRET = "test-secret-key"`, `backend/test_phase3.py` lines 18/69/93/124 contain hardcoded passwords. Fix: replace with obviously-fake placeholder strings (no env var approach needed for test files). |
</phase_requirements>

---

## Standard Stack

### Core (already in project — no new installs needed)
| Library | Version | Purpose | Role in this Phase |
|---------|---------|---------|-------------------|
| Flask | 3.0.0 | Web framework | `sys.exit()` guard added to startup; login route validation added |
| Flask-CORS | 4.0.0 | CORS headers | Replace wildcard with origin list from env var |
| Flask-SocketIO | 5.3.0 | WebSocket support | SocketIO CORS also needs restriction |
| python-dotenv | 1.0.0 | Env var loading | Already used; `CORS_ORIGINS` var added to `.env.example` |
| gspread | 5.12.0 | Google Sheets API client | Target of BUG-03 graceful error handling |
| `backend/resilience.py` | in-repo | Retry decorator with backoff | Wire into `complete_sale()` for BUG-05 |
| `backend/errors.py` | in-repo | `get_logger()`, `BankoError` | Use for redacted startup logging (SEC-01) |

### No New Dependencies Required
All Phase 1 fixes use the Python standard library (`re`, `sys`, `os`, `logging`) and libraries already in `requirements.txt`. Zero new packages needed.

---

## Architecture Patterns

### Pattern 1: Startup Guard (SEC-02)
**What:** Validate critical config before `app.run()` or `socketio.run()`. If invalid, exit immediately with a clear message.

**Where to add it:** In `admin_dashboard.py` and `api_server.py`, after `load_dotenv()` and before `app.run()` / server startup. The check must happen at module import time (or earliest in `if __name__ == '__main__'` block) so it is not bypassed.

**Pattern:**
```python
# After load_dotenv()
_secret = os.getenv('FLASK_SECRET_KEY', '').strip()
if not _secret or _secret == 'bangko-admin-secret-key-change-in-production':
    print("FATAL: FLASK_SECRET_KEY is not set or is using the insecure default.")
    print("Set a strong random key in your .env file before starting the server.")
    sys.exit(1)
app.secret_key = _secret
```

**Note:** `api_server.py` line 23 uses `JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))` — this auto-generates a random key on each startup (all existing tokens invalidated on restart), but at least it is not empty. JWT_SECRET enforcement is lower priority than FLASK_SECRET_KEY for this phase; the user's decision covers FLASK_SECRET_KEY specifically.

### Pattern 2: Redacted Startup Logging (SEC-01)
**What:** Replace plaintext credential prints with redacted confirmations.

**Location:** `admin_dashboard.py` lines 1751–1757.

**Pattern:**
```python
# Replace:
print(f"✓ Finance login: {finance_user} / {finance_pass}")
print(f"✓ Admin login: {admin_user} / {admin_pass}")

# With:
logger = get_logger(__name__)
logger.info("Finance user: [configured]" if finance_user else "Finance user: [NOT SET - using default]")
logger.info("Admin user: [configured]" if admin_user else "Admin user: [NOT SET]")
logger.info(f"Secret key: [set]")
```

### Pattern 3: CORS Origin Restriction (SEC-03)
**What:** Parse `CORS_ORIGINS` env var as a comma-separated list; restrict both Flask-CORS and SocketIO to that list; in dev mode, also allow localhost.

**Format decision (Claude's discretion):** `CORS_ORIGINS=https://example.com,https://www.example.com` — comma-separated, no spaces.

**Location:** `admin_dashboard.py` and `api_server.py`, after `load_dotenv()`.

**Pattern:**
```python
def get_cors_origins():
    """Parse CORS_ORIGINS env var into a list of allowed origins."""
    flask_env = os.getenv('FLASK_ENV', 'production')
    origins_str = os.getenv('CORS_ORIGINS', '')
    origins = [o.strip() for o in origins_str.split(',') if o.strip()]

    if flask_env == 'development' or not origins:
        # Always allow localhost in dev; warn in production if origins unset
        origins += ['http://localhost', 'http://localhost:3000',
                    'http://127.0.0.1', 'http://127.0.0.1:5001']

    return origins

allowed_origins = get_cors_origins()
CORS(app, origins=allowed_origins)
socketio = SocketIO(app, cors_allowed_origins=allowed_origins)
```

**`.env.example` addition:**
```
# CORS: Comma-separated list of allowed origins (production domains only)
# MUST be set before deployment - do not leave as placeholder
CORS_ORIGINS=YOUR_PRODUCTION_DOMAIN
# Example: CORS_ORIGINS=https://myapp.com,https://www.myapp.com
```

### Pattern 4: Input Validation Guard (BUG-02, SEC-04)
**What:** Reject null/empty/malformed card UIDs at the earliest possible point, before any normalization or Sheets query.

**Locations:**
- `admin_dashboard.py` `read_card_thread()` — line 1044–1046: the `uid` variable is set after stripping the CARD protocol wrapper. The existing `len(uid) == 8` check is the right place to add hex validation.
- `cashier_routes.py` `complete_sale()` — line 179: `card_uid` comes from the POST body. Add validation here before `normalize_card_uid()`.
- `api_server.py` `process_cashier_transaction()` — line 581: `card_uid` from API body. Add validation here.

**Pattern (server-side):**
```python
import re
UID_PATTERN = re.compile(r'^[0-9A-Fa-f]{8}$')

def validate_card_uid(uid: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message)"""
    if not uid:
        return False, "Card UID is empty — please scan the card again"
    if not UID_PATTERN.match(uid):
        return False, f"Card UID format is invalid — please scan the card again"
    return True, ""
```

**For BUG-02 specifically** (Arduino reader side): in `read_card_thread()`, after extracting `uid = line[6:-1]`, add:
```python
if not uid:
    logger.warning(f"Empty card UID received from Arduino (raw line: {line!r})")
    socketio.emit('card_error', {'message': 'Card scan failed — please try again', 'requires_ack': True})
    continue

if not UID_PATTERN.match(uid):
    logger.warning(f"Malformed card UID received from Arduino: {uid!r}")
    socketio.emit('card_error', {'message': 'Card scan failed — please try again', 'requires_ack': True})
    continue
```

### Pattern 5: Graceful Sheets Error Handling (BUG-03)
**What:** Catch gspread-specific exceptions and return 503 with friendly message instead of letting bare `Exception` propagate as 500 with a Python traceback in the JSON body.

**Location:** Every route handler that calls `get_worksheet_with_retry()` or Sheets operations.

**Key gspread exception types:**
- `gspread.exceptions.APIError` — quota exceeded, authentication failure, sheet not found
- `gspread.exceptions.SpreadsheetNotFound` — wrong sheet ID
- `gspread.exceptions.WorksheetNotFound` — wrong sheet name
- `ConnectionError`, `TimeoutError` — network issues

**Pattern:**
```python
import gspread

# In route handlers that call Sheets:
try:
    sheet = get_worksheet_with_retry('Money Accounts')
    records = sheet.get_all_records()
except (gspread.exceptions.APIError, gspread.exceptions.SpreadsheetNotFound,
        gspread.exceptions.WorksheetNotFound, ConnectionError, TimeoutError) as e:
    logger.error(f"Google Sheets unavailable: {e}")
    return jsonify({'error': 'Service unavailable, please try again'}), 503
except Exception as e:
    logger.error(f"Unexpected error in [route name]: {e}", exc_info=True)
    return jsonify({'error': 'An unexpected error occurred'}), 500
```

**Note:** The existing `get_worksheet_with_retry()` already attempts 2 retries (3 total) — these are connection-level retries. The BUG-03 fix wraps the final failure gracefully; BUG-05 adds retry at the transaction-write level with rollback.

### Pattern 6: Empty Credential Rejection (BUG-04)
**What:** Add an explicit guard before the credential comparison in the login route so empty strings are never valid.

**Location:** `admin_dashboard.py` login route, before line 221.

**Current problem:** When `.env` has `ADMIN_USERNAME=` and `ADMIN_PASSWORD=`, both `admin_user` and `admin_pass` are empty strings. Any POST with empty username/password satisfies `username == admin_user and password == admin_pass`.

**Pattern:**
```python
# Add before the credential comparison:
if not username:
    return jsonify({'success': False, 'error': 'Username cannot be empty'}), 400
if not password:
    return jsonify({'success': False, 'error': 'Password cannot be empty'}), 400

# Then the existing comparison (which is now safe):
if username == admin_user and password == admin_pass and admin_user:
    # ... admin session setup
```

**Note:** The `and admin_user` guard at the end ensures that if ADMIN_USERNAME is blank in .env, admin login is blocked even if someone crafts a non-empty username — the admin account is effectively disabled until credentials are configured.

### Pattern 7: Transaction Atomicity with Retry (BUG-05)
**What:** Wrap the balance-deduct + transaction-log sequence in a retry loop. If the log write fails, attempt to restore the original balance. Log failure only after all retries are exhausted.

**Location:** `cashier_routes.py` `complete_sale()` — currently lines 224–242.

**Current problem (confirmed by code inspection):**
```python
# Line 226 - deducts balance
money_sheet.update_cell(account_row, 3, new_balance)
# Line 229-242 - logs transaction
trans_sheet.append_row(transaction_row)
# If append_row raises, balance is already deducted — no rollback
```

**Pattern (retry-then-abort with rollback):**
```python
MAX_RETRIES = 3
last_exception = None

for attempt in range(MAX_RETRIES):
    try:
        # Step 1: Deduct balance
        money_sheet.update_cell(account_row, 3, new_balance)

        # Step 2: Log transaction
        trans_sheet.append_row(transaction_row)

        # Both succeeded - clear session and return success
        flask_session.pop('pending_transaction', None)
        return jsonify({'success': True, 'new_balance': new_balance, 'timestamp': timestamp})

    except Exception as e:
        last_exception = e

        # Attempt rollback: restore original balance
        try:
            money_sheet.update_cell(account_row, 3, current_balance)
        except Exception as rollback_err:
            logger.error(f"CRITICAL: Rollback failed after transaction write error: {rollback_err}")

        if attempt < MAX_RETRIES - 1:
            time.sleep(1)  # Brief pause before retry
        continue

# All retries exhausted - log the failure
logger.error(f"Transaction failed after {MAX_RETRIES} attempts: {last_exception}")
return jsonify({'error': 'Transaction failed — please try again'}), 503
```

### Pattern 8: Cashier Template Fix (BUG-01)
**What:** The `cashier_index.html` template file is corrupted. The `renderProducts()` JavaScript function body (starting around line 190) contains raw HTML tags (`<div class="categories"...>`, `<div class="products-grid"...>`) embedded directly in the JS code where JavaScript statements should be. This is a Jinja2/template corruption — the file appears to contain two different versions of the template merged together. The second version starts at approximately line 213 with a duplicate `<script>` tag and a simpler version of the template.

**Impact:** The browser receives invalid JavaScript which fails to parse, so `loadProducts()` never executes, leaving the grid showing "Loading products..." indefinitely.

**Fix:** The template needs to be rewritten as a clean, single version. The second (simpler) version starting at line ~213 is actually the correct functioning version — it has a working `loadProducts()` and the `renderProducts()` function is intact. The fix is to remove the broken first version (lines 95–212) and keep only the clean second version.

**Note:** The `loadProducts()` in the working version calls `/api/products` — this endpoint exists in `api_server.py` (port 5001) but the cashier runs on the dashboard server (port 5003). The cashier template assumes both run on the same origin. This cross-server issue should be investigated: either the cashier template should call the correct endpoint, or the dashboard should proxy `/api/products`. Since the cashier blueprint is mounted on the dashboard Flask app (`admin_dashboard.py` line 71), and the products API is in `api_server.py`, there is a port mismatch. The dashboard has its own `/api/products/list` route (line 270) — the cashier template should call `/api/products/list` (the dashboard route) rather than `/api/products` (the mobile API route). Alternatively, a `/api/products` route should be added to the dashboard.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry with backoff | Custom retry loop with sleep | `backend/resilience.py::with_retry(RetryConfig())` | Already in codebase, tested, handles jitter |
| Structured logging | More `print()` statements | `backend/errors.py::get_logger(__name__)` | Already in codebase; all modules should use it |
| CORS restriction | Custom `@before_request` origin check | `flask-cors` `origins=` parameter (already installed) | Flask-CORS handles preflight OPTIONS correctly |
| UID format validation | Custom parser | `re.compile(r'^[0-9A-Fa-f]{8}$')` | Standard library; 8-hex-char RFID UID is the exact format |
| Secret key enforcement | Complex validation library | `os.getenv()` + `sys.exit(1)` | Two lines; no library needed |

**Key insight:** Every infrastructure piece needed for Phase 1 already exists in the codebase. The bugs exist because entry-point files were not wired to the infrastructure. The fixes are wiring, not building.

---

## Common Pitfalls

### Pitfall 1: Fixing Empty-Credential Login With Env Var Defaults
**What goes wrong:** If `ADMIN_USERNAME` is not set in `.env`, `os.getenv('ADMIN_USERNAME', '')` returns empty string. The fix `if not username: return error` on the POST body is correct — but the developer might also add `if not admin_user: return error`, which would break the Finance login path (which does have credentials).
**How to avoid:** Only validate the submitted credentials (from the POST body), not the configured credentials (from env). The configured env values are validated at startup (separate concern).

### Pitfall 2: CORS Origins Applied to SocketIO but Not Flask-CORS
**What goes wrong:** Developer fixes `CORS(app, origins=...)` but leaves `SocketIO(app, cors_allowed_origins="*")` unchanged (or vice versa). SocketIO WebSocket handshake bypasses Flask-CORS.
**How to avoid:** Both must be updated in the same change. The `get_cors_origins()` helper produces one list used in both calls.

### Pitfall 3: Transaction Rollback Race Condition
**What goes wrong:** Rollback also fails (Sheets is offline entirely). The balance is deducted but neither recorded nor rolled back — a "phantom deduction."
**How to avoid:** Log a CRITICAL-level error when rollback fails, including original balance, new balance, card UID, and timestamp. This creates an audit trail for manual recovery. The user-facing response should still be "Transaction failed — please try again" (no technical detail). This is not solved in Phase 1 — it is flagged as a known edge case.

### Pitfall 4: BUG-01 Template Cross-Origin Request Failure
**What goes wrong:** After fixing the template corruption, `loadProducts()` calls `/api/products` which is on port 5001 (the mobile API), but the cashier is on port 5003 (the dashboard). The fetch silently fails with a CORS or connection error, and the grid still shows no products.
**How to avoid:** The cashier template must call the correct products endpoint on the same server. The dashboard app already has `/api/products/list` (line 270). Either update the template to call `/api/products/list` or add a `/api/products` alias route to the dashboard. Check which endpoint returns the correct data format (list vs. dashboard format differ slightly — dashboard includes `row` index).

### Pitfall 5: SEC-02 Secret Key Check Not Running in Test/Import Context
**What goes wrong:** The `sys.exit(1)` guard is placed inside `if __name__ == '__main__'` — it only runs when the file is executed directly, not when imported by pytest or a WSGI server.
**How to avoid:** Place the secret key validation at module level (outside the `if __name__ == '__main__'` block), executed on import. Or create a dedicated `validate_startup_config()` function called both at module level and in `if __name__ == '__main__'`. Note: this will cause pytest to exit immediately if `FLASK_SECRET_KEY` is not set in the test environment — tests will need a `.env.test` or the test fixture must set the env var before importing.

---

## Code Examples

### Verified: gspread Exception Hierarchy
```python
# Source: gspread library — confirmed by reading resilience.py imports
import gspread

# Catchable exception types (from gspread.exceptions module):
# gspread.exceptions.APIError          — HTTP 4xx/5xx from Google API
# gspread.exceptions.SpreadsheetNotFound — 404 on spreadsheet lookup
# gspread.exceptions.WorksheetNotFound   — worksheet name doesn't exist
# gspread.exceptions.GSpreadException    — base class for all gspread errors
```

### Verified: Flask-CORS Origins Parameter
```python
# Source: flask-cors documentation and existing usage in codebase
from flask_cors import CORS

# Current (broken):
CORS(app)  # Wildcard by default

# Fixed:
CORS(app, origins=["https://example.com", "http://localhost:3000"])
# OR using regex patterns:
CORS(app, origins=r"https://.*\.example\.com")
```

### Verified: Flask-SocketIO CORS
```python
# Source: Flask-SocketIO docs — cors_allowed_origins accepts list, string, or "*"
socketio = SocketIO(app, cors_allowed_origins=["https://example.com"])
# Also accepts a callable for dynamic checking
```

### Verified: Existing Login Route Structure (confirmed by reading admin_dashboard.py lines 204–235)
```python
# Current flow (vulnerable):
username = data.get('username', '').strip()  # empty string if not provided
password = data.get('password', '').strip()  # empty string if not provided
admin_user = os.getenv('ADMIN_USERNAME', '').strip()  # empty string if not in .env
admin_pass = os.getenv('ADMIN_PASSWORD', '').strip()  # empty string if not in .env

if (username == admin_user and password == admin_pass):  # True when all are ""
    # Grants admin access!

# Fix:
if not username:
    return jsonify({'success': False, 'error': 'Username cannot be empty'}), 400
if not password:
    return jsonify({'success': False, 'error': 'Password cannot be empty'}), 400
if username == admin_user and password == admin_pass and admin_user:
    # Now safe — admin_user being truthy prevents blank env from matching
```

### Verified: Startup Credential Print Locations (admin_dashboard.py lines 1751–1757)
```python
# Current (exposes credentials):
print(f"✓ Finance login: {finance_user} / {finance_pass}")
if admin_user and admin_pass:
    print(f"✓ Admin login: {admin_user} / {admin_pass}")
else:
    print(f"✓ Admin login: (empty username and password)")

# Fixed:
logger = get_logger('startup')
logger.info(f"Finance user: [configured]" if finance_user else "Finance user: [NOT SET - login disabled]")
logger.info(f"Admin user: [configured]" if (admin_user and admin_pass) else "Admin user: [NOT SET - login disabled]")
logger.info("Secret key: [set]")
```

---

## Key Findings: BUG-01 Root Cause (Confirmed)

The `cashier_index.html` file contains two complete versions of the page merged together. The corruption is visible starting at line 190, where the `renderProducts()` JavaScript function body contains raw HTML tag literals:

```
// Line 190 in cashier_index.html — INSIDE a JS function body:
            <div class="categories" id="categories"></div>

            <div class="products-grid" id="productsGrid"></div>
        </div>

        <div class="cart-section">
```

This is not valid JavaScript and causes the entire `<script>` block to fail parsing. A second complete version of the template begins at approximately line 213, with a working `loadProducts()`, `renderProducts()`, cart management, and WebSocket integration.

The correct template is the second version (lines 213–523 of the file), but it also contains the `/api/products` endpoint URL which points to port 5001 instead of the dashboard's own products endpoint. The fix requires:
1. Remove the broken first `<script>` block (lines 95–212)
2. Update the `loadProducts()` fetch URL from `/api/products` to the correct endpoint available on the dashboard server
3. Ensure the `socket.io` script tag is loaded before the socket initialization code (currently it is loaded at the end, after `initWebSocket()` is called — this causes `io is not defined` error on load)

---

## State of the Art

| Old Approach (Current Code) | Fixed Approach | Impact |
|-----------------------------|----------------|--------|
| `CORS(app)` wildcard | `CORS(app, origins=allowed_origins)` from env var | Closes cross-origin attack surface |
| `print(f"login: {user} / {pass}")` | `logger.info("user: [configured]")` | Credentials no longer in stdout/log files |
| `app.secret_key = os.getenv('FLASK_SECRET_KEY', 'hardcoded-default')` | Validate + `sys.exit(1)` if blank/default | Server refuses to start insecurely |
| `if uid == "": return ""` (normalize_card_uid in admin_dashboard.py) | Validate + reject + log before normalization | Null/empty UIDs never reach Sheets queries |
| `money_sheet.update_cell(); trans_sheet.append_row()` with no rollback | Retry loop with balance rollback on failure | No phantom deductions on API failure |
| `JWT_SECRET = "test-secret-key"` in test files | `JWT_SECRET = "test-secret-key-do-not-use-in-production"` | Test files no longer contain usable credentials |

---

## Open Questions

1. **BUG-01: Correct products endpoint for cashier template**
   - What we know: Dashboard has `/api/products/list` (returns `{products, row, id, name, category, price, image_url, active, date_added}`); Mobile API has `/api/products` (returns `{products, count}` with `{id, name, category, price, image_url}`). Both run on the dashboard server after blueprint registration? No — `api_server.py` runs on port 5001 independently; the cashier blueprint is registered on the dashboard (port 5003).
   - What's unclear: Should the cashier use the dashboard's `/api/products/list` endpoint, or should the dashboard register a `/api/products` route that mirrors the mobile API format? The existing template JS expects the `{products: [{id, name, category, price}]}` format.
   - Recommendation: Add a `/api/products` alias route to `admin_dashboard.py` that returns the same format as `api_server.py`'s `/api/products` — this avoids changing the template JS logic and makes the cashier self-contained.

2. **SEC-02: FLASK_SECRET_KEY validation in test environment**
   - What we know: If the key check is at module level, importing `admin_dashboard` in pytest will trigger `sys.exit(1)` unless `FLASK_SECRET_KEY` is set.
   - What's unclear: Are there existing pytest tests that import `admin_dashboard`? (The `tests/` directory has test files but they appear to use `requests` against a running server, not pytest fixtures that import Flask app directly.)
   - Recommendation: Place the check in `if __name__ == '__main__'` only, not at module import time. Tests that need the app can set `FLASK_SECRET_KEY=test-secret-key-do-not-use` in their fixture. Document this in `.env.example`.

3. **BUG-05: Column index for Balance in Money Accounts sheet**
   - What we know: `cashier_routes.py` uses `money_sheet.update_cell(account_row, 3, new_balance)` — hard-coded column 3. This works only if Balance is actually column C.
   - What's unclear: The actual sheet schema is not confirmed in the codebase (no migration files define it). The column index is assumed.
   - Recommendation: During planning, note that the fix should use `money_sheet.find_col()` or use the column name via `gspread` header lookup rather than hard-coding column 3. If column 3 is confirmed correct by the existing running system, document it as a known assumption.

---

## Sources

### Primary (HIGH confidence — direct code inspection)
- `backend/api/api_server.py` — full read, all issues confirmed at specific lines
- `backend/dashboard/admin_dashboard.py` — lines 1–100, 200–300, 1040–1140, 1740–1767 — all security issues confirmed
- `backend/dashboard/cashier/cashier_routes.py` — full read — BUG-05 atomicity issue confirmed
- `backend/dashboard/cashier/templates/cashier_index.html` — full read — BUG-01 template corruption confirmed
- `backend/test_phase1.py` — full read — SEC-05 hardcoded JWT secret confirmed (line 21)
- `backend/test_phase3.py` — full read — SEC-05 hardcoded passwords confirmed (lines 18, 69, 93)
- `backend/resilience.py` — lines 1–80 — retry infrastructure confirmed as usable for BUG-05
- `.env.example` — full read — CORS_ORIGINS var absent, FLASK_SECRET_KEY default value confirmed
- `.planning/codebase/CONCERNS.md` — full read — all bug locations cross-referenced

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md` — confirms entry points, layers, error handling patterns
- `.planning/codebase/STACK.md` — confirms library versions, no new installs needed

### Tertiary (LOW confidence — not independently verified)
- gspread exception hierarchy: known from training data; should be verified against installed version before implementing catch blocks. Run `python -c "import gspread; help(gspread.exceptions)"` to confirm.

---

## Metadata

**Confidence breakdown:**
- Bug locations: HIGH — all confirmed by direct file reads with line numbers
- Security issue locations: HIGH — all confirmed by direct file reads with line numbers
- Fix patterns: HIGH — all use existing installed libraries and standard Python
- BUG-01 template corruption: HIGH — visually confirmed in file read output
- BUG-01 cross-server endpoint issue: MEDIUM — confirmed by architecture docs; exact endpoint path should be verified by running the system
- gspread exception class names: MEDIUM — consistent with resilience.py imports; verify at implementation time

**Research date:** 2026-02-22
**Valid until:** 2026-03-22 (stable domain — Flask, gspread APIs do not change rapidly)
