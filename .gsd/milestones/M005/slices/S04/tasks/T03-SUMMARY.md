---
id: T03
parent: S04
milestone: M005
provides:
  - QRModels.swift with QrCartItem, QrCartResponse, QrConfirmRequest, QrConfirmResponse structs
  - QRPayViewModel.swift with QRPayState enum and async handleScannedURL/confirm methods
  - QRScannerView.swift (UIViewControllerRepresentable wrapping AVCaptureSession for QR scanning)
  - QRPayView.swift (SwiftUI view: scan → load → confirm → success/error state machine)
  - HomeView.swift "Pay with QR" button always visible with sheet presentation
  - project.pbxproj registered with AA000026-AA000029 build files, BB000026-BB000029 file refs, EE000017 QR group, camera usage description in both target configs
key_files:
  - mobile/ios/BankongSetonStudent/Models/QRModels.swift
  - mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift
  - mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift
  - mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift
  - mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift
  - mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj
key_decisions:
  - QRPayView uses @StateObject QRPayViewModel (not @Observable) to match existing ObservableObject pattern in the codebase
  - Sheet modifier placed on the Button itself (not on the VStack) to avoid multiple-sheet conflicts with other future sheets
  - camera usage description added as INFOPLIST_KEY_NSCameraUsageDescription in both Debug and Release target build configs (project uses GENERATE_INFOPLIST_FILE=YES — no separate Info.plist)
  - EE000017 assigned as QR group ID (next available after EE000016 LostCard group)
patterns_established:
  - pbxproj manual registration pattern: AA00002x (PBXBuildFile) + BB00002x (PBXFileReference) + EExxxxxx (PBXGroup) + FF000002 PBXSourcesBuildPhase entry
  - UIViewControllerRepresentable pattern: ScannerViewController holds AVCaptureSession; Coordinator implements AVCaptureMetadataOutputObjectsDelegate; starts/stops session in viewWillAppear/viewWillDisappear
observability_surfaces:
  - UI state transitions scanning→loading→confirming→success/error are the primary runtime signals
  - grep 'QRPayState\|QRPayViewModel' mobile/ios/BankongSetonStudent/ViewModels/ — verifies ViewModel present
  - grep 'showQrPay' mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift — confirms button wired
  - grep 'NSCameraUsageDescription' mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj — confirms camera permission registered
duration: 30m
verification_result: passed
completed_at: 2026-03-17
blocker_discovered: false
---

# T03: Build iOS QR views — AVFoundation scanner, confirmation, HomeView wiring, pbxproj registration

**Created 4 new Swift QR payment files, wired "Pay with QR" button in HomeView, and registered all files in project.pbxproj with camera usage description in both target build configs.**

## What Happened

T01 prerequisites were confirmed present: `APIClient.getQrCart(token:)`, `APIClient.confirmQrPayment(token:)`, `jwtRequest()` helper, `APIEndpoints.qrCart`, `APIEndpoints.qrConfirm` all existed. The `APIError` enum had `httpError(Int)`, `unauthorized`, and `networkError(Error)` cases needed by QRPayViewModel.

Implemented all 4 Swift files and updated HomeView and project.pbxproj as specified in the plan:

1. **QRModels.swift** — 4 Codable structs: `QrCartItem`, `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse` (with `new_balance` CodingKey mapping)
2. **QRPayViewModel.swift** — `@MainActor ObservableObject` with `QRPayState` enum (scanning/loading/confirming/success/error); handles 402/404/410/401/network errors with specific user messages
3. **QRScannerView.swift** — `UIViewControllerRepresentable` wrapping `ScannerViewController` which uses `AVCaptureSession`+`AVCaptureMetadataOutput`; Coordinator implements `AVCaptureMetadataOutputObjectsDelegate`; starts/stops session in `viewWillAppear`/`viewWillDisappear`
4. **QRPayView.swift** — SwiftUI state machine switching on `viewModel.state`; scanning shows full-screen camera; confirming shows cart items with Pay Now button; success shows checkmark with auto-dismiss at 3s; error shows specific message with Close button
5. **HomeView.swift** — Added `@State private var showQrPay = false`; added always-visible "Pay with QR" button after balance card using `Label("Pay with QR", systemImage: "qrcode.viewfinder")`; sheet presents `QRPayView` with success callback that refreshes balance
6. **project.pbxproj** — Added PBXBuildFile AA000026-AA000029, PBXFileReference BB000026-BB000029, PBXGroup EE000017 (QR, path=QR), all 4 files in PBXSourcesBuildPhase FF000002, INFOPLIST_KEY_NSCameraUsageDescription in FF000013 (Debug) and FF000014 (Release) target build configs

Also added `## Observability Impact` section to T03-PLAN.md (pre-flight requirement).

## Verification

All 5 T03 plan verification commands pass:
```
OK: QRPayView in HomeView
OK: QRScannerView uses AVFoundation
OK: new IDs in pbxproj
OK: QRModels.swift exists
OK: camera usage description
```

Additional deep checks pass:
- 8 occurrences of AA00002[6-9] in pbxproj (2 each: PBXBuildFile + PBXSourcesBuildPhase)
- 2 occurrences of NSCameraUsageDescription (Debug + Release target configs)
- EE000017 QR group present
- All 4 model structs (QrCartItem/QrCartResponse/QrConfirmRequest/QrConfirmResponse) in QRModels.swift
- httpError(402) handler in QRPayViewModel.swift

S04 slice artifact checks pass:
```
OK: QRPayView.swift
OK: pbxproj has QR file entries
```

## Diagnostics

- **Camera permission denied at runtime:** `ScannerViewController.setupSession()` returns early (guard fails on device input) — scanner shows black screen, no crash; fix: check device Settings > Privacy > Camera
- **iOS 401 on QR endpoints:** `KeychainHelper.read(forKey:"jwt_token")` is nil — add `print("jwt stored: \(KeychainHelper.read(forKey:"jwt_token") != nil)")` in AuthManager.login to confirm Keychain write
- **QRPayView not opening:** check `showQrPay` state var is in HomeView struct (not in nested view); confirm APIClient is provided as environmentObject in MainTabView/ContentView
- **pbxproj syntax broken:** `plutil -lint mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` on macOS confirms validity

## Deviations

None — implementation followed T03-PLAN.md exactly.

## Known Issues

None.

## Files Created/Modified

- `mobile/ios/BankongSetonStudent/Models/QRModels.swift` — new; 4 QR model structs
- `mobile/ios/BankongSetonStudent/ViewModels/QRPayViewModel.swift` — new; QRPayState enum + async ViewModel
- `mobile/ios/BankongSetonStudent/Views/QR/QRScannerView.swift` — new; UIViewControllerRepresentable with AVFoundation
- `mobile/ios/BankongSetonStudent/Views/QR/QRPayView.swift` — new; SwiftUI state-machine payment view
- `mobile/ios/BankongSetonStudent/Views/Home/HomeView.swift` — added showQrPay state + Pay with QR button + sheet
- `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj` — registered 4 new files + EE000017 group + camera usage description
- `.gsd/milestones/M005/slices/S04/tasks/T03-PLAN.md` — added ## Observability Impact section (pre-flight)
