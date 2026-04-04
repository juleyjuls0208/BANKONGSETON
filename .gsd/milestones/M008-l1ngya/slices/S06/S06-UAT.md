# S06: Manual On-Device UAT Gate — UAT

**Milestone:** M008-l1ngya
**Written:** 2026-04-04T09:55:11.734Z

## UAT Type

- UAT mode: manual-device-acceptance
- Verdict: BLOCKED — Physical iOS 17+ device required
- All six scenarios documented with BLOCKED verdict and prior automated coverage references

## Preconditions

- Physical iOS 17+ device (iPhone or iPad)
- BankongSetonStudent app installed via Apple Developer provisioning profile
- Backend API running on the same network
- S06-UAT-RESULT.md consulted for prior automated coverage context

## Completion Instructions

1. Acquire physical iOS 17+ device
2. Install BankongSetonStudent app
3. Ensure backend is running
4. Execute scenarios S06-01 through S06-06
5. Update S06-UAT-RESULT.md with actual PASS/FAIL verdicts and screenshot evidence
6. Proceed to milestone close

## Prior Automated Coverage

tests/test_verify_m008_s05_ios_integration_contract.py (17 assertions) covers all surfaces validated at source level before device testing.
