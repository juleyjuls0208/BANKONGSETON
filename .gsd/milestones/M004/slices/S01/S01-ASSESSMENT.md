---
date: 2026-03-16
triggering_slice: M004/S01
verdict: no-change
---

# Reassessment: M004/S01

## Changes Made

No changes.

S01 delivered exactly what the roadmap specified. The APDU retry loop is in firmware, structural contract is verified (verify-m004.sh 5/5), and the S01→S02 boundary contracts are intact. S02 is well-scoped and its description matches what actually needs to happen next.

## Success Criterion Coverage

- `Student taps Android phone → APDU ok=YES attempt N/3 in Serial Monitor → complete_sale_nfc CALLED in server log → cashier sees success modal` → S02
- `Physical RFID card tap after firmware change still produces success (no regression)` → S02
- `python -m py_compile backend/dashboard/cashier/cashier_routes.py exits 0` → already verified in S01 (verify-m004.sh check(e)); S02 re-confirms after backend cleanup

All three success criteria have at least one remaining owning slice. Coverage check passes.

## Requirement Coverage Impact

- R025: contract proof level holds (verify-m004.sh 5/5); runtime proof (hardware tap → ok=YES) remains an S02 gate — no change to ownership or status
- R021: contract verified in M003/S02; advancing to validated remains an S02 gate — no change
- R020, R022, R023: still "leaves for later" per milestone scope — no change

## Decision References

- D037 — APDU retry loop pattern confirmed; pre-delay placement (outside loop) confirmed correct during T01 execution
- D038 — Already recorded: complete_sale_nfc Money Accounts lookup should use direct string comparison (aligning to D032); this is the "backend cleanup" work in S02
