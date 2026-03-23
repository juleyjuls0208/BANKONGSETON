# S09: Override Remediation + Final Device Acceptance Closure

**Goal:** Apply the M007 user override before final closure by restoring stitch-parity UI behavior (including dark-mode startup), removing PIN from login, replacing legacy transactions filter taxonomy with `QR Pay` / `Card Pay` / `Load`, then re-running runtime + physical-device acceptance evidence.
**Demo:** Reviewer can launch the app and verify dark mode on first render, stitch-faithful login without PIN, transactions filters shown as `QR Pay` / `Card Pay` / `Load`, and updated `S09-RUNTIME-PROOF.*` + `S09-UAT-RESULT.md` + `M007-VALIDATION.md` proving final iOS 17+ pass/fail closure.

## Must-Haves

- **R055 (owned):** Stitch reference parity is re-established for overridden surfaces (login/home/transactions) and legacy UI regressions are removed.
- **R056 + R059 (support):** Updated controls remain fully interactive with realistic loading/empty/error/success handling; no dead-end controls introduced by override fixes.
- **R057 (support):** Payment UX remains QR-only after override remediation.
- **R058 (owned):** Transactions filter taxonomy is exactly `QR Pay`, `Card Pay`, and `Load` (legacy `Debit`/`Credit Card` labels removed).
- **R062 + R063 (support):** Final build still feels responsive on physical iOS 17+ and closure evidence reflects post-override behavior.

## Proof Level

- This slice proves: final-assembly
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py tests/test_verify_m007_s09_override_contract.py`
- `rtk proxy sh scripts/verify-m007-s09.sh`
- `rtk proxy python -c "from pathlib import Path; login=Path('mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift').read_text(encoding='utf-8'); assert 'PIN' not in login, 'PIN UI still present'; tx=Path('mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift').read_text(encoding='utf-8'); required=['QR Pay','Card Pay','Load']; missing=[x for x in required if x not in tx]; assert not missing, missing"`
- `rtk proxy python -c "from pathlib import Path; app=Path('mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift').read_text(encoding='utf-8'); assert '.dark' in app or 'UIUserInterfaceStyle' in app, 'dark-mode startup marker missing'"`
- `rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['Dark mode default verified','Login PIN removed','Transactions filters: QR Pay, Card Pay, Load','Final S09 UAT verdict']; missing=[x for x in required if x not in txt]; assert not missing, missing"`

## Observability / Diagnostics

- Runtime signals: phased verifier output (`phase=...`, `guidance=...`) now includes override-surface checks before artifact completeness.
- Inspection surfaces: `scripts/verify-m007-s09.sh`, `tests/test_verify_m007_s09_override_contract.py`, `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`.
- Failure visibility: override regressions are localized to explicit diagnostics (`legacy_ui`, `login_pin`, `dark_mode_default`, `tx_filter_taxonomy`) with remediation guidance.
- Redaction constraints: runtime/UAT artifacts remain credential-safe and exclude QR token payloads or personally identifying data.

## Integration Closure

- Upstream surfaces consumed: S07 integrated UX contract/evidence, existing S09 phased verifier/runtime serializer from T01, and M007 validation references.
- New wiring introduced in this slice: override-specific UI contracts + filter taxonomy enforcement + refreshed runtime/UAT closure evidence.
- What remains before the milestone is truly usable end-to-end: nothing once override-specific checks and physical UAT pass and `M007-VALIDATION.md` records explicit post-override closure.

## Tasks

- [x] **T01: Author S09 phased runtime verifier and evidence contract tests** `est:1h 20m`
  - Why: S09 closure needs a deterministic, inspectable gate before Apple-host execution and manual UAT can be trusted.
  - Files: `scripts/verify-m007-s09.sh`, `scripts/verify-m007-s09-runtime.py`, `tests/test_verify_m007_s09_runtime_contract.py`, `tests/test_verify_m007_s09_evidence_contract.py`
  - Do: Implement an S09 verifier with phase-tagged diagnostics and guidance hooks, add a runtime-proof serializer for JSON/Markdown artifacts, and add pytest contracts asserting required phase markers plus proof-schema expectations.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py && rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s09.sh').read_text(encoding='utf-8'); required=['set -euo pipefail','fail_with_guidance','phase=s07_baseline','phase=apple_tooling','phase=simulator_build','phase=xctrace_templates','phase=artifact_completeness','guidance=']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
  - Done when: S09 verifier/runtime-proof contracts are executable and fail with localized guidance instead of ambiguous shell errors.
- [x] **T02: Implement override UI remediation (stitch parity, dark-mode default, no PIN, new transaction filters)** `est:1h 35m`
  - Why: User override explicitly reports demo-blocking regressions (legacy look, wrong startup theme, unwanted PIN input, wrong transaction filter labels).
  - Files: `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`, `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`, `tests/test_verify_m007_s09_override_contract.py`
  - Do: Enforce dark-mode startup, remove PIN UI/state from login while preserving auth flow, replace transaction filter options to `QR Pay` / `Card Pay` / `Load` with correct matching behavior, and add/refresh override contract assertions that fail on legacy labels/components.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s09_override_contract.py && rtk proxy python -c "from pathlib import Path; login=Path('mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift').read_text(encoding='utf-8'); assert 'PIN' not in login" && rtk proxy python -c "from pathlib import Path; tx=Path('mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift').read_text(encoding='utf-8'); required=['QR Pay','Card Pay','Load']; missing=[x for x in required if x not in tx]; assert not missing, missing"`
  - Done when: Override deltas are visible in source and verifier coverage with no remaining legacy UI/filter/login-theme regressions.
- [ ] **T03: Re-run runtime + physical-device UAT and publish post-override closure evidence** `est:1h 25m`
  - Why: Final acceptance must prove the override is satisfied on real iOS runtime, not just source-level edits.
  - Files: `scripts/verify-m007-s09.sh`, `scripts/verify-m007-s09-runtime.py`, `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`, `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`, `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`, `.gsd/milestones/M007/M007-VALIDATION.md`
  - Do: Execute S09 verifier on Apple-capable host after T02 changes, run physical iOS 17+ UAT including explicit checks for dark mode default, login-without-PIN, and transaction filter taxonomy, then update milestone validation with final post-override verdict.
  - Verify: `rtk proxy sh scripts/verify-m007-s09.sh && rtk proxy python -m pytest -q tests/test_verify_m007_s09_evidence_contract.py tests/test_verify_m007_s09_override_contract.py && rtk proxy python -c "from pathlib import Path; txt=Path('.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md').read_text(encoding='utf-8'); required=['Dark mode default verified','Login PIN removed','Transactions filters: QR Pay, Card Pay, Load','Final S09 UAT verdict','Sign-off']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
  - Done when: Runtime proof and signed UAT artifacts explicitly show the override checks passing and milestone validation declares closure.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`
- `mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/LoginViewModel.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`
- `scripts/verify-m007-s09.sh`
- `scripts/verify-m007-s09-runtime.py`
- `tests/test_verify_m007_s09_override_contract.py`
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
- `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`
- `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`
- `.gsd/milestones/M007/M007-VALIDATION.md`
