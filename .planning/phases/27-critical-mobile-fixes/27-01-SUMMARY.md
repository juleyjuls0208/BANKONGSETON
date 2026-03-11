# Phase 27-01 Summary — iOS Critical Fixes

**Completed:** 2026-03-09  
**Requirements:** REQ-BUG-MOB-01, REQ-BUG-MOB-03

## What Was Done

### Task 1: Student model + APIClient hardening
- Added `cardStatus: String?` (mapped to `"card_status"`) to `Student` struct in `LoginModels.swift`
- Added `case invalidURL` to `APIError` enum in `APIClient.swift`
- Replaced 2 `fatalError("Invalid URL")` calls with `throw APIError.invalidURL` — app can no longer crash on invalid URLs

### Task 2: AuthManager — isCardLost persistence fix
- Removed `"isCardLost"` from the `keysToDelete` array in `clearAll()` — the flag now survives logout as intended
- Added conditional clearance in `login()`: when `student.cardStatus == "active"`, calls `KeychainHelper.delete(forKey: "isCardLost")` — stale lost-card state is cleared on confirmed card reactivation

## Files Modified
- `mobile/ios/BankongSetonStudent/Models/LoginModels.swift`
- `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
- `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`

## Verification
- Zero `fatalError` calls remain in APIClient.swift ✅
- `isCardLost` appears only in `handleCardLost()` (save) and `login()` (delete when active), NOT in `clearAll()` ✅
- `cardStatus: String?` field present in Student struct ✅
