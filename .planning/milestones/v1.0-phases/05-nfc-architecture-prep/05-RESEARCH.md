# Phase 5: NFC Architecture Prep - Research

**Researched:** 2026-02-28
**Domain:** Flask REST API extensions, UUID token auth, Google Sheets persistence, Android HCE documentation
**Confidence:** HIGH

## Summary

Phase 5 is a backend-only phase: add two new Flask endpoints (`/api/nfc/register`, `/api/nfc/pay`) to `backend/api/api_server.py`, persist VirtualCard records to a new Google Sheets tab, and write an integration guide for future Android HCE implementers. No Android code ships in this phase.

The existing `backend/nfc_payments.py` file contains a `VirtualCard` class and `NFCPaymentManager` — but both are **in-memory only**, use a bespoke token format, and model far more complexity (PIN, biometrics, multi-card, expiry, refresh) than the locked decisions require. Phase 5 will **replace** the token logic with server-generated UUID v4, strip out all out-of-scope features, wire the simplified manager to Google Sheets, and expose the two endpoints. The existing file is raw material, not a finished solution.

The cashier payment flow in `api_server.py` currently accepts only RFID card UIDs (8-character hex). Phase 5 must modify it to also accept UUID v4 virtual card tokens, with a clean disambiguation strategy (UUID regex vs. RFID hex regex — see Claude's Discretion below). The integration guide (`docs/nfc-integration-guide.md`) must be self-contained for a future Android developer who will implement HCE in v2.

**Primary recommendation:** Build a thin `NFCService` class in `nfc_payments.py` (replacing most of the current logic), wire it to a `VirtualCards` Google Sheet via the `ensure_*_sheet` pattern already established in `admin_dashboard.py`, add the two Flask routes to `api_server.py`, extend the cashier transaction endpoint for dual-source disambiguation, and write the guide last.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**VirtualCard Registration Flow**
- One virtual card per student — registering again silently replaces the old one
- Virtual card token has no expiry — valid until the student re-registers
- Registration is student-initiated: student must be logged in (valid JWT) to call `/api/nfc/register`
- Re-registration silently replaces the existing virtual card with no warning or confirmation step

**Payment Token Format**
- Token format: UUID v4 (e.g. `550e8400-e29b-41d4-a716-446655440000`)
- Server generates the UUID and returns it in the `/api/nfc/register` response — Android stores and replays it
- NFC payload (what the phone sends via HCE when tapped) contains the plain UUID string, no envelope or wrapping
- How the cashier POS distinguishes NFC virtual card token from RFID card UID: Claude's discretion (see below)

**Device Authentication Model**
- Server issues a separate device token during `/api/nfc/register`, returned alongside the virtual card UUID
- Device token is sent by Android as an `X-Device-Token` request header on every `/api/nfc/pay` call
- Device token has no expiry — lifetime matches the virtual card (valid until re-registration)
- Both JWT (student identity) AND `X-Device-Token` (device identity) are required and validated on `/api/nfc/pay`; missing or invalid either → rejected

**Integration Guide (docs/nfc-integration-guide.md)**
- Full error code table: every 4xx response documented with cause and resolution
- Kotlin code snippets: HCE service subclass, registration API call, payment flow — copy-paste ready
- Full end-to-end sequence diagram: app registers → server stores VirtualCard → student taps phone → cashier reads NFC payload → POST `/api/nfc/pay` → debit + response
- Android setup section: exact manifest entries, `HostApduService` subclass structure, AID the cashier reader must select

### Claude's Discretion
- How the cashier POS software distinguishes an NFC UUID token from an RFID card UID (could detect by format, UUID regex, field name, or separate endpoint)
- Exact Google Sheets schema for VirtualCards (column layout, sheet name)
- Device token format (can be UUID v4 or similar random token)
- Error message wording for NFC-specific failures

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| NFC-01 | NFC payment API endpoints exist and are documented (`/api/nfc/register`, `/api/nfc/pay`) | Flask Blueprint/route pattern from existing `api_server.py`; documented with inline docstrings matching existing endpoint style |
| NFC-02 | VirtualCard model in nfc_payments.py is fully integrated with Google Sheets (persisted, not just in-memory) | `ensure_*_sheet` pattern from `admin_dashboard.py`; gspread `append_row` + `get_all_records` pattern already in use |
| NFC-03 | Transaction flow accepts both RFID card UID and NFC virtual card token as payment sources | UUID v4 regex disambiguation in `process_cashier_transaction`; look up VirtualCard row from sheet, resolve to money_card |
| NFC-04 | API authentication supports NFC device token alongside JWT (ready for Android HCE integration) | `X-Device-Token` header check in `require_auth` decorator extension or inline in `/api/nfc/pay` handler |
| NFC-05 | NFC integration guide written in docs/ explaining what the Android app needs for v2 | `docs/NFC_IMPLEMENTATION.md` exists as prior art (pre-planning era); new guide must match locked decisions not the old doc's design |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | Already installed | HTTP routing, request/response | All existing endpoints use it; zero new dependency |
| gspread | Already installed | Google Sheets read/write | All persistence in this project uses gspread |
| PyJWT (jwt) | Already installed | JWT decode for auth | `require_auth` decorator in `api_server.py` already uses it |
| uuid (stdlib) | stdlib | UUID v4 generation | Already imported in `nfc_payments.py`; no install needed |
| secrets (stdlib) | stdlib | Device token generation | Already used in `api_server.py` for session tokens |
| re (stdlib) | stdlib | UUID vs. RFID disambiguation regex | Already used for `UID_PATTERN` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytz | Already installed | Philippine timezone in `created_at` | Consistent with all other timestamp fields |
| functools.wraps | stdlib | Auth decorator | Already used in `require_auth` |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Google Sheets for VirtualCards | In-memory dict | In-memory fails NFC-02 (does not survive restart) — ruled out |
| UUID v4 device token | HMAC token | UUID is simpler, sufficient for this security model; HMAC adds complexity with no benefit given no expiry |
| Separate `/api/nfc/pay` endpoint | Extend existing cashier transaction | Separate endpoint keeps NFC auth (JWT + device token) cleanly separate from cashier JWT-only; cleaner for the Android developer |

**Installation:** No new packages required. All dependencies are already present.

---

## Architecture Patterns

### Recommended Project Structure

No new files or directories are strictly required. All changes land in existing files:

```
backend/
├── nfc_payments.py        # MODIFY: strip to thin VirtualCard + NFCService; add Sheets persistence
└── api/
    └── api_server.py      # MODIFY: add /api/nfc/register, /api/nfc/pay; extend cashier transaction
docs/
└── nfc-integration-guide.md  # CREATE: Android HCE integration guide
```

### Pattern 1: ensure_*_sheet for VirtualCards

**What:** Get-or-create the VirtualCards sheet with correct headers, matching the pattern used for Products and Settings in `admin_dashboard.py`.

**When to use:** Called at the top of every NFC endpoint that reads or writes VirtualCards.

```python
# Mirrors ensure_products_sheet() in admin_dashboard.py:146
def ensure_virtual_cards_sheet():
    """Get VirtualCards worksheet, creating it with headers if missing."""
    global db
    try:
        return get_worksheet_with_retry('VirtualCards')
    except gspread.exceptions.WorksheetNotFound:
        sheet = db.add_worksheet(title='VirtualCards', rows=200, cols=6)
        sheet.update('A1:F1', [[
            'StudentID', 'VirtualCardToken', 'DeviceToken',
            'MoneyCardNumber', 'CreatedAt', 'IsActive'
        ]])
        logger.info("event=virtual_cards_sheet_created")
        return sheet
```

**Google Sheets schema (Claude's discretion — recommended):**

| Column | Value | Notes |
|--------|-------|-------|
| A: StudentID | `"2024-001"` | FK to Users sheet |
| B: VirtualCardToken | UUID v4 string | What Android stores and NFC sends |
| C: DeviceToken | `secrets.token_urlsafe(32)` | Sent as X-Device-Token header |
| D: MoneyCardNumber | RFID UID string | FK to Money Accounts sheet |
| E: CreatedAt | ISO timestamp (Asia/Manila) | Informational |
| F: IsActive | `"TRUE"` / `"FALSE"` | For silent replace: set old row FALSE, append new row |

**Why 6 columns:** Minimal but sufficient. No PIN, biometric, device name — those are out of scope (locked decisions say one-card-per-student, no expiry, no PIN).

### Pattern 2: active_sessions auth (existing pattern for /api/nfc/register)

**What:** `/api/nfc/register` requires student to be logged in. The existing student auth uses `active_sessions` dict (not JWT). Existing student endpoints (`/api/student/balance`, `/api/student/transactions`) all read from `active_sessions`. Use the same pattern.

```python
@app.route('/api/nfc/register', methods=['POST'])
def nfc_register():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if token not in active_sessions:
        return jsonify({'error': 'Invalid or expired token'}), 401
    session = active_sessions[token]
    student_id = session['student_id']
    # ... generate virtual_card_token = str(uuid.uuid4())
    # ... generate device_token = secrets.token_urlsafe(32)
    # ... upsert into VirtualCards sheet
    return jsonify({
        'virtual_card_token': virtual_card_token,
        'device_token': device_token
    })
```

**Important:** `active_sessions` auth, NOT `require_auth` JWT decorator. The existing student-facing endpoints use session tokens (from `/api/auth/login`), not JWT. `require_auth` is used only for cashier/admin routes.

### Pattern 3: JWT + X-Device-Token dual auth for /api/nfc/pay

**What:** The cashier POS calls `/api/nfc/pay`. It sends both the JWT (for cashier identity) and the `X-Device-Token` (device identity from the student's phone, extracted from the NFC payload). Both must be valid.

```python
@app.route('/api/nfc/pay', methods=['POST'])
@require_auth(roles=['admin', 'cashier'])   # JWT validation
def nfc_pay():
    device_token = request.headers.get('X-Device-Token', '')
    if not device_token:
        return jsonify({'error': 'X-Device-Token header required'}), 401
    
    data = request.get_json()
    virtual_card_token = data.get('virtual_card_token', '').strip()
    items = data.get('items', [])
    total = float(data.get('total', 0))
    
    # Look up VirtualCard row by VirtualCardToken AND DeviceToken
    vc_sheet = ensure_virtual_cards_sheet()
    records = vc_sheet.get_all_records()
    matched = None
    for r in records:
        if r.get('VirtualCardToken') == virtual_card_token and \
           r.get('DeviceToken') == device_token and \
           str(r.get('IsActive', '')).upper() == 'TRUE':
            matched = r
            break
    
    if not matched:
        return jsonify({'error': 'Invalid virtual card token or device token'}), 401
    
    money_card = matched['MoneyCardNumber']
    # ... reuse existing balance deduction + transaction logging logic
```

### Pattern 4: UUID vs RFID disambiguation in cashier transaction (Claude's discretion)

**What:** `POST /api/cashier/transaction` currently accepts `card_uid` (RFID hex). NFC payments go through `/api/nfc/pay` (separate endpoint), so the cashier transaction endpoint does NOT need to change for NFC tokens. The cashier POS software simply calls a different endpoint depending on whether it received a UUID from an NFC tap or an RFID UID from a card scan.

**Recommended approach:** Keep the existing `/api/cashier/transaction` for RFID-only. Add `/api/nfc/pay` for NFC-only. The cashier POS identifies the source by which endpoint it calls. This is the cleanest, most backward-compatible approach.

**Why not a single endpoint with auto-detection:**
- UUID v4 regex: `^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`
- RFID UID regex: `^[0-9A-Fa-f]{8}$`
- These patterns are mutually exclusive — auto-detection would work — but a separate endpoint is cleaner because it has different auth (JWT + X-Device-Token vs. JWT only) and different request semantics. Keep them separate.

### Pattern 5: upsert for silent re-registration

**What:** "One card per student — re-registration silently replaces." Use find-and-deactivate-old + append-new:

```python
# Deactivate any existing active card for this student
for idx, r in enumerate(records, start=2):
    if str(r.get('StudentID')) == str(student_id) and \
       str(r.get('IsActive', '')).upper() == 'TRUE':
        vc_sheet.update_cell(idx, 6, 'FALSE')  # col F = IsActive

# Append new row
vc_sheet.append_row([
    student_id,
    virtual_card_token,
    device_token,
    money_card,
    get_philippines_time().isoformat(),
    'TRUE'
])
```

### Anti-Patterns to Avoid

- **Storing device token in Android only:** The device token must be verified server-side by looking it up in the VirtualCards sheet. Storing it only in-memory would violate NFC-02.
- **Reusing `require_auth` for `/api/nfc/register`:** Student endpoints use `active_sessions`, not JWT. Using `require_auth` would require students to have JWT tokens, which they don't — they have session tokens.
- **Modifying the existing `NFCPaymentManager` class incrementally:** The existing class has PIN, biometric, expiry, multi-card, device_bindings — none of which are in scope. A clean rewrite of just what's needed is safer than patching around out-of-scope features.
- **Trusting only one of JWT or device token on `/api/nfc/pay`:** Both must be checked. Failing to check `X-Device-Token` against the sheet means any cashier with a valid JWT could fabricate NFC payments.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| UUID generation | Custom token format | `uuid.uuid4()` (stdlib) | Already in scope per locked decisions; stdlib is correct |
| Device token generation | Custom HMAC/hash | `secrets.token_urlsafe(32)` | Already the pattern for session tokens in `api_server.py:99` |
| Sheet creation guard | Try/except bare | `ensure_*_sheet()` pattern | Already established in `admin_dashboard.py:146,1912`; creates sheet with headers if missing |
| Gspread retry logic | Custom retry loop | `get_worksheet_with_retry()` | Already exists in `api_server.py:81`; use it, don't copy-paste |

**Key insight:** This project has zero new external dependencies for Phase 5. Everything needed is either stdlib or already installed.

---

## Common Pitfalls

### Pitfall 1: Wrong auth pattern for /api/nfc/register

**What goes wrong:** Using `@require_auth` decorator (JWT) on `/api/nfc/register` breaks student login flow.

**Why it happens:** There are two separate auth systems in this codebase — `active_sessions` (for students, used in all `/api/student/*` endpoints) and JWT `require_auth` (for cashiers/admins, used in `/api/cashier/*` and `/api/products`). It's easy to grab the wrong one.

**How to avoid:** `/api/nfc/register` is a student action (student must be logged in). Use `active_sessions` dict check — identical to `get_balance()` lines 322-325.

**Warning signs:** If registration returns 401 for a valid student session, wrong auth pattern is in use.

### Pitfall 2: nfc_payments.py NFCPaymentManager is in-memory only

**What goes wrong:** The existing `NFCPaymentManager` stores everything in `self.virtual_cards` dict. A server restart loses all registrations. This violates NFC-02.

**Why it happens:** The class was written speculatively without Google Sheets integration.

**How to avoid:** Do not call `get_nfc_manager()` as the persistence layer. Write directly to/from the VirtualCards sheet in the endpoint handlers (or a new `NFCService` class that takes a sheets client as a parameter).

### Pitfall 3: Token field not matching between registration and payment

**What goes wrong:** `/api/nfc/register` returns `virtual_card_token` but `/api/nfc/pay` looks up `VirtualCardToken` in the sheet — if column name or key name mismatches, lookups always fail.

**Why it happens:** Python dict key names (from `get_all_records()`) are taken from the sheet header row. If the header says `VirtualCardToken` but the code checks `virtual_card_token`, lookup fails silently.

**How to avoid:** Define column names as constants at the module level. Verify `ensure_virtual_cards_sheet()` header row matches exactly what the lookup code references.

### Pitfall 4: Deactivation by StudentID is insufficient without IsActive check

**What goes wrong:** Re-registration that "silently replaces" must actually deactivate the old row, not just append a new one. If the lookup code only filters on `VirtualCardToken` (not `IsActive`), old deactivated tokens can still match.

**Why it happens:** The upsert logic appends a new row but forgets to filter by `IsActive == TRUE` during lookup.

**How to avoid:** All VirtualCard lookups must include `IsActive == 'TRUE'` as a filter condition.

### Pitfall 5: NFC guide describes a different design than the implemented API

**What goes wrong:** The guide is written first or separately and drifts from the actual endpoint behavior. A future Android developer follows the guide and gets 401s because the token format, header names, or endpoint paths don't match.

**Why it happens:** Integration guides are usually written before or without running the code.

**How to avoid:** Write `docs/nfc-integration-guide.md` last, after the endpoints are working. Copy actual request/response shapes from the code into the guide. The existing `docs/NFC_IMPLEMENTATION.md` describes the old design (APDU-based, biometric, PIN) — do NOT reuse it as a template; it contradicts the locked decisions.

### Pitfall 6: X-Device-Token header missing from CORS configuration

**What goes wrong:** Android app sends `X-Device-Token` header, but CORS rejects it because it's not in the allowed headers list.

**Why it happens:** Flask-CORS by default allows standard headers. Custom headers like `X-Device-Token` must be explicitly added.

**How to avoid:** Add `X-Device-Token` to Flask-CORS `allow_headers` in `api_server.py`. Check the existing `CORS(app, origins=get_cors_origins())` call — it may need `allow_headers=['Authorization', 'Content-Type', 'X-Device-Token']`.

---

## Code Examples

### /api/nfc/register — full response shape

```python
# POST /api/nfc/register
# Header: Authorization: Bearer <session_token>
# Body: {} (no body needed — student identity comes from session)

# Success 200:
{
    "virtual_card_token": "550e8400-e29b-41d4-a716-446655440000",  # UUID v4
    "device_token": "abc123...",    # secrets.token_urlsafe(32)
    "money_card": "5F6E7D8C",       # for Android to display
    "message": "Virtual card registered"
}

# Error responses:
# 401 {"error": "Invalid or expired token"}           — missing/bad session
# 403 {"error": "No money card registered"}           — student has no RFID card
# 503 {"error": "Service unavailable, please try again"} — Sheets down
```

### /api/nfc/pay — full request/response shape

```python
# POST /api/nfc/pay
# Header: Authorization: Bearer <cashier_jwt_token>
# Header: X-Device-Token: <device_token>
# Body:
{
    "virtual_card_token": "550e8400-e29b-41d4-a716-446655440000",
    "items": [{"id": "PROD-001", "name": "Burger", "price": 50, "qty": 2}],
    "total": 100.00
}

# Success 200:
{
    "success": true,
    "new_balance": 400.00,
    "timestamp": "2026-02-28 10:30:45"
}

# Error responses:
# 400 {"error": "Invalid transaction data"}           — missing fields or total <= 0
# 401 {"error": "No token provided"}                 — missing JWT
# 401 {"error": "Invalid or expired token"}          — bad JWT
# 401 {"error": "X-Device-Token header required"}    — missing device token
# 401 {"error": "Invalid virtual card token or device token"} — token mismatch or inactive
# 400 {"error": "Insufficient funds", "balance": 300.00}
# 503 {"error": "Service unavailable, please try again"}
```

### UUID v4 validation regex

```python
import re
UUID_V4_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$',
    re.IGNORECASE
)

def is_uuid_v4(value: str) -> bool:
    return bool(UUID_V4_PATTERN.match(value))
```

This is useful in the guide to document what the cashier reader should send, and as a defensive check in the endpoint.

### Android HCE AID selection (for integration guide)

```kotlin
// res/xml/apdu_service.xml
// AID must be registered on the cashier NFC reader to route APDU SELECT to BankoHceService
// Recommended AID: F049494F4E41 (custom, non-conflicting with payment AIDs)
// Encoded as hex string in apdu_service.xml:
// <aid-group android:description="@string/app_name" android:category="other">
//     <aid-filter android:name="F049494F4E41"/>
// </aid-group>
```

### Android HCE processCommandApdu (for integration guide)

```kotlin
// BankoHceService.kt
class BankoHceService : HostApduService() {
    private val SELECT_AID_HEADER = byteArrayOf(0x00, 0xA4.toByte(), 0x04, 0x00)
    private val RESPONSE_OK = byteArrayOf(0x90.toByte(), 0x00)
    private val RESPONSE_UNKNOWN = byteArrayOf(0x6D, 0x00)

    override fun processCommandApdu(apdu: ByteArray, extras: Bundle?): ByteArray {
        // SELECT AID command
        if (apdu.take(4).toByteArray().contentEquals(SELECT_AID_HEADER)) {
            val token = getStoredToken() ?: return RESPONSE_UNKNOWN
            val tokenBytes = token.toByteArray(Charsets.UTF_8)
            return tokenBytes + RESPONSE_OK
        }
        return RESPONSE_UNKNOWN
    }

    override fun onDeactivated(reason: Int) { /* no-op */ }

    private fun getStoredToken(): String? {
        val prefs = EncryptedSharedPreferences.create(
            applicationContext, "nfc_prefs",
            MasterKeys.getOrCreate(MasterKeys.AES256_GCM_SPEC),
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
        return prefs.getString("virtual_card_token", null)
    }
}
```

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `nfc_payments.py` `NFCPaymentManager` (in-memory, complex) | Thin Sheets-backed service with UUID v4 tokens | Existing code is starting point only; the new implementation is simpler |
| `docs/NFC_IMPLEMENTATION.md` (APDU detail, biometric, PIN flow) | `docs/nfc-integration-guide.md` (matches locked decisions: UUID, no PIN, X-Device-Token) | Old guide documents a different design; do not port it |

**Deprecated/outdated:**
- `NFCPaymentManager._generate_secure_token()`: generates a `random_hex + sha256_hash` token — replaced by `str(uuid.uuid4())` per locked decision
- `NFCPaymentManager.TOKEN_VALIDITY_HOURS = 24 * 7`: tokens had expiry — locked decision says no expiry
- `NFCPaymentManager.MAX_CARDS_PER_STUDENT = 2`: multi-card — locked decision says one per student, silent replace
- `VirtualCard.pin_hash`, `biometric_enabled`, `transaction_count`: all out of scope for Phase 5

---

## Open Questions

1. **Does `GET /api/nfc/register` or `POST /api/nfc/register`?**
   - What we know: REQUIREMENTS.md says "GET /api/nfc/register" in NFC-01. CONTEXT.md says registration is student-initiated and creates a new resource.
   - What's unclear: GET creating a resource is semantically wrong (RESTful convention is POST for creation). The success criterion says "Calling GET /api/nfc/register... returns documented success responses."
   - Recommendation: Implement as `POST /api/nfc/register` (correct REST semantics for resource creation). The success criterion language is loose — the planner should use POST. Document it clearly in the guide.

2. **How does the cashier NFC reader extract the UUID from the APDU payload?**
   - What we know: The phone sends a plain UUID string as the APDU response body (not wrapped). The cashier hardware reads the NFC tap.
   - What's unclear: The current cashier POS is Arduino-based for RFID. An NFC reader reads APDU differently from RFID UID reads. Whether the cashier hardware supports HCE APDU reading is a v2 concern — Phase 5 only documents the API contract.
   - Recommendation: Integration guide should note that the cashier reader must support ISO 14443-4 (HCE) and send the token string to `/api/nfc/pay` as `virtual_card_token` in the JSON body, alongside the JWT and X-Device-Token. This is sufficient for a future developer.

3. **Should `/api/nfc/pay` log to the same Transactions Log sheet as cashier transactions?**
   - What we know: NFC-03 says "payment request... is accepted and debits the same student account." NFC-02 says VirtualCard is persisted to Google Sheets.
   - What's unclear: Whether NFC payments should appear in the Transactions Log sheet alongside RFID payments.
   - Recommendation: Yes — `/api/nfc/pay` should append to Transactions Log with a distinct `TransactionType` of `"NFC Purchase"` (vs. existing `"Purchase"`). This ensures the student's transaction history (already built in Phase 4) shows NFC payments. The row format is identical to existing cashier transactions.

---

## Sources

### Primary (HIGH confidence)
- Codebase direct read — `backend/api/api_server.py` (full file, 825 lines): auth patterns, active_sessions, require_auth decorator, existing cashier transaction endpoint, gspread sheet names
- Codebase direct read — `backend/nfc_payments.py` (full file, 402 lines): existing VirtualCard/NFCPaymentManager structure
- Codebase direct read — `backend/dashboard/admin_dashboard.py`: `ensure_products_sheet()` at line 146, `ensure_settings_sheet()` at line 1912 — the pattern to replicate
- `.planning/phases/05-nfc-architecture-prep/05-CONTEXT.md` — locked decisions

### Secondary (MEDIUM confidence)
- `docs/NFC_IMPLEMENTATION.md` — prior-art HCE Kotlin examples (AID, APDU service, manifest); content is for a different token design but the Android-side code structure is reusable for the guide
- Android developer docs (via `docs/NFC_IMPLEMENTATION.md` which reflects standard HCE API): `HostApduService`, `apdu_service.xml`, manifest entries

### Tertiary (LOW confidence)
- None — all findings verified against codebase or are stdlib patterns.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all existing imports verified in codebase
- Architecture: HIGH — all patterns traced to existing code in the same repo
- Pitfalls: HIGH — derived from direct code inspection, not speculation
- Integration guide content: MEDIUM — Android HCE patterns from prior art in `docs/NFC_IMPLEMENTATION.md`; exact AID value is discretionary

**Research date:** 2026-02-28
**Valid until:** 2026-04-01 (stable domain — Flask, gspread, Android HCE API are not fast-moving)
