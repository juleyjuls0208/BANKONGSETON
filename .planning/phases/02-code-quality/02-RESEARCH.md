# Phase 2: Code Quality - Research

**Researched:** 2026-02-26
**Domain:** Python refactoring — structured logging, centralized utilities, thread safety, dead code removal, dependency migration
**Confidence:** HIGH

## Summary

Phase 2 is a pure refactoring phase with no new user-visible functionality. Five requirements address five independent concerns: replace 60+ bare `print()` calls with structured key=value logging (QUAL-01), consolidate two divergent `normalize_card_uid()` implementations into a new `backend/utils.py` (QUAL-02), wrap four unguarded globals in `admin_dashboard.py` with a `threading.Lock`-based class also in `utils.py` (QUAL-03), move dead code (`mobile/BankongSetonApp`, `web_app_complete.py`, other unreachable files found by vulture) to `_archive/` at repo root (QUAL-04), and hard-cut oauth2client to google-auth (QUAL-05).

The critical blocker from STATE.md — "QUAL-05 may require credential file format change" — is **resolved**: the existing `credentials.json` is already a standard service account JSON, which is exactly what `google.oauth2.service_account.Credentials.from_service_account_file()` expects. No credential file changes are needed. Additionally, gspread ≥ 5.x ships a `gspread.service_account(filename=...)` convenience wrapper that handles auth internally, which may be even cleaner than calling `gspread.authorize()` manually.

The `setup_logging()` in `errors.py` currently creates a file handler (writes to `logs/` directory) which contradicts the user decision of console-only output. The function must be updated as part of QUAL-01 to strip the file handler and keep only the `StreamHandler`. All files should call `get_logger(__name__)` (not `logging.getLogger(__name__)` directly) so log records flow through the `'bangko'` logger hierarchy.

**Primary recommendation:** Create `backend/utils.py` first (QUAL-02 + QUAL-03), then update logging infrastructure (QUAL-01), then migrate auth (QUAL-05), then archive dead code (QUAL-04). Order matters: `cashier_routes.py` currently imports `normalize_card_uid` from `admin_dashboard.py` via a dynamic `sys.path.insert`; centralizing to `utils.py` breaks that import path and must be updated simultaneously.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Logging format + output**
- Format: structured key=value per log line (e.g. `level=INFO event=card_read uid=A1B2C3`)
- Log levels: all standard Python levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Output destination: console only (stdout/stderr) — no log files
- What to log: security-sensitive and I/O events — card UID operations, Sheets API calls, auth events, server startup/shutdown, and errors
- All bare print() statements replaced with appropriate logger calls

**Dead code removal scope**
- Full codebase audit using a tool (e.g. vulture) to identify all unreachable/unused code
- Dead code (whole files or folders) is moved to `_archive/` at the repo root, not deleted
- Future-phase placeholder stubs (e.g. NFC-related files) are whitelisted and left in place
- Unused imports and unused local variables inside .py files: Claude's discretion on what to clean up
- BankongSetonApp folder is explicitly included in the removal

**Thread safety design**
- Wrap global state variables in admin_dashboard.py with a simple class using `threading.Lock`
- Expose get/set methods — minimal surface area, no complex accessors
- Class lives in `backend/utils.py` alongside the UID normalization utility
- Scope: cover all card-read-related state paths, not just the known race condition
- Include a concurrency test: fire two concurrent card reads and assert state is consistent

**Dependency migration**
- Hard cutover from oauth2client to google-auth — no compatibility shim
- Replace with the standard Google-recommended stack: `google-auth`, `google-auth-httplib2`, `google-api-python-client`
- Include a smoke test that authenticates with Google Sheets using the new auth to verify migration
- Pin all dependencies with exact versions in requirements.txt (not just migrated ones)

### Claude's Discretion
- Exact decision on which unused imports vs unused local variables to remove inside .py files
- Progress bar or visual indicator choice during any tooling runs (if applicable)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QUAL-01 | All 60+ debug print() statements replaced with structured logging (get_logger()) | setup_logging() in errors.py needs file-handler removal + console-only rewrite; 60 print() in admin_dashboard.py, 5 in api_server.py, 23 in migrate_transactions.py, 3 in cashier_routes.py, 2 each in arduino_bridge.py and notifications.py |
| QUAL-02 | Card UID normalization centralized in a single utility function (backend/utils.py) | Two divergent implementations found: admin version handles None (returns ""), api version does not (crashes on None); merged canonical version with None guard goes to backend/utils.py; cashier_routes.py imports via dynamic sys.path and must be updated |
| QUAL-03 | Global state in admin_dashboard.py wrapped in thread-safe singleton with locking | Four globals: `arduino`, `arduino_bridge`, `card_reading_active`, `pending_student_id`; all accessed in read_card_thread and route handlers; ThreadSafeState class with threading.Lock in backend/utils.py |
| QUAL-04 | Dead code removed (BankongSetonApp folder, unused files) | Confirmed: mobile/BankongSetonApp exists; backend/dashboard/web_app_complete.py is legacy duplicate; vulture at 90% finds 8 unused imports in admin_dashboard.py + wsgi.py; nfc_payments.py is placeholder stub — whitelist |
| QUAL-05 | oauth2client replaced with google-auth library (deprecated dependency) | 4 active files use ServiceAccountCredentials: admin_dashboard.py, api_server.py, config_validator.py, migrate_transactions.py; credentials.json is standard service account JSON — no format change needed; gspread ≥ 5.x supports google-auth natively |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `google-auth` | ≥ 2.0 | Google API authentication | Official Google replacement for deprecated oauth2client |
| `google-auth-httplib2` | ≥ 0.1 | HTTP transport adapter for google-auth | Required by gspread.authorize() when using google-auth manually |
| `gspread` | ≥ 5.12 (already in requirements) | Google Sheets client | Already used; built-in service_account() helper available |
| `vulture` | 2.14 (already installed) | Static dead code detection | Standard Python dead code finder; already present in environment |
| Python `threading.Lock` | stdlib | Mutual exclusion for shared state | No external dependency needed; standard solution for this scope |
| Python `logging` | stdlib | Structured log output | Already imported everywhere; just needs proper formatter |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `google-api-python-client` | ≥ 2.0 | Google API client (user decision requirement) | Required by user decision as part of the "standard Google-recommended stack" even though gspread wraps Sheets access directly |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `gspread.authorize(credentials)` | `gspread.service_account(filename=path)` | service_account() is cleaner (one line) but authorize() is more explicit and familiar; either works |
| `threading.Lock` class | `threading.RLock` | RLock allows re-entrant locking by same thread; not needed here since get/set methods don't call each other |
| vulture CLI | manual audit | vulture is faster but has false positives at 60% confidence; Flask route functions are flagged as "unused" because vulture doesn't trace HTTP routing |

**Installation (for requirements.txt update):**
```bash
pip install google-auth google-auth-httplib2 google-api-python-client
pip freeze > requirements.txt  # then edit to exact versions
```

---

## Architecture Patterns

### Recommended Project Structure Changes

```
backend/
├── utils.py              # NEW: normalize_card_uid() + ThreadSafeState class
├── errors.py             # MODIFY: setup_logging() console-only, key=value format
├── dashboard/
│   ├── admin_dashboard.py    # MODIFY: use ThreadSafeState, update imports, replace print()
│   └── cashier/
│       └── cashier_routes.py # MODIFY: import normalize_card_uid from utils (not admin_dashboard)
├── api/
│   └── api_server.py         # MODIFY: use utils.normalize_card_uid, replace print()
└── config_validator.py       # MODIFY: google-auth auth pattern

_archive/                  # NEW at repo root
├── mobile/BankongSetonApp/   # MOVED from mobile/
└── web_app_complete.py       # MOVED from backend/dashboard/
```

### Pattern 1: Centralized UID Utility (QUAL-02)

**What:** Single `normalize_card_uid()` in `backend/utils.py` that merges both existing versions.
**When to use:** Any file that normalizes card UIDs before comparison or storage.

**Canonical implementation (merges admin + api versions):**
```python
# backend/utils.py
def normalize_card_uid(uid) -> str:
    """Normalize card UID: strip whitespace, remove leading zeros, uppercase."""
    if not uid:
        return ""
    return str(uid).strip().lstrip('0').upper()
```

**Import pattern for cashier_routes.py** (replaces dynamic sys.path):
```python
# At top of cashier_routes.py — replaces the inline import inside route handlers
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from utils import normalize_card_uid
```

Note: `cashier_routes.py` already uses `sys.path.insert` inside route function bodies. Moving to top-level import is cleaner but must be verified to not break the blueprint registration path.

### Pattern 2: Thread-Safe State Class (QUAL-03)

**What:** Minimal class wrapping the four globals with a single `threading.Lock`.
**When to use:** All card-read-related state access paths.

```python
# backend/utils.py
import threading

class CardReaderState:
    """Thread-safe wrapper for Arduino/card-reading global state."""
    
    def __init__(self):
        self._lock = threading.Lock()
        self.arduino = None
        self.arduino_bridge = None
        self.card_reading_active = False
        self.pending_student_id = None
    
    def get(self, key: str):
        with self._lock:
            return getattr(self, key)
    
    def set(self, key: str, value) -> None:
        with self._lock:
            setattr(self, key, value)
    
    def update(self, **kwargs) -> None:
        """Atomic multi-key update."""
        with self._lock:
            for key, value in kwargs.items():
                setattr(self, key, value)

# Singleton instance — replaces globals in admin_dashboard.py
card_reader_state = CardReaderState()
```

**Migration in admin_dashboard.py:**
```python
# BEFORE:
global arduino, card_reading_active
card_reading_active = True
if arduino and arduino.is_open:
    arduino.close()
    arduino = None

# AFTER:
from utils import card_reader_state
card_reader_state.set('card_reading_active', True)
arduino = card_reader_state.get('arduino')
if arduino and arduino.is_open:
    arduino.close()
    card_reader_state.set('arduino', None)
```

### Pattern 3: Console-Only Structured Logging (QUAL-01)

**What:** `setup_logging()` rewritten to emit key=value format to stdout only, no file handler.
**When to use:** Called once at application startup.

**Updated setup_logging() in errors.py:**
```python
def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Configure console-only structured logging."""
    logger = logging.getLogger('bangko')
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    
    handler = logging.StreamHandler()  # stdout only
    handler.setLevel(logging.DEBUG)
    
    # key=value format: level=INFO event=... etc.
    # Use a custom Formatter that outputs key=value pairs
    handler.setFormatter(logging.Formatter(
        fmt='level=%(levelname)s logger=%(name)s %(message)s',
        datefmt=None
    ))
    logger.addHandler(handler)
    return logger
```

**Log call style (key=value):**
```python
logger = get_logger(__name__)

# Card read event
logger.info("event=card_read uid=%s student_id=%s", normalized_uid, student_id)

# Sheets API call
logger.info("event=sheets_query sheet=%s rows=%d", sheet_name, len(rows))

# Auth event
logger.warning("event=auth_failed reason=invalid_credentials")

# Error
logger.error("event=sheets_error code=%s message=%s", error_code, str(e))
```

**All files:** Use `from errors import get_logger` then `logger = get_logger(__name__)` — not `logging.getLogger(__name__)` directly. This ensures records propagate through the `'bangko'` root logger.

### Pattern 4: google-auth Migration (QUAL-05)

**What:** Replace `oauth2client.service_account.ServiceAccountCredentials` with `google.oauth2.service_account.Credentials`.
**Source:** gspread official docs (Context7: /websites/gspread_en_v6_2_1)

**Before (oauth2client):**
```python
from oauth2client.service_account import ServiceAccountCredentials
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
client = gspread.authorize(creds)
```

**After (google-auth) — Option A, explicit:**
```python
from google.oauth2.service_account import Credentials
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
credentials = Credentials.from_service_account_file(credentials_path, scopes=scopes)
gc = gspread.authorize(credentials)
```

**After (google-auth) — Option B, gspread shortcut:**
```python
import gspread
gc = gspread.service_account(filename=credentials_path)
```

Note: Option B uses gspread's own default scopes (spreadsheets + drive). The existing `scope` list in all three files matches these defaults, so Option B is safe and produces the least code change.

**Credential file format:** The existing `credentials.json` is already a standard service account JSON (confirmed: keys include `type`, `project_id`, `private_key_id`, `private_key`, `client_email`). This is the exact same format both oauth2client and google-auth expect. **No credential file changes needed.**

### Anti-Patterns to Avoid

- **Importing normalize_card_uid from admin_dashboard in cashier_routes:** After centralization, the inline `from admin_dashboard import normalize_card_uid` must be removed. If left, behavior diverges silently when one copy is updated.
- **Using `global` keyword after introducing CardReaderState:** The `global arduino, card_reading_active` declarations in route functions must all be removed or they'll shadow the state object.
- **Leaving setup_logging's file handler:** The current `setup_logging()` creates a `logs/` directory and file handler on every call. With console-only output this side effect must be removed; the parameter `log_dir` should be dropped.
- **Vulture false positives on Flask routes:** All `@app.route` and `@socketio.on` decorated functions will be flagged by vulture as "unused functions" at 60% confidence. These are NOT dead code — Flask discovers them via decorators, not direct calls. Only act on 80-90% confidence results or whole-file/whole-folder dead code.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Google Sheets auth | Custom token refresh logic | `google.oauth2.service_account.Credentials` | Handles token expiry, retries, scopes automatically |
| Dead code detection | Manual file-by-file audit | `vulture` (already installed, v2.14) | Traverses AST; finds unused imports, functions, variables |
| Thread locking | Hand-rolled flag variables | `threading.Lock` via context manager | `with self._lock:` is exception-safe; flag variables are not |
| Log formatting | Custom print() wrapper | Python `logging` with `Formatter` | Handles log levels, propagation, handler chaining correctly |

**Key insight:** The `threading.Lock` pattern with `with` statement is the only safe approach — bare flag variables (like the existing `card_reading_active = True; ... card_reading_active = False`) have a TOCTOU race even in CPython due to the GIL not protecting multi-step state transitions.

---

## Common Pitfalls

### Pitfall 1: cashier_routes.py Dynamic Import Path

**What goes wrong:** `cashier_routes.py` imports `normalize_card_uid` and `get_sheets_client` via inline `sys.path.insert` inside route function bodies (lines 150-152, 228-231). When these are centralized to `utils.py`, the old imports silently import the now-stale `admin_dashboard` copy.

**Why it happens:** The file uses late/lazy imports because of circular-dependency risk at module load time.

**How to avoid:** After adding `backend/utils.py`, update `cashier_routes.py`'s inline imports to `from utils import normalize_card_uid`. The `sys.path.insert` for `..` already points at `backend/`, so `utils` is importable once created.

**Warning signs:** Tests pass for admin dashboard but cashier transactions normalize UIDs differently.

### Pitfall 2: setup_logging Called Multiple Times

**What goes wrong:** `setup_logging()` is called in `config_validator.py` and potentially at module level in other files. Multiple calls add duplicate handlers, causing double-printed log lines.

**Why it happens:** `logger.handlers.clear()` guards against this if all callers use the `'bangko'` named logger, but child loggers (`get_logger(__name__)`) propagate to the root — if the root logger also has handlers, entries get printed twice.

**How to avoid:** `setup_logging()` should call `logging.getLogger('bangko').handlers.clear()` before adding handler. Also set `logger.propagate = False` on the 'bangko' logger. One authoritative call site at application startup.

**Warning signs:** Log lines appear twice in console output.

### Pitfall 3: `gspread.authorize()` Scope Format

**What goes wrong:** oauth2client used `scope` as a list of URLs. `google.oauth2.service_account.Credentials.from_service_account_file()` uses the keyword argument `scopes=` (plural, keyword-only). Passing `scope` (without `s`) as positional fails silently or raises a type error.

**Why it happens:** Parameter name difference between the two libraries.

**How to avoid:** Always use `Credentials.from_service_account_file(path, scopes=scope_list)`. If using `gspread.service_account(filename=path)`, no explicit scopes needed.

**Warning signs:** `ValueError: Invalid credentials` or `google.auth.exceptions.TransportError`.

### Pitfall 4: Vulture False Positives on Flask/SocketIO Handlers

**What goes wrong:** vulture flags every `@app.route` and `@socketio.on` decorated function as "unused" at 60% confidence, because route functions are called dynamically by Flask, not by name.

**Why it happens:** vulture does AST analysis, not runtime call graph analysis.

**How to avoid:** Run vulture at `--min-confidence 80` for actionable results. The 8 confirmed unused imports at 90% are real. Don't remove Flask route functions based on vulture output.

**Warning signs:** Deleting route functions based on vulture output causes 404s in production.

### Pitfall 5: Thread Safety Scope — All Paths, Not Just read_card_thread

**What goes wrong:** Wrapping globals only in `read_card_thread` but not in the route handlers (`/connect_serial`, `/disconnect_serial`, `/start_register`, `/link_money_card`) leaves those paths unguarded.

**Why it happens:** The race is subtle: the thread sets `card_reading_active = False` while a route handler is reading it.

**How to avoid:** Use `CardReaderState.get()/set()` in ALL code paths that touch the four globals, including: `read_card_thread`, `connect_serial`, `disconnect_serial`, `start_register`, `link_money_card` and any other handler that references `arduino`.

---

## Code Examples

Verified patterns from official sources:

### google-auth Service Account Auth (Explicit)
```python
# Source: gspread official docs (Context7: /websites/gspread_en_v6_2_1)
from google.oauth2.service_account import Credentials
import gspread

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
credentials = Credentials.from_service_account_file(
    'path/to/credentials.json',
    scopes=scopes
)
gc = gspread.authorize(credentials)
```

### google-auth Service Account Auth (gspread shortcut)
```python
# Source: gspread official docs (Context7: /websites/gspread_en_v6_2_1)
import gspread
gc = gspread.service_account(filename='path/to/credentials.json')
```

### Thread-Safe State Access
```python
# Standard Python threading — stdlib
import threading

class CardReaderState:
    def __init__(self):
        self._lock = threading.Lock()
        self.arduino = None
        self.card_reading_active = False
    
    def get(self, key):
        with self._lock:
            return getattr(self, key)
    
    def set(self, key, value):
        with self._lock:
            setattr(self, key, value)
```

### Concurrency Test Pattern (required by user decision)
```python
# tests/ — two concurrent card reads assert consistent state
import threading
from backend.utils import card_reader_state

def test_concurrent_card_reads_state_consistency():
    results = []
    errors = []
    
    def set_active():
        try:
            card_reader_state.set('card_reading_active', True)
            val = card_reader_state.get('card_reading_active')
            results.append(val)
        except Exception as e:
            errors.append(e)
    
    t1 = threading.Thread(target=set_active)
    t2 = threading.Thread(target=set_active)
    t1.start(); t2.start()
    t1.join(); t2.join()
    
    assert not errors
    assert card_reader_state.get('card_reading_active') is True
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `oauth2client.service_account.ServiceAccountCredentials` | `google.oauth2.service_account.Credentials` | oauth2client deprecated ~2021, EOL 2022 | Drop-in replacement; same credential JSON format |
| `gspread.authorize(oauth2client_creds)` | `gspread.authorize(google_auth_creds)` or `gspread.service_account()` | gspread ≥ 5.0 (2022) | gspread.service_account() is new simpler API |

**Deprecated/outdated:**
- `oauth2client`: EOL, no longer maintained, security patches stopped. Official Google recommendation is `google-auth`.
- `setup_logging(log_dir=...)` file-handler pattern: contradicts user decision; must be removed.

---

## Open Questions

1. **gspread.service_account() vs gspread.authorize()**
   - What we know: Both work with gspread ≥ 5.x and google-auth credentials
   - What's unclear: `service_account()` uses gspread's default scopes (spreadsheets + drive) — identical to the current `scope` list in all files. Planner should pick one pattern and apply consistently.
   - Recommendation: Use `gspread.service_account(filename=path)` as it requires the fewest lines and no explicit import of `google.oauth2`; reserve explicit form for config_validator.py where separate credential validation is needed.

2. **`backend/utils.py` import path for cashier_routes.py**
   - What we know: cashier_routes.py uses `sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))` to reach `backend/` directory — this is the same path where `utils.py` will live.
   - What's unclear: Whether there is a circular import risk if `utils.py` imports from `errors.py` (for logging).
   - Recommendation: `utils.py` should NOT import from `errors.py`; logging in utils should use `logging.getLogger('bangko.utils')` directly to avoid any import cycle.

3. **Exact pinned versions for requirements.txt**
   - What we know: User decision requires all dependencies pinned with exact versions
   - What's unclear: Current environment doesn't have packages installed (no venv active), so `pip freeze` can't be run now
   - Recommendation: Planner task should include a step to install packages in the project venv and capture exact versions via `pip freeze`.

---

## Sources

### Primary (HIGH confidence)
- `/websites/gspread_en_v6_2_1` (Context7) — service account auth with google-auth, gspread.service_account() API
- Direct codebase reads: `backend/errors.py`, `admin_dashboard.py:1-220`, `api_server.py:1-180`, `config_validator.py`, `cashier_routes.py`, `migrate_transactions.py`
- Python stdlib docs: `threading.Lock` — standard library, well-established

### Secondary (MEDIUM confidence)
- Codebase vulture run: `python -m vulture backend/ --min-confidence 80/60` — actual output captured above
- Credential file key inspection: `config/credentials.json` keys confirmed as standard service account format

### Tertiary (LOW confidence)
- None — all claims verified via codebase inspection or official docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified via Context7 gspread official docs + codebase inspection
- Architecture: HIGH — based on direct code reads of all affected files
- Pitfalls: HIGH — identified from actual code patterns in codebase, not hypothetical

**Research date:** 2026-02-26
**Valid until:** 2026-04-26 (stable libraries; gspread and google-auth are mature)
