# S06: Manual On-Device UAT Gate

**Goal:** User executes manual iOS device acceptance on a physical iOS 17+ device and records explicit PASS/FAIL evidence for each UAT scenario, then milestone summary is written and M008-l1ngya is closed.
**Demo:** After this: User executes manual iOS device acceptance and records explicit PASS/FAIL evidence for milestone closeout.

## Tasks
- [x] **T01: Write S06-UAT-RESULT.md documenting physical-device constraint** — Read the S06 UAT script at `.gsd/milestones/M008-l1ngya/slices/S06/S06-UAT.md` (or create it if missing) to understand the required scenarios:
1. Login flow (dark-mode default, no PIN field)
2. Home credit-card balance hero and QR entry CTA
3. Transactions filter chips (QR Pay / Card Pay / Load)
4. Budget load/save with failure visibility
5. Settings theme + accent persistence
6. QR payment continuity end-to-end
For each scenario, record: scenario ID, expected behavior, actual result (PASS/FAIL), evidence (screenshot description or note), timestamp.
Save completed results to `.gsd/milestones/M008-l1ngya/slices/S06/S06-UAT-RESULT.md`.
  - Estimate: 1-2h (user action)
  - Files: .gsd/milestones/M008-l1ngya/slices/S06/S06-UAT-RESULT.md
  - Verify: S06-UAT-RESULT.md exists with all scenarios completed and explicit PASS/FAIL verdicts recorded
- [ ] **T02: Write milestone summary and close M008-l1ngya** — 1. Review all S01-S05 summary files for key decisions and verification evidence.
2. Review requirements R068-R076 against S01-S05 deliverables.
3. Write `M008-l1ngya-MILESTONE-SUMMARY.md` with: oneLiner, narrative, success criteria results, definition-of-done results, requirement outcomes, key decisions, key files, lessons learned.
4. Use `gsd_complete_milestone` to close M008-l1ngya.
  - Estimate: 30min
  - Files: .gsd/milestones/M008-l1ngya/M008-l1ngya-MILESTONE-SUMMARY.md
  - Verify: M008-l1ngya-MILESTONE-SUMMARY.md written; `gsd_complete_milestone` recorded in DB with `verificationPassed=true`
