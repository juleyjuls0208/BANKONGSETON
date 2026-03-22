# M007 / S03 Transactions UAT Checklist

This checklist is the manual acceptance companion for `scripts/verify-m007-s03.sh`.
Use it for device/simulator demo closure of Transactions search/filter/state-fidelity behavior.

## Inputs / Reusable References

- Automated verifier: `scripts/verify-m007-s03.sh`
- Behavior contract: `tests/test_verify_m007_s03_transactions_behavior_contract.py`
- Design contract: `tests/test_verify_m007_s03_transactions_design_contract.py`
- Transactions UI source: `mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift`
- Transactions VM source: `mobile/ios/BankongSetonStudent/ViewModels/TransactionsViewModel.swift`

## Preconditions

1. Account has enough history to exercise pagination (recommended: 25+ transactions).
2. Data includes both debit-like and credit-like transaction types.
3. iOS app builds and launches (simulator or device).
4. You can temporarily toggle network connectivity to simulate fetch failures.
5. Do **not** record PIN/JWT/PII in evidence captures; record only structural state and non-sensitive copy.

## Automated Preflight (Run First)

1. `rtk proxy bash scripts/verify-m007-s03.sh`
2. `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

Expected: both commands pass before final sign-off (platform constraints noted if running outside macOS).

## Manual Acceptance Scenarios

Mark each scenario with one outcome: `[x] PASS` or `[x] FAIL`, plus notes.

---

### 1) Populated search narrowing

**Steps**
1. Open **Transactions/History** with a populated list.
2. Enter a search query that should match only a subset (e.g., known type/date/amount fragment).
3. Observe the list update while search text is present.

**Expected**
- List narrows to matching rows only.
- No blocking error overlay appears during local narrowing.
- Clearing search restores the broader derived list.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 2) Filter switching (All / Debit / Credit)

**Steps**
1. With populated transactions visible, use the segmented filter control.
2. Switch through **All**, **Debit**, and **Credit**.
3. Optionally keep a search query active while switching filters.

**Expected**
- Each filter selection updates visible rows accordingly.
- Combined search+filter behavior remains coherent.
- "Clear Search & Filter" resets both controls.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 3) No-match recovery path

**Steps**
1. Apply a query/filter combination guaranteed to produce zero matches.
2. Confirm the dedicated "No matching transactions" state appears.
3. Tap **Clear Search & Filter** from that state.

**Expected**
- Filtered-empty card appears (not base-empty card).
- Recovery CTA is actionable and restores non-empty results (when source data exists).
- User is not dead-ended.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 4) Load-more continuity (happy path)

**Steps**
1. Scroll to/present the bottom of a populated Transactions list where **Load More** is available.
2. Tap **Load More**.
3. Wait for pagination to complete.

**Expected**
- Additional older transactions append/appear.
- Existing rows remain visible during and after pagination.
- Pagination progress surface behaves correctly (button/progress swap).

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 5) Non-blocking pagination failure handling

**Steps**
1. Start from a populated list.
2. Temporarily disable network.
3. Tap **Load More** to force a pagination failure.
4. Re-enable network.
5. Tap **Retry Load More**.

**Expected**
- Pagination failure message/card appears.
- Previously loaded transactions remain visible (no blocking initial-error takeover).
- Retry recovers pagination once connectivity is restored.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 6) Initial-load failure and retry

**Steps**
1. Fully restart to a fresh Transactions load with network disabled.
2. Confirm initial-load error card appears.
3. Re-enable network.
4. Tap **Retry**.

**Expected**
- Dedicated initial-load error surface appears when base load fails.
- Retry loads transactions successfully once network is available.
- Initial-error state does not persist after successful reload.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

## Final Slice-UAT Sign-off

- [ ] All six scenarios marked PASS
- [ ] Automated preflight command(s) run and recorded
- [ ] No sensitive credentials/PII captured in artifacts
- Sign-off name/date:
