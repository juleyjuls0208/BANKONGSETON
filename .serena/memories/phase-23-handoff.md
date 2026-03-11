# Phase 23 Handoff — iPhone App Version

## Status
Plans 01–05 are fully executed (Swift code written). Plan 06 (final gate) is next.

## What Was Built
All Swift source files for a SwiftUI iOS student app at:
`mobile/ios/BankongSetonStudent/`

| Plan | Contents | Status |
|------|----------|--------|
| 23-01 | Xcode project scaffold, KeychainHelper, APIClient, AuthManager, Models | ✅ Done |
| 23-02 | LoginView + LoginViewModel | ✅ Done |
| 23-03 | HomeView, TransactionsView, ReceiptView, MainTabView | ✅ Done |
| 23-04 | BudgetView + BudgetViewModel | ✅ Done |
| 23-05 | SettingsView, LostCardView, SettingsViewModel | ✅ Done |
| 23-06 | Final gate — NOT YET EXECUTED | ⬜ TODO |

## What Needs to Happen Next — Plan 06

Plan file: `.planning/phases/23-iphone-app-version/23-06-PLAN.md`

**Task 1 (auto):** Run build & invariant checks:
- `xcodebuild build -project mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj -scheme BankongSetonStudent -destination "generic/platform=iOS Simulator" CODE_SIGN_IDENTITY="" CODE_SIGNING_REQUIRED=NO`
- `grep -r "₱" mobile/ios/` → must be zero matches
- `grep -rn "NavigationView" mobile/ios/` → must be zero matches
- `grep -n "struct BudgetView\|struct SettingsView" mobile/ios/BankongSetonStudent/Views/MainTabView.swift` → must be zero matches
- Spot-checks for navigationDestination, NFC Payment synthetic row, Purchase filter strings, isCardLost Keychain save, no NFC in SettingsView

**Task 2 (human checkpoint — blocking):** Open Xcode on Mac, run on iOS Simulator, verify all 7 screens. Type "approved" to proceed.

**Task 3 (auto, after checkpoint approved):** Update planning artifacts:
- `.planning/ROADMAP.md` — mark all 23-0x-PLAN.md as [x], phase status → Complete
- `.planning/STATE.md` — advance current phase past 23
- `.planning/REQUIREMENTS.md` — mark REQ-23-01 through REQ-23-10 satisfied

Then write `.planning/phases/23-iphone-app-version/23-06-SUMMARY.md`.

## Key Technical Notes
- API base: `https://juley2823.pythonanywhere.com/api`
- Currency: ฿ (Thai Baht) only — NEVER ₱ (Philippine Peso)
- No NavigationView — NavigationStack only (iOS 16+)
- No NFC features on iOS
- Keychain keys: auth_token, student_id, student_name, last_balance, theme_mode, isCardLost, budget_alert_month, budgetAlerted80, budgetAlerted100
- CARD_LOST = special 403 handling → APIError.cardLost

## Working Directory
`C:/Users/admin/Desktop/projects/BANKONGSETON`

## gsd-tools path
`C:/Users/admin/.claude/get-shit-done/bin/gsd-tools.cjs`

## How to Continue
In the new chat, say:
> "Continue executing Plan 06 for Phase 23 (iPhone App Version). Read the handoff memory at phase-23-handoff."

Then run `gsd-executor` agent with Plan 06 context, or manually execute Task 1 checks, present the human checkpoint, then run Task 3 after approval.
