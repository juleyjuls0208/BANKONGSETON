# Phase 4: Student App + Notifications - Research

**Researched:** 2026-02-26
**Domain:** Android (Kotlin/Views), Python/Flask backend, Firebase Cloud Messaging
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Balance display & sync**
- Fetch fresh balance from backend on every app open — no background polling, no periodic timer
- While loading: show a spinner over the balance number, then reveal the value
- A manual refresh button (icon) sits near the balance so students can force-update without closing the app
- If the API call fails: show a toast/snackbar ("Couldn't update balance — check your connection"); keep the last known value displayed

**Transaction history UX**
- Flat list, newest transaction first — no date or type grouping
- Visual distinction between transaction types: color-coded amount (red for purchases, green for top-ups) plus an icon per type
- Infinite scroll — load the next batch as student scrolls (not a "Load more" button, not all at once)
- Empty state: friendly illustration with "No transactions yet" message

**Itemized receipt view**
- Tapping a canteen purchase navigates to a dedicated receipt screen (not inline expand, not bottom sheet)
- Per line item: item name, unit price, quantity, line total
- Transaction-level summary on receipt screen: date, time, total paid, balance before and after
- Non-canteen transactions (top-ups, etc.) are NOT tappable — no detail navigation for those rows

**Push notifications**
- Triggered server-side: after every transaction where the resulting balance < threshold, the backend fires an FCM push
- Device token registration: the student app sends its FCM token to the backend on login / first run; backend stores it per student
- Notification message: "Low Balance: Your canteen balance is ฿[amount]. Please top up soon."
- Threshold is a single global value set by the admin in the dashboard settings — no per-student overrides

### Claude's Discretion
- Exact FCM token storage location in Google Sheets (new column on Students sheet, or separate sheet)
- Retry behavior if FCM delivery fails
- Exact dashboard UI placement for the threshold setting field
- App-side token refresh handling (FCM token rotation)
- Loading skeleton or animation details beyond the balance spinner

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APP-01 | Student can see their current card balance on the home screen | `HomeActivity.kt` exists + `GET /api/student/balance` endpoint exists — wire up correctly |
| APP-02 | Student can see a scrollable list of all their transactions (date, amount, type) | `TransactionsActivity.kt` + `GET /api/student/transactions` exist — need infinite scroll + type colors + icons |
| APP-03 | Student can tap a canteen purchase and see an itemized receipt | `TransactionsAdapter` currently inline-expands — must replace with navigation to new `ReceiptActivity` |
| APP-04 | App shows balance update after a transaction is processed | On-open fetch covers this; manual refresh button needed |
| APP-05 | App handles API errors gracefully (shows error message, not crash) | Toast pattern exists in `HomeActivity`; needs snackbar + last-value persistence |
| NOTF-01 | Student receives push notification when balance drops below threshold | `firebase-admin` Python SDK + trigger in cashier transaction route needed |
| NOTF-02 | Admin can configure the low-balance threshold globally from the dashboard | New settings page/section in admin dashboard + env/Sheets persistence |
</phase_requirements>

---

## Summary

Phase 4 is split across three surfaces: the Android app (Kotlin/Views — **not** Compose), the Flask API backend (`backend/api/api_server.py`), and the Flask admin dashboard (`backend/dashboard/admin_dashboard.py`). All three surfaces have substantial scaffolding already in place.

The Android app (`mobile/student_app_v2`) already has all four Activities declared (`HomeActivity`, `TransactionsActivity`, `SettingsActivity`, `FCMService`), Retrofit wired to `GET /api/student/balance` and `GET /api/student/transactions`, and the FCM SDK integrated. The main work is behavioral: infinite scroll, receipt navigation, refresh button, error handling, FCM token registration on login, and notification permission handling.

The backend already has `POST /api/users/fcm-token` declared and `FCMToken` column migration in `migrate_transactions.py`. The critical missing piece is: (1) the `firebase-admin` Python package integration to actually fire FCM pushes server-side, (2) the low-balance check triggered after cashier transactions, and (3) a backend endpoint + admin UI to read/write the global threshold. There is also a **token auth mismatch** to fix: login issues opaque session tokens (stored in `active_sessions`), but `POST /api/users/fcm-token` uses `@require_auth` which expects JWT — it will always return 401 for real app users.

**Primary recommendation:** Fix the auth mismatch first (switch FCM token registration to use `active_sessions` like balance/transactions), then add `firebase-admin` and the low-balance trigger, then wire the Android app changes.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| firebase-admin (Python) | 6.5.0 | Server-side FCM push dispatch | Official Google SDK; `messaging.send()` handles auth, retry, HTTP/2 — no hand-rolling requests |
| RecyclerView + LinearLayoutManager | Already in `build.gradle.kts` (1.3.2) | Infinite-scroll transaction list | Already in project; OnScrollListener pattern is standard |
| EncryptedSharedPreferences | Already in project (1.1.0-alpha06) | Persist last-known balance for offline display | Already in `SecureStorage.kt` — just add `saveLastBalance()` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| firebase-admin (Python) | latest stable | Backend: FCM push | Install via `pip install firebase-admin` |
| requests (Python) | already in env | N/A — use firebase-admin instead | Do NOT use raw HTTP to FCM API |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| firebase-admin Python SDK | Raw HTTP POST to FCM v1 API | Hand-rolling OAuth2 token refresh is error-prone; SDK handles it |
| EncryptedSharedPreferences for last balance | Room/DataStore | Overkill for a single scalar; SecureStorage.kt pattern already established |
| Activity-based receipt navigation | Bottom sheet | User decided: dedicated receipt screen |

**Installation (backend):**
```bash
pip install firebase-admin
```

Add to `requirements-test.txt` or a new `requirements-api.txt`:
```
firebase-admin>=6.0.0
```

---

## Architecture Patterns

### Recommended Project Structure Changes

**Android app — new file:**
```
mobile/student_app_v2/app/src/main/java/com/bankongseton/student/
├── ReceiptActivity.kt          ← NEW: dedicated receipt screen for canteen purchases
├── HomeActivity.kt             ← MODIFY: add refresh icon button, persist last balance
├── TransactionsActivity.kt     ← MODIFY: infinite scroll, type coloring, tap-to-receipt
├── TransactionsAdapter.kt      ← MODIFY: remove inline expand, add click listener for canteen txns
├── Models.kt                   ← MODIFY: add offset/page param for pagination
├── ApiClient.kt                ← MODIFY: add offset param to getTransactions; add FCM token endpoint
├── LoginActivity.kt            ← MODIFY: register FCM token after login
└── FCMService.kt               ← VERIFY: onNewToken saves to shared prefs (already done)
```

**Backend — new/modified files:**
```
backend/
├── api/
│   ├── api_server.py           ← MODIFY: fix FCM token auth; add low-balance check after transaction
│   └── fcm_sender.py           ← NEW: firebase-admin init + send_low_balance_push() helper
├── dashboard/
│   ├── admin_dashboard.py      ← MODIFY: add GET/POST /api/settings/threshold route
│   └── templates/
│       └── dashboard.html      ← MODIFY: add threshold setting UI field
└── migrate_transactions.py     ← VERIFY: FCMToken column migration already present
```

---

### Pattern 1: Firebase Admin SDK Initialization (Python)

**What:** Initialize once at module level (not per-request). Guard against double-init.

**When to use:** `fcm_sender.py` — initialize when the module is imported, not inside the send function.

```python
# Source: Context7 /firebase/firebase-admin-python
import firebase_admin
from firebase_admin import credentials, messaging
import os

_firebase_app = None

def get_firebase_app():
    global _firebase_app
    if _firebase_app is None:
        cred_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'firebase-credentials.json')
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
    return _firebase_app

def send_low_balance_push(fcm_token: str, balance: float) -> bool:
    """Returns True on success, False on failure."""
    try:
        get_firebase_app()
        message = messaging.Message(
            notification=messaging.Notification(
                title="Low Balance",
                body=f"Your canteen balance is ฿{balance:.2f}. Please top up soon."
            ),
            token=fcm_token
        )
        messaging.send(message)
        return True
    except Exception as e:
        logger.error("event=fcm_send_failed error=%s", e)
        return False
```

**Note:** Firebase credentials file (`firebase-credentials.json`) is separate from Google Sheets credentials. It's the service account JSON downloaded from Firebase Console → Project Settings → Service accounts. Store alongside `credentials.json` in `config/`.

---

### Pattern 2: Infinite Scroll in RecyclerView (Android)

**What:** Load 20 items at a time; when user scrolls near the bottom, fetch the next batch.

**When to use:** `TransactionsActivity.kt`

```kotlin
// Standard RecyclerView infinite scroll pattern
recyclerView.addOnScrollListener(object : RecyclerView.OnScrollListener() {
    override fun onScrolled(recyclerView: RecyclerView, dx: Int, dy: Int) {
        val layoutManager = recyclerView.layoutManager as LinearLayoutManager
        val lastVisible = layoutManager.findLastVisibleItemPosition()
        val totalItems = layoutManager.itemCount
        if (!isLoading && !isLastPage && lastVisible >= totalItems - 3) {
            loadMoreTransactions()
        }
    }
})
```

Backend: `GET /api/student/transactions?limit=20&offset=40`

The backend already accepts `limit` via `request.args.get('limit', 50)`. Add `offset` support:
```python
limit = int(request.args.get('limit', 20))
offset = int(request.args.get('offset', 0))
transactions = transactions[offset:offset + limit]
```

---

### Pattern 3: Auth Mismatch Fix — FCM Token Registration

**Problem:** `POST /api/users/fcm-token` uses `@require_auth(roles=['student'])` which decodes a JWT. But `/api/auth/login` returns an opaque `secrets.token_urlsafe(32)` token stored in `active_sessions`. JWT decode of an opaque token always fails → 401.

**Fix:** Add FCM token registration as a session-based route (like balance/transactions), OR switch login to issue JWT tokens.

**Recommended fix (minimal change):** Replace the `@require_auth` decorator on `register_fcm_token` with the same session-check pattern used by `get_balance`:

```python
@app.route('/api/users/fcm-token', methods=['POST'])
def register_fcm_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token not in active_sessions:
        return jsonify({'error': 'Invalid or expired token'}), 401
    session = active_sessions[token]
    student_id = session['student_id']
    # ... rest of FCM token storage logic
```

---

### Pattern 4: Low-Balance Check After Cashier Transaction

**What:** After successfully deducting balance in `process_cashier_transaction`, check if new_balance < threshold and fire FCM if student has a token stored.

**When to use:** In `api_server.py` after `trans_sheet.append_row(transaction_row)`.

```python
# After transaction committed — check low balance
try:
    threshold = float(os.getenv('LOW_BALANCE_THRESHOLD', 50))
    if new_balance < threshold:
        # Look up FCM token for this student
        # student_id already resolved above
        users_sheet = get_worksheet_with_retry('Users')
        user_records = users_sheet.get_all_records()
        for user in user_records:
            if str(user.get('StudentID')) == str(student_id):
                fcm_token = user.get('FCMToken', '').strip()
                if fcm_token:
                    from fcm_sender import send_low_balance_push
                    send_low_balance_push(fcm_token, new_balance)
                break
except Exception as notif_error:
    logger.warning("event=low_balance_notify_failed error=%s", notif_error)
    # Never block the transaction response
```

---

### Pattern 5: Global Threshold Setting — Backend Storage

**What:** Store `LOW_BALANCE_THRESHOLD` as a configurable value the admin can change without redeploying.

**Options and recommendation:**
- **Option A (env var only):** `LOW_BALANCE_THRESHOLD` already in `.env` — admin cannot change at runtime.
- **Option B (Google Sheets "Settings" row):** A new `Settings` sheet or a config row in an existing sheet. Admin POST updates it; backend reads it on each notification check.
- **Option C (in-memory + env fallback):** Store in a module-level variable, expose GET/POST API, reset on restart.

**Recommendation (Claude's Discretion):** Option B — a new `Settings` sheet with one row per config key (`key`, `value`). This survives restarts, is visible to anyone with Sheets access, and is consistent with the project's "Google Sheets as database" decision. The admin dashboard reads and writes via `/api/settings/threshold`.

```
Settings sheet:
| Key                   | Value |
|-----------------------|-------|
| low_balance_threshold | 50    |
```

---

### Pattern 6: Passing Receipt Data to ReceiptActivity

**What:** When a transaction row is tapped, navigate to `ReceiptActivity` with the transaction data.

**Android pattern — pass via Intent extras (serialize to JSON string):**

```kotlin
// In TransactionsAdapter click handler
val gson = Gson()
val txnJson = gson.toJson(transaction)
val intent = Intent(context, ReceiptActivity::class.java)
intent.putExtra("transaction_json", txnJson)
context.startActivity(intent)

// In ReceiptActivity
val txnJson = intent.getStringExtra("transaction_json")
val transaction = Gson().fromJson(txnJson, Transaction::class.java)
```

`Gson` is already a dependency (`com.google.code.gson:gson:2.10.1`).

---

### Anti-Patterns to Avoid

- **Double-initializing Firebase app:** Call `firebase_admin.initialize_app()` only once. Wrap in a guard (`if not firebase_admin._apps`). The pattern above uses a singleton getter.
- **Blocking the transaction response on FCM:** Always fire FCM in a try/except after committing the transaction row. Never let FCM failure roll back or delay the payment response.
- **Firing FCM during every transaction check:** Only fire when `new_balance < threshold` AND student has a non-empty FCM token. No token = silent skip, not an error.
- **Storing Firebase service account in credentials.json:** These are separate files. Google Sheets uses one service account; Firebase may use a different one (or the same project's SA with Firebase Admin role). Keep them distinct in `config/`.
- **Loading all transactions at once for infinite scroll:** The backend already loads all records and slices by `limit`. For proper pagination, add `offset` to the slice — the existing `transactions[:limit]` becomes `transactions[offset:offset+limit]`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Firebase push dispatch | Raw `requests.post()` to FCM API | `firebase-admin` Python SDK `messaging.send()` | OAuth2 token refresh, retry, error handling all handled |
| FCM token validation | Custom token format check | Firebase SDK raises `UnregisteredError` on invalid token — catch and clear stored token | Tokens expire; SDK signals this cleanly |
| Infinite scroll pagination | Custom scroll detection from scratch | RecyclerView `OnScrollListener` + `findLastVisibleItemPosition()` | Standard Android pattern, well-tested |

**Key insight:** Firebase Admin SDK is the only safe way to send push notifications server-side. The legacy FCM HTTP v1 API requires manual OAuth2 Bearer token rotation — the SDK handles this transparently.

---

## Common Pitfalls

### Pitfall 1: FCM Token Auth Mismatch (CRITICAL)
**What goes wrong:** `POST /api/users/fcm-token` returns 401 for all real app users because it uses JWT auth but login issues opaque session tokens.
**Why it happens:** The endpoint was written anticipating a JWT login flow that was never implemented. The actual login route (`/api/auth/login`) issues opaque tokens stored in `active_sessions`.
**How to avoid:** Fix `register_fcm_token` to use session-based auth (same as `get_balance`). Do NOT rewrite login to use JWT — that would break all other session-based endpoints.
**Warning signs:** App always shows "FCM token registered" = false; notifications never arrive.

### Pitfall 2: Firebase App Double-Initialization
**What goes wrong:** `firebase_admin.initialize_app()` called twice → `ValueError: The default Firebase app already exists`.
**Why it happens:** Module reloaded in development, or initialized in multiple places.
**How to avoid:** Use `if not firebase_admin._apps:` guard before initializing, or wrap in a singleton getter function.
**Warning signs:** Server crashes on startup with `ValueError`.

### Pitfall 3: Stale FCM Token
**What goes wrong:** Notification fails silently because FCM token in Sheets is outdated (app reinstall, Firebase token rotation).
**Why it happens:** FCM tokens rotate; `FCMService.onNewToken()` saves to SharedPreferences but only syncs to backend on next login.
**How to avoid (Claude's Discretion):** On login, always call `POST /api/users/fcm-token` even if app already has a token — this keeps Sheets in sync. The `onNewToken` callback fires on rotation; make sure app sends it to backend (requires auth token — only possible when logged in, so buffer and send on next login).
**Warning signs:** Notifications stop arriving after user reinstalls app or resets device.

### Pitfall 4: Transaction Infinite Scroll — All Records Loaded
**What goes wrong:** `get_transactions` already loads all Sheets records into memory before slicing. With `offset`, it still fetches everything from Sheets each page.
**Why it happens:** Google Sheets has no SQL-style OFFSET; full scan is unavoidable.
**How to avoid:** This is acceptable for the school's scale (hundreds, not millions of transactions). Document it. The in-memory sort+slice is correct. Don't over-engineer.
**Warning signs:** Only a problem if Transactions Log exceeds ~10,000 rows (not a concern for v1).

### Pitfall 5: Receipt Screen — `BalanceBefore` Not in Transaction Response
**What goes wrong:** Receipt screen requires "balance before and after" but current `get_transactions` only returns `balance` (= `BalanceAfter`). `BalanceBefore` is in the Sheets row but not returned.
**Why it happens:** The `get_transactions` endpoint was written without the receipt screen in mind.
**How to avoid:** Add `balance_before` field to the transaction dict in `get_transactions`. Check the Sheets column: it's `BalanceBefore` in the transaction row (`BalanceBefore` is logged by the cashier transaction route as `BalanceBefore`).
**Warning signs:** Receipt screen shows "Balance before: ฿0.00" for all transactions.

**Verification:** The cashier transaction in `process_cashier_transaction` logs: `[timestamp, normalized_card, 'Purchase', -total, new_balance, 'Success', json.dumps(items)]` — note `BalanceBefore` is NOT in this row (only 7 columns). The `get_transactions` endpoint reads `BalanceAfter` from column index. Need to verify the actual Sheets column layout or add `BalanceBefore` to the cashier transaction log row.

---

## Code Examples

### Send FCM Push (Python)
```python
# Source: Context7 /firebase/firebase-admin-python
import firebase_admin
from firebase_admin import credentials, messaging

# Initialize once (module-level guard)
def _init_firebase():
    if not firebase_admin._apps:
        cred_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'firebase-credentials.json')
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

def send_low_balance_push(fcm_token: str, balance: float) -> bool:
    try:
        _init_firebase()
        message = messaging.Message(
            notification=messaging.Notification(
                title="Low Balance",
                body=f"Your canteen balance is ฿{balance:.2f}. Please top up soon."
            ),
            token=fcm_token
        )
        messaging.send(message)
        return True
    except Exception:
        return False
```

### Add offset pagination to get_transactions (Python)
```python
# In api_server.py get_transactions()
limit = int(request.args.get('limit', 20))
offset = int(request.args.get('offset', 0))
# ... sort all transactions ...
transactions.sort(key=lambda x: x['timestamp'], reverse=True)
total = len(transactions)
transactions = transactions[offset:offset + limit]
return jsonify({
    'transactions': transactions,
    'count': len(transactions),
    'total': total,
    'has_more': (offset + limit) < total
})
```

### Add balance_before to transaction response (Python)
```python
# In api_server.py get_transactions() — extend the transaction dict
transactions.append({
    'timestamp': record.get('Timestamp', ''),
    'type': record.get('TransactionType', ''),
    'amount': float(record.get('Amount', 0)),
    'balance': float(record.get('BalanceAfter', 0)),
    'balance_before': float(record.get('BalanceBefore', 0) or 0),  # NEW
    'description': f"{record.get('TransactionType', '')} - {record.get('Status', '')}",
    'items': items
})
```

### Infinite scroll in RecyclerView (Kotlin)
```kotlin
// In TransactionsActivity.kt
private var currentOffset = 0
private val pageSize = 20
private var isLoading = false
private var hasMore = true

recyclerView.addOnScrollListener(object : RecyclerView.OnScrollListener() {
    override fun onScrolled(rv: RecyclerView, dx: Int, dy: Int) {
        val lm = rv.layoutManager as LinearLayoutManager
        if (!isLoading && hasMore && lm.findLastVisibleItemPosition() >= lm.itemCount - 3) {
            loadTransactions(append = true)
        }
    }
})

private fun loadTransactions(append: Boolean = false) {
    if (!append) { currentOffset = 0; hasMore = true }
    isLoading = true
    val token = secureStorage.getAuthToken() ?: return
    ApiClient.apiService.getTransactions("Bearer $token", pageSize, currentOffset)
        .enqueue(object : Callback<TransactionsResponse> {
            override fun onResponse(...) {
                isLoading = false
                response.body()?.let {
                    hasMore = it.hasMore ?: false
                    currentOffset += it.transactions.size
                    if (append) adapter.appendTransactions(it.transactions)
                    else adapter.setTransactions(it.transactions)
                }
            }
            // ...
        })
}
```

### Settings sheet GET/POST (Python)
```python
@app.route('/api/settings/threshold', methods=['GET'])
@login_required
def get_threshold():
    try:
        settings_sheet = get_worksheet_with_retry('Settings')
        records = settings_sheet.get_all_records()
        for r in records:
            if r.get('Key') == 'low_balance_threshold':
                return jsonify({'threshold': float(r.get('Value', 50))})
        return jsonify({'threshold': float(os.getenv('LOW_BALANCE_THRESHOLD', 50))})
    except Exception:
        return jsonify({'threshold': float(os.getenv('LOW_BALANCE_THRESHOLD', 50))})

@app.route('/api/settings/threshold', methods=['POST'])
@login_required
def set_threshold():
    data = request.get_json()
    value = float(data.get('threshold', 50))
    # upsert Settings sheet row
    ...
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FCM Legacy API (server key) | FCM HTTP v1 API + `firebase-admin` SDK | 2023 (legacy API deprecated June 2024) | **Legacy FCM server key no longer works** — must use `firebase-admin` SDK or HTTP v1 with OAuth2 |
| `notifyDataSetChanged()` | `DiffUtil` / `ListAdapter` | Best practice ~2020 | Minor — `notifyDataSetChanged()` works but causes full list rebind; fine for this scale |

**Deprecated/outdated:**
- **FCM Legacy HTTP API (server key):** Google deprecated the old `https://fcm.googleapis.com/fcm/send` endpoint. It was shut down June 2024. Any docs or examples showing a raw HTTP POST with `Authorization: key=YOUR_SERVER_KEY` are obsolete. **Must use `firebase-admin` Python SDK** which uses HTTP v1 internally.

---

## Open Questions

1. **Does `process_cashier_transaction` log `BalanceBefore` to Sheets?**
   - What we know: The transaction row appended is `[timestamp, card, 'Purchase', -total, new_balance, 'Status', items_json]` — 7 columns. `BalanceBefore` is NOT in this row.
   - What's unclear: The `get_transactions` endpoint reads `record.get('BalanceBefore', 0)` — this will return 0 for all cashier transactions if the column is absent/empty.
   - Recommendation: Add `current_balance` (before deduction) to the transaction row when logging. Update `process_cashier_transaction` to append 8 columns: `[timestamp, card, 'Purchase', -total, current_balance, new_balance, 'Status', items_json]`.

2. **Is `FCMToken` column already present in the live Google Sheets `Users` sheet?**
   - What we know: `migrate_transactions.py::migrate_users_schema()` adds it if absent. It's unknown if this migration was ever run on the live sheet.
   - What's unclear: Column position (affects the `chr(64 + fcm_col_idx)` letter conversion in `register_fcm_token` — this breaks beyond column Z).
   - Recommendation: Wave 0 plan task should run `migrate_users_schema()` or manually verify the column exists. Also fix the column-letter conversion to use `gspread`'s `col_values` pattern (or `rowcol_to_a1`).

3. **Firebase service account credentials file location**
   - What we know: `config/credentials.json` is the Google Sheets service account. Firebase Admin needs its own service account JSON (same Firebase project).
   - What's unclear: Whether to use the same service account (add Firebase Admin role to it) or create a separate one.
   - Recommendation: Use the same `config/credentials.json` if that service account has Firebase Admin SDK permissions (common in school projects using one GCP project). Document this in Wave 0. If not, a new `config/firebase-credentials.json` is needed.

4. **App currently uses opaque tokens; FCM token endpoint uses JWT auth**
   - Already documented in Pitfall 1. This is a confirmed bug, not a question.

---

## Validation Architecture

> `workflow.nyquist_validation` is not set in `.planning/config.json` — skip this section.

*(The config.json has `"workflow": { "research": true, "plan_check": true, "verifier": true }` but no `nyquist_validation` key — section omitted.)*

---

## Sources

### Primary (HIGH confidence)
- `/firebase/firebase-admin-python` (Context7) — FCM `messaging.send()`, `credentials.Certificate()`, app initialization pattern
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/` — all existing Android code (direct codebase read)
- `backend/api/api_server.py` — all existing backend endpoints (direct codebase read)
- `backend/dashboard/admin_dashboard.py` — all admin routes (direct codebase read)
- `backend/migrate_transactions.py` — FCMToken migration status (direct codebase read)
- `.env.example` — `LOW_BALANCE_THRESHOLD` already defined

### Secondary (MEDIUM confidence)
- `mobile_rebuild_plan.md` — original design intent for FCM and push notifications (project planning doc)
- `FCM_SETUP.md` in `mobile/student_app_v2/` — Firebase project setup guidance (project doc, consistent with official Firebase docs)

### Tertiary (LOW confidence)
- FCM Legacy API deprecation timeline: training data + cross-checked with Firebase changelog. The June 2024 shutdown date is well-established but not re-verified via live web fetch.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Firebase Admin SDK is the only current option; Android libs already in project
- Architecture: HIGH — full codebase read, all existing patterns identified, gaps confirmed
- Pitfalls: HIGH — auth mismatch is a confirmed code-level bug; others are verified from codebase inspection

**Research date:** 2026-02-26
**Valid until:** 2026-03-28 (Firebase SDK stable; Android RecyclerView patterns stable)
