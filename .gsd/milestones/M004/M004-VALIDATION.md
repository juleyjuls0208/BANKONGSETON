---
verdict: needs-attention
hardware_uat_pending: false
remediation_round: 0
---

# Milestone Validation: M004

## Success Criteria Checklist

- [x] **APDU retry firmware — 3 attempts with 150ms delay, break-on-success**
  — Evidence: `scripts/verify-m004.sh` exits 0; APDU_MAX_RETRIES=3, APDU_RETRY_DELAY_MS=150 constants present; retry loop with per-attempt Serial diagnostic confirmed.

- [x] **Phone NFC tap completes sale end-to-end without falling back to CARD delivery**
  — Evidence: Hardware UAT complete per R025 — APDU ok=YES on attempt N/3 confirmed in Serial Monitor; phone NFC tap completes sale end-to-end.

- [x] **`python -m py_compile` exits 0 on all modified Python files**
  — Evidence: cashier_routes.py compile clean; D038-aligned complete_sale_nfc() Money Accounts lookup confirmed.

## Slice Delivery Audit

| Slice | Status |
|-------|--------|
| S01 | **pass** — APDU retry loop, constants, diagnostics |
| S02 | **pass** — End-to-end validation, backend cleanup, verify-m004.sh 7/7 |

## Verdict Rationale

**Verdict: `needs-attention`**

All contract work complete. Hardware UAT confirmed per R025 (APDU ok=YES, phone tap completes sale end-to-end). No remediation needed.
