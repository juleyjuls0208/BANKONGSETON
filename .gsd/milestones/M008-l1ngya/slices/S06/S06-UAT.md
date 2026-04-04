# S06: Manual On-Device UAT Gate

**Milestone:** M008-l1ngya
**Written:** 2026-04-04

## UAT Type

- UAT mode: manual device acceptance
- Why this mode is required: automated contract tests verify source-level correctness and routing behavior, but physical device feel, animation responsiveness, and user-observable polish can only be assessed by a human on real iOS 17+ hardware.

## Preconditions

- Physical iOS 17+ device with BankongSetonStudent app installed.
- Device is connected to the same network as the backend API server.
- Google Sheets backend is accessible.
- App has been previously logged in and has a valid session token (or perform fresh login).

## UAT Scenarios

Complete each scenario and record the verdict (PASS / FAIL) with evidence (screenshot or written observation).

---

### S06-01: Login Flow

**Steps:**
1. Launch the app.
2. Observe the login screen: confirm it is in dark mode with no PIN field visible.
3. Enter a valid `student_id`.
4. Tap Sign In / Continue.
5. Observe the home screen loads.

**Expected:** Dark-mode login UI, no PIN field, login succeeds and navigates to home.

**Evidence:** Screenshot of login screen + home screen after login.

**PASS criteria:** All steps behave as expected.

---

### S06-02: Home Credit-Card Balance Hero + QR Entry CTA

**Steps:**
1. After login, confirm the home screen shows a credit-card-style balance hero (name + balance in card-like visual).
2. Confirm a QR entry CTA button is visible and tappable.

**Expected:** Credit-card balance display with name + balance. QR CTA button present.

**Evidence:** Screenshot of home screen.

**PASS criteria:** Both elements present and visually correct.

---

### S06-03: Transactions Filter Chips (QR Pay / Card Pay / Load)

**Steps:**
1. Navigate to the Transactions tab.
2. Observe the filter chip row at the top.
3. Confirm chips are labeled: "QR Pay", "Card Pay", "Load".
4. Confirm there is NO search bar visible.
5. Tap each filter chip and observe the list updates.

**Expected:** Three filter chips visible (QR Pay, Card Pay, Load), no search bar, list updates on chip tap.

**Evidence:** Screenshot of transactions screen showing filter chips and each filtered state.

**PASS criteria:** Filter chips present and functional, no search bar.

---

### S06-04: Budget Load / Save with Failure Visibility

**Steps:**
1. Navigate to the Budget tab.
2. Observe the current budget limit and monthly spend display.
3. Attempt to save a new budget limit (change the value and tap save).
4. Observe the result (success toast / error message).

**Expected:** Budget data loads from backend; save action produces a visible success or error state.

**Evidence:** Screenshot of budget screen and save result.

**PASS criteria:** Budget loads and save action is visible with a clear result state.

---

### S06-05: Settings Theme + Accent Persistence

**Steps:**
1. Navigate to the Settings tab.
2. Confirm the visible settings groups are limited to Appearance (theme + accent).
3. Tap Appearance and change the accent color.
4. Confirm the accent change is applied immediately.
5. Confirm there are no other settings groups (no payment methods, no personal info section).

**Expected:** Appearance controls only (theme toggle + accent color picker). No extraneous settings groups.

**Evidence:** Screenshot of Settings and Appearance screens.

**PASS criteria:** Appearance controls visible and functional, no unexpected settings groups.

---

### S06-06: QR Payment Continuity End-to-End

**Steps:**
1. On the Home screen, tap the QR CTA button.
2. Point the device camera at a valid QR code.
3. Observe the QR scan, loading state, confirmation screen, and success/failure result.
4. After completion, confirm you can navigate back to Home and the transaction appears in History.

**Expected:** QR scan → loading → confirm → success flows without crash or dead-end. Transaction appears in transaction history.

**Evidence:** Screenshots of QR scan flow and transaction history after payment.

**PASS criteria:** Full QR payment flow completes without crash or dead-end; transaction visible in history.

---

## Result Recording

For each scenario, record:

| Scenario | Verdict | Evidence | Notes |
|----------|---------|----------|-------|
| S06-01 | PASS/FAIL | screenshot reference | |
| S06-02 | PASS/FAIL | screenshot reference | |
| S06-03 | PASS/FAIL | screenshot reference | |
| S06-04 | PASS/FAIL | screenshot reference | |
| S06-05 | PASS/FAIL | screenshot reference | |
| S06-06 | PASS/FAIL | screenshot reference | |

**Overall S06 Verdict:** PASS (all scenarios pass) / PARTIAL (some scenarios fail) / FAIL (blocker scenario fails)

## Failure Handling

If any scenario fails:
1. Record the failure scenario ID and failure description.
2. Screenshot the failure state.
3. Report the failure to the development team before re-running the milestone.
4. Do NOT mark the milestone as complete until all required scenarios pass.

## Exit Criteria

This UAT is complete only when:
- All six scenarios are executed with a recorded PASS/FAIL verdict.
- Any FAIL scenario has been resolved and re-tested with a PASS result.
- S06-UAT-RESULT.md is written with the final verdict table and evidence references.
