# M007 / S04 Budget + Receipt + Lost-Card UAT Checklist

This checklist is the manual acceptance companion for `scripts/verify-m007-s04.sh`.
Use it to close S04 demo readiness on simulator/device without rediscovering scope.

## Inputs / Reusable References

- Automated verifier: `scripts/verify-m007-s04.sh`
- Behavior contract: `tests/test_verify_m007_s04_budget_lostcard_behavior_contract.py`
- Design contract: `tests/test_verify_m007_s04_budget_receipt_lostcard_design_contract.py`
- Budget screen: `mobile/ios/BankongSetonStudent/Views/Budget/BudgetView.swift`
- Receipt screen: `mobile/ios/BankongSetonStudent/Views/Receipt/ReceiptView.swift`
- Lost-card screen: `mobile/ios/BankongSetonStudent/Views/LostCard/LostCardView.swift`

## Preconditions

1. iOS app builds and launches on simulator/device.
2. Test account has transaction history (recommended: one transaction with explicit items + one without items to validate fallback rendering).
3. Tester can temporarily toggle network to force recoverable error states.
4. Do **not** capture PIN/JWT/auth-token/PII in notes or screenshots; log only structural state/copy outcomes.

## Automated Preflight (Run First)

1. `rtk proxy bash scripts/verify-m007-s04.sh`
2. `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

Expected: both commands pass before final sign-off (note platform/tooling constraints explicitly if unavailable).

## Manual Acceptance Scenarios

Mark each scenario with exactly one outcome: `[x] PASS` or `[x] FAIL`, then add short notes.

---

### 1) Budget save success flow

**Steps**
1. Open **Budget** screen.
2. Enter a new valid monthly limit.
3. Tap **Save Limit**.

**Expected**
- Save action is enabled for valid numeric input.
- Save completes without dead-end controls.
- Success state appears (`Budget limit saved successfully.`) and no save-error card remains visible.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 2) Budget load failure and retry recovery

**Steps**
1. Disable network.
2. Open **Budget** (or pull-to-refresh).
3. Confirm load error state appears.
4. Re-enable network.
5. Tap **Retry Load**.

**Expected**
- Load failure state card appears with actionable retry control.
- Retry action restores data once network is back.
- Screen returns to ready state without ambiguous blank/loading lockup.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 3) Budget save failure and retry recovery

**Steps**
1. Open **Budget** with network enabled.
2. Enter a new valid monthly limit.
3. Disable network before tapping save.
4. Tap **Save Limit** to force save failure.
5. Re-enable network.
6. Tap **Retry Save**.

**Expected**
- Save failure state card appears with explicit retry CTA.
- Retry save succeeds after connectivity returns.
- No dead control remains after successful retry.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 4) Receipt continuity from Home and Transactions

**Steps**
1. From **Home**, open a navigable recent transaction.
2. Confirm **Receipt** opens.
3. Return and open **Transactions/History**.
4. Open a navigable transaction from the history list.

**Expected**
- Receipt entry works from both Home and Transactions paths.
- Receipt summary and item cards render in both entry paths.
- Navigation flow remains coherent (no broken route/back-stack behavior).

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 5) Receipt fallback item behavior + scope-clean constraints

**Steps**
1. Open a receipt for a transaction with missing/empty item details.
2. Observe item list rendering.
3. Inspect visible actions on the receipt surface.

**Expected**
- Fallback item explanation is visible for synthesized line-item mode.
- At least one line item row still renders deterministically.
- Receipt remains scope-clean: **no** `Download PDF`, `Report Issue`, `Report Receipt`, or equivalent utility-action buttons.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 6) Lost-card success flow

**Steps**
1. From **Settings**, open **Report Lost Card**.
2. Tap **Report Lost Card** while network is available.
3. Wait for completion, then tap **Back to Settings**.

**Expected**
- Flow transitions through idle → loading → success.
- Success card copy is shown and completion action returns to Settings.
- No dead post-success control remains.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 7) Lost-card failure + retry/session coherence

**Steps**
1. From **Report Lost Card**, disable network.
2. Tap **Report Lost Card** to force failure.
3. Confirm error state and retry controls.
4. Re-enable network.
5. Tap **Retry Report**.

**Expected**
- Flow transitions through idle/loading/error with explicit failure copy.
- Error state exposes actionable retry and safe dismiss/back controls.
- Retry succeeds when network recovers (or, for session-boundary failures, app transitions coherently via existing auth handling).

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

## Final Slice-UAT Sign-off

- [ ] All seven scenarios marked PASS
- [ ] Automated preflight command outputs captured
- [ ] No sensitive credentials/PII captured in artifacts
- Sign-off name/date:
