---
sliceId: S07
uatType: artifact-driven
verdict: PARTIAL
date: 2026-03-23T15:32:22.670166+08:00
---

# UAT Result — S07

## Checks

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| Preconditions #1 — Student test account exists and can sign in. | human-follow-up | NEEDS-HUMAN | Requires real test account + live sign-in on physical iOS device; cannot be proven from artifacts alone in this harness. |
| Preconditions #2 — Account has enough balance for success + insufficiency/expired scenario. | human-follow-up | NEEDS-HUMAN | Requires live backend account state setup and cashier coordination; not verifiable from static artifacts. |
| Preconditions #3 — Cashier can generate valid and expired/invalid QR. | human-follow-up | NEEDS-HUMAN | Requires live cashier runtime + token generation checks on demo environment. |
| Preconditions #4 — Transaction history has enough data for search/filter/load-more. | human-follow-up | NEEDS-HUMAN | Requires seeded live data and on-device list behavior validation. |
| Preconditions #5 — Settings screen can edit display name + accent locally. | human-follow-up | NEEDS-HUMAN | Needs device interaction to confirm UI state persistence behavior end-to-end. |
| Preconditions #6 — Lost-card API path is reachable for report/retry/dismiss checks. | human-follow-up | NEEDS-HUMAN | Requires live API reachability from iOS runtime and exercised lost-card flow. |
| Automated preflight — `rtk proxy python -m pytest -q tests/test_verify_m007_s07_integration_behavior_contract.py tests/test_verify_m007_s07_scope_guard_contract.py` | runtime | PASS | Executed successfully; 8 tests passed. |
| Automated preflight — `rtk proxy sh scripts/verify-m007-s07.sh` | runtime | PASS | Executed successfully; phases `preflight`, `contract`, `scope`, `integration`, `diagnostic-surface` all passed. |
| Automated preflight — `rtk proxy python -c "from pathlib import Path; txt=Path('scripts/verify-m007-s07.sh').read_text(...); required=[...]; ..."` | artifact | PASS | Executed marker check; output `marker_check=passed` confirming required diagnostic markers (`fail_with_guidance`, `guidance=`, `phase=preflight`, `phase=diagnostic-surface`). |
| Automated preflight — `rtk proxy xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'platform=iOS Simulator,name=iPhone 15' build` | runtime | NEEDS-HUMAN | Harness lacks Apple build toolchain. Exact stderr: `Error: Failed to execute command: xcodebuild` / `program not found` (exit 1). Per UAT instruction, recorded and continued. |
| S07-01 — Login → Home bootstrap continuity | human-follow-up | NEEDS-HUMAN | Requires physical iOS 17+ device run to validate spinner lock/dead-end/actionability outcomes; not objectively executable in this artifact-only harness. |
| S07-02 — Home control actionability + QR entry | human-follow-up | NEEDS-HUMAN | Requires real UI taps, scanner permission behavior, and return-path responsiveness checks on device. |
| S07-03 — QR happy path + one-shot success completion | human-follow-up | NEEDS-HUMAN | Requires live cashier QR scan, payment confirmation, manual + auto-dismiss behavior observation, and duplicate side-effect validation in runtime. |
| S07-04 — QR failure + retry recovery | human-follow-up | NEEDS-HUMAN | Requires generating invalid/expired QR or backend failure live and verifying retry-to-success recovery in app runtime. |
| S07-05 — Post-QR continuity (Home refresh + receipt access from Home/Transactions) | human-follow-up | NEEDS-HUMAN | Requires post-payment live data refresh + receipt route checks via app navigation stack on device. |
| S07-06 — Transactions search/filter/load-more + pagination retry | human-follow-up | NEEDS-HUMAN | Requires on-device interaction with loaded transaction pages and induced pagination failure/retry behavior. |
| S07-07 — Budget loading/saving + failure-retry behavior | human-follow-up | NEEDS-HUMAN | Requires live budget API interactions and save failure simulation from app runtime. |
| S07-08 — Settings local persistence + lost-card actionability | human-follow-up | NEEDS-HUMAN | Requires on-device local persistence confirmation across navigation + lost-card report/retry/dismiss path execution. |
| S07-09 — Logout/login continuity with persisted local settings | human-follow-up | NEEDS-HUMAN | Requires actual auth boundary crossing on device and persisted settings re-check after re-login. |
| S07-10 — Reduce Motion parity across full journey | human-follow-up | NEEDS-HUMAN | Requires iOS Accessibility setting toggle + replay of journey to evaluate animation/actionability parity. |
| S07-11 — Reduce Motion failure/retry parity | human-follow-up | NEEDS-HUMAN | Requires live failure/retry scenarios while Reduce Motion is ON to confirm parity. |
| Readiness artifact presence (supporting evidence) — `.gsd/milestones/M007/slices/S07/S07-UAT.md` and `.gsd/milestones/M007/slices/S07/S07-DEMO-READINESS.md` | artifact | PASS | Executed `rtk proxy python -c ...`; output `readiness_docs=present`. |

## Overall Verdict

PARTIAL — All automatable S07 artifact/runtime preflight checks passed except simulator build could not be executed due missing `xcodebuild`, and all physical-device journey checks remain human-required.

## Notes

- Executed all automatable artifact-driven checks from S07-UAT.
- Verified integration/scope contracts and phased verifier pass in this harness.
- Environment constraint captured exactly for simulator build: `xcodebuild` not installed/available.
- Remaining S07-01..S07-11 checks require physical iOS 17+ device + live school demo backend/cashier flow to close as PASS/FAIL.
