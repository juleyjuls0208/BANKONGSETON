# M007 / S05 Settings Persistence + Scope-Clean UAT Checklist

This checklist is the manual acceptance companion for `scripts/verify-m007-s05.sh`.
Use it to close S05 demo readiness on simulator/device without rediscovering scope.

## Inputs / Reusable References

- Automated verifier: `scripts/verify-m007-s05.sh`
- Behavior contract: `tests/test_verify_m007_s05_settings_behavior_contract.py`
- Design contract: `tests/test_verify_m007_s05_settings_design_contract.py`
- Settings view model: `mobile/ios/BankongSetonStudent/ViewModels/SettingsViewModel.swift`
- Settings screen: `mobile/ios/BankongSetonStudent/Views/Settings/SettingsView.swift`
- Shared accent consumers:
  - `mobile/ios/BankongSetonStudent/App/ContentView.swift`
  - `mobile/ios/BankongSetonStudent/UI/Shell/StitchTabShell.swift`
  - `mobile/ios/BankongSetonStudent/UI/Components/StitchPrimaryButtonStyle.swift`

## Preconditions

1. iOS app builds and launches on simulator/device.
2. Tester can sign in and reach Home + Settings.
3. Tester can terminate and relaunch the app (to validate persisted settings).
4. Do **not** capture personal info values, auth tokens, or other sensitive data in notes/screenshots.

## Automated Preflight (Run First)

1. `rtk proxy python -m pytest -q tests/test_verify_m007_s05_settings_behavior_contract.py tests/test_verify_m007_s05_settings_design_contract.py`
2. `rtk proxy sh scripts/verify-m007-s05.sh`
3. `rtk proxy bash scripts/verify-m007-s05.sh`
4. `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build`

Shell fallback note:
- If `/bin/bash` is unavailable in the current host (common on Windows-only harnesses), use `rtk proxy sh scripts/verify-m007-s05.sh` as the executable verifier path and record the bash limitation in UAT notes.

## Manual Acceptance Scenarios

Mark each scenario with exactly one outcome: `[x] PASS` or `[x] FAIL`, then add short notes.

---

### 1) Personal-info save + in-app persistence

**Steps**
1. Open **Settings**.
2. Update **Display name**.
3. Tap **Save Personal Info**.
4. Navigate to Home, then return to Settings.

**Expected**
- Save action is enabled and actionable.
- Status transitions from idle/applying to saved (`Personal info saved on this device.`).
- Edited display name remains populated after leaving and re-entering Settings.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 2) Personal-info persistence after app relaunch

**Steps**
1. After scenario 1 succeeds, terminate the app.
2. Relaunch and sign back into the same account (if needed).
3. Open **Settings** and **Home**.

**Expected**
- Persisted display name remains available in Settings after relaunch.
- Home resolves display name through settings-first fallback path (without requiring a backend profile write).

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 3) Accent apply + shared-surface propagation

**Steps**
1. Open **Settings → Appearance**.
2. Select a non-default accent option.
3. Tap **Apply Accent**.
4. Navigate across tabs and screens containing shared controls.

**Expected**
- Accent status transitions to saved (`Accent applied across the app.`).
- Accent color is reflected beyond Settings (tab shell + primary action buttons).
- No dead/decorative apply controls remain.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 4) Accent persistence after app relaunch

**Steps**
1. After scenario 3, terminate the app.
2. Relaunch and navigate through shell + primary-action surfaces.

**Expected**
- Selected accent remains active after relaunch.
- Shared shell/button accent remains coherent with the selected/persisted color.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 5) Scope-clean Settings surface

**Steps**
1. Open **Settings**.
2. Inspect all visible groups/actions.

**Expected**
- In-scope actionable controls remain: Personal Info save, Appearance apply, Report Lost Card, Logout.
- Out-of-scope/dead controls are absent: `Privacy & Security`, `Tuition Auto-Pay`, `Campus Discounts`, payment-method management.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

---

### 6) Lost-card and logout continuity

**Steps**
1. In **Settings**, tap **Report Lost Card** and confirm navigation enters lost-card flow.
2. Return to Settings.
3. Tap **Logout**.

**Expected**
- Lost-card route is actionable (no dead link).
- Logout button is actionable and transitions session state coherently.
- No inert account-action buttons remain.

**Result**
- [ ] PASS
- [ ] FAIL
- Notes:

## Final Slice-UAT Sign-off

- [ ] All six scenarios marked PASS
- [ ] Automated preflight outputs captured (or platform-limitation note added)
- [ ] No sensitive personal data captured in evidence
- Sign-off name/date:
