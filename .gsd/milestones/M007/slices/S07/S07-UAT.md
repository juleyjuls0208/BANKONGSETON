# S07 UAT Checklist

## Device & Build Context

- Milestone/Slice: **M007 / S07**
- App target: `BankongSetonStudent` (`mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj`)
- Required runtime: **physical iOS 17+ device**
- Test environment: school demo backend + cashier QR flow available
- Tester: ____________________
- Date: ____________________
- Device model: ____________________
- iOS version: ____________________
- Build identifier (commit/build no.): ____________________

### Preconditions

1. Student test account exists and can sign in.
2. Account has enough balance for one successful QR payment and at least one insufficiency/expired scenario can be triggered.
3. Cashier can generate a valid QR and (when needed) an expired/invalid QR for failure-path checks.
4. Transaction history has enough data to exercise search, filter, and load-more.
5. Settings screen can edit display name + accent locally.
6. Lost-card API path is reachable for report/retry/dismiss checks.

### Automated Preflight (run before manual walk)

- [ ] `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
- [ ] `rtk proxy sh scripts/verify-m007-s07.sh`
- [ ] `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
- [ ] `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

If `xcodebuild` is unavailable in the current harness, record exact stderr and continue manual device checks.

## Journey Checkpoints

| ID | Checkpoint | Result (PASS/FAIL) | Evidence (short note + screenshot/log ref) |
|---|---|---|---|
| S07-01 | Login → Home bootstrap continuity | ____ | ____ |
| S07-02 | Home control actionability + QR entry | ____ | ____ |
| S07-03 | QR happy path + one-shot success completion | ____ | ____ |
| S07-04 | QR failure + retry recovery | ____ | ____ |
| S07-05 | Post-QR continuity (Home refresh + receipt access from Home/Transactions) | ____ | ____ |
| S07-06 | Transactions search/filter/load-more + pagination retry | ____ | ____ |
| S07-07 | Budget loading/saving + failure-retry behavior | ____ | ____ |
| S07-08 | Settings local persistence + lost-card actionability | ____ | ____ |
| S07-09 | Logout/login continuity with persisted local settings | ____ | ____ |
| S07-10 | Reduce Motion parity across full journey | ____ | ____ |
| S07-11 | Reduce Motion failure/retry parity | ____ | ____ |

---

## Detailed Test Cases

### S07-01 — Login → Home bootstrap continuity

**Steps**
1. Launch app in signed-out state.
2. Sign in with the test student account.
3. Wait until Home is fully rendered.

**Expected outcomes**
- App lands on Home without spinner lock or navigation dead-end.
- Balance card, QR card, and recent transactions section are visible.
- No visible in-scope control appears disabled without reason.

**Edge checks**
- Pull-to-refresh on Home completes and does not break layout or controls.

---

### S07-02 — Home controls + QR entry actionability

**Steps**
1. Tap `Pay with QR` once.
2. Close QR view using `Cancel`.
3. Tap `Pay with QR` again.

**Expected outcomes**
- QR flow opens on each tap (no dead tap).
- Second open behaves the same as first open.
- Home remains responsive after returning.

**Edge checks**
- If scanner permission is denied, error state appears with actionable guidance (not silent failure).

---

### S07-03 — QR happy path + one-shot completion semantics

**Steps**
1. Scan a valid cashier QR.
2. Confirm cart details and tap `Confirm QR Payment`.
3. On success screen, tap `Done` once.
4. Repeat once without tapping `Done` and allow auto-dismiss timer.

**Expected outcomes**
- State progression is coherent: scanning → loading → confirming → success.
- Success completion executes once (no duplicate dismiss/refresh side effects).
- App returns to coherent post-payment state after either manual or auto completion.

**Edge checks**
- No duplicate transaction insertion due to double completion trigger.

---

### S07-04 — QR failure + retry recovery

**Steps**
1. Trigger QR failure using invalid/expired token (or simulated backend failure).
2. Confirm error message is visible and actionable.
3. Tap retry (`Retry Scan`) and scan a valid QR.
4. Complete payment successfully.

**Expected outcomes**
- Error state shows clear failure reason.
- Retry returns to active scan flow.
- User can recover to success without relaunching app.

**Edge checks**
- Camera-access failure path surfaces `Open Settings` action when applicable.

---

### S07-05 — Post-QR refresh + receipt access continuity

**Steps**
1. Immediately after successful QR completion, verify Home balance/recent list refresh.
2. Open receipt from Home recent transaction entry.
3. Navigate to Transactions tab and open receipt from transaction list.

**Expected outcomes**
- Home data reflects post-payment refresh (no stale pre-payment snapshot).
- Receipt route works from both Home and Transactions.
- Navigation back-stack remains stable.

**Edge checks**
- No out-of-scope receipt utility actions (Download PDF / Report Issue) appear.

---

### S07-06 — Transactions search/filter/load-more + retry continuity

**Steps**
1. Open Transactions tab.
2. Enter search term matching one known transaction.
3. Change segmented filter (`All`, `Debit`, `Credit`) and verify list recomputation.
4. Tap `Clear Search & Filter`.
5. Tap `Load More` until additional page is fetched.
6. If pagination error appears, tap `Retry Load More`.

**Expected outcomes**
- Search and filter recompute deterministically from loaded data.
- Clear button resets query+filter and restores full derived list.
- Load-more appends additional records and keeps existing list visible.
- Pagination failure is surfaced separately and can recover without wiping existing rows.

**Edge checks**
- Initial-load error and pagination error remain distinct (no incorrect empty-state swap).

---

### S07-07 — Budget load/save + retry behavior

**Steps**
1. Open Budget screen and wait for initial load.
2. Modify budget and save.
3. Trigger a save failure scenario (if available) and retry.

**Expected outcomes**
- Loading/success/error feedback is visible and understandable.
- Save action is always actionable when input is valid.
- Retry path recovers without forcing app restart.

**Edge checks**
- Budget value shown after save matches the last successful submission.

---

### S07-08 — Settings persistence + lost-card actionability

**Steps**
1. Open Settings.
2. Change display name and accent, then apply/save.
3. Navigate away and back to Settings.
4. Confirm changes persisted locally.
5. Open `Report Lost Card`.
6. Exercise report action; if error appears, test retry and dismiss controls.

**Expected outcomes**
- Display name/accent persist across navigation boundaries without backend write dependency.
- Lost-card flow exposes actionable report/retry/dismiss/done controls.
- Logout button remains actionable.

**Edge checks**
- Out-of-scope settings categories do not reappear (`Payment Method`, `Tuition Auto-Pay`, `Campus Discounts`, `Privacy & Security`).

---

### S07-09 — Logout/login continuity with persisted local settings

**Steps**
1. From Settings, tap logout.
2. Sign in again with same account.
3. Re-open Home/Settings.

**Expected outcomes**
- Logout/login cycle works without stuck auth state.
- Locally persisted display name/accent remain applied after re-login.
- Core demo flows remain actionable after auth boundary crossing.

**Edge checks**
- QR flow still opens normally after re-login.

---

### S07-10 — Reduce Motion parity (full replay)

**Steps**
1. Enable iOS **Reduce Motion**.
2. Replay S07-01 through S07-09 in abbreviated form.

**Expected outcomes**
- Animations are simplified/restrained.
- State changes remain understandable.
- No actionability regressions introduced by reduced-motion mode.

**Edge checks**
- No screen transition causes perceptible sluggishness or visual confusion.

---

### S07-11 — Reduce Motion failure/retry parity

**Steps**
1. Keep Reduce Motion ON.
2. Re-run failure/retry checks for:
   - QR error + retry
   - Transactions pagination retry
   - Budget save/retry

**Expected outcomes**
- Failure states remain explicit.
- Retry controls remain discoverable and functional.
- Recovery behavior matches default-motion behavior.

**Edge checks**
- No hidden transition suppresses critical error feedback.

## PASS / FAIL Summary

- Automated preflight overall: ____________________
- Manual checkpoints overall: ____________________
- Blocking defects found: ____________________
- Environment constraints (if any): ____________________
- Final S07 UAT verdict: **PASS / FAIL**
- Sign-off (tester + date): ____________________

## Evidence & Redaction Notes

- Do not capture credentials, auth tokens, or personal data values.
- Prefer structural evidence: screen names, state transitions, visible control actionability, verifier phase output.
- Attach artifacts/links:
  - Screenshots/video references: ____________________
  - Verifier output reference: ____________________
  - Additional notes: ____________________
