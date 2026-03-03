# Phase 10: Documentation Gaps — Research

**Researched:** 2026-03-02
**Domain:** Technical documentation (Markdown) — cashier Flask Blueprint endpoint reference + FCM operational behaviour note
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOC-02 | `docs/api-reference.md` — all REST API endpoints, request/response format, auth | Source-verified: `/cashier/api/*` routes are completely absent from current api-reference.md; all 10 routes catalogued below from cashier_routes.py |
| DOC-04 | `docs/cashier-guide.md` — how cashier POS works, Arduino setup, card reading flow | Source-verified: cashier-guide.md endpoint table is missing `GET /cashier/api/lookup-student` (Phase 7.1 addition); FCM note needs to accurately describe what `complete_sale` actually does |
</phase_requirements>

---

## Summary

Phase 10 is a pure documentation task with two deliverables: (1) add a complete `/cashier/api/*` section to `docs/api-reference.md`, and (2) update `docs/cashier-guide.md` with an accurate FCM operational note and a corrected endpoint table.

The cashier blueprint (`backend/dashboard/cashier/cashier_routes.py`) is a **separate Flask app** from `backend/api_server.py`. The existing `api-reference.md` documents only `api_server.py` endpoints — the entire cashier blueprint is undocumented there. The cashier guide already has a partial endpoint table but it is stale: `GET /cashier/api/lookup-student` (added in Phase 7.1) is absent.

**Critical source-code finding:** The phase description states cashier POS does NOT trigger FCM push notifications. This is **incorrect as of Phase 7**. `cashier_routes.py` `complete_sale()` at lines 534–576 **does** call `send_purchase_push()` and `send_low_balance_push()` from `backend/api/fcm_sender.py` via a lazy import. The FCM call is fire-and-forget inside a `try/except` that logs a warning on failure and never blocks the transaction response. The cashier-guide note must accurately reflect this reality — not create a false impression that FCM is absent from the cashier path.

**Primary recommendation:** Write the `/cashier/api/*` section in `api-reference.md` directly from source inspection of `cashier_routes.py`, and add a carefully worded operational note in `cashier-guide.md` that accurately describes cashier's FCM behaviour (it *does* send FCM, fire-and-forget, imported from `backend/api/fcm_sender.py`).

---

## Standard Stack

This phase requires no library installation. All work is Markdown editing.

| Tool | Purpose | Notes |
|------|---------|-------|
| Markdown (GFM) | Documentation format | Match style of existing `api-reference.md` and `cashier-guide.md` |
| Source inspection | Extract endpoint facts | All details come from `cashier_routes.py` source |

---

## Architecture Patterns

### Existing Documentation Style (HIGH confidence — direct inspection)

Both target documents follow a consistent style that MUST be matched exactly.

**`docs/api-reference.md` conventions:**
- H3 heading per endpoint: `### METHOD /path`
- **Auth:** line immediately after heading
- Bold **Request Body** / **Response NNN** section titles
- Tables for request fields and error responses
- JSON fenced code blocks for examples
- `---` horizontal rule between endpoints
- Endpoint Index table at top (must be updated too)

**`docs/cashier-guide.md` conventions:**
- Uses `---` section dividers
- Endpoint table has columns: `Method | Path | Auth Required | Description`
- Operational notes use `>` blockquote with ⚠️ emoji for warnings
- "Related Documentation" section at bottom

### Two-Document Pattern

```
docs/
├── api-reference.md    ← add new "## Cashier Blueprint API" section
└── cashier-guide.md    ← update endpoint table + add FCM note
```

The plan needs **one task per document** (2 tasks total), or both can be a single task since they are closely related. One plan, one wave is appropriate.

---

## Complete Cashier Blueprint Endpoint Inventory

All 10 routes verified from `cashier_routes.py` source (confidence: HIGH — direct inspection):

| # | Method | Path | Auth | Decorator | Handler |
|---|--------|------|------|-----------|---------|
| 1 | GET | `/cashier/login` | None | (none) | `login()` — renders login page |
| 2 | POST | `/cashier/api/login` | None | (none) | `api_login()` — validates hardcoded creds, sets JWT cookie |
| 3 | GET | `/cashier/` | JWT cashier/admin | `@jwt_required` | `index()` — renders POS page |
| 4 | GET | `/cashier/api/ports` | JWT cashier/admin | `@jwt_required` | `get_ports()` — lists COM ports |
| 5 | POST | `/cashier/api/connect-arduino` | JWT cashier/admin | `@jwt_required` | `connect_arduino()` — opens serial connection |
| 6 | GET | `/cashier/api/products` | JWT cashier/admin | `@jwt_required` | `get_products()` — lists active products |
| 7 | POST | `/cashier/api/logout` | None (cookie cleared) | (none) | `api_logout()` — deletes JWT cookie |
| 8 | GET | `/cashier/api/lookup-student` | JWT cashier/admin | `@jwt_required` | `lookup_student()` — search by name/ID for manual mode |
| 9 | POST | `/cashier/api/process-sale` | JWT cashier/admin | `@jwt_required` | `process_sale()` — stores pending txn, emits WebSocket event |
| 10 | POST | `/cashier/api/complete-sale` | JWT cashier/admin | `@jwt_required` | `complete_sale()` — validates card, deducts balance, writes Sheets row, sends FCM + email |

**Auth mechanism:** JWT stored in `jwt_token` **HttpOnly cookie** (NOT Authorization header). This is different from `api_server.py`'s Bearer token in the Authorization header. The cashier blueprint verifies the cookie with `request.cookies.get("jwt_token")`.

---

## Detailed Request/Response Facts (from source)

### POST /cashier/api/login (lines 133–156)

**Request:**
```json
{ "username": "cashier", "password": "cashier123" }
```
**Response 200:** `{"success": true}` + sets `jwt_token` HttpOnly cookie (8h expiry)
**Response 401:** `{"error": "Invalid credentials"}`

---

### GET /cashier/api/ports (lines 165–181)

**Response 200:**
```json
{ "ports": ["COM3", "COM4"] }
```
Returns `{"ports": []}` when pyserial unavailable (web/cloud mode).

---

### POST /cashier/api/connect-arduino (lines 184–225)

**Request:**
```json
{ "port": "COM3" }
```
**Response 200:** `{"success": true, "message": "Connected to COM3"}`
**Response 400:** `{"error": "Port required"}`
**Response 500:** `{"error": "Failed to connect: <reason>"}` or `{"error": "Arduino bridge not available"}`
**Response 503:** `{"error": "Service unavailable, please try again"}`

---

### GET /cashier/api/products (lines 228–251)

**Response 200:**
```json
{
  "products": [
    { "id": "PROD-001", "name": "Fried Rice", "category": "Food", "price": 25.0, "active": true }
  ]
}
```
**Response 503:** `{"error": "Service unavailable, please try again"}`

> Note: Returns ALL products (both active and inactive). The `active` boolean field is included; the POS frontend filters to show only active items.

---

### POST /cashier/api/logout (lines 254–259)

**Response 200:** `{"success": true}` + deletes `jwt_token` cookie
**Auth:** No decorator — always succeeds regardless of whether cookie exists.

---

### GET /cashier/api/lookup-student (lines 262–312)

**Query Parameters:** `?q=<search_string>` (minimum 2 characters)
**Response 200:**
```json
{
  "students": [
    { "id": "202501", "name": "Juan dela Cruz", "balance": 250.0, "card_uid": "ABCD1234" }
  ]
}
```
Returns empty list if `q` < 2 chars. Returns up to 10 matches.
**Response 503/500:** error objects

---

### POST /cashier/api/process-sale (lines 315–356)

**Request:**
```json
{ "items": [{"name": "Rice", "price": 20, "qty": 1}], "total": 20.0 }
```
**Response 200:**
```json
{ "status": "waiting_for_card", "message": "Please tap student card" }
```
**Response 400:** `{"error": "Invalid sale data"}`
**Side effect:** Emits `cashier_request_card` WebSocket event with `{"timeout": 5000, "total": <total>}`.

---

### POST /cashier/api/complete-sale (lines 359–622)

**Request (RFID card mode):**
```json
{ "card_uid": "ABCD1234" }
```
**Request (manual web mode):**
```json
{ "manual_student_id": "202501" }
```
**Response 200:**
```json
{ "success": true, "new_balance": 200.0, "timestamp": "2026-02-28 14:32:00" }
```

**Error Responses:**

| Status | Condition |
|--------|-----------|
| 400 | No `card_uid` or `manual_student_id` provided |
| 400 | `card_uid` does not match `^[0-9A-Fa-f]{8}$` |
| 400 | No pending transaction in session |
| 400 | Insufficient funds (`{"error": "Insufficient funds", "balance": ..., "required": ...}`) |
| 400 | Student has no card assigned (manual mode) |
| 403 | Card reported as lost |
| 403 | Card status not active |
| 404 | Card not found in Money Accounts sheet |
| 404 | Student not found (manual mode) |
| 500 | Manual student lookup failed |
| 503 | Google Sheets unavailable |

**Transaction row written to Transactions Log (11 columns):**

| Col | Field | Example |
|-----|-------|---------|
| 1 | TransactionID | `TXN-20260228143200` |
| 2 | Timestamp | `2026-02-28 14:32:00` |
| 3 | StudentID | `202501` |
| 4 | MoneyCardNumber | `ABCD1234` |
| 5 | TransactionType | `Purchase` or `Manual` |
| 6 | Amount | `25.0` (positive deduction value) |
| 7 | BalanceBefore | `275.0` |
| 8 | BalanceAfter | `250.0` |
| 9 | Status | `Completed` |
| 10 | ErrorMessage | `""` |
| 11 | ItemsJson | `[{"name":"Rice","price":20,"qty":1}]` |

---

## FCM Behaviour — Critical Accuracy Note

**Source-verified (lines 534–576 of `cashier_routes.py`):**

The cashier POS **DOES** send FCM push notifications. The current cashier-guide description is incomplete:

- After `complete_sale` writes the Sheets row, it calls `send_purchase_push(fcm_token, total, new_balance)` from `backend/api/fcm_sender.py`
- If `new_balance < threshold`, it also calls `send_low_balance_push(fcm_token, new_balance)`
- Both calls are wrapped in a single `try/except` block — **fire-and-forget**: failure logs a warning but never blocks or rolls back the transaction
- `fcm_sender.py` is imported lazily via `sys.path.insert` inside the try block, mirroring the email service pattern

**What the cashier-guide note should say:**

The note must NOT say "cashier POS does not trigger FCM" — that is factually wrong. Instead, the note should accurately describe:
1. Cashier POS **does** send FCM notifications after a completed sale (purchase push + optional low-balance push)
2. FCM is fire-and-forget — failure does not affect the transaction
3. FCM requires `FCMToken` to be populated in the Users sheet (registered by the student app)
4. If `FCMToken` is empty (student never logged into the app), no notification is sent — this is silent and expected

> **Reconciliation with phase description:** The phase description says "cashier POS does not trigger FCM push notifications." This appears to reflect the **original** Phase 6 docs state (when cashier-guide was written before Phase 7 FCM fix). Phase 7 added the FCM call to `complete_sale`. The correct action is to document the **current code reality** (FCM IS sent), not to preserve a stale claim.

---

## Gaps in Existing cashier-guide.md Endpoint Table

The current endpoint table in cashier-guide.md (lines 141–153) lists 8 endpoints but is **missing** `GET /cashier/api/lookup-student` (added in Phase 7.1). The planner must include updating this table as part of DOC-04.

**Current table state:**
```
GET  /cashier/login               No       Renders login page
POST /cashier/api/login           No       Authenticates
POST /cashier/api/logout          Session  Logs out
GET  /cashier/api/ports           Session  Returns COM ports
POST /cashier/api/connect-arduino Session  Connects serial
GET  /cashier/api/products        JWT+Sess Returns active products
POST /cashier/api/process-sale    Session  Initiates sale
POST /cashier/api/complete-sale   Session  Finalises sale
```

**Missing:**
```
GET  /cashier/api/lookup-student  JWT      Search students by name/ID (manual web mode)
```

**Auth accuracy corrections needed:**
- `/cashier/api/logout` — has no `@jwt_required` decorator, so "Session" is inaccurate; should be "None" or "None (cookie cleared)"
- `/cashier/api/products` — decorated with `@jwt_required`, so "JWT + Session" is the right description (JWT cookie is the session)
- Most "Session" labels should say "JWT cookie" to be accurate to the implementation

---

## Existing cashier-guide.md Transaction Row — Correction Needed

The cashier-guide.md Section "Transaction Record Written to Sheets" (lines 122–136) documents a **7-column row** with no `BalanceBefore` column and `Status=Success`. The actual source writes an **11-column row** with `BalanceBefore`, `StudentID`, `TransactionID`, `ErrorMessage`, and `Status=Completed`. This table is stale from before Phase 7. The planner must decide whether to update this table in the same task (it falls under DOC-04 scope).

---

## Where to Insert in api-reference.md

The `api-reference.md` currently ends with a Troubleshooting section and a "See also" footer (line 572). The cashier blueprint section should be inserted as a new top-level section **before** the Troubleshooting section, with its own endpoint index subsection and full per-endpoint entries. The Endpoint Index table near the top should also be updated or a note added that cashier blueprint routes are documented separately.

**Recommended placement:**
```markdown
---

## Cashier Blueprint API

> **Note:** These endpoints are served by the cashier dashboard server ...
[endpoint index table]
[per-endpoint entries]
```

---

## Don't Hand-Roll

This phase has no code. All deliverables are Markdown edits.

| Problem | Don't Do | Do Instead |
|---------|----------|-----------|
| Documenting FCM behaviour | Guess or copy phase description verbatim | Read lines 534–576 of cashier_routes.py and document actual code |
| Transaction row column count | Copy the old 7-col table | Verify from lines 484–496 of cashier_routes.py (11 cols) |
| Auth type for endpoints | Guess | Check each route's decorator in cashier_routes.py source |

---

## Common Pitfalls

### Pitfall 1: Repeating the Stale "cashier POS does not send FCM" Claim
**What goes wrong:** Phase description says cashier POS does NOT trigger FCM. If the planner writes this into docs verbatim, the docs will be factually wrong.
**Why it happens:** Phase description reflected code state BEFORE Phase 7. Phase 7 added FCM to `complete_sale`.
**How to avoid:** Document what the code actually does (lines 534–576) — cashier DOES send FCM, fire-and-forget.
**Warning signs:** Any documentation that says "only api_server.py sends FCM" is incorrect.

### Pitfall 2: Missing the lookup-student Endpoint
**What goes wrong:** Phase 7.1 added `GET /cashier/api/lookup-student` but it is not in cashier-guide.md's endpoint table.
**Why it happens:** Docs were written before Phase 7.1.
**How to avoid:** Cross-reference source routes against the guide table; include lookup-student in both the api-reference section and the guide table.

### Pitfall 3: Wrong Auth Type in cashier-guide.md Table
**What goes wrong:** Existing table says "Session" for most endpoints. Cashier uses a JWT stored in an HttpOnly **cookie** — not a session token or an Authorization header.
**How to avoid:** Use "JWT cookie" as the auth description. The `@jwt_required` decorator reads `request.cookies.get("jwt_token")`.

### Pitfall 4: Confusing the Two Flask Apps
**What goes wrong:** Documenting cashier blueprint endpoints inside the existing "student REST API" context of api-reference.md without a clear separator.
**How to avoid:** Add a prominent section header and introductory paragraph that explains the cashier blueprint is served by a **different Flask app** (dashboard server, port 5003) vs api_server.py (port 5001).

### Pitfall 5: Stale 7-Column Transaction Row Table in cashier-guide.md
**What goes wrong:** cashier-guide.md line 123 says "7-column row" — but current code writes 11 columns.
**How to avoid:** Update the transaction row table in cashier-guide.md during this phase (it is in-scope for DOC-04 accuracy).

---

## Code Examples

### Auth Mechanism (source: cashier_routes.py lines 101–125)

```python
# Cashier JWT is in a cookie, NOT Authorization header
def jwt_required(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.cookies.get("jwt_token")   # <-- cookie, not header
            if not token:
                return redirect(url_for("cashier.login"))
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if roles and payload.get("role") not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            request.user = payload
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### FCM Fire-and-Forget Pattern (source: cashier_routes.py lines 534–576)

```python
# Fire-and-forget: never blocks transaction response
try:
    threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
    # ... read threshold from Settings sheet ...
    fcm_token = str(user.get("FCMToken", "")).strip()
    if fcm_token:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))
        from fcm_sender import send_purchase_push
        send_purchase_push(fcm_token, total, new_balance)
        if new_balance < threshold:
            from fcm_sender import send_low_balance_push
            send_low_balance_push(fcm_token, new_balance)
except Exception as notif_error:
    logger.warning("event=low_balance_notify_failed error=%s", notif_error)
```

### Transaction Row Written (source: cashier_routes.py lines 484–496)

```python
transaction_row = [
    transaction_id,       # TXN-YYYYMMDDHHMMSS
    timestamp,            # "2026-02-28 14:32:00"
    resolved_student_id,  # "202501"
    normalized_card,      # "ABCD1234"
    transaction_type,     # "Purchase" or "Manual"
    total,                # 25.0  (positive deduction value)
    current_balance,      # 275.0 (balance BEFORE deduction)
    new_balance,          # 250.0 (balance AFTER deduction)
    "Completed",          # Status
    "",                   # ErrorMessage
    json.dumps(items),    # '[{"name":"Rice","price":20,"qty":1}]'
]
```

---

## Open Questions

1. **Whether to update the stale 7-column transaction table in cashier-guide.md**
   - What we know: The table is factually wrong (7 cols claimed, 11 written); it is in DOC-04 scope
   - What's unclear: Roadmap only mentions adding the FCM note — the stale table was not explicitly called out as TD-11
   - Recommendation: Fix the table in the same task — it is a documentation accuracy issue within DOC-04 scope and costs one extra paragraph edit

2. **Whether to update the Endpoint Index table at the top of api-reference.md**
   - What we know: The index table lists only api_server.py routes; adding cashier routes there would intermix two apps
   - Recommendation: Add a note in the index table pointing to the new section, rather than inlining all cashier routes in the index — keeps the index clean

---

## Sources

### Primary (HIGH confidence)
- `backend/dashboard/cashier/cashier_routes.py` — all 10 routes, auth decorators, request/response shapes, FCM call, transaction row structure (direct source inspection)
- `docs/api-reference.md` — confirmed absence of `/cashier/api/*` section; existing style conventions
- `docs/cashier-guide.md` — confirmed missing lookup-student endpoint; stale 7-col transaction table; stale FCM absence claim
- `.planning/REQUIREMENTS.md` — DOC-02 and DOC-04 requirement definitions (Pending status)
- `.planning/ROADMAP.md` — Phase 10 success criteria and gap IDs (TD-10, TD-11)
- `.planning/STATE.md` — Phase 7 FCM decision log confirming FCM was added to cashier path in 07-01

### Secondary (MEDIUM confidence)
- `.planning/config.json` — `nyquist_validation` not present → Validation Architecture section omitted

---

## Metadata

**Confidence breakdown:**
- Endpoint inventory: HIGH — all 10 routes inspected directly from source
- Request/response shapes: HIGH — read from handler implementations in source
- FCM behaviour: HIGH — source lines 534–576 are unambiguous; reconciliation with phase description documented
- Stale doc gaps: HIGH — direct comparison of guide table vs source routes
- Auth mechanism: HIGH — `jwt_required` decorator implementation read directly

**Research date:** 2026-03-02
**Valid until:** 2026-04-02 (stable — no planned changes to cashier_routes.py in remaining phases)
