---
sliceId: S02
uatType: artifact-driven
verdict: PASS
date: 2026-03-22T15:39:00+00:00
---

# UAT Result — S02

## Checks

| Check | Mode | Result | Notes |
|-------|------|--------|-------|
| Home QR-only entry | artifact | PASS | `HomeView.swift` exposes a single `Pay with QR` CTA and explicit `home-qr-pay-button` identifier (`lines 42/44/52`). No payment-method chooser text/options were found in the Home QR entry surface. |
| Valid **token-only** scan happy path | artifact | PASS | `QRPayViewModel.swift` accepts token payloads and gates scans to scanning state (`lines 18-31`), then transitions through `loading → confirming → success` (`lines 27/31/88`). `QRPayView.swift` includes explicit `Confirm QR Payment` action (`line 114`) and success completion/dismiss (`Done`, `onSuccess`, `dismiss`; lines `147-149`, auto-dismiss `157-158`). |
| Post-success continuity refresh | artifact | PASS | `HomeView.swift` wires `QRPayView { ... }` success callback to `viewModel.load(...)` refresh (`lines 54-56`), and existing refresh surfaces remain (`refreshable`/`task` load lines `112/115`). |
| Invalid/expired QR path | artifact | PASS | Invalid payloads set explicit invalid-QR error (`QRPayViewModel.swift` line `23`), and expired/cart-confirm failures (`404/410`) map to expiry message (`lines 32/91`). Error UI provides actionable controls: `Retry Scan`, `Close`, and flow `Cancel` (`QRPayView.swift` lines `183/188/43`). |
| Insufficient balance path | artifact | PASS | Confirm path handles `APIError.httpError(402)` and surfaces insufficient-balance messaging (`QRPayViewModel.swift` lines `89-90`), with retry/close/cancel controls available in error flow (`QRPayView.swift` lines `183/188/43`). |
| Camera denied path | artifact | PASS | `QRScannerView.swift` now checks camera authorization and request flow (`authorizationStatus` line `50`, `requestAccess` line `56`), emits denied guidance (`lines 62/68`), and QR error UI exposes `Open Settings` plus retry/close actions (`QRPayView.swift` lines `177/183/188`). |
| Retry from non-happy path | artifact | PASS | `Retry Scan` triggers `viewModel.reset()` (`QRPayView.swift` lines `183-184`) and `reset()` returns to `.scanning` (`QRPayViewModel.swift` lines `103-104`). Scan processing is additionally guarded to scanning state (`lines 18/77`) to prevent duplicate/non-scanning races. |

## Overall Verdict

PASS — S02 QR-only Home+QR flow now satisfies the checklist as artifact-verifiable behavior and state-contract evidence.

## Notes

- Evidence was re-validated after code fixes using deterministic source-contract checks:
  - `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift`
  - `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift`
  - `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift`
  - `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- Artifact contract command executed successfully: `rtk proxy python -c "..."` → `S02 artifact contract PASS`.
- Live device/simulator confirmation is still recommended for milestone final acceptance, but S02 is no longer blocked on a `PARTIAL` UAT verdict.
