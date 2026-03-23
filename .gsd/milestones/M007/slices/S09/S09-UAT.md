# S09 UAT Checklist (Post-Override Closure Run)

## Device & Build Context

- Milestone/Slice: **M007 / S09**
- App target: `BankongSetonStudent` (`mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj`)
- Required runtime: **Apple-capable host + physical iOS 17+ device**
- Tester: ____________________
- Date: ____________________
- Device model: ____________________
- iOS version: ____________________
- App build identifier (commit/build no.): ____________________

## Preconditions

1. Latest S09 override code is installed (dark-mode default, no PIN login, `QR Pay`/`Card Pay`/`Load` filters).
2. Student test account exists and can sign in via **Student ID only**.
3. Cashier can issue valid and invalid/expired QR tokens.
4. Test account has enough balance for one successful payment.
5. Transaction history has enough records to test search + filters + load-more.
6. Budget/settings/lost-card backend paths are reachable.

## Automated Preflight (must run before manual UAT)

- [ ] `rtk proxy python -m pytest -q tests/test_verify_m007_s09_runtime_contract.py tests/test_verify_m007_s09_evidence_contract.py tests/test_verify_m007_s09_override_contract.py`
- [ ] `rtk proxy sh scripts/verify-m007-s09.sh`
- [ ] `rtk proxy python -c "from pathlib import Path; login=Path('mobile/ios/BankongSetonStudent/Views/Auth/LoginView.swift').read_text(encoding='utf-8'); assert 'PIN' not in login, 'PIN UI still present'; tx=Path('mobile/ios/BankongSetonStudent/Views/Transactions/TransactionsView.swift').read_text(encoding='utf-8'); required=['QR Pay','Card Pay','Load']; missing=[x for x in required if x not in tx]; assert not missing, missing"`
- [ ] `rtk proxy python -c "from pathlib import Path; app=Path('mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift').read_text(encoding='utf-8'); assert '.dark' in app or 'UIUserInterfaceStyle' in app, 'dark-mode startup marker missing'"`

If Apple tooling is unavailable, record full stderr and mark runtime gate blocked (do not mark PASS).

---

## Override-Specific Acceptance Matrix

| ID | Checkpoint | Result (PASS/FAIL) | Evidence (short note + screenshot/log ref) |
|---|---|---|---|
| OVR-01 | Dark mode on first render after cold launch | ____ | ____ |
| OVR-02 | Login flow has no PIN field and succeeds via Student ID | ____ | ____ |
| OVR-03 | Transactions chips show exactly `QR Pay`, `Card Pay`, `Load` | ____ | ____ |
| OVR-04 | Legacy labels (`Debit`, `Credit Card`) are absent | ____ | ____ |

## Full Journey Acceptance Matrix (S07 scenarios required by S09 closure)

| ID | Checkpoint | Result (PASS/FAIL) | Evidence (short note + screenshot/log ref) |
|---|---|---|---|
| S07-01 | Login → Home bootstrap continuity | ____ | ____ |
| S07-02 | Home control actionability + QR entry | ____ | ____ |
| S07-03 | QR happy path + one-shot success completion | ____ | ____ |
| S07-04 | QR failure + retry recovery | ____ | ____ |
| S07-05 | Post-QR continuity refresh + receipt access | ____ | ____ |
| S07-06 | Transactions search/filter/load-more + retry | ____ | ____ |
| S07-07 | Budget load/save + retry behavior | ____ | ____ |
| S07-08 | Settings persistence + lost-card actionability | ____ | ____ |
| S07-09 | Logout/login continuity with persisted local settings | ____ | ____ |
| S07-10 | Reduce Motion parity across full journey | ____ | ____ |
| S07-11 | Reduce Motion failure/retry parity | ____ | ____ |

---

## Detailed Test Cases

### OVR-01 — Dark mode default on first render

**Steps**
1. Ensure app is terminated.
2. Launch app from cold start.
3. Observe login screen and top-level shell colors.

**Expected outcomes**
- App starts in dark-mode visuals without requiring manual theme toggle.
- No bright/light legacy startup frame flashes before dark UI settles.

**Edge case**
- Relaunch app after sign-out and confirm dark-mode default still holds.

---

### OVR-02 — PIN-free login contract

**Steps**
1. Open login screen.
2. Confirm only Student ID input is visible.
3. Enter valid Student ID and sign in.

**Expected outcomes**
- No PIN field, PIN hint, or PIN validation message appears.
- Sign-in succeeds and lands on Home.

**Edge case**
- Enter invalid/unknown Student ID and confirm failure message is actionable (no PIN-related copy appears).

---

### OVR-03 / OVR-04 — Transactions taxonomy and legacy-label absence

**Steps**
1. Navigate to Transactions tab.
2. Inspect filter chip labels.
3. Tap each chip (`QR Pay`, `Card Pay`, `Load`) and observe list change.
4. Search UI text for any legacy labels (`Debit`, `Credit Card`).

**Expected outcomes**
- Only `QR Pay`, `Card Pay`, `Load` are shown as payment-type filters.
- Legacy labels are not visible anywhere on this surface.
- Chip selection updates filtered rows without dead controls.

**Edge case**
- Combine a chip with search text; clear both and verify list returns to full loaded set.

---

### S07-01..S07-11 — Full integrated journey replay (post-override)

Execute the same journey contract from S07 with S09 overrides in place. For each scenario row, mark PASS/FAIL and capture evidence.

**Expected global outcomes**
- No visible in-scope control is dead.
- QR-only payment flow remains intact.
- Transactions behavior (search/filter/load-more/error retry) remains functional with new taxonomy.
- Settings persistence and lost-card flows remain actionable.
- Reduce Motion does not break actionability or failure/retry semantics.

**Critical edge checks**
- QR failure recovery returns to a usable scan state.
- Pagination retry does not wipe already loaded transactions.
- Logout/login cycle preserves local settings but does not break QR entry.

---

## Final Sign-off Block

- Runtime verifier overall verdict (`S09-RUNTIME-PROOF.json`): ____________________
- Override checkpoints overall: ____________________
- S07 scenario matrix overall: ____________________
- Blocking defects found: ____________________
- Environment constraints (if any): ____________________
- Final S09 UAT verdict: **PASS / FAIL**
- Sign-off (tester + date): ____________________

## Evidence & Redaction Notes

- Do not capture secrets, auth tokens, or personal data values.
- Prefer structural evidence: scenario ID, visible state, control actionability, verifier phase output.
- Attach artifact references:
  - Runtime proof: `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.json`
  - Human proof: `.gsd/milestones/M007/slices/S09/S09-RUNTIME-PROOF.md`
  - UAT result: `.gsd/milestones/M007/slices/S09/S09-UAT-RESULT.md`
