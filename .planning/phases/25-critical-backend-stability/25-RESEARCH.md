# Phase 25: Critical Backend Stability - Research

**Researched:** 2026-03-09
**Domain:** Python/Flask backend — concurrency safety, CORS security, error isolation, caching
**Confidence:** HIGH (all findings from direct source code inspection)

---

## Summary

Phase 25 targets four specific, already-located bugs in the BankongSeton Flask backend. All four issues were confirmed by reading the source code directly — this is not speculative research. The work is surgical: no new dependencies are needed, no architecture changes are required, and every fix is self-contained within 1–3 functions.

The most dangerous issue is the race condition in `nfc_pay()` and `process_cashier_transaction()`: both functions read a balance, compute a new value, and write it back — three separate Google Sheets API calls with no locking. On PythonAnywhere's single-worker WSGI, a `threading.Lock()` per card-ID is sufficient to eliminate double-spend. The CORS wildcard (`*`) in `wsgi.py` is a security misconfiguration with a misleading comment that must be replaced with a real origin allowlist. The email crash is a missing `try/except` around a code block that executes *after* the transaction has already been committed to Sheets. The cache module (`cache.py`) is fully implemented and production-ready but is never imported by `api_server.py`.

**Primary recommendation:** Fix all four issues in sequence — locks first (highest risk), then CORS (security), then email guard (correctness), then cache wiring (performance). Each fix is independent and can be committed separately.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-SEC-01 | CORS in production `wsgi.py` restricted to configured origins; `*` wildcard removed | Wildcard confirmed at `wsgi.py` line 36; `get_cors_origins()` in `api_server.py` already handles env-var-based origin list |
| REQ-BUG-01 | Balance debit uses atomic read-modify-write; two concurrent requests to same card result in exactly one deduction | Race confirmed in `nfc_pay()` lines 1031–1061 and `process_cashier_transaction()` lines 1323–1366; per-card `threading.Lock()` is the fix |
| REQ-BUG-04 | Email failure during already-committed cashier transaction caught silently; transaction returns 200 | Unguarded email block confirmed at `process_cashier_transaction()` lines 1431–1456; wrapping in `try/except Exception` is the fix |
| REQ-PERF-01 | `TTLCache` imported and active in `api_server.py`; repeated calls within TTL period skip Google Sheets | `cache.py` is fully implemented (line 206: `_global_cache`); `api_server.py` has zero imports of it; wire-up is the fix |
</phase_requirements>

---

## Standard Stack

### Core (already in use — no new dependencies needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `threading` | stdlib | Per-card mutex for read-modify-write atomicity | Built-in, no install; correct for single-WSGI-worker PythonAnywhere |
| `flask` | existing | HTTP layer | Already in use |
| `gspread` | existing | Google Sheets API client | Already in use |

### No New Libraries Required
All four fixes use only Python stdlib (`threading`, `try/except`) or internal modules already present (`cache.py`). Do not introduce `redis`, `celery`, `filelock`, or any external locking primitive — they are unnecessary for single-worker WSGI.

---

## Architecture Patterns

### Pattern 1: Per-Card Threading Lock (REQ-BUG-01)

**What:** A module-level dict maps card IDs to `threading.Lock()` instances. A separate `threading.Lock()` protects the dict itself. The debit code acquires the card's lock before reading balance and releases it after writing.

**When to use:** Any read-modify-write on shared mutable state in a threaded single-process environment.

```python
# Source: direct code analysis of api_server.py + Python stdlib docs
import threading

_card_locks: dict = {}
_card_locks_lock = threading.Lock()

def _get_card_lock(card_id: str) -> threading.Lock:
    with _card_locks_lock:
        if card_id not in _card_locks:
            _card_locks[card_id] = threading.Lock()
        return _card_locks[card_id]

# Inside nfc_pay() and process_cashier_transaction():
card_lock = _get_card_lock(card_id)
with card_lock:
    # READ balance
    # CHECK balance >= total
    # WRITE new balance
```

**Why per-card and not global:** A global lock would serialize ALL payment requests. Per-card locks only serialize requests for the *same* card, allowing parallel payments on different cards.

### Pattern 2: Silent Email Guard (REQ-BUG-04)

**What:** Wrap the entire post-commit email block in `try/except Exception` with a `logger.warning()` (no re-raise). The transaction `return jsonify(...)` is outside and after the guard.

```python
# Source: direct code analysis of api_server.py lines 1430–1456
# BEFORE (dangerous):
if student_id:
    # ... email logic ...
    email_service.send_receipt(...)   # raises → 500 despite committed txn
return jsonify({"success": True, ...})

# AFTER (correct):
try:
    if student_id:
        # ... email logic ...
        email_service.send_receipt(...)
except Exception as e:
    logger.warning(f"Email notification failed (transaction committed): {e}")
return jsonify({"success": True, ...})
```

### Pattern 3: Cache Wire-Up (REQ-PERF-01)

**What:** Import the already-implemented `cache.py` helpers into `api_server.py`. Wrap `users_sheet.get_all_records()` calls with `get_cached()` / `set_cached()`. Invalidate on any write that modifies users (report_lost_card, nfc_register).

```python
# Source: direct code analysis of cache.py
from cache import get_cached, set_cached, invalidate_cached

# READ path (e.g., login, get_profile, get_balance):
USERS_CACHE_KEY = "users_all"
USERS_TTL = 30  # seconds

user_records = get_cached(USERS_CACHE_KEY)
if user_records is None:
    users_sheet = get_worksheet_with_retry("Users")
    user_records = users_sheet.get_all_records()
    set_cached(USERS_CACHE_KEY, user_records, ttl=USERS_TTL)

# WRITE path (report_lost_card, nfc_register):
# ... perform write ...
invalidate_cached(USERS_CACHE_KEY)
```

**`cache.py` public API (confirmed from source):**
- `get_cached(key: str) -> Any | None`
- `set_cached(key: str, value: Any, ttl: float = None) -> None`
- `invalidate_cached(key: str) -> None`
- `get_cache_stats() -> dict`
- Class: `TTLCache(default_ttl=30, max_size=200)` — thread-safe with `RLock`

### Pattern 4: CORS Origin Restriction (REQ-SEC-01)

**What:** Replace `os.environ.setdefault('CORS_ORIGINS', '*')` in `wsgi.py` with a real production origin. The `get_cors_origins()` function in `api_server.py` already reads from this env var correctly.

```python
# Source: wsgi.py line 36 (current — BAD):
os.environ.setdefault('CORS_ORIGINS', '*')

# Fix (GOOD):
os.environ.setdefault('CORS_ORIGINS', 'https://juley2823.pythonanywhere.com')
```

**Important:** The comment near line 36 says "Android HTTP clients don't send Origin headers, so `*` is safe here." This comment is **misleading** — Android clients not sending Origin headers means CORS *doesn't apply* to them, not that wildcard is required. The comment should be removed or corrected. The `get_cors_origins()` function already handles the "no Origin header" case correctly via Flask-CORS behavior.

### Anti-Patterns to Avoid

- **Global lock for all payments:** Eliminates parallelism. Use per-card locks.
- **Removing the email code entirely:** REQ-BUG-04 says catch silently, not delete. Keep the email attempt.
- **Importing `TTLCache` class directly and creating a new instance:** `cache.py` already exposes `get_cached`/`set_cached`/`invalidate_cached` as module-level convenience functions backed by the singleton `_global_cache`. Use those, not `TTLCache()`.
- **Caching the whole Sheet object:** Cache the *result* of `get_all_records()` (a list of dicts), not the worksheet handle itself.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Thread-safe TTL cache | Custom dict + expiry logic | `cache.py` (already exists) | Already implemented, tested, thread-safe with RLock |
| Per-resource locking | Complex semaphore scheme | `threading.Lock()` dict | Stdlib, correct, minimal |
| CORS origin parsing | Custom header inspection | `get_cors_origins()` already in `api_server.py` | Already handles dev/prod split |

---

## Common Pitfalls

### Pitfall 1: Acquiring Lock Too Late (REQ-BUG-01)
**What goes wrong:** Lock acquired after `get_all_records()` — race still possible between two threads that both read before either writes.
**Why it happens:** Instinct to lock only the write, not the read-check-write sequence.
**How to avoid:** Lock must encompass the READ, the CHECK, and the WRITE as one atomic block.
**Warning signs:** Lock is acquired after any `get_all_records()` or `get_all_values()` call inside the debit path.

### Pitfall 2: Forgetting to Invalidate Cache on Write (REQ-PERF-01)
**What goes wrong:** `report_lost_card` marks a card as lost in Sheets, but cache still returns the old (active) record for up to 30s — card appears valid when it should be blocked.
**Why it happens:** Cache added to read paths but write paths not audited.
**How to avoid:** Any endpoint that writes to the Users sheet MUST call `invalidate_cached("users_all")`. Affected endpoints: `report_lost_card`, `nfc_register` (adds new user row).
**Warning signs:** After `report_lost_card`, a subsequent `nfc_pay` within 30s succeeds.

### Pitfall 3: Re-raising Email Exception (REQ-BUG-04)
**What goes wrong:** `except Exception as e: raise` or `except Exception as e: return error_response(e)` — transaction still returns 500.
**How to avoid:** `except` block must only log; no re-raise, no error response. The `return jsonify({"success": True, ...})` must execute unconditionally after the guard.

### Pitfall 4: Setting CORS to Empty String (REQ-SEC-01)
**What goes wrong:** `os.environ.setdefault('CORS_ORIGINS', '')` — `get_cors_origins()` returns empty list → Flask-CORS blocks all cross-origin requests, breaking the app.
**How to avoid:** Set to actual production domain: `'https://juley2823.pythonanywhere.com'`

### Pitfall 5: Lock Object Not Module-Level (REQ-BUG-01)
**What goes wrong:** Lock created inside the function on each call — new lock object every request, no mutual exclusion.
**How to avoid:** `_card_locks` dict and `_card_locks_lock` must be module-level globals, initialized once at import time.

---

## Code Examples

### Exact Race Condition Location 1 — `nfc_pay()` (lines 1031–1061)
```python
# Source: api_server.py direct inspection
# Current (BROKEN — no lock):
money_records = money_sheet.get_all_records()        # READ
for r in money_records:
    if str(r.get("CardID")) == str(card_id):
        current_balance = float(r.get("Balance", 0)) # READ
        new_balance = round(current_balance - total, 2)
        money_sheet.update_cell(balance_row_idx, balance_col_idx, new_balance)  # WRITE
        break
```

### Exact Race Condition Location 2 — `process_cashier_transaction()` (lines 1323–1366)
```python
# Source: api_server.py direct inspection
# Current (BROKEN — no lock, hardcoded col C):
money_records = money_sheet.get_all_records()        # READ
for i, record in enumerate(money_records):
    if str(record.get("CardID")) == str(card_id):
        current_balance = float(record.get("Balance", 0))  # READ
        new_balance = current_balance - total
        money_sheet.update(f"C{account_row}", [[new_balance]])  # WRITE (col C hardcoded)
        break
```

Note: The hardcoded `C` column is REQ-BUG-09 scope (Phase 33). Do NOT change it in Phase 25.

### Exact Email Block — `process_cashier_transaction()` (lines 1431–1456)
```python
# Source: api_server.py direct inspection
# Current (BROKEN — outside try/except, after commit):
        # ... transaction committed to sheets above ...

    if student_id:
        users_sheet = get_worksheet_with_retry("Users")
        user_records = users_sheet.get_all_records()
        for user in user_records:
            if user.get("StudentID") == student_id:
                email = user.get("Email", "")
                if email:
                    from email_service import email_service
                    email_service.send_receipt(...)   # ← unguarded crash point
                break

return jsonify({"success": True, ...})
```

### `cache.py` Module Interface (lines 195–240 approx.)
```python
# Source: cache.py direct inspection
# Module-level singleton already created:
_global_cache = TTLCache(default_ttl=30, max_size=200)

def get_cached(key: str) -> Any:
    return _global_cache.get(key)

def set_cached(key: str, value: Any, ttl: float = None) -> None:
    _global_cache.set(key, value, ttl=ttl)

def invalidate_cached(key: str) -> None:
    _global_cache.invalidate(key)
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| Global lock for all payments | Per-card lock dict | Parallel payments on different cards remain fast |
| WSGI-level env var `*` | Env var set to specific origin(s) | Eliminates reflected-origin attacks, XSS escalation |
| Uncaught email after commit | Silent catch + log | Transaction always returns 200 on success |
| Uncached Sheets reads | TTLCache 30s | Reduces Google Sheets API quota consumption |

---

## Open Questions

1. **Which endpoints write to Users sheet?**
   - What we know: `report_lost_card` and `nfc_register` confirmed as writers.
   - What's unclear: Are there other endpoints that modify user records?
   - Recommendation: Grep `api_server.py` for `users_sheet.update` / `users_sheet.append` during planning wave 0 to confirm the full list before adding cache invalidation.

2. **Does `email_service` import lazily (inside the function) by design?**
   - What we know: `from email_service import email_service` appears inside the `if student_id:` block at line ~1448, not at the top of the file.
   - What's unclear: Is this intentional (circular import avoidance, optional dependency)?
   - Recommendation: Leave the lazy import in place. The fix is only to wrap the block in `try/except`, not to restructure imports.

3. **Production domain for CORS allowlist**
   - What we know: `https://juley2823.pythonanywhere.com` appears in project URLs in STATE.md.
   - What's unclear: Are there additional legitimate origins (staging, mobile deep-link scheme)?
   - Recommendation: Set to `https://juley2823.pythonanywhere.com` as the default. Document that `CORS_ORIGINS` env var can be overridden in PythonAnywhere's environment variables panel for future additions.

---

## Validation Architecture

> Nyquist validation setting not confirmed — including minimal manual verification steps.

### Phase Requirements → Verification Map

| ID | Behavior to Verify | Method |
|----|-------------------|--------|
| REQ-SEC-01 | `wsgi.py` no longer contains `'*'` as CORS value | Code inspection: `grep -n "CORS_ORIGINS" backend/api/wsgi.py` |
| REQ-BUG-01 | Lock dict exists at module level; lock acquired before `get_all_records()` in both debit paths | Code inspection of both functions |
| REQ-BUG-04 | Email block wrapped in `try/except`; `return jsonify({"success": True})` is outside/after the guard | Code inspection of `process_cashier_transaction` |
| REQ-PERF-01 | `api_server.py` imports `get_cached`, `set_cached`, `invalidate_cached`; `users_all` key used in read paths; invalidated in write paths | Code inspection + `grep -n "get_cached\|set_cached\|invalidate_cached" backend/api/api_server.py` |

---

## Sources

### Primary (HIGH confidence — direct source code inspection)
- `backend/api/api_server.py` — 1544 lines, full read; all bug locations confirmed with line numbers
- `backend/api/wsgi.py` — CORS wildcard confirmed line 36
- `backend/cache.py` — TTLCache implementation confirmed; module-level convenience functions confirmed
- `.planning/REQUIREMENTS.md` — REQ-SEC-01, REQ-BUG-01, REQ-BUG-04, REQ-PERF-01 exact text
- `.planning/STATE.md` — project context, PythonAnywhere single-worker WSGI confirmed
- `.planning/ROADMAP.md` — Phase 25 scope and success criteria

### No External Sources Required
All research findings come from direct code inspection. No library documentation, no web search needed — the fixes use Python stdlib (`threading`) and an internal module (`cache.py`) that is already fully implemented.

---

## Metadata

**Confidence breakdown:**
- Bug locations: HIGH — confirmed by reading source with line numbers
- Fix patterns: HIGH — standard Python threading, try/except, direct cache wire-up
- Side effects / invalidation scope: MEDIUM — `report_lost_card` and `nfc_register` confirmed; other Users writers need grep verification
- CORS production domain: MEDIUM — derived from STATE.md; should be confirmed against actual PythonAnywhere config

**Research date:** 2026-03-09
**Valid until:** 2026-04-09 (source code is stable; only invalidated if api_server.py is significantly refactored)
