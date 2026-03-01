# Phase 6: Documentation - Research

**Researched:** 2026-03-01
**Domain:** Technical writing, Markdown documentation, codebase archaeology
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- All 8 required docs are written **from scratch** — do not patch or update existing docs
- All existing docs in `docs/` are **moved to `docs/archive/`** after the 8 new docs are written
- Code walkthrough during writing is the source of truth — existing docs may be used as reference but are not trusted for accuracy
- Phases 4 (Student App + Notifications) and 5 (NFC Architecture) are not fully complete at the time Phase 6 executes; docs for those phases are written based on **what is actually shipped in the code**
- When a section covers an unimplemented feature (e.g., FCM push not fully wired), mark it inline with: `Note: [Feature] is not yet implemented.`
- When Phases 4 and 5 complete, `student-app.md` and `nfc-integration-guide.md` should be updated as part of finishing those phases
- **Code is the source of truth.** When code and existing docs disagree, the code wins
- Each doc is verified by **reading the source code it describes** during writing
- All 8 docs are produced in a **single agent pass** (not one at a time with review gates)
- **All 8 docs target developers** — assume technical literacy
- `docs/api-reference.md`: Every REST endpoint gets method, path, request body, response body, auth requirement, and at least one JSON example
- `docs/setup.md`: Step-by-step with exact copy-pasteable commands at every step
- Every relevant doc includes a **troubleshooting section** covering common errors (inline, not a separate doc)

### Claude's Discretion

- Internal formatting/style within each doc (headers, table vs. list for API params, etc.)
- Whether to use fenced code blocks vs. inline code for short commands
- Exact troubleshooting entries chosen (agent identifies common failure points from the code)
- Order of sections within each doc
- Whether to cross-reference between docs

### Deferred Ideas (OUT OF SCOPE)

- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOC-01 | `docs/architecture.md` — system overview, layers, data flow, entry points | `.planning/codebase/ARCHITECTURE.md` + source files; fully mapped, HIGH confidence |
| DOC-02 | `docs/api-reference.md` — all REST API endpoints, request/response format, auth | `backend/api/api_server.py` fully read (984 lines); 12 endpoints identified |
| DOC-03 | `docs/google-sheets-schema.md` — all Sheets structure (columns, purpose, relationships) | Sheets inferred from code: Users, Money Accounts, Transactions Log, Lost Card Reports, Products, VirtualCards, Settings |
| DOC-04 | `docs/cashier-guide.md` — how cashier POS works, Arduino setup, card reading flow | `cashier_routes.py` + `arduino_bridge.py` fully read |
| DOC-05 | `docs/student-app.md` — Android app architecture, screens, API calls | `mobile/student_app_v2/` source read: 12 Kotlin files identified |
| DOC-06 | `docs/nfc-integration-guide.md` — step-by-step guide for implementing NFC in Android (v2 prep) | Existing `docs/nfc-integration-guide.md` (373 lines, written in Phase 5) as reference; rewrite from scratch per decision |
| DOC-07 | `docs/admin-guide.md` — admin dashboard features, roles, product management | `admin_dashboard.py` (2014 lines) partially read; needs full walkthrough during writing |
| DOC-08 | `docs/setup.md` — environment setup, Google Sheets creation, credentials, first run | `.env.example`, `config_validator.py`, `requirements_api.txt` all read; complete picture |
</phase_requirements>

---

## Summary

Phase 6 is a pure documentation task: write 8 Markdown files from scratch by reading the source code that each document describes, then archive the 29 existing docs. The codebase is well-structured (Flask API + admin dashboard + cashier blueprint + Android app) and the planning artifacts (`.planning/codebase/*.md`) provide a reliable starting map, but the agent must verify every claim against current code because those maps were written at project start (2026-02-22) before several phases executed.

The single hardest challenge is `api-reference.md`: `backend/api/api_server.py` is 984 lines with 12 distinct REST endpoints, and each endpoint must be documented with full request/response schemas and at least one JSON example. The Google Sheets schema doc is the second hardest: there are 7 sheets (Users, Money Accounts, Transactions Log, Lost Card Reports, Products, VirtualCards, Settings) and the exact column names are only reliable by reading actual gspread `get_all_records()` calls and `append_row()` calls in the source.

**Primary recommendation:** Execute all 8 docs in a single agent pass, starting with `architecture.md` and `setup.md` (least source-reading required), then `api-reference.md` (most), and ending with `google-sheets-schema.md` (requires synthesizing column names from all files). Move existing docs to `docs/archive/` only after all 8 new docs are written.

---

## Standard Stack

No libraries to install. This phase is 100% Markdown authoring. The output is `.md` files written to `docs/`.

### Doc Format Conventions (Developer Standard)

| Convention | Standard | Rationale |
|-----------|---------|-----------|
| Code blocks | Fenced with language tag (` ```bash`, ` ```json`, ` ```kotlin`) | Enables syntax highlighting in any renderer |
| Command examples | Full copy-paste ready, no `<placeholder>` style — use realistic values | Reduces setup errors |
| API tables | Method + Path + Auth + Description in a table; then request/response details as sub-sections | Standard REST API doc pattern |
| File paths | Always from repo root (e.g., `backend/api/api_server.py`) | Consistent navigation |
| Cross-references | Use relative Markdown links (`[Setup Guide](setup.md)`) | Works in GitHub and local |
| Headers | H1 for title, H2 for major sections, H3 for subsections | Standard depth limit |
| Troubleshooting | H2 section at the bottom of each doc | Consistent location across all docs |

---

## Architecture Patterns

### Recommended Document Structure

```
docs/
├── README.md               # Index: links to all 8 docs + purpose
├── architecture.md         # DOC-01: system overview, layers, data flow
├── setup.md               # DOC-08: environment setup, credentials, first run
├── api-reference.md        # DOC-02: all REST endpoints
├── google-sheets-schema.md # DOC-03: all sheets, columns, relationships
├── cashier-guide.md        # DOC-04: cashier POS + Arduino wiring
├── student-app.md          # DOC-05: Android app architecture
├── nfc-integration-guide.md # DOC-06: NFC HCE implementation for v2
├── admin-guide.md          # DOC-07: admin dashboard features
└── archive/                # All 29 existing docs moved here
```

### Pattern: Write in Code-Read Order

For each doc, the agent should:
1. Read the primary source file(s) listed in CONTEXT.md
2. Extract facts (endpoints, column names, config keys) directly from code
3. Write the doc using only verified facts
4. Add a troubleshooting section based on error handling patterns in the code

This prevents the most common documentation pitfall: writing from memory or from existing (potentially stale) docs.

---

## Source File Map (Critical for Writing)

The agent MUST read these files to write each doc accurately:

### DOC-01: architecture.md
- `.planning/codebase/ARCHITECTURE.md` — comprehensive map (verified against current code)
- `.planning/codebase/STACK.md` — technology stack
- `.planning/codebase/STRUCTURE.md` — directory layout
- `.planning/codebase/INTEGRATIONS.md` — external integrations
- **Key facts to capture:** 5 server layers, 3 entry points, Google Sheets as database, dual-server architecture (API port 5001, Dashboard port 5003), JWT vs session auth split

### DOC-02: api-reference.md
- `backend/api/api_server.py` (984 lines) — ALL 12 endpoints are here
- **Endpoints confirmed in source:**
  1. `GET /api/health` — no auth
  2. `POST /api/auth/login` — no auth; body `{ student_id }`
  3. `POST /api/auth/logout` — session token (Bearer)
  4. `GET /api/student/profile` — session token (Bearer)
  5. `GET /api/student/balance` — session token (Bearer)
  6. `GET /api/student/transactions?limit=20&offset=0` — session token (Bearer)
  7. `POST /api/users/fcm-token` — session token (Bearer)
  8. `GET /api/products?category=Food` — no auth (open)
  9. `POST /api/products` — JWT (admin/cashier role)
  10. `POST /api/cashier/transaction` — JWT (admin/cashier role)
  11. `POST /api/nfc/register` — session token (Bearer)
  12. `POST /api/nfc/pay` — JWT (admin/cashier) + `X-Device-Token` header
- **Auth system NOTE:** Two parallel auth mechanisms exist:
  - `active_sessions` dict (session tokens) — used by student endpoints
  - `@require_auth` JWT decorator — used by cashier/admin endpoints
  - NFC register uses session token; NFC pay uses JWT + X-Device-Token
- **Port:** 5001 (env `API_PORT`)

### DOC-03: google-sheets-schema.md
- `backend/api/api_server.py` — primary source for column names
- `backend/dashboard/admin_dashboard.py` — Products sheet creation
- `backend/nfc_payments.py` — VirtualCards sheet creation
- **Sheets confirmed in code:**
  1. **Users** — columns: `StudentID, Name, IDCardNumber, MoneyCardNumber, Status, ParentEmail, DateRegistered, FCMToken` (FCMToken added in Phase 4)
  2. **Money Accounts** — columns: `MoneyCardNumber, StudentIDCard(?), Balance, Status, LastUpdated`; column C = Balance (hardcoded `update_cell(row, 3, balance)`)
  3. **Transactions Log** — columns: `Timestamp, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ItemsJson` (8 cols; NFC Pay writes 7 without Status)
  4. **Lost Card Reports** — referenced in docs/context; not directly written by current code but exists per original schema
  5. **Products** — columns: `ID, Name, Category, Price, ImageURL, Active, DateAdded` (from `ensure_products_sheet()` in admin_dashboard.py)
  6. **VirtualCards** — columns: `StudentID, VirtualCardToken, DeviceToken, MoneyCardNumber, CreatedAt, IsActive` (from `nfc_payments.py` VIRTUAL_CARDS_HEADERS)
  7. **Settings** — columns: `Key, Value` (read in api_server.py for `low_balance_threshold`)
- **CRITICAL PITFALL:** Transactions Log column layout differs slightly between cashier_routes.py and api_server.py — cashier writes 7 columns (no BalanceBefore at position 5), api_server writes 8. The agent must document both variants and note the discrepancy.
- **Card UID format:** 8 hex chars uppercase, e.g., `ABCD1234` (regex `^[0-9A-Fa-f]{8}$`)

### DOC-04: cashier-guide.md
- `backend/dashboard/cashier/cashier_routes.py` (385 lines) — full POS flow
- `backend/dashboard/arduino_bridge.py` (101 lines) — serial protocol
- `docs/context.md` (existing doc in repo) — hardware wiring (from original project context)
- **Cashier endpoints (at `/cashier/*` prefix):**
  - `GET /cashier/login` — login page
  - `POST /cashier/api/login` — credentials: `cashier`/`cashier123` (hardcoded)
  - `POST /cashier/api/logout`
  - `GET /cashier/api/ports` — list COM ports
  - `POST /cashier/api/connect-arduino` — body `{ port }`
  - `GET /cashier/api/products` — product grid
  - `POST /cashier/api/process-sale` — body `{ items, total }`; starts card reading
  - `POST /cashier/api/complete-sale` — body `{ card_uid }`; finalizes transaction
- **Serial protocol:** Arduino sends `<CARD|ABCD1234>` over serial at 9600 baud
- **Card read timeout:** 5 seconds (hardcoded in `ArduinoBridge`)
- **Arduino wiring (from docs/context.md):** RC522 on SPI (SS=pin10, RST=pin9, MOSI=11, MISO=12, SCK=13, VCC=**3.3V CRITICAL**)
- **Transaction flow:** `process-sale` stores pending transaction in Flask session → WebSocket `cashier_request_card` event → Arduino bridge reads card → `complete-sale` called with card_uid → balance deducted → transaction logged

### DOC-05: student-app.md
- `mobile/student_app_v2/` (12 Kotlin files)
- `ApiClient.kt` — Retrofit interface, BASE_URL hardcoded to `192.168.68.104:5001`
- `Models.kt` — all request/response DTOs
- `HomeActivity.kt`, `LoginActivity.kt`, `TransactionsActivity.kt`, `ReceiptActivity.kt` — screens
- `FCMService.kt` — push notifications
- `SecureStorage.kt` — encrypted SharedPreferences
- **Key architectural facts:**
  - BASE_URL is hardcoded in `ApiClient.kt:38` — must be changed for each deployment
  - All API calls: `GET /api/student/balance`, `GET /api/student/transactions`, `POST /api/auth/login`, `POST /api/auth/logout`, `POST /api/users/fcm-token`
  - Session token stored in `EncryptedSharedPreferences` (not JWT; the API returns a session token)
  - `getTransactions` uses `limit=20, offset=0` (changed from 50 in Phase 4)
  - `google-services.json` required for FCM (present in repo — note this is unusual, usually gitignored)
  - Thai Baht ฿ symbol used throughout (Phase 4-05 fix)

### DOC-06: nfc-integration-guide.md
- `backend/nfc_payments.py` — NFCService class, VirtualCards sheet operations
- `docs/nfc-integration-guide.md` — existing Phase 5 guide (use as reference, rewrite from scratch)
- `backend/api/api_server.py:497-651` — nfc_register and nfc_pay endpoint implementations
- **Key content to preserve from existing guide:** BankoHceService Kotlin snippet, AID constant (`F049494F4E41`), APDU response format (`virtual_card_token|device_token` + `0x9000`), sequence diagram

### DOC-07: admin-guide.md
- `backend/dashboard/admin_dashboard.py` (2014 lines) — must be walked during writing
- Focus on: admin vs. finance roles, product management, student management, transaction monitoring, settings configuration
- **CRITICAL:** Agent must read `admin_dashboard.py` lines 200+ during writing to accurately list features (not done in research phase due to file size)

### DOC-08: setup.md
- `.env.example` — all 17 environment variables with comments
- `backend/api/requirements_api.txt` — API dependencies
- `backend/dashboard/requirements.txt` — dashboard dependencies
- `config/credentials.json` path (not committed; setup doc must explain how to create it)
- `backend/config_validator.py` — startup validation checks
- **Two servers to start:**
  1. `python backend/api/api_server.py` — port 5001
  2. `python backend/dashboard/admin_dashboard.py` — port 5003
- **Google Sheets setup:** Create spreadsheet → enable Sheets API → create service account → download JSON → rename to `credentials.json` → place in `config/` → share sheet with service account email
- **Required sheets to create manually** (none are auto-created on first run except Products and VirtualCards)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Doc index | Manual navigation | `docs/README.md` with table linking all 8 docs | Consistent entry point |
| API param description | Prose paragraphs | Markdown tables (Method\|Path\|Auth\|Description) | Scannable by developers |
| Sheet column listing | Prose description | Markdown tables with column\|type\|description\|notes | Matches how devs reference schemas |
| Wiring diagram | ASCII art from scratch | Reference existing `docs/context.md` hardware section | Already correct and complete |
| JSON examples | Pseudocode | Actual JSON with realistic values | Devs copy-paste directly |

---

## Common Pitfalls

### Pitfall 1: Trusting Existing Docs for Column Names
**What goes wrong:** Writing `google-sheets-schema.md` based on `docs/GOOGLE_SHEETS_FORMAT.md` or `docs/context.md` which may reflect original design, not current code.
**Why it happens:** Existing docs were written before Phases 1-5 changed the schema (added FCMToken column, BalanceBefore column, VirtualCards sheet, Settings sheet, Products sheet).
**How to avoid:** Read `append_row()` calls and `get_all_records()` field accesses in `api_server.py`, `cashier_routes.py`, and `nfc_payments.py` — these are the ground truth.
**Warning signs:** If a column name isn't referenced in any Python file, it's suspect.

### Pitfall 2: Confusing Session Tokens with JWT Tokens
**What goes wrong:** `api-reference.md` labels all auth as "JWT Bearer token" when student endpoints actually use session tokens from `active_sessions` dict (not JWT).
**Why it happens:** Both use `Authorization: Bearer <token>` header but they are validated differently (dict lookup vs. `jwt.decode()`).
**How to avoid:** For each endpoint, read whether it checks `token not in active_sessions` (session auth) or uses `@require_auth` decorator (JWT auth). Document them distinctly.
**Warning signs:** `/api/auth/login` returns `token` (session token); `/api/nfc/pay` uses `@require_auth` (JWT).

### Pitfall 3: Missing the Dual Transaction Log Format
**What goes wrong:** `google-sheets-schema.md` shows one Transactions Log column layout when there are actually two code paths that write different numbers of columns.
**Why it happens:** `cashier_routes.py:307-314` writes 7 columns (no BalanceBefore at index 5); `api_server.py:850-858` writes 8 columns (has BalanceBefore); NFC pay writes 7 columns in a different order.
**How to avoid:** Document all three write paths with the actual column indices. Note the inconsistency explicitly.
**Warning signs:** `BalanceBefore` appears in `api_server.py` transactions but not in all cashier transactions.

### Pitfall 4: Hardcoded Cashier Credentials
**What goes wrong:** `cashier-guide.md` omits mentioning that cashier login credentials (`cashier`/`cashier123`) are hardcoded in `cashier_routes.py:69`.
**Why it happens:** Easy to overlook when documenting the flow.
**How to avoid:** Note this explicitly as a known limitation / security concern in the cashier guide. Advise changing before deployment.

### Pitfall 5: BASE_URL in Android App
**What goes wrong:** `student-app.md` doesn't mention that `ApiClient.kt:38` has a hardcoded IP address (`192.168.68.104:5001`) that must be changed for any deployment.
**Why it happens:** It's easy to treat it as a config detail.
**How to avoid:** Call it out prominently in setup section of `student-app.md`. Reference `BASE_URL_SETUP.md` that already exists in the mobile directory.

### Pitfall 6: FCMToken Column Not Present in Fresh Sheets
**What goes wrong:** `setup.md` implies the Users sheet works out-of-the-box, but FCMToken column must be manually added (it was added as a migration in Phase 4, not via schema auto-creation).
**Why it happens:** Column was added via migration, not in initial sheet setup instructions.
**How to avoid:** Setup doc must explicitly list all columns for each sheet that the developer must create manually, including FCMToken in Users.

### Pitfall 7: Two Separate Flask Servers
**What goes wrong:** `setup.md` or `architecture.md` implies there is one server when there are actually two: API (port 5001) and Admin Dashboard (port 5003), both must run simultaneously.
**Why it happens:** Single-server assumption.
**How to avoid:** Be explicit: "Run both servers in separate terminals. The Android app connects to port 5001. The cashier POS and admin dashboard connect to port 5003."

---

## Code Examples

### API Auth Pattern (Two Types)

```python
# Session token auth (student endpoints) — api_server.py:324-327
token = request.headers.get('Authorization', '').replace('Bearer ', '')
if token not in active_sessions:
    return jsonify({'error': 'Invalid or expired token'}), 401

# JWT auth (cashier/admin endpoints) — api_server.py:123-146
@require_auth(roles=['admin', 'cashier'])
def protected_endpoint():
    # request.user contains JWT payload
    ...
```

### Actual API Response for Login (from api_server.py:230-238)

```json
{
  "token": "abc123...",
  "student": {
    "id": "202501",
    "name": "Juan dela Cruz",
    "id_card": "ABCD1234",
    "money_card": "EF012345",
    "status": "Active"
  }
}
```

### VirtualCards Sheet Headers (from nfc_payments.py:30-37)

```python
VIRTUAL_CARDS_HEADERS = [
    'StudentID', 'VirtualCardToken', 'DeviceToken',
    'MoneyCardNumber', 'CreatedAt', 'IsActive'
]
```

### Products Sheet Headers (from admin_dashboard.py:153)

```python
['ID', 'Name', 'Category', 'Price', 'ImageURL', 'Active', 'DateAdded']
```

### Serial Protocol (from arduino_bridge.py:65-67)

```
# Expected format from Arduino:
<CARD|ABCD1234>
# Where ABCD1234 is the 8-hex-char card UID
```

### Transaction Row Written by api_server.py (api_server.py:850-858)

```python
transaction_row = [
    timestamp,         # col 1: Timestamp
    normalized_card,   # col 2: MoneyCardNumber
    'Purchase',        # col 3: TransactionType
    -total,            # col 4: Amount (negative = debit)
    current_balance,   # col 5: BalanceBefore
    new_balance,       # col 6: BalanceAfter
    'Success',         # col 7: Status
    json.dumps(items)  # col 8: ItemsJson
]
```

### Transaction Row Written by cashier_routes.py (cashier_routes.py:307-314)

```python
transaction_row = [
    timestamp,         # col 1: Timestamp
    normalized_card,   # col 2: MoneyCardNumber
    'Purchase',        # col 3: TransactionType
    -total,            # col 4: Amount (negative)
    new_balance,       # col 5: BalanceAfter (NOTE: no BalanceBefore here)
    'Success',         # col 6: Status
    json.dumps(items)  # col 7: ItemsJson
]
```

---

## State of the Art

| Old Pattern | Current Pattern | Changed In | Impact on Docs |
|-------------|----------------|------------|----------------|
| oauth2client auth | google-auth (Credentials.from_service_account_file) | Phase 2 (QUAL-05) | Setup doc must use `google-auth` install, not `oauth2client` |
| Single Products fallback (products.json) | Products Google Sheet with fallback to products.json | Phase 1 bug fix | api-reference.md documents Products sheet as primary |
| BalanceBefore absent from Transactions Log | BalanceBefore at column 5 (api_server.py) | Phase 4 (APP-03) | google-sheets-schema.md must note this column |
| getTransactions page size = 50 | Changed to 20 (Phase 4-04 decision) | Phase 4 | student-app.md documents `limit=20` |
| active_sessions not checked for lost card | Lost card check invalidates session | Phase 1 | api-reference.md notes card_status guard |
| FCMToken absent from Users | FCMToken column added in Phase 4 | Phase 4 | setup.md must include FCMToken in Users sheet column list |

---

## Open Questions

1. **Transactions Log column layout inconsistency**
   - What we know: `cashier_routes.py` writes 7 columns (no BalanceBefore); `api_server.py` writes 8 (with BalanceBefore); NFC pay writes 7 (different order)
   - What's unclear: Is this intentional? Does the sheet always have all 8 columns?
   - Recommendation: Document all three write paths in `google-sheets-schema.md`. Planner should add a task to read existing production sheet headers to confirm actual column count. For now, document that the sheet should have 8 columns and note that cashier transactions may have empty BalanceBefore.

2. **Admin dashboard (admin_dashboard.py) not fully read**
   - What we know: File is 2014 lines. Lines 1-199 read. Routes for admin features (product CRUD, student management, load balance, etc.) are in the unread section.
   - What's unclear: Exact routes, admin vs. finance role split, any routes not in the planning codebase map
   - Recommendation: Writing task for `admin-guide.md` must include reading lines 200-2014 of `admin_dashboard.py`. Planner should flag this as the largest single-file source read in the phase.

3. **Lost Card Reports sheet in use?**
   - What we know: Described in original `docs/context.md` schema. Not directly written by any code read in this research session.
   - What's unclear: Whether the sheet exists, whether any Python code currently writes to it
   - Recommendation: During writing, search `admin_dashboard.py` for `Lost Card Reports` to confirm. If not actively used by current code, document it as "designed but not yet implemented" in `google-sheets-schema.md`.

4. **google-services.json committed to repo**
   - What we know: `mobile/student_app_v2/google-services.json` exists in the repository tree.
   - What's unclear: Whether it contains real credentials or a placeholder
   - Recommendation: `student-app.md` and `setup.md` should note that developers need their own `google-services.json` from their Firebase project. Flag this for review if real credentials are in the repo.

---

## Execution Order Recommendation

The planner should order tasks to minimize context-switching and enable natural cross-referencing:

1. **`docs/architecture.md`** (DOC-01) — reads `.planning/codebase/*.md`; writes first, establishes vocabulary
2. **`docs/setup.md`** (DOC-08) — reads `.env.example`, requirements files; references architecture.md
3. **`docs/google-sheets-schema.md`** (DOC-03) — reads api_server.py + nfc_payments.py + admin_dashboard.py for column names
4. **`docs/api-reference.md`** (DOC-02) — reads api_server.py (full 984 lines); most content-dense doc
5. **`docs/cashier-guide.md`** (DOC-04) — reads cashier_routes.py + arduino_bridge.py
6. **`docs/admin-guide.md`** (DOC-07) — reads admin_dashboard.py lines 200-2014
7. **`docs/student-app.md`** (DOC-05) — reads mobile/student_app_v2/ Kotlin files
8. **`docs/nfc-integration-guide.md`** (DOC-06) — reads nfc_payments.py + existing guide as reference
9. **`docs/README.md`** — index written last, links to all 8 completed docs
10. **Move existing docs to `docs/archive/`** — done last, after all 8 are written and verified

---

## Sources

### Primary (HIGH confidence)
- `backend/api/api_server.py` — 984 lines, all 12 endpoints verified by reading source
- `backend/dashboard/cashier/cashier_routes.py` — 385 lines, all cashier routes read
- `backend/dashboard/arduino_bridge.py` — 101 lines, serial protocol confirmed
- `backend/nfc_payments.py` — 80 lines read, VirtualCards schema confirmed
- `backend/dashboard/admin_dashboard.py` — lines 1-199 read, full file requires reading during writing
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/ApiClient.kt` — Retrofit interface confirmed
- `mobile/student_app_v2/app/src/main/java/com/bankongseton/student/Models.kt` — DTOs confirmed
- `.env.example` — all 17 env vars confirmed
- `.planning/codebase/ARCHITECTURE.md` — architecture map (written 2026-02-22, verified)
- `.planning/codebase/STACK.md` — stack map (written 2026-02-22, verified)
- `.planning/codebase/STRUCTURE.md` — directory map (written 2026-02-22, verified)
- `.planning/codebase/INTEGRATIONS.md` — integrations map (written 2026-02-22, verified)
- `docs/nfc-integration-guide.md` — existing Phase 5 guide (373 lines, written from source)

### Secondary (MEDIUM confidence)
- `docs/context.md` — original hardware spec (Arduino wiring); verified against arduino_bridge.py serial expectations

### Tertiary (LOW confidence — verify during writing)
- Lost Card Reports sheet existence and current usage — not confirmed by code read in this session
- `admin_dashboard.py` lines 200-2014 — not read; admin routes and role-split assumed from ARCHITECTURE.md

---

## Metadata

**Confidence breakdown:**
- API endpoints: HIGH — all 12 endpoints confirmed by reading api_server.py line by line
- Google Sheets schema: HIGH for 4 sheets (Users, Money Accounts, Transactions Log, Products, VirtualCards, Settings); MEDIUM for Lost Card Reports (not confirmed by current code)
- Android app: HIGH — 12 Kotlin files listed; ApiClient and Models read in full
- Arduino/cashier flow: HIGH — cashier_routes.py and arduino_bridge.py fully read
- Admin dashboard: MEDIUM — file is 2014 lines, only first 199 lines read; requires code walkthrough during writing

**Research date:** 2026-03-01
**Valid until:** 2026-04-01 (stable codebase — no active development expected before Phase 6 executes)
