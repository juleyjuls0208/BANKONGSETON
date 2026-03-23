# S06: Motion and Performance Tuning (iOS 17+)

**Goal:** Tune motion across the redesigned iOS app so interactions feel premium and responsive on iOS 17+ while staying restrained and accessibility-aware.
**Demo:** On iOS 17+ runtime, tab changes, primary-button presses, QR/LostCard/Budget/Transactions state changes, and list interactions feel cohesive and snappy; with Reduce Motion enabled, transitions simplify without breaking control clarity or actionability.

## Must-Haves

- R062 (owned): Centralized motion policy is applied across shared primitives and high-impact screens, with Reduce Motion-aware behavior and restrained timing.
- R055 (support): Motion language stays stitch-faithful and consistent across home/QR/transactions/budget/lost-card surfaces.
- R056 (support): Introducing motion does not create dead/hidden in-scope controls; actionable paths remain intact.
- R059 (support): Stateful flows (loading/empty/error/success) use clear, lightweight transitions rather than abrupt cuts or decorative loops.
- R063 (support): Slice outputs include deterministic verifier/tests plus iOS 17+ runtime/UAT profiling checklist evidence.

## Proof Level

- This slice proves: operational
- Real runtime required: yes
- Human/UAT required: yes

## Verification

- `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py`
- `rtk proxy sh scripts/verify-m007-s06.sh`
- `rtk proxy bash scripts/verify-m007-s06.sh`
- `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s06.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); required=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in required if x not in out]; assert not missing, missing"`
- `rtk proxy python -c "import subprocess; p=subprocess.run(['rtk','proxy','sh','scripts/verify-m007-s06.sh'], capture_output=True, text=True); out=(p.stdout or '') + (p.stderr or ''); tags=['preflight','behavior-contract','design-contract','static-contract']; missing=[x for x in tags if x not in out]; assert not missing, missing; assert any(marker in out.lower() for marker in ['fail','pass','missing','required','forbidden'])"`
- `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
- `rtk proxy xcrun xctrace list templates`
- `rtk proxy python -c "from pathlib import Path; assert Path('.gsd/milestones/M007/slices/S06/S06-UAT.md').exists()"`

## Observability / Diagnostics

- Runtime signals: shared motion token usage and Reduce Motion branches are explicit in primitives and stateful screens; no infinite decorative animation loops in in-scope paths.
- Inspection surfaces: `tests/test_verify_m007_s06_motion_behavior_contract.py`, `tests/test_verify_m007_s06_motion_design_contract.py`, `scripts/verify-m007-s06.sh`, and `.gsd/milestones/M007/slices/S06/S06-UAT.md`.
- Failure visibility: verifier phase output localizes regressions (`preflight`, `behavior-contract`, `design-contract`, `static-contract`) with required/forbidden marker guidance.
- Redaction constraints: verification checks only structural markers and state contracts; no secrets or personal data are logged.

## Integration Closure

- Upstream surfaces consumed: `AppTheme`, `StitchPrimaryButtonStyle`, `StitchTabShell`, `StitchCard`, plus S02-S05 stateful views (`QRPayView`, `TransactionsView`, `BudgetView`, `LostCardView`, `HomeView`).
- New wiring introduced in this slice: one shared motion policy seam consumed by shared primitives and high-impact state screens, including Reduce Motion branching.
- What remains before the milestone is truly usable end-to-end: S07 final integration and full on-device journey gate.

## Tasks

- [x] **T01: Establish centralized motion policy and Reduce Motion wiring in shared primitives** `est:2h`
  - Why: S06 cannot converge on a coherent feel if each screen uses ad hoc timings/curves; shared primitives must consume one policy first.
  - Files: `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`, `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`, `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
  - Do: Add a centralized motion token/policy surface in `AppTheme`, wire it into button press feedback/tab transitions/card rendering behavior, and add Reduce Motion-aware branches without introducing unconditional iOS 17-only APIs.
  - Verify: `rtk proxy python -c "from pathlib import Path; theme=Path('mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift').read_text(); btn=Path('mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift').read_text(); shell=Path('mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift').read_text(); card=Path('mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift').read_text(); all_text='\n'.join([theme,btn,shell,card]); required=['accessibilityReduceMotion','motion']; missing=[x for x in required if x not in all_text]; assert not missing, missing"`
  - Done when: Shared primitives consume one motion policy seam and include explicit Reduce Motion handling.
- [ ] **T02: Apply restrained motion tuning to QR, transactions, budget, lost-card, and home states** `est:2h`
  - Why: R062 and R059 are judged on stateful user flows, not only primitive-level polish.
  - Files: `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`, `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`, `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`, `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`, `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
  - Do: Replace abrupt state cuts with subtle tokenized transitions, gate non-essential animation with Reduce Motion, keep existing in-scope control affordances/identifiers, and remove any decorative long-running loops from demo-critical paths.
  - Verify: `rtk proxy python -c "from pathlib import Path; files=['mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift','mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift','mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift','mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift','mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift']; txt='\n'.join(Path(f).read_text() for f in files); assert 'accessibilityReduceMotion' in txt; assert 'repeatForever' not in txt"`
  - Done when: Key stateful screens use restrained motion tied to shared policy and remain fully actionable in default + Reduce Motion paths.
- [ ] **T03: Add S06 contract tests, phased verifier, and iOS 17+ UAT/perf checklist** `est:1h`
  - Why: S06 closure must be deterministic; without test/verifier/UAT artifacts, motion acceptance is subjective and fragile.
  - Files: `tests/test_verify_m007_s06_motion_behavior_contract.py`, `tests/test_verify_m007_s06_motion_design_contract.py`, `scripts/verify-m007-s06.sh`, `.gsd/milestones/M007/slices/S06/S06-UAT.md`
  - Do: Add behavior/design source-contract tests, implement a fail-fast S06 verifier (`preflight`, `behavior-contract`, `design-contract`, `static-contract`), and document manual iOS 17+ runtime checks including Reduce Motion path and Animation Hitches profiling commands.
  - Verify: `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py && rtk proxy sh scripts/verify-m007-s06.sh`
  - Done when: Both S06 tests and verifier pass, and S06-UAT exists with manual/profiling acceptance steps.

## Files Likely Touched

- `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
- `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
- `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
- `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
- `tests/test_verify_m007_s06_motion_behavior_contract.py`
- `tests/test_verify_m007_s06_motion_design_contract.py`
- `scripts/verify-m007-s06.sh`
- `.gsd/milestones/M007/slices/S06/S06-UAT.md`
