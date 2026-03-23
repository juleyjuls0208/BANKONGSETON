# M007 / S06 Motion and Performance Tuning (iOS 17+) UAT Checklist

This checklist is the manual acceptance companion for `scripts/verify-m007-s06.sh`.
Use it to close S06 with explicit default-motion, Reduce Motion, and iOS 17+ profiling evidence.

## Inputs / Reusable References

- Automated verifier: `scripts/verify-m007-s06.sh`
- Behavior contract: `tests/test_verify_m007_s06_motion_behavior_contract.py`
- Design contract: `tests/test_verify_m007_s06_motion_design_contract.py`
- Motion policy: `mobile/ios/BankongSetonStudent/UI/Theme/AppTheme.swift`
- Shared primitives:
  - `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`
  - `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
  - `mobile/ios/BankongSetonStudent/UI/Components/StitchCard.swift`
- In-scope stateful screens:
  - `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
  - `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
  - `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
  - `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`
  - `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`

## Preconditions

1. iOS app builds and launches on iOS 17+ simulator/device.
2. Tester can sign in and navigate Home, QR Pay, Transactions, Budget, and Lost Card.
3. Tester can toggle **Reduce Motion** on device/simulator:
   - **Settings → Accessibility → Motion → Reduce Motion**
4. For profiling checks, Xcode command-line tools are available (`xcodebuild`, `xctrace`).
5. Do **not** capture personal data, auth tokens, or sensitive payloads in notes/screenshots.

## Automated Preflight (Run First)

1. `rtk proxy python -m pytest -q tests/test_verify_m007_s06_motion_behavior_contract.py tests/test_verify_m007_s06_motion_design_contract.py`
2. `rtk proxy sh scripts/verify-m007-s06.sh`
3. `rtk proxy bash scripts/verify-m007-s06.sh`
4. `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`
5. `rtk proxy xcrun xctrace list templates`

Shell fallback note:
- If `/bin/bash` is unavailable in the current host (common on Windows-only harnesses), use `rtk proxy sh scripts/verify-m007-s06.sh` as the executable verifier path and record the bash limitation in UAT notes.

## Manual Acceptance Scenarios

Mark each scenario with exactly one outcome: `[x] PASS` or `[x] FAIL`, then add short notes.

---

### 1) Default-motion baseline: tab switches + primary-button press feedback

**Steps**
1. Ensure **Reduce Motion = OFF**.
2. Navigate across all tab items repeatedly.
3. Press and release primary CTA buttons on Home/Transactions/Budget/Lost Card.

**Expected**
- Tab selection transitions feel cohesive and quick (no lag spikes).
- Primary buttons provide restrained tactile press feedback (no exaggerated bounce).
- Interaction remains responsive and interruptible.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 2) Default-motion path: QR flow state transitions

**Steps**
1. Open **QR Pay** from Home.
2. Exercise state transitions: scanning → loading → confirming → success/error.
3. Retry/cancel from error state and confirm controls still work.

**Expected**
- State transitions are clear and smooth, not flashy.
- Success/error states are visually distinct and promptly actionable.
- Confirm/Retry/Done controls remain immediately actionable after each transition.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 3) Default-motion path: Transactions, Budget, Lost Card, Home state transitions

**Steps**
1. In **Transactions**, trigger loading/empty/error/list/pagination states where possible.
2. In **Budget**, trigger load/save success/failure states.
3. In **Lost Card**, progress through idle/loading/success/error states.
4. In **Home**, observe error banner and recent-transactions loading/empty/list changes.

**Expected**
- State cards transition consistently across screens.
- No abrupt, jarring cuts in key state changes.
- No decorative continuous loops in in-scope paths.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 4) Reduce Motion path: simplified transitions without loss of clarity

**Steps**
1. Enable **Reduce Motion = ON**.
2. Repeat scenarios 1–3 (tab switch, QR, Transactions, Budget, Lost Card, Home).

**Expected**
- Transitions simplify (primarily opacity/low-motion behavior).
- Screen-state changes remain understandable.
- No controls disappear or become ambiguous due to reduced-motion branch.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 5) Actionability continuity under Reduce Motion

**Steps**
1. With **Reduce Motion = ON**, exercise all in-scope action controls:
   - Home: `Pay with QR`
   - QR: `Confirm QR Payment`, `Retry Scan`, `Done`
   - Transactions: retry/load-more/filter-clear controls
   - Budget: save/retry/refresh controls
   - Lost Card: report/retry/dismiss controls
2. Toggle Reduce Motion OFF/ON during app session and repeat selected actions.

**Expected**
- Every listed control remains actionable in both motion modes.
- No dead taps, blocked navigation, or delayed control availability caused by transitions.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 6) iOS 17+ profiling: Animation Hitches capture

**Steps**
1. Confirm Animation Hitches template exists:
   - `rtk proxy xcrun xctrace list templates`
2. Record an Animation Hitches trace while performing:
   - rapid tab switches
   - QR flow transitions
   - Transactions list scrolling + pagination
   - Budget save/load transitions
3. Save trace and note any hitch clusters.

**Expected**
- No sustained hitch clusters during normal in-scope interactions.
- Any isolated hitch has a reproducible context documented in notes.
- Motion remains subjectively “premium and responsive” rather than “fancy/slow.”

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

## Final Slice-UAT Sign-off

- [ ] All six scenarios marked PASS
- [ ] Automated preflight outputs captured (or platform-limitation note added)
- [ ] Profiling evidence captured for iOS 17+ runtime path
- [ ] No sensitive personal data captured in evidence
- Sign-off name/date:
