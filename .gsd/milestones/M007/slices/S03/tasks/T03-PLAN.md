---
estimated_steps: 4
estimated_files: 4
skills_used:
  - test
  - debug-like-expert
  - lint
  - review
---

# T03: Add S03 verifier harness and manual Transactions acceptance checklist

**Slice:** S03 — Transactions Redesign + Search/Filter + State Fidelity
**Milestone:** M007

## Description

Close S03 with repeatable evidence: a one-command verifier that runs both S03 pytest contracts and static guardrails, plus a concise manual checklist for runtime/demo acceptance of search/filter/state-fidelity behavior.

## Steps

1. Create `scripts/verify-m007-s03.sh` to run S03 behavior/design contract suites and fail fast with actionable guidance.
2. Add static marker checks for critical S03 invariants (search control wiring, filter control wiring, load-more hook, and explicit state markers for loading/base-empty/filtered-empty/error/pagination-error/populated).
3. Write `.gsd/milestones/M007/slices/S03/S03-UAT.md` with manual pass/fail steps covering populated search, filter toggles, no-match recovery, load-more continuity, and non-blocking pagination failure UX.
4. Ensure verifier script and checklist reference actual file paths/commands so downstream slices (S06/S07) can reuse them without extra context.

## Must-Haves

- [ ] `scripts/verify-m007-s03.sh` gives deterministic pass/fail closure for S03 contracts.
- [ ] Static checks cover key search/filter/state-fidelity markers beyond pytest invocation.
- [ ] Manual checklist is explicit enough for a fresh executor to run without research docs.
- [ ] Slice verification artifacts are reusable by later integration slices.

## Verification

- `rtk proxy bash scripts/verify-m007-s03.sh`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

## Observability Impact

- Signals added/changed: S03 gains a standard, scriptable inspection surface for contract and state-marker regressions.
- How a future agent inspects this: run `scripts/verify-m007-s03.sh` and follow `.gsd/milestones/M007/slices/S03/S03-UAT.md`.
- Failure state exposed: verifier output reports failing phase + remediation hint, reducing ambiguity during cross-slice integration.

## Inputs

- `tests/test_verify_m007_s03_transactions_behavior_contract.py` — behavior contract suite from T01.
- `tests/test_verify_m007_s03_transactions_design_contract.py` — design contract suite from T02.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — static marker source for search/filter/state surfaces.
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift` — static marker source for state split and pagination handling.

## Expected Output

- `scripts/verify-m007-s03.sh` — one-command S03 automated verifier.
- `.gsd/milestones/M007/slices/S03/S03-UAT.md` — manual Transactions acceptance checklist for device/demo validation.
- `tests/test_verify_m007_s03_transactions_behavior_contract.py` — finalized behavior checks aligned with verifier expectations.
- `tests/test_verify_m007_s03_transactions_design_contract.py` — finalized design checks aligned with verifier expectations.
