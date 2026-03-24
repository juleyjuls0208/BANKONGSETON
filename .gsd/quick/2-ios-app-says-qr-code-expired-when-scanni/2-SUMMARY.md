# Quick Task: iOS app says QR Code expired when scanning qr code

**Date:** 2026-03-24
**Branch:** gsd/quick/2-ios-app-says-qr-code-expired-when-scanni

## What Changed
- Added QR endpoint override support in iOS networking so QR flows can call a trusted scanned QR URL base (including LAN cashier hosts) instead of always forcing the hardcoded cloud API base.
- Updated `QRPayViewModel` to persist and reuse the resolved QR API base across both cart fetch and confirm requests, preventing false “QR expired” errors when the scanned QR points to a valid trusted non-default host.
- Implemented trusted-host safeguards for URL-based QR payloads (default API host over HTTPS, localhost, `.local`, and private IPv4 ranges) to avoid sending JWTs to untrusted hosts.
- Added contract tests covering the new endpoint-override behavior and trusted URL handling.

## Files Modified
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `tests/test_verify_quick_q2_ios_qr_endpoint_contract.py`

## Verification
- Ran:
  - `rtk proxy python -m pytest tests/test_verify_m007_s02_qr_behavior_contract.py tests/test_verify_m007_s02_qr_design_contract.py tests/test_verify_quick_q2_ios_qr_endpoint_contract.py`
- Result: **12 passed**.
- Verified both default-token flow contracts and the new URL-host override contracts remain intact.
