---
sliceId: S02
uatType: artifact-driven
verdict: PARTIAL
date: 2026-03-22T15:09:07.911658+00:00
---

# UAT Result — S02

## Checks

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| Home QR-only entry | artifact | PASS | Artifact check via `rtk proxy rg -n "Pay with QR|home-qr-pay-button|only payment method" mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` shows QR-only CTA (`Pay with QR`) and `home-qr-pay-button` (lines 102/106/114/117). `rtk proxy rg -n "Button\\s*\\{" ...` shows one actionable button in the entry card (line 111). No in-UI chooser labels found. |
| Valid **token-only** scan happy path | human-follow-up | NEEDS-HUMAN | Static evidence present: state machine includes `scanning/loading/confirming/success` (`QRPayViewModel.swift` lines 5-8), token-only acceptance via `isValidToken(payload)` (lines 131-132), and transitions to loading/confirming/success (lines 41/46/81/86). UI contains `Confirm QR Payment` (QRPayView line 198) and success dismiss (`Done` + `dismiss`, lines 239-241; auto-dismiss lines 254-255). Not executed with real camera + valid token payload. |
| Post-success continuity refresh | human-follow-up | NEEDS-HUMAN | Static wiring exists: `HomeView` presents `QRPayView` with success callback (lines 50-52), callback triggers `refreshAfterQRSuccess`, and refresh reloads balance + transactions (`HomeViewModel` lines 25-26 and 40-42). No live observation of immediate Home balance/transaction refresh after an actual payment confirmation. |
| Invalid/expired QR path | human-follow-up | NEEDS-HUMAN | Static handling exists: invalid payload error text (`QRPayViewModel` line 34), expired handling for cart/confirm 404/410 (lines 49 and 94), and actionable controls in error UI (`Retry Scan` line 289, `Close` line 292, `Cancel` toolbar line 27 in `QRPayView.swift`). Not live-tested with known invalid/expired QR payload to verify runtime behavior and no scanner stall. |
| Insufficient balance path | human-follow-up | NEEDS-HUMAN | Static handling exists: `confirm` catches `APIError.httpError(402)` (`QRPayViewModel` line 87) and surfaces `Insufficient balance...` (line 89), with actionable retry/close/cancel controls in error view (`QRPayView` lines 289/292/27). Not live-tested against a cart total above available balance. |
| Camera denied path | human-follow-up | NEEDS-HUMAN | Static handling exists: camera permission branches in `QRScannerView` (`authorizationStatus` line 80; denied/restricted messages lines 92/99/102), `Open Settings` action in error UI (`QRPayView` lines 280-283), plus retry/close controls (lines 289/292). Camera usage description present in project settings (`project.pbxproj` lines 551/579). Not executed with device/simulator camera permission actually denied. |
| Retry from non-happy path | human-follow-up | NEEDS-HUMAN | Static retry path exists: `Retry Scan` button calls `viewModel.reset()` (`QRPayView` line 289), `reset()` transitions back to `.scanning` (`QRPayViewModel` lines 116-117), and success path remains reachable (`confirm_success` transition line 86). Not runtime-validated by retrying from an error state then scanning a valid token. |

## Overall Verdict

PARTIAL — QR-only entry implementation is artifact-verified, but scan/permission/backend-dependent UAT scenarios require real device/simulator execution and remain human follow-up.

## Notes

- Evidence was collected via artifact inspection (`rtk proxy rg -n ...`) within `mobile/ios/BankongSetonStudent`.
- Because this slice checklist is explicitly manual and camera/runtime dependent, checks #2–#7 cannot be truthfully marked PASS without live execution on iOS simulator/device plus backend test payloads.
- Recommended manual follow-up: run rows #2, #4, #5, #6 first (required non-happy-path coverage), then re-run #7 retry continuity and #3 post-success refresh on the same build.
