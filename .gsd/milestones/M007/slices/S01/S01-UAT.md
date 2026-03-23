# S01: Design System + Navigation Shell Rework — UAT

**Milestone:** M007
**Written:** 2026-03-23

## UAT Type

- UAT mode: mixed (artifact-driven + human-experience)
- Why this mode is sufficient: S01 changes are mostly visual/shell composition work; source-contract tests prove wiring, and manual app walkthrough proves no dead controls/regressed navigation in the redesigned shell.

## Preconditions

1. Run on a macOS host with Xcode (iOS Simulator available, iPhone 15 runtime preferred).
2. App builds for scheme `BankongSetonStudent`.
3. Test account credentials are available.
4. Do not capture PINs, auth tokens, or personal identifiers in evidence.

## Automated Preflight (Run First)

1. `rtk proxy python -m pytest -q tests/test_verify_m007_s01_design_system_contract.py`
2. `rtk proxy python -m pytest -q tests/test_verify_m007_s01_shell_login_contract.py`
3. `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

If command (3) cannot run in the current environment, record the platform limitation explicitly and do not mark runtime checks as passed.

## Smoke Test

1. Launch app in simulator.
2. Sign in successfully.
3. Confirm redesigned tab shell renders and all 4 tabs are tappable.
4. Return to Login by logging out or auth boundary flow.
5. **Expected:** login, shell, and navigation transitions all remain interactive with no dead in-scope control.

## Test Cases

### 1. Login visual + behavior continuity

1. Open app to Login screen.
2. Verify stitch-style form/card presentation is visible (tokenized field/button/card styling).
3. Enter invalid credentials and submit.
4. Enter valid credentials and submit.
5. **Expected:**
   - Invalid submit surfaces error text.
   - Submit button follows loading/disabled behavior while auth is in flight.
   - Valid submit transitions to redesigned main tab shell.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

### 2. Tab shell routing + active-state feedback

1. From signed-in state, tap each tab in order: Home → Transactions → Budget → Settings.
2. Tap back and forth between non-adjacent tabs (e.g., Settings → Home → Transactions).
3. Observe selected-tab visual state each time.
4. **Expected:**
   - Each tab opens the correct destination view.
   - Selected state updates consistently for the active tab.
   - No tab tap is dead/inert.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

### 3. Session-boundary handling in shell

1. While signed in, trigger a session-boundary event (e.g., forced logout path or session-expired alert path used by current build/test environment).
2. Acknowledge alert/action.
3. **Expected:**
   - User is returned to login gate cleanly.
   - No stuck intermediate shell state remains.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

### 4. Cross-screen style reuse proof (non-login destinations)

1. Navigate to Home and Transactions.
2. Inspect major surfaces (cards/list rows/CTA treatment) for shared visual language with Login + shell.
3. Interact with at least one Home action and one Transactions row interaction.
4. **Expected:**
   - Home/Transactions use the same base design language (spacing/radius/typography/surface depth).
   - Core interactions still work (no regression in tappable controls).

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

## Edge Cases

### Loading and error surfaces remain coherent

1. Introduce a temporary network failure (or use backend unavailability) during login and transactions/home refresh moments.
2. Recover network and retry.
3. **Expected:**
   - Error/loading states are visible and understandable.
   - Recovery path returns to normal interactive state without app restart.

## Failure Signals

- Login CTA becomes visually present but not actionable.
- Any tab is tappable but does not change destination.
- Session-boundary flow leaves app stranded in signed-in shell.
- Home/Transactions regress to mixed ad hoc styling or broken row interactions.
- Preflight tests fail (`test_verify_m007_s01_design_system_contract.py` or `test_verify_m007_s01_shell_login_contract.py`).

## Requirements Proved By This UAT

- **R055** — Stitch-faithful visual foundation is visible across login + tab shell + downstream destinations.
- **R056 (partial)** — No dead in-scope controls in S01 surfaces (login submit + tab shell interactions + key downstream actions).

## Not Proven By This UAT

- Full QR flow redesign behavior (S02 scope).
- Transactions search/filter and complete state-fidelity matrix (S03 scope).
- Budget/receipt/lost-card redesign completeness (S04 scope).
- Settings persistence/scope cleanup (S05 scope).
- Motion/performance tuning on physical iOS 17+ device (S06/S07 scope).

## Notes for Tester

- Treat preflight test outputs + runtime walkthrough evidence together; do not accept one without the other.
- If Xcode/simulator is unavailable in the current host, keep this UAT marked incomplete and record the environment blocker.
- Capture concise notes focused on pass/fail behavior; avoid sensitive data in screenshots/logs.
