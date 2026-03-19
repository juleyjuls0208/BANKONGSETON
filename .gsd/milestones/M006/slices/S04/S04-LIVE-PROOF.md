# S04 Live Runtime Proof Summary

## Run Metadata

- Summary generated at: `2026-03-19T05:53:52Z`
- Evidence generated at: `2026-03-19T05:53:42Z`
- Base URL: `http://127.0.0.1:5010`
- Wrapper command: `rtk proxy bash scripts/verify-m006-s04.sh --dry-run-preflight`
- Evidence JSON: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- Evidence Schema: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.schema.json`

## Overall Verdict

- `live_ready`: ❌ false
- `schema_valid`: ✅ true
- `dry_run_preflight`: `true`
- Breakdown: `live_success=0`, `offline_fallback=0`, `failed=0`

## Required Flow Outcomes (live_success required)

| Flow | Canonical Endpoint | Resolved Endpoint | Status | Success | Offline | Classification | Error |
|---|---|---|---:|:---:|:---:|---|---|
| products | `/api/products` | `n/a` | n/a | ❌ | ❌ | `failed` | - |
| rfid_complete_sale | `/api/complete-sale` | `n/a` | n/a | ❌ | ❌ | `failed` | - |
| qr_confirm | `/api/qr/confirm` | `n/a` | n/a | ❌ | ❌ | `failed` | - |
| nfc_complete_sale | `/api/complete-sale-nfc` | `n/a` | n/a | ❌ | ❌ | `failed` | - |

## Preflight

- `ok`: ❌ false
- `missing_env`: GOOGLE_SHEETS_ID, FLASK_SECRET_KEY, JWT_SECRET, FINANCE_PASSWORD
- `missing_inputs`: card_uid (--card-uid or VERIFY_S04_CARD_UID), virtual_card_token (--virtual-card-token or VERIFY_S04_VIRTUAL_CARD_TOKEN), student_jwt (--student-jwt or VERIFY_S04_STUDENT_JWT)
- `missing_files`: none
- `errors`:
  - Missing required environment variables: GOOGLE_SHEETS_ID, FLASK_SECRET_KEY, JWT_SECRET, FINANCE_PASSWORD
  - Missing verifier runtime inputs: card_uid (--card-uid or VERIFY_S04_CARD_UID), virtual_card_token (--virtual-card-token or VERIFY_S04_VIRTUAL_CARD_TOKEN), student_jwt (--student-jwt or VERIFY_S04_STUDENT_JWT)

## Diagnostics

- Queue status snapshot: `null` (not collected or preflight blocked)

## Artifact Pointers

- Machine-readable evidence: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.json`
- Human-readable evidence: `.gsd/milestones/M006/slices/S04/S04-LIVE-PROOF.md`
- Milestone validation reference: `.gsd/milestones/M006/M006-VALIDATION.md`
- Requirement traceability reference: `.gsd/REQUIREMENTS.md` (R053)
