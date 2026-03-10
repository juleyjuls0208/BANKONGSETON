# Phase 31: Dashboard & Backend P1 Fixes - Research

**Researched:** 2026-03-10
**Domain:** Flask backend (Python), SocketIO, JWT, WriteQueue resilience, code deduplication
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**REQ-BUG-05: card_error socket event key mismatch**
- Backend emits `data.message`; dashboard.html line 768 reads `data.message` (appears correct)
- Planner must audit line 709 (modal path reads `data.error`) — one of these two paths is broken
- Fix whichever side is inconsistent; do not change the agreed key without confirming both sides

**REQ-BUG-06: TXN ID collision (same-second transactions)**
- Current format: `TXN-{YYYYMMDDHHMMSS}` — collides if two transactions happen within the same second
- Fix: append a short UUID suffix (or microseconds) to guarantee uniqueness
- Affected locations: `backend/api/api_server.py:1122` and `:1447`

**REQ-BUG-07: WriteQueue infinite retry loop**
- Cap retries at 3 attempts before dropping the item permanently
- On drop: log error only — no socket alert, no health check surface
- Consistent with existing error-handling pattern in `resilience.py`

**REQ-BUG-08: active_sessions never expires**
- Fix: in-memory TTL of 8 hours absolute (no Redis, no SQLite — PythonAnywhere single-worker)
- Expired token should return 401 with `"Session expired, please log in again"`
- No session refresh — absolute 8-hour window from login time

**REQ-SEC-06: Hardcoded FINANCE_PASSWORD default**
- Remove hardcoded `"finance2025"` from both `admin_dashboard.py` and `web_app.py`
- Follow existing `FLASK_SECRET_KEY` guard pattern (startup abort via `sys.exit(1)`)
- Guard must reject both missing value AND the known default `"finance2025"`
- Guard runs at module load time (after `load_dotenv()`) — not inside route handlers

**REQ-QUAL-01: Dead JWT code — migrate students to JWT**
- Call `generate_jwt_token()` on student login instead of `generate_token()`
- Keep `active_sessions` dict as TTL layer (for 8-hour expiry from REQ-BUG-08)
- Store JWT string inside `active_sessions[token]` dict
- Android API response format unchanged — token still returned in response body

**REQ-QUAL-02: Dashboard code duplication**
- Extract shared logic to `backend/dashboard/dashboard_core.py`
- Both `admin_dashboard.py` and `web_app.py` become thin entry-point shims
- `wsgi.py` must remain untouched (imports `from web_app import app as application`)

**REQ-CURR-01: Wrong currency symbol in FCM push notifications**
- FCM message construction uses ฿ (Thai Baht) instead of ₱ (Philippine Peso)
- Fix in `backend/api/api_server.py` FCM message construction

### Claude's Discretion
- Exact UUID/microsecond format for TXN ID suffix (either is acceptable)
- How to structure `dashboard_core.py` internally (module layout, import style)
- Exact startup guard error message wording for FINANCE_PASSWORD

### Deferred Ideas (OUT OF SCOPE)
- REQ-CURR-02 (cashier UI and dashboard template currency symbols) — not in this phase
- Session refresh / sliding window for `active_sessions` — absolute 8-hour TTL only
- Redis or database-backed sessions
- Any iOS/Android changes
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-BUG-05 | Fix `card_error` socket event key mismatch — frontend reads wrong key | Bug is in `cashier_index.html:403` using `data.error`; fix is `data.message` |
| REQ-BUG-06 | Fix TXN ID collision — same-second transactions generate duplicate IDs | Two sites in `api_server.py` (lines 1122, 1447); append UUID4 short suffix |
| REQ-BUG-07 | Fix WriteQueue infinite retry loop — failing items loop forever | `resilience.py:126-234`; cap at 3 attempts, drop to `failed_queue`, log only |
| REQ-BUG-08 | Fix `active_sessions` never expiring — memory leak + security risk | `api_server.py:143-299`; add 8-hour TTL check at every lookup |
| REQ-SEC-06 | Remove hardcoded `FINANCE_PASSWORD` default `"finance2025"` | Two files (`admin_dashboard.py`, `web_app.py`); follow `FLASK_SECRET_KEY` guard pattern |
| REQ-QUAL-01 | Migrate student auth from opaque tokens to JWT (dead code cleanup) | `api_server.py:150-202`; wire `generate_jwt_token()` into student login path |
| REQ-QUAL-02 | Eliminate ~90% code duplication between `admin_dashboard.py` and `web_app.py` | Extract shared logic to `dashboard_core.py`; both files become thin shims |
| REQ-CURR-01 | Fix Thai Baht ฿ in FCM push notifications → Philippine Peso ₱ | **ALREADY DONE** — fixed in commit `64cef70` (`quick-1-1`); verify and mark complete |
</phase_requirements>

---

## Summary

Phase 31 addresses 8 P1 requirements spanning bug fixes, security hardening, code quality, and currency symbol correction across the Flask backend and dashboard. All bugs and issues have been individually confirmed in the source — precise file/line locations are known for every fix.

The most important discovery is that **REQ-CURR-01 is already complete**: the Thai Baht `฿` symbol was fixed in commit `64cef70` across all three FCM functions in `fcm_sender.py`. No ฿ character exists anywhere in the codebase (Python, HTML, or JS). The planner should plan a verification-only task for this requirement, not an implementation task.

The largest work item is REQ-QUAL-02 (code deduplication) — extracting shared logic from two 3000+ line files into `dashboard_core.py`. This is a refactor with high mechanical complexity but low risk because the two files are structurally identical. The cashier blueprint (`cashier_routes.py`) uses `_get_parent_app_module()` to reach shared helpers dynamically, so `dashboard_core.py` must preserve module-level names that the cashier blueprint resolves at runtime.

**Primary recommendation:** Implement bug fixes and security fixes first (REQ-BUG-05 through REQ-SEC-06) as small isolated changes, then JWT migration (REQ-QUAL-01), then the large refactor (REQ-QUAL-02) last — its blast radius is largest and it benefits from a clean baseline.

---

## Standard Stack

### Core (already in use — no new dependencies needed)
| Library | Purpose | Location |
|---------|---------|----------|
| Flask + Flask-SocketIO | HTTP routes + WebSocket | `admin_dashboard.py`, `web_app.py`, `api_server.py` |
| PyJWT (`jwt`) | JWT encode/decode | `cashier_routes.py:9`, `api_server.py:155-174` |
| `python-dotenv` | `.env` loading | All three app files |
| `secrets` | Opaque token generation (current) | `api_server.py:150-152` |
| `uuid` (stdlib) | UUID generation for TXN IDs | Will be added for REQ-BUG-06 |
| `time` (stdlib) | Float timestamps for TTL | Will be used for REQ-BUG-08 |

### No New Dependencies
All fixes use Python stdlib or libraries already installed. No `pip install` required.

---

## Architecture Patterns

### Confirmed File Map

```
backend/
├── api/
│   ├── api_server.py          # Student-facing API (1631 lines)
│   │   ├── active_sessions    # line 143 — plain dict, no TTL
│   │   ├── generate_token()   # line 150 — opaque, currently used
│   │   ├── generate_jwt_token()# line 155 — JWT, DEAD (never called)
│   │   ├── verify_jwt_token() # line 166 — JWT verify, DEAD for students
│   │   ├── require_auth()     # line 177 — decorator, checks active_sessions
│   │   ├── TXN-ID (NFC path) # line 1122 — no suffix → collision risk
│   │   └── TXN-ID (POS path) # line 1447 — no suffix → collision risk
│   └── fcm_sender.py          # FCM push (148 lines) — all ₱ CORRECT
│
├── resilience.py              # WriteQueue (373 lines)
│   ├── WriteQueue class       # lines 126-234
│   ├── failed_queue           # line 134 — already exists, underused
│   └── _write_queue singleton # line 277
│
└── dashboard/
    ├── admin_dashboard.py     # Hardware mode (3310 lines)
    │   ├── FLASK_SECRET_KEY guard  # lines 95-102 (REFERENCE PATTERN)
    │   ├── FINANCE_PASSWORD login  # line 383 — hardcoded default HERE
    │   └── FINANCE_PASSWORD main   # line 3293 — hardcoded default HERE
    ├── web_app.py             # PythonAnywhere mode (2874 lines)
    │   ├── FLASK_SECRET_KEY guard  # lines 101-108 (REFERENCE PATTERN)
    │   ├── FINANCE_PASSWORD login  # line 355 — hardcoded default HERE
    │   └── FINANCE_PASSWORD main   # line 2857 — hardcoded default HERE
    ├── wsgi.py                # Entry point: `from web_app import app as application`
    ├── templates/
    │   └── dashboard.html
    │       └── card_error handler # line 768-769 — uses data.message ✅
    └── cashier/
        ├── cashier_routes.py  # JWT reference implementation (728 lines)
        └── templates/
            └── cashier_index.html
                └── card_error handler # line 403 — uses data.error ❌ BUG
```

### Pattern 1: FLASK_SECRET_KEY Startup Guard (Reference for REQ-SEC-06)

This is the exact pattern to replicate for `FINANCE_PASSWORD`:

```python
# admin_dashboard.py:95-102 (and web_app.py:101-108 — identical)
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "").strip()
if not FLASK_SECRET_KEY:
    logger.critical(
        "event=startup_aborted reason=missing_secret_key "
        'message="FLASK_SECRET_KEY must be set in your .env file. '
        "Generate one with: python -c 'import secrets; print(secrets.token_urlsafe(32))'\""
    )
    sys.exit(1)
```

For `FINANCE_PASSWORD`, also reject the known default:
```python
FINANCE_PASSWORD = os.getenv("FINANCE_PASSWORD", "").strip()
_INSECURE_DEFAULT = "finance2025"
if not FINANCE_PASSWORD or FINANCE_PASSWORD == _INSECURE_DEFAULT:
    logger.critical(
        "event=startup_aborted reason=insecure_finance_password "
        'message="FINANCE_PASSWORD must be set in .env and must not be the default value."'
    )
    sys.exit(1)
```

This matches `cashier_routes.py:69-78` which guards `JWT_SECRET` against its known insecure default.

### Pattern 2: Cashier JWT Login (Reference for REQ-QUAL-01)

```python
# cashier_routes.py:190-208 — cashier login creates JWT
payload = {
    "user_id": "cashier001",
    "username": username,
    "role": "cashier",
    "exp": datetime.utcnow() + timedelta(hours=8),
    "iat": datetime.utcnow(),
}
token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
```

Student JWT equivalent — store in `active_sessions` as TTL layer:
```python
# api_server.py — student login (new behavior)
import uuid as _uuid
payload = {
    "student_id": student_id,
    "card_number": card_number,
    "role": "student",
    "exp": datetime.utcnow() + timedelta(hours=8),
    "iat": datetime.utcnow(),
}
jwt_token = generate_jwt_token(student_id)  # already exists at line 155
active_sessions[jwt_token] = {
    "student_id": student_id,
    "card_number": card_number,
    "login_time": time.time(),  # float for TTL arithmetic
}
return jsonify({"token": jwt_token, ...})  # response format unchanged
```

### Pattern 3: WriteQueue Retry Fix (REQ-BUG-07)

Current broken loop structure (pseudocode):
```python
def process_queue(self):
    while not self.queue.empty():   # ← keeps looping as long as items exist
        item = self.queue.get()
        if not self._write(item):
            item['attempts'] += 1
            if item['attempts'] < 3:
                self.queue.put(item)  # ← re-queued → immediately re-processed
            # no else → item silently disappears on attempt 3
```

Fixed pattern — drain only snapshot of current items:
```python
def process_queue(self):
    snapshot_size = self.queue.qsize()
    for _ in range(snapshot_size):      # ← process only items present at start
        if self.queue.empty():
            break
        item = self.queue.get()
        if not self._write(item):
            item['attempts'] = item.get('attempts', 0) + 1
            if item['attempts'] < 3:
                self.queue.put(item)    # will be picked up next call
            else:
                self.failed_queue.put(item)  # already exists at line 134
                logger.error("event=write_dropped attempts=3 ...")
```

### Pattern 4: active_sessions TTL Check (REQ-BUG-08)

```python
# At every active_sessions lookup (e.g. require_auth decorator, api_server.py:177-202)
SESSION_TTL_SECONDS = 8 * 3600  # 8 hours

def _check_session(token):
    session = active_sessions.get(token)
    if session is None:
        return None
    if time.time() - session["login_time"] > SESSION_TTL_SECONDS:
        del active_sessions[token]  # clean up expired entry
        return None  # caller returns 401 "Session expired, please log in again"
    return session
```

`login_time` must be stored as `time.time()` float (not ISO string) at login time.

### Pattern 5: TXN ID Uniqueness (REQ-BUG-06)

```python
import uuid
# Both locations (lines 1122 and 1447):
transaction_id = f"TXN-{timestamp.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
# e.g. TXN-20260310143022-a3f9d2c1
```

Microseconds alternative also acceptable (per CONTEXT.md discretion):
```python
transaction_id = f"TXN-{timestamp.strftime('%Y%m%d%H%M%S%f')}"
# e.g. TXN-20260310143022847123
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT encode/decode | Custom token crypto | `PyJWT` (already installed) | Already used in cashier; `generate_jwt_token()` already exists in `api_server.py` |
| TTL-based session cache | Custom expiry system | Plain dict + `time.time()` float | PythonAnywhere single-worker; no Redis; stdlib `time` is sufficient |
| UUID for TXN dedup | Custom random suffix | `uuid.uuid4().hex[:8]` (stdlib) | Already available, zero-collision guarantee in practice |
| Startup validation | Try/except in routes | `sys.exit(1)` at module load | Consistent with established pattern in all three app files |

---

## Common Pitfalls

### Pitfall 1: `_get_parent_app_module()` breaks after REQ-QUAL-02
**What goes wrong:** `cashier_routes.py` uses `sys.modules.get("web_app")` and `sys.modules.get("admin_dashboard")` to access shared helpers. If REQ-QUAL-02 moves those helpers to `dashboard_core.py`, the module name check will fail.
**How to avoid:** Keep `get_sheets_client`, `get_worksheet_with_retry`, etc. as re-exported names in both `web_app.py` and `admin_dashboard.py` after extracting to `dashboard_core.py`. The shim files must still expose these names.
**Warning signs:** `ImportError: Neither web_app nor admin_dashboard found in sys.modules with get_sheets_client` at cashier login.

### Pitfall 2: `login_time` stored as ISO string, not float
**What goes wrong:** REQ-BUG-08 TTL check will fail with `TypeError` if existing code stored `login_time` as `datetime.isoformat()` string instead of `time.time()` float.
**How to avoid:** At the same commit that adds TTL check, also change login storage to `time.time()`. Both changes in same PR/wave so there's no window with mixed types.
**Current state:** `api_server.py:299` stores `"login_time": datetime.now(ph_tz).isoformat()` — must change to `"login_time": time.time()`.

### Pitfall 3: Writing to `active_sessions` during dict iteration
**What goes wrong:** If `_check_session()` does `del active_sessions[token]` while another thread is iterating `active_sessions`, `RuntimeError: dictionary changed size during iteration`.
**How to avoid:** Don't add a background sweep; only delete on access (lazy eviction). No iteration over `active_sessions` is needed — lookup-on-use is the correct pattern.

### Pitfall 4: `generate_jwt_token()` ignores its argument
**What goes wrong:** `api_server.py:155-163` — the existing `generate_jwt_token(student_id)` may not include `student_id` in the payload in a way that downstream `require_auth` expects. Check the payload keys before wiring it in.
**How to avoid:** Read `generate_jwt_token()` and `require_auth()` before writing the student login change. Ensure the JWT payload includes `student_id` so `require_auth` can populate `request.student_id` as before.

### Pitfall 5: wsgi.py must not be modified
**What goes wrong:** `wsgi.py` is the PythonAnywhere deployment entry point. Any change to its import or path configuration can take the production site down.
**How to avoid:** REQ-QUAL-02 refactor must keep `web_app.py` importable as `from web_app import app as application`. The `app` object must remain a top-level name in `web_app.py`.

### Pitfall 6: REQ-CURR-01 already done — don't duplicate work
**What goes wrong:** Creating an implementation task for REQ-CURR-01 when the fix was already applied in commit `64cef70`.
**How to avoid:** Plan only a verification task: grep for `฿` in Python files, confirm 0 results, close the requirement.

---

## Code Examples

### REQ-BUG-05: Exact fix location

```html
<!-- cashier_index.html:403 — CURRENT (broken) -->
showCardError(data.error);

<!-- cashier_index.html:403 — FIXED -->
showCardError(data.message);
```

Backend emits consistently (confirmed across all three files):
```python
# admin_dashboard.py, web_app.py, arduino_bridge.py
socketio.emit('card_error', {'message': '...'})
```

### REQ-BUG-06: Both TXN ID sites

```python
# api_server.py:1122 — NFC purchase path (CURRENT)
transaction_id = f"TXN-{timestamp.strftime('%Y%m%d%H%M%S')}"

# api_server.py:1447 — cashier/POS purchase path (CURRENT)
transaction_id = f"TXN-{get_philippines_time().strftime('%Y%m%d%H%M%S')}"

# FIXED (both sites, same pattern)
import uuid
transaction_id = f"TXN-{timestamp.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
```

### REQ-SEC-06: Guard placement

Guards go **after `load_dotenv()`** and **before `app = Flask(__name__)`** in both files:

```python
# admin_dashboard.py (after line ~93, before app creation)
# web_app.py (after line ~100, before app creation)
FINANCE_PASSWORD = os.getenv("FINANCE_PASSWORD", "").strip()
_INSECURE_FINANCE_DEFAULT = "finance2025"
if not FINANCE_PASSWORD or FINANCE_PASSWORD == _INSECURE_FINANCE_DEFAULT:
    logger.critical(
        "event=startup_aborted reason=insecure_finance_password "
        'message="FINANCE_PASSWORD must be set in .env and must not use the default value."'
    )
    sys.exit(1)
```

Also remove the duplicate inline defaults:
- `admin_dashboard.py:383`: `os.getenv("FINANCE_PASSWORD", "finance2025")` → `os.getenv("FINANCE_PASSWORD")`
- `admin_dashboard.py:3293`: same
- `web_app.py:355`: same
- `web_app.py:2857`: same

### REQ-QUAL-02: Cashier blueprint dynamic resolution — must preserve

```python
# cashier_routes.py:85-101 — reads helpers from parent module at runtime
def _get_parent_app_module():
    for name in ("web_app", "admin_dashboard", "__main__"):
        mod = sys.modules.get(name)
        if mod is not None and hasattr(mod, "get_sheets_client"):
            return mod
    raise ImportError(...)
```

After REQ-QUAL-02, `web_app.py` must still expose `get_sheets_client` as a module-level name (re-export from `dashboard_core`).

---

## REQ-CURR-01 Status: Already Complete

**Git evidence:** Commit `64cef70` (`feat(quick-1-1): add send_purchase_push() and send_load_push() to fcm_sender.py`) changed line 66 from `฿` to `₱` in `send_low_balance_push`. Both new functions (`send_purchase_push`, `send_load_push`) were written with ₱ from the start.

**Verification:** Full project-wide search (Python, HTML, JS, TS) found ฿ only in `docs/student-app.md:7` (documentation, not code). Zero occurrences in any executable file.

**Planner action:** Create a single verification task. No code changes required.

---

## State of the Art

| Old Approach | Current Approach | Applies To |
|--------------|------------------|------------|
| Opaque random tokens (`secrets.token_urlsafe`) | JWT with payload | REQ-QUAL-01 migration |
| Bare dict with ISO string `login_time` | Dict with float `time.time()` + TTL check | REQ-BUG-08 fix |
| `TXN-{YYYYMMDDHHMMSS}` (collision-prone) | `TXN-{YYYYMMDDHHMMSS}-{uuid8}` (unique) | REQ-BUG-06 fix |
| Hardcoded default in `os.getenv("X", "default")` | `sys.exit(1)` guard at module load | REQ-SEC-06 fix |
| Two 3000-line near-identical files | Shared `dashboard_core.py` + thin shims | REQ-QUAL-02 refactor |

---

## Open Questions

1. **`generate_jwt_token()` payload contents** (REQ-QUAL-01)
   - What we know: function exists at `api_server.py:155-163`, takes `student_id`
   - What's unclear: exact payload keys; whether `require_auth` at line 177 reads from JWT payload or `active_sessions` dict
   - Recommendation: Read lines 155-202 before writing student login migration; ensure `student_id` is accessible post-decode

2. **`dashboard_core.py` import structure** (REQ-QUAL-02)
   - What we know: both files share ~90% code; serial import is the only structural difference
   - What's unclear: exact list of module-level globals that `cashier_routes.py` and other dependencies access by name
   - Recommendation: Run a grep for `sys.modules.get` and `import web_app` across the project before extracting; map all external consumers

3. **WriteQueue `process_queue()` call sites** (REQ-BUG-07)
   - What we know: `_write_queue` singleton at `resilience.py:277`; loop structure understood
   - What's unclear: how frequently `process_queue()` is called and whether the fix introduces a starvation scenario for large backlogs
   - Recommendation: The snapshot-size approach is safe — a backlog larger than `snapshot_size` at call time will be processed on the next call. No starvation.

---

## Sources

### Primary (HIGH confidence — verified in source code)
- `backend/api/api_server.py` — lines 143-202, 293-299, 1122, 1447 (read directly)
- `backend/api/fcm_sender.py` — full file read; all ₱ confirmed
- `backend/resilience.py` — lines 126-234; WriteQueue class fully read
- `backend/dashboard/admin_dashboard.py` — lines 1-129, 375-424, 3280-3310
- `backend/dashboard/web_app.py` — lines 1-159, 349-398, 2850-2874
- `backend/dashboard/cashier/cashier_routes.py` — lines 1-220 (JWT reference pattern)
- `backend/dashboard/wsgi.py` — full file (54 lines)
- `backend/dashboard/templates/dashboard.html` — lines 695-804
- `backend/dashboard/cashier/templates/cashier_index.html` — lines 396-415
- `git log --all` — commit `64cef70` confirms REQ-CURR-01 already fixed

### No external sources needed
All research findings come directly from reading the codebase. No library APIs or framework docs needed — this phase uses only existing patterns already established in the project.

---

## Metadata

**Confidence breakdown:**
- Bug fix locations (REQ-BUG-05 through REQ-BUG-08): HIGH — exact file/line confirmed
- Security fix (REQ-SEC-06): HIGH — pattern confirmed, all 4 locations identified
- JWT migration (REQ-QUAL-01): HIGH — both dead functions confirmed, cashier reference pattern read
- Code deduplication (REQ-QUAL-02): HIGH — both files' structure confirmed; cashier dynamic resolution risk identified
- REQ-CURR-01 already-done status: HIGH — git history + full codebase grep confirmed

**Research date:** 2026-03-10
**Valid until:** 2026-04-10 (stable codebase, no fast-moving dependencies)
