---
id: T02
parent: S09
milestone: M007
provides:
  - Dark-mode default startup is enforced at app bootstrap.
  - Login is now student-ID-only (PIN UI/state/request payload removed) while preserving sign-in flow.
  - Transactions taxonomy is remapped to `QR Pay` / `Card Pay` / `Load` with override regression contracts.
key_files:
  - mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift
  - mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift
  - mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift
  - mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift
  - mobile/ios/BankongSetonStudent/Models/LoginModels.swift
  - mobile/ios/BankongSetonStudent/Models/TransactionModels.swift
  - mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift
  - tests/test_verify_m007_s09_override_contract.py
  - .gsd/milestones/M007/slices/S09/S09-PLAN.md
  - .gsd/DECISIONS.md
  - .gsd/KNOWLEDGE.md
key_decisions:
  - D090 — Use student-ID-only iOS login payload aligned with backend `/api/auth/login` contract.
patterns_established:
  - Override contract tests now emit explicit failure labels (`dark_mode_default`, `login_pin_present`, `legacy_filter_label`, `stitch_drift`).
  - Transaction filter mapping uses `normalizedFilterCategory` to deterministically project backend type values into `QR Pay` / `Card Pay` / `Load`.
observability_surfaces:
  - tests/test_verify_m007_s09_override_contract.py
  - scripts/verify-m007-s09.sh phased diagnostics (`phase=...`, `guidance=...`)
  - .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json
  - .gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md
duration: 47m
verification_result: passed
completed_at: 2026-03-23T19:30:53+08:00
blocker_discovered: false
---

# T02: Implement override UI remediation (stitch parity, dark-mode default, no PIN, new transaction filters)

**Enforced dark-first startup, removed PIN from iOS student login end-to-end, and replaced transactions taxonomy with `QR Pay` / `Card Pay` / `Load` under new override contract tests.**

## What Happened

Implemented the override remediation across bootstrap, auth, and transactions surfaces.

- App bootstrap now sets `.preferredColorScheme(.dark)` to remove light-first startup regression.
- Login screen and state were refactored to remove PIN entirely:
  - Removed PIN field and PIN copy from `LoginView`.
  - Removed PIN state/validation from `LoginViewModel`.
  - Updated API auth call path to student-ID-only request contract (`APIClient.login(studentId:)` + `LoginRequest` model).
- Transactions filter taxonomy was updated from legacy debit/credit semantics to override labels:
  - `TransactionFilter` now uses `.qrPay`, `.cardPay`, `.load`.
  - `TransactionsView` filter labels now render `QR Pay`, `Card Pay`, `Load`.
  - `Transaction.matchesFilter(...)` now routes through `normalizedFilterCategory` for deterministic mapping from existing transaction type strings.
- Added `tests/test_verify_m007_s09_override_contract.py` to fail fast on override regressions (dark-mode marker, PIN remnants, legacy filter labels/taxonomy, stitch-surface drift markers).
- Persisted a downstream decision (`D090`) and appended non-obvious override gotchas to `.gsd/KNOWLEDGE.md`.

## Verification

Ran the task-level override verification gate and slice-level verification commands.

- T02 override checks all passed (new override pytest + static dark/login/filter assertions).
- Slice-level multi-test suite (`runtime_contract + evidence_contract + override_contract`) passed.
- Slice runtime script still fails on this Windows host at `apple_tooling` because `xcodebuild/xcrun` are unavailable.
- UAT marker file check still fails because `S09-UAT-RESULT.md` is not yet authored (planned in T03).

## Verification Evidence

| # | Command | Exit Code | Verdict | Duration |
|---|---------|-----------|---------|----------|
| 1 | `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py` | 0 | ✅ pass | 0.31s |
| 2 | `rtk proxy python -c "from pathlib import Path; app=Path('mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift').read_text(encoding='utf-8'); assert '.dark' in app or 'UIUserInterfaceStyle' in app"` | 0 | ✅ pass | ~0.08s |
| 3 | `rtk proxy python -c "from pathlib import Path; login=Path('mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift').read_text(encoding='utf-8'); assert 'PIN' not in login, 'PIN control still present'"` | 0 | ✅ pass | ~0.08s |
| 4 | `rtk proxy python -c "from pathlib import Path; tx=Path('mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift').read_text(encoding='utf-8'); required=['QR Pay','Card Pay','Load']; missing=[x for x in required if x not in tx]; assert not missing, missing; banned=['Debit','Credit Card']; bad=[x for x in banned if x in tx]; assert not bad, bad"` | 0 | ✅ pass | ~0.09s |
| 5 | `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py tests/test_verify_m007_s09_override_contract.py` | 0 | ✅ pass | 0.43s |
| 6 | `rtk proxy sh scripts/verify-m007-s09.sh` | 1 | ❌ fail | ~8.6s |
| 7 | `rtk proxy python -c "from pathlib import Path; login=Path('mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift').read_text(encoding='utf-8'); assert 'PIN' not in login, 'PIN UI still present'; tx=Path('mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift').read_text(encoding='utf-8'); required=['QR Pay','Card Pay','Load']; missing=[x for x in required if x not in tx]; assert not missing, missing"` | 0 | ✅ pass | ~0.09s |
| 8 | `rtk proxy python -c "from pathlib import Path; app=Path('mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift').read_text(encoding='utf-8'); assert '.dark' in app or 'UIUserInterfaceStyle' in app, 'dark-mode startup marker missing'"` | 0 | ✅ pass | ~0.08s |
| 9 | `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['Dark mode default verified','Login PIN removed','Transactions filters: QR Pay, Card Pay, Load','Final S09 UAT verdict']; missing=[x for x in required if x not in txt]; assert not missing, missing"` | 1 | ❌ fail | ~0.09s |

## Diagnostics

- Override regression gate: `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py`
- Runtime phased diagnostics: `rtk proxy sh scripts/verify-m007-s09.sh` then inspect:
  - `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
  - `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`
- Static source checkpoints:
  - `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`
  - `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`
  - `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`

## Deviations

- Minor local adaptation: updated `APIClient.swift` and `LoginModels.swift` (in addition to plan-listed login view/view-model files) so PIN removal remains runtime-correct against the backend login contract.
- Recorded decision D090 and appended two override-specific knowledge entries for downstream agents.

## Known Issues

- `scripts/verify-m007-s09.sh` fails on this host at `apple_tooling` because `xcodebuild`/`xcrun` are unavailable (expected in non-Apple environment).
- `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md` is still missing; corresponding slice verification remains failing until T03 generates signed UAT evidence.
- LSP diagnostics for Swift are unavailable in this environment (`No language server found`), so verification relied on pytest + static assertions.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift` — enforced dark-mode default at app bootstrap.
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift` — removed PIN UI/copy and kept stitch-parity login structure with student-ID-only input.
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift` — removed PIN state/validation and switched auth call to student-ID-only.
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift` — changed login request signature/body to student-ID-only.
- `mobile/ios/BankongSetonStudent/Models/LoginModels.swift` — removed PIN from login request model payload.
- `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift` — replaced filter enum taxonomy and added deterministic category mapping for override filters.
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift` — replaced visible filter labels with `QR Pay` / `Card Pay` / `Load`.
- `tests/test_verify_m007_s09_override_contract.py` — added override contract suite for dark mode, login PIN removal, and taxonomy regression checks.
- `.gsd/milestones/M007/slices/S09/S09-PLAN.md` — marked T02 complete.
- `.gsd/DECISIONS.md` — appended D090 (student-ID-only login contract decision).
- `.gsd/KNOWLEDGE.md` — added S09 override implementation guardrails for login contract and transaction taxonomy.
