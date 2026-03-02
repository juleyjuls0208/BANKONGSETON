# Phase 12: Receipt & FCM Wiring - Research

**Researched:** 2026-03-02
**Domain:** Python/Flask backend code inspection — transaction row schema, FCM wiring, startup migration
**Confidence:** HIGH (direct code inspection of all 5 source files listed in CONTEXT.md)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Transaction row schema
- Accept the current 11-column format as correct — do NOT trim to 8 columns
- The 11-column schema is: `TransactionID, Timestamp, StudentID, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ErrorMessage, ItemsJson`
- BalanceBefore at position 7 (1-indexed) is acceptable; Android API reads by header name, not column index
- Verify all 11 columns are present and in the correct order in the code
- Verify the Transactions Google Sheet header row matches the 11-column structure
- Update `backend/config_validator.py` to reflect the actual 11-column schema (currently hardcoded as 8 columns)

#### Verification standard
- Static code inspection only — no live end-to-end testing required for this phase
- Document exact line numbers for each verified feature (e.g. "BalanceBefore at `cashier_routes.py:527`")
- Output per-requirement status: APP-03, NOTF-01, and `migrate_users_schema` startup each get VERIFIED / BROKEN / PARTIAL with code evidence
- If anything is found broken during inspection: fix it within the same plan run, then re-run inspection and update status to VERIFIED

#### FCM notification scope
- Preserve both FCM pushes in `cashier_routes.py`: (1) purchase confirmation push on every successful sale, (2) low-balance push when `new_balance < threshold`
- NOTF-01 formally requires only the low-balance push; the purchase push is a beneficial addition — keep it
- Explicitly verify that FCM failures are non-blocking: a failed push must never roll back or prevent the sale from completing
- FCM verification scope for this phase: `cashier_routes.py` only (the "cashier POS" path per NOTF-01). How to handle `api_server.py` and `admin_dashboard.py` FCM paths is left to Claude's discretion — they already have the pattern from earlier phases

#### Contradiction resolution
- The Integration Audit was written before Phase 7 fixed the gaps; the contradiction is expected
- Cross-check whether Phase 11 (cashier security hardening) introduced the line number shift (Phase 7 VERIFICATION referenced lines 307-316; current code is at ~527) — confirm features survived Phase 11's credential removal
- The verification report should explicitly document that the Integration Audit predates Phase 7, explaining the contradiction's origin
- After verifying APP-03 and NOTF-01 are present, update `INTEGRATION_AUDIT.md` to mark both requirements as resolved with a reference to the Phase 12 verification

### Claude's Discretion
- Whether to treat `api_server.py` and `admin_dashboard.py` FCM paths as in-scope for this phase's verification (NOTF-01 specifies cashier POS, but noting their presence would be useful)
- Exact format of the resolution note added to `INTEGRATION_AUDIT.md`
- Approach for tracing the Phase 11 vs Phase 7 line number change (git blame vs manual diff)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| APP-03 | Student can tap a canteen purchase transaction and see the itemized receipt (what was bought, price per item, total) | Requires `ItemsJson` column in transaction row (col 11) and BalanceBefore populated. Direct inspection shows both are **ALREADY PRESENT** in `cashier_routes.py:520-532`. |
| NOTF-01 | Student receives a push notification when their balance drops below a configurable threshold | Requires `send_low_balance_push()` called from `complete_sale` when `new_balance < threshold`. Direct inspection shows this is **ALREADY PRESENT** in `cashier_routes.py:606-609`, and `migrate_users_schema()` is called at `api_server.py:111-113`. |
</phase_requirements>

---

## Summary

Direct code inspection of all five named source files confirms that **Phase 7 already fixed both APP-03 and NOTF-01**. The Integration Audit's claims of "FCM never called from cashier" and "7-column cashier writes missing BalanceBefore" were accurate at the time of audit (2026-03-01) but were resolved by Phase 7. The line number shift from ~307 to ~527 is a confirmed side-effect of Phase 11's credential-removal refactor (the `_init_cashier_credentials` callback block and related guard code was inserted at the top of the file, pushing all route handlers down ~220 lines).

The only **real gap** uncovered is in `config_validator.py`: the `Transactions Log` schema definition at lines 235-237 lists 10 columns (missing `ItemsJson`), while the actual `cashier_routes.py` transaction row writes 11 columns. The CONTEXT.md states this is "currently hardcoded as 8 columns" — inspection shows it's actually 10. Regardless, it needs `ItemsJson` added to make it match the runtime 11-column schema. This is the sole code change required for this phase.

The migration startup call at `api_server.py:110-115` is present and non-fatal (wrapped in try/except). No fix needed there.

**Primary recommendation:** This phase is almost entirely a documentation/verification exercise. The one code change is adding `'ItemsJson'` to the `Transactions Log` column list in `config_validator.py` line 237. The rest is: write VERIFICATION.md with exact line-number evidence, update INTEGRATION_AUDIT.md to mark APP-03 and NOTF-01 as resolved.

---

## Exact Code State (Direct Inspection Results)

### Finding 1: Transaction Row — 11 Columns Present ✅ VERIFIED

**File:** `backend/dashboard/cashier/cashier_routes.py`
**Lines:** 520–532

```python
transaction_row = [
    transaction_id,       # col 1: TransactionID (TXN-...)
    timestamp,            # col 2: Timestamp
    resolved_student_id,  # col 3: StudentID
    normalized_card,      # col 4: MoneyCardNumber
    transaction_type,     # col 5: TransactionType ('Manual' or 'Purchase')
    total,                # col 6: Amount (positive deduction value)
    current_balance,      # col 7: BalanceBefore  ← APP-03 requires this
    new_balance,          # col 8: BalanceAfter
    "Completed",          # col 9: Status
    "",                   # col 10: ErrorMessage
    json.dumps(items),    # col 11: ItemsJson     ← APP-03 requires this
]
```

**Status:** APP-03 — VERIFIED. All 11 columns present. BalanceBefore at column 7 (1-indexed). ItemsJson at column 11.

**Line shift explanation:** Phase 7 VERIFICATION cited lines 307-316. Current code is at lines 520-532. The ~220-line shift was introduced by Phase 11 (cashier security hardening), which inserted `_init_cashier_credentials()` callback function, `_get_parent_app_module()` helper, `get_worksheet_with_retry()`, and `ensure_products_sheet()` at the top of the file, before the route handlers.

---

### Finding 2: FCM Calls in complete_sale — Both Pushes Present ✅ VERIFIED

**File:** `backend/dashboard/cashier/cashier_routes.py`
**Lines:** 570–612

```python
# FCM purchase push (always) + low-balance push (if threshold breached)
# Never blocks or rolls back the transaction response
try:
    threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
    # [threshold read from Settings sheet with fallback to env var]
    # [FCM token lookup from Users sheet]
    if fcm_token:
        from fcm_sender import send_purchase_push
        send_purchase_push(fcm_token, total, new_balance)    # line ~605
        if new_balance < threshold:
            from fcm_sender import send_low_balance_push
            send_low_balance_push(fcm_token, new_balance)    # line ~609
    break
except Exception as notif_error:
    logger.warning("event=low_balance_notify_failed error=%s", notif_error)
```

**Status:** NOTF-01 — VERIFIED.
- `send_low_balance_push()` called when `new_balance < threshold` ✅
- `send_purchase_push()` called on every successful sale ✅
- Entire FCM block wrapped in `try/except Exception` — failures are non-blocking ✅
- Transaction response (`return jsonify(...)` at line 643) only reached after FCM block completes or fails safely ✅

**FCM path import:** `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))` then `from fcm_sender import send_purchase_push` — this correctly resolves to `backend/api/fcm_sender.py`.

---

### Finding 3: migrate_users_schema() at api_server startup ✅ VERIFIED

**File:** `backend/api/api_server.py`
**Lines:** 109–115

```python
# Run schema migration at startup (idempotent — skips if all columns exist)
try:
    from migrate_transactions import migrate_users_schema
    migrate_users_schema()
except Exception as _mig_err:
    logger.warning("event=migrate_users_startup_failed error=%s", _mig_err)
```

**Status:** VERIFIED. Called unconditionally at module load time after `db = get_sheets_client()`. Non-fatal try/except ensures Sheets API outage at startup logs a warning but never crashes the server.

---

### Finding 4: config_validator.py Transactions Schema — NEEDS UPDATE ⚠️

**File:** `backend/config_validator.py`
**Lines:** 235–237

```python
'Transactions Log': ['TransactionID', 'Timestamp', 'StudentID', 
                     'MoneyCardNumber', 'TransactionType', 'Amount', 
                     'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage'],
```

**Current count:** 10 columns (missing `ItemsJson`)
**Runtime actual:** 11 columns (`cashier_routes.py` writes `ItemsJson` as column 11)

**NOTE:** The CONTEXT.md states "currently hardcoded as 8 columns" — this is outdated. The file already has 10 columns (BalanceBefore and BalanceAfter were added at some prior phase). The only missing column is `ItemsJson`.

**Required fix:** Add `'ItemsJson'` to the end of the `Transactions Log` column list.

---

### Finding 5: fcm_sender.py Functions — Both Present ✅

**File:** `backend/api/fcm_sender.py`

| Function | Purpose | Signature |
|----------|---------|-----------|
| `send_low_balance_push(fcm_token, balance)` | Low-balance alert | Returns `bool`, never raises |
| `send_purchase_push(fcm_token, amount, new_balance)` | Purchase confirmation | Returns `bool`, never raises |
| `send_load_push(fcm_token, amount, new_balance)` | Money loaded alert | Returns `bool`, never raises |

All three functions: lazy `firebase_admin` import inside function body, `_init_firebase()` guard against double-init, full `try/except` wrapping that catches `UnregisteredError` (stale FCM token) and all other Firebase errors. Firebase credentials loaded from `config/firebase-credentials.json` relative to `backend/`.

---

## Architecture Patterns

### Pattern: Contradiction Resolution Documentation

This phase resolves a documented contradiction between two reports. The VERIFICATION.md must:
1. State the contradiction explicitly (Integration Audit 2026-03-01 claimed X; Phase 7 VERIFICATION claimed Y)
2. Explain the origin (audit predates Phase 7 fixes)
3. Provide line-number evidence for current state
4. Note the Phase 11 line-shift as explanation for why line numbers changed

### Pattern: INTEGRATION_AUDIT.md Update Format

The audit has two sections (Part 1 dated 2026-03-01, Part 2 dated 2026-03-02). APP-03 and NOTF-01 appear in Part 1 requirements table. The update should:
- Change `🔴 BROKEN` to `✅ VERIFIED` for APP-03 and NOTF-01 entries in the requirements table
- Add a resolution note referencing Phase 12 VERIFICATION.md
- Update the Break 3 description under Flow 1 (NOTF-01) to note it was fixed in Phase 7

### Pattern: config_validator.py Schema Update

The `required_schema` dict at line 230 is a plain Python dict literal. Adding `ItemsJson`:

```python
'Transactions Log': ['TransactionID', 'Timestamp', 'StudentID',
                     'MoneyCardNumber', 'TransactionType', 'Amount',
                     'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage',
                     'ItemsJson'],  # ← add this
```

The validator uses subset checking (`[col for col in expected_columns if col not in actual_columns]`), so adding `ItemsJson` to the expected list means validation will warn if the Sheets header row is missing it. This is the desired behavior.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Verifying code features | Runtime test harness | Direct static code inspection | Phase is inspection-only; CONTEXT.md explicitly requires static inspection with line numbers |
| FCM error handling | Custom retry logic | Existing `try/except` in `fcm_sender.py` | Already correct and non-blocking |
| Schema validation logic | New validator | Update existing `config_validator.py` dict | Only one line needs changing |

---

## Common Pitfalls

### Pitfall 1: Misreading "8 columns" in CONTEXT.md
**What goes wrong:** Treating "currently hardcoded as 8 columns" in CONTEXT.md as ground truth and looking for an 8-column list.
**Why it happens:** CONTEXT.md was written from memory of older audit; the audit itself may have cited "8 columns" from the *old* cashier_routes, not the current config_validator.py state.
**How to avoid:** Direct file inspection confirms 10 columns currently in config_validator.py (lines 235-237). The fix adds 1 column (`ItemsJson`), not 3.
**Warning signs:** If you can't find an 8-column list, you're not looking at stale data — you're looking at the current correct file.

### Pitfall 2: Assuming FCM block must be inside the transaction's try/except
**What goes wrong:** Moving the FCM block to be inside the retry loop, making FCM failures potentially roll back the transaction.
**Why it happens:** Looks like FCM should be "part of" the sale.
**How to avoid:** FCM block (lines 570-612) is correctly placed AFTER `flask_session.pop("pending_transaction", None)` (line 568) and BEFORE `return jsonify(...)` (line 643). It is a separate, non-transactional side effect. Do not move it inside the retry loop.
**Warning signs:** Any `return` statement inside the FCM try block that doesn't return 200 would be a bug.

### Pitfall 3: Attempting git blame for line-shift investigation
**What goes wrong:** Spending time on git history forensics when the shift is already explained by Phase 11's known inserts.
**Why it happens:** CONTEXT.md mentions "git blame vs manual diff" as discretionary approach.
**How to avoid:** The line shift is obvious from reading the file: ~220 lines of `_init_cashier_credentials`, `_get_parent_app_module`, `get_worksheet_with_retry`, `ensure_products_sheet` functions were inserted between line 40 and the original route handlers. No git archaeology needed.

### Pitfall 4: Updating the wrong INTEGRATION_AUDIT.md table
**What goes wrong:** Updating only the executive summary or only one of the two tables, missing the requirements map.
**Why it happens:** The file has two parts (2026-03-01 and 2026-03-02 audits) with overlapping requirement rows.
**How to avoid:** Search for `APP-03` and `NOTF-01` in both the Part 1 requirements table (around lines 270-273) and the Part 2 requirements table (around line 567). Note that APP-03 and NOTF-01 are only in Part 1 (Part 2 audit used different requirement group labels). Update both the status icon and the description in the Part 1 table only.

---

## Code Examples

### The complete_sale transaction_row (verified, current)
```python
# Source: backend/dashboard/cashier/cashier_routes.py lines 520-532
transaction_row = [
    transaction_id,       # TransactionID
    timestamp,            # Timestamp
    resolved_student_id,  # StudentID
    normalized_card,      # MoneyCardNumber
    transaction_type,     # TransactionType
    total,                # Amount
    current_balance,      # BalanceBefore   ← col 7 (1-indexed)
    new_balance,          # BalanceAfter
    "Completed",          # Status
    "",                   # ErrorMessage
    json.dumps(items),    # ItemsJson       ← col 11 (1-indexed)
]
```

### The FCM block (verified, current, non-blocking)
```python
# Source: backend/dashboard/cashier/cashier_routes.py lines 570-612
# This block is AFTER session.pop() and BEFORE return jsonify() — never blocks sale
try:
    threshold = float(os.getenv("LOW_BALANCE_THRESHOLD", 50))
    try:
        # Read threshold from Settings sheet (per-run, not cached)
        settings_sheet = db.worksheet("Settings")
        settings_records = settings_sheet.get_all_records()
        for row in settings_records:
            if str(row.get("Key", "")).strip().lower() == "low_balance_threshold":
                threshold = float(row.get("Value", threshold))
                break
    except Exception as settings_err:
        logger.warning("event=settings_read_failed ...")
    users_sheet2 = db.worksheet("Users")
    user_records2 = users_sheet2.get_all_records()
    for user in user_records2:
        if normalize_card_uid(user.get("MoneyCardNumber", "")) == normalized_card:
            fcm_token = str(user.get("FCMToken", "")).strip()
            if fcm_token:
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "api"))
                from fcm_sender import send_purchase_push
                send_purchase_push(fcm_token, total, new_balance)     # purchase push (always)
                if new_balance < threshold:
                    from fcm_sender import send_low_balance_push
                    send_low_balance_push(fcm_token, new_balance)     # low-balance push (conditional)
            break
except Exception as notif_error:
    logger.warning("event=low_balance_notify_failed error=%s", notif_error)
# Sale completes regardless of FCM outcome ↓
return jsonify({"success": True, "new_balance": new_balance, "timestamp": timestamp})
```

### The config_validator.py fix
```python
# Source: backend/config_validator.py lines 235-237 (current — needs update)
# CURRENT (10 columns, missing ItemsJson):
'Transactions Log': ['TransactionID', 'Timestamp', 'StudentID',
                     'MoneyCardNumber', 'TransactionType', 'Amount',
                     'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage'],

# AFTER FIX (11 columns, matches runtime):
'Transactions Log': ['TransactionID', 'Timestamp', 'StudentID',
                     'MoneyCardNumber', 'TransactionType', 'Amount',
                     'BalanceBefore', 'BalanceAfter', 'Status', 'ErrorMessage',
                     'ItemsJson'],
```

### The migrate_users_schema startup (verified, current)
```python
# Source: backend/api/api_server.py lines 109-115
# Run schema migration at startup (idempotent — skips if all columns exist)
try:
    from migrate_transactions import migrate_users_schema
    migrate_users_schema()
except Exception as _mig_err:
    logger.warning("event=migrate_users_startup_failed error=%s", _mig_err)
```

---

## Verification Deliverables This Phase Must Produce

Based on CONTEXT.md locked decisions, this phase must produce:

| Deliverable | Location | Content |
|-------------|----------|---------|
| VERIFICATION.md | `.planning/phases/12-receipt-fcm-wiring/12-VERIFICATION.md` | Per-requirement status with exact line number evidence |
| config_validator.py fix | `backend/config_validator.py:237` | Add `'ItemsJson'` to Transactions Log column list |
| INTEGRATION_AUDIT.md update | `.planning/INTEGRATION_AUDIT.md` | Mark APP-03 and NOTF-01 as resolved, cite Phase 12 verification |

---

## Open Questions

1. **Should the Transactions Google Sheet header row also be verified?**
   - What we know: `config_validator.py` validates headers against the live sheet. The validator runs during setup (`python config_validator.py`), not at runtime.
   - What's unclear: We cannot inspect the live Google Sheet header row in this static research phase.
   - Recommendation: CONTEXT.md says "Verify the Transactions Google Sheet header row matches the 11-column structure" — acknowledge this as requiring runtime access and note it in VERIFICATION.md as "cannot be verified statically; validator will confirm on next run."

2. **`api_server.py` and `admin_dashboard.py` FCM paths — are they in scope?**
   - What we know: Both files call FCM functions. `api_server.py` calls `send_low_balance_push` from `process_cashier_transaction`. This is in addition to the cashier path.
   - What's unclear: CONTEXT.md says scope is `cashier_routes.py` only, but noting their presence would be useful.
   - Recommendation: Note them in VERIFICATION.md as "in-scope for completeness" — NOTF-01 specifies cashier POS; `api_server.py` FCM is an additional verified path, not required for NOTF-01 satisfaction.

---

## Sources

### Primary (HIGH confidence)
- Direct file read: `backend/dashboard/cashier/cashier_routes.py` — full file, 658 lines, all route handlers inspected
- Direct file read: `backend/api/api_server.py` — lines 100-149, startup sequence verified
- Direct file read: `backend/config_validator.py` — lines 225-270, schema definition verified
- Direct file read: `backend/api/fcm_sender.py` — full file, 148 lines, all FCM functions verified
- Direct file read: `.planning/INTEGRATION_AUDIT.md` — full file, 632 lines, audit claims traced to specific lines
- Direct file read: `.planning/phases/12-receipt-fcm-wiring/12-CONTEXT.md` — constraints and locked decisions
- Direct file read: `.planning/REQUIREMENTS.md` — APP-03 and NOTF-01 requirement definitions

### Tertiary (LOW — historical context only)
- `.planning/STATE.md` — Phase 11 decision log confirms `cashier_bp.record_once()` and `_init_cashier_credentials` were added in Phase 11, explaining the line shift

---

## Metadata

**Confidence breakdown:**
- Transaction row schema: HIGH — Direct line-by-line inspection of cashier_routes.py:520-532
- FCM wiring: HIGH — Direct inspection of cashier_routes.py:570-612 and fcm_sender.py
- migrate_users_schema startup: HIGH — Direct inspection of api_server.py:109-115
- config_validator.py gap: HIGH — Direct inspection of config_validator.py:235-237 (10 cols, need 11)
- Line shift explanation: HIGH — Phase 11 STATE.md decision log confirms the inserts

**Research date:** 2026-03-02
**Valid until:** N/A — this is static code inspection of a specific commit state; results are permanent until code changes

---

## Plan Guidance for Planner

The planner should structure this phase as **3 tasks in a single wave**:

| # | Task | File(s) | Action |
|---|------|---------|--------|
| 1 | Inspect and document | `cashier_routes.py`, `api_server.py`, `config_validator.py`, `fcm_sender.py` | Write VERIFICATION.md with line-number evidence for APP-03, NOTF-01, and migrate startup — all three status: VERIFIED |
| 2 | Fix config_validator.py | `backend/config_validator.py:237` | Add `'ItemsJson'` to Transactions Log column list (one-line change) |
| 3 | Update audit | `.planning/INTEGRATION_AUDIT.md` | Mark APP-03 and NOTF-01 as resolved; add resolution note citing Phase 12 VERIFICATION.md |

No new code required beyond the config_validator fix. No runtime testing required. Phase 7 already did the implementation work; this phase certifies it.
