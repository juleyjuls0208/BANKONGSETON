# Phase 12: Receipt & FCM Wiring - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Verify that `cashier_routes.py`'s `complete_sale` function (1) writes a transaction row that includes BalanceBefore and (2) calls the FCM notification function when balance drops below threshold. Also verify that `migrate_users_schema()` is called at `api_server` startup. Fix any of the three if missing. This phase resolves the contradiction between the Phase 7 VERIFICATION (claims all three are fixed) and the Integration Audit (marks APP-03 and NOTF-01 as broken).

Creating new notification types, adding new transaction fields, or changing authentication are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Transaction row schema
- Accept the current 11-column format as correct — do NOT trim to 8 columns
- The 11-column schema is: `TransactionID, Timestamp, StudentID, MoneyCardNumber, TransactionType, Amount, BalanceBefore, BalanceAfter, Status, ErrorMessage, ItemsJson`
- BalanceBefore at position 7 (1-indexed) is acceptable; Android API reads by header name, not column index
- Verify all 11 columns are present and in the correct order in the code
- Verify the Transactions Google Sheet header row matches the 11-column structure
- Update `backend/config_validator.py` to reflect the actual 11-column schema (currently hardcoded as 8 columns)

### Verification standard
- Static code inspection only — no live end-to-end testing required for this phase
- Document exact line numbers for each verified feature (e.g. "BalanceBefore at `cashier_routes.py:527`")
- Output per-requirement status: APP-03, NOTF-01, and `migrate_users_schema` startup each get VERIFIED / BROKEN / PARTIAL with code evidence
- If anything is found broken during inspection: fix it within the same plan run, then re-run inspection and update status to VERIFIED

### FCM notification scope
- Preserve both FCM pushes in `cashier_routes.py`: (1) purchase confirmation push on every successful sale, (2) low-balance push when `new_balance < threshold`
- NOTF-01 formally requires only the low-balance push; the purchase push is a beneficial addition — keep it
- Explicitly verify that FCM failures are non-blocking: a failed push must never roll back or prevent the sale from completing
- FCM verification scope for this phase: `cashier_routes.py` only (the "cashier POS" path per NOTF-01). How to handle `api_server.py` and `admin_dashboard.py` FCM paths is left to Claude's discretion — they already have the pattern from earlier phases

### Contradiction resolution
- The Integration Audit was written before Phase 7 fixed the gaps; the contradiction is expected
- Cross-check whether Phase 11 (cashier security hardening) introduced the line number shift (Phase 7 VERIFICATION referenced lines 307-316; current code is at ~527) — confirm features survived Phase 11's credential removal
- The verification report should explicitly document that the Integration Audit predates Phase 7, explaining the contradiction's origin
- After verifying APP-03 and NOTF-01 are present, update `INTEGRATION_AUDIT.md` to mark both requirements as resolved with a reference to the Phase 12 verification

### Claude's Discretion
- Whether to treat `api_server.py` and `admin_dashboard.py` FCM paths as in-scope for this phase's verification (NOTF-01 specifies cashier POS, but noting their presence would be useful)
- Exact format of the resolution note added to `INTEGRATION_AUDIT.md`
- Approach for tracing the Phase 11 vs Phase 7 line number change (git blame vs manual diff)

</decisions>

<specifics>
## Specific Ideas

- The Phase 7 VERIFICATION referenced `cashier_routes.py:307-316` for the transaction row. Current code has it at ~line 527. Phase 11 touched `cashier_routes.py` to remove hardcoded credentials — this is the likely source of the line shift. The verification should confirm features survived, not investigate git history forensically.
- `backend/config_validator.py:237` has a hardcoded 8-column list for Transactions. This is the specific line to fix.
- `api_server.py:111-113` already has `migrate_users_schema()` — this likely requires no fix, just documentation of its presence.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/dashboard/cashier/cashier_routes.py`: `complete_sale()` function — the primary inspection and fix target
- `backend/api/api_server.py`: `migrate_users_schema()` startup call at lines 111-113 — likely already correct
- `backend/config_validator.py:237`: Transactions column schema definition — needs update to 11 columns
- `backend/fcm_sender.py`: `send_purchase_push()` and `send_low_balance_push()` — the FCM functions being called

### Established Patterns
- FCM calls wrapped in try/except so failures are non-blocking — this pattern exists in `cashier_routes.py` (~line 570) and must be confirmed present
- Transaction row construction uses a Python list literal — easy to count columns and verify order
- `migrate_users_schema()` is imported and called in a non-fatal try/except at `api_server.py:111-113`

### Integration Points
- `INTEGRATION_AUDIT.md` at `.planning/INTEGRATION_AUDIT.md` — needs APP-03 and NOTF-01 status updated after verification
- `backend/config_validator.py` — Transactions schema list needs updating from 8 to 11 columns
- Phase 12 VERIFICATION.md will be the canonical reference that closes out the audit contradiction

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 12-receipt-fcm-wiring*
*Context gathered: 2026-03-02*
