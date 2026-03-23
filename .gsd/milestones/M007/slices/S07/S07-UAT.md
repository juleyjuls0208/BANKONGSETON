# S07 UAT Checklist

## Device & Build Context

- Milestone: M007
- Slice: S07 — Final Integration + Device Demo Readiness Gate
- Platform target: iOS 17+
- Build target: `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj` (`BankongSetonStudent`)
- Tester name: _TBD_
- Date/time: _TBD_
- Device/simulator: _TBD_
- OS version: _TBD_
- Reduce Motion default at start: OFF

## Evidence Capture Rules (Redaction + Scope)

1. Do not record credentials, auth tokens, or personal data in notes/screenshots.
2. Evidence should be structural/state-based (screen names, state labels, control actionability, verifier output).
3. Keep scope aligned to S07: QR-only payment path, integrated refresh continuity, transactions/budget/settings/lost-card actionability.

## Automated Preflight (Run Before Manual Flow)

- [ ] `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py`
- [ ] `rtk proxy sh scripts/verify-m007-s07.sh`
- [ ] `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(encoding='utf-8'); required=['fail_with_guidance','guidance=','phase=preflight','phase=diagnostic-surface']; missing=[x for x in required if x not in txt]; assert not missing, missing"`
- [ ] `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

If `xcodebuild` is unavailable in this environment, mark as constrained and capture the exact stderr message.

## Journey Checkpoints

Record exactly one result per checkpoint (`PASS` or `FAIL`) and add short evidence notes.

| ID | Flow checkpoint | PASS criteria | FAIL criteria | Result | Evidence notes |
|---|---|---|---|---|---|
| S07-01 | Login → Home bootstrap continuity | Login succeeds, Home renders primary controls, no dead controls | App stalls, wrong route, or any control is non-actionable | _TBD_ | _TBD_ |
| S07-02 | Home controls + QR entry actionability | `Pay with QR` and other visible in-scope controls respond on first tap | Dead tap, delayed activation, or route mismatch | _TBD_ | _TBD_ |
| S07-03 | QR happy path (scan/confirm/success/done) | QR states transition correctly; Done exits once and continuity hook runs | Duplicate completion, stuck state, or missing success dismissal | _TBD_ | _TBD_ |
| S07-04 | QR failure + retry path | Error state visible; retry recovers to scan/confirm path with controls still live | Retry dead, error hidden, or unrecoverable loop | _TBD_ | _TBD_ |
| S07-05 | Post-QR refresh + receipt access | Home data refreshes; receipt accessible from Home and Transactions | Stale data, missing refreshed entry, or broken receipt route | _TBD_ | _TBD_ |
| S07-06 | Transactions search/filter/load-more | Search/filter/pagination all work; retry buttons recover from failures | Search/filter desync, load-more dead, or pagination failure unrecoverable | _TBD_ | _TBD_ |
| S07-07 | Budget load/save + retry behavior | Budget screen surfaces loading/success/error; retry/save controls remain actionable | Save/retry does nothing or state feedback is missing | _TBD_ | _TBD_ |
| S07-08 | Settings persistence + lost-card actions | Display/accent settings persist locally; lost-card report/retry/dismiss actions work | Persistence lost, missing action, or dead lost-card control | _TBD_ | _TBD_ |
| S07-09 | Logout/login continuity | Logout completes cleanly; relogin works; persisted local settings still present | Logout stuck, relogin broken, or persistence reset unexpectedly | _TBD_ | _TBD_ |
| S07-10 | Reduce Motion parity (full journey replay) | With Reduce Motion ON, transitions simplify without losing clarity/actionability | Missing feedback, hidden state transitions, or dead controls in reduced mode | _TBD_ | _TBD_ |
| S07-11 | Reduce Motion failure/retry parity | QR + Transactions + Budget retry/failure flows remain understandable/actionable | Failure paths become ambiguous or non-recoverable in reduced mode | _TBD_ | _TBD_ |

## Manual Scenario Steps (Detailed)

### S07-01: Login → Home bootstrap continuity (Default Motion)

**Steps**
1. Launch app signed out on iOS 17+.
2. Log in with test account.
3. Confirm Home appears with expected in-scope controls.

**Expected PASS behavior**
- Home appears without spinner lock.
- Primary controls are immediately actionable.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-02: Home controls + QR entry actionability (Default Motion)

**Steps**
1. Tap `Pay with QR` from Home.
2. Return and re-enter QR once to verify repeated actionability.

**Expected PASS behavior**
- QR sheet/screen opens consistently.
- No dead taps or delayed control activation.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-03: QR happy path continuity (Default Motion)

**Steps**
1. Complete scan/confirm flow with a valid QR payload.
2. Wait for success state and use `Done`.

**Expected PASS behavior**
- State path: scanning → loading → confirming → success.
- Success completion occurs once; app returns to coherent post-payment state.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-04: QR failure + retry path (Default Motion)

**Steps**
1. Trigger QR failure (invalid/expired payload or simulated failure).
2. Use retry action.
3. Complete a successful payment after retry.

**Expected PASS behavior**
- Error message is visible and actionable.
- Retry returns to active scan path and supports eventual success.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-05: Post-QR refresh + receipt access (Default Motion)

**Steps**
1. After successful QR payment dismissal, inspect Home balance/recent list.
2. Open receipt from Home recent transaction.
3. Navigate to Transactions and open receipt from list.

**Expected PASS behavior**
- Home refresh is visible after QR completion.
- Receipt route works from both Home and Transactions.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-06: Transactions search/filter/load-more + retry (Default Motion)

**Steps**
1. Enter search text; verify list narrows.
2. Apply transaction type filter; verify list updates.
3. Clear search/filter; verify list restores.
4. Trigger load-more; confirm pagination appends items.
5. If pagination error appears, use retry and confirm recovery.

**Expected PASS behavior**
- Search/filter are deterministic and reversible.
- Load-more/pagination error retry controls remain actionable.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-07: Budget load/save + failure/retry behavior (Default Motion)

**Steps**
1. Open Budget screen and wait for load state to resolve.
2. Edit budget value and save.
3. Trigger/save failure scenario if available and retry.

**Expected PASS behavior**
- State feedback is clear for loading/success/error.
- Save/retry controls always respond.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-08: Settings persistence + lost-card actionability (Default Motion)

**Steps**
1. Open Settings and change display name/accent.
2. Navigate away and back to confirm persisted values.
3. Open Lost Card from Settings.
4. Trigger report action; if error appears, retry/dismiss accordingly.

**Expected PASS behavior**
- Local settings persist across navigation boundaries.
- Lost-card report/retry/dismiss controls are actionable.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-09: Logout/login continuity with persisted local settings (Default Motion)

**Steps**
1. Logout from Settings.
2. Login again.
3. Confirm settings persistence and end-to-end flow remains coherent.

**Expected PASS behavior**
- Logout/login cycle is stable.
- Local display/accent persistence survives auth boundary.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-10: Reduce Motion parity (Full Journey)

**Steps**
1. Enable iOS Reduce Motion.
2. Replay S07-01 through S07-09 quickly.

**Expected PASS behavior**
- Motion is reduced/simplified while state transitions remain understandable.
- No feature/actionability regressions in reduced-motion mode.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

### S07-11: Reduce Motion failure/retry parity

**Steps**
1. Keep Reduce Motion enabled.
2. Trigger failure/retry flows in QR, Transactions, and Budget.

**Expected PASS behavior**
- Error and retry states remain explicit and usable.
- No hidden state jumps or dead retry controls.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes: _TBD_

## Failure / Retry Notes

- QR retry behavior evidence: _TBD_
- Transactions pagination retry evidence: _TBD_
- Budget save retry evidence: _TBD_
- Reduce Motion retry behavior evidence: _TBD_

## PASS / FAIL Summary

- Automated preflight status: _TBD_
- Manual checkpoint status: _TBD_
- Overall S07 UAT verdict: _TBD_ (PASS / FAIL)
- Blocking issues (if FAIL): _TBD_
- Environment constraints (if any): _TBD_
- Evidence links / artifact paths: _TBD_
- Sign-off (name/date): _TBD_
