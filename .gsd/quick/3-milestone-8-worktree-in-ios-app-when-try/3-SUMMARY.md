# Quick Task: milestone 8 worktree. in ios app, when trying to scan, it says "QR Code Expired."

**Date:** 2026-03-25
**Branch:** gsd/quick/3-milestone-8-worktree-in-ios-app-when-try

## What Changed
- Fixed iOS QR payment networking to use a dedicated QR backend default (`https://bankoseton.pythonanywhere.com/api`) instead of the general student API base URL.
- Updated QR API request builder to support endpoint-specific fallback base URLs while still honoring trusted QR URL overrides from scanned payloads.
- Expanded trusted QR host checks to include both configured public API hosts (student + QR) and improved fallback log wording.

## Files Modified
- `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift`
- `.gsd/quick/3-milestone-8-worktree-in-ios-app-when-try/3-SUMMARY.md`

## Verification
- Verified diffs to ensure QR cart fetch and QR confirm now default to `APIEndpoints.qrBaseURL`.
- Attempted build verification with:
  - `rtk xcodebuild -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination 'generic/platform=iOS Simulator' build` (failed: `rtk` has no `xcodebuild` subcommand)
  - `rtk proxy xcodebuild ...` (failed: `xcodebuild` not installed in this environment)
- Attempted LSP diagnostics on Swift files (failed: no Swift language server available in this environment).
