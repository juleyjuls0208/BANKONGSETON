# Plan 23-01 Summary: Xcode Project Skeleton + Core Infrastructure

**Phase:** 23-iphone-app-version  
**Plan:** 01 — Wave 1  
**Completed:** 2026-03-09  
**Status:** DONE

---

## What Was Built

### Xcode Project
- `BankongSetonStudent.xcodeproj/project.pbxproj` — hand-crafted on Windows (no Xcode CLI available). References all 24 final Swift source files across all plans so the `.pbxproj` never needs editing again. Bundle ID: `com.bankongseton.student`, min iOS 16.0, Swift 5.0.

### Core Infrastructure (6 Swift files)
- **`App/BankongSetonStudentApp.swift`** — `@main` entry point; injects `AuthManager` and `APIClient` as `@EnvironmentObject` at the root `ContentView`.
- **`App/ContentView.swift`** — Routes to `LoginView()` when `authManager.isLoggedIn == false`, otherwise `MainTabView()`. Includes stub `LoginView` and stub `MainTabView` (replaced by Plans 02 and 03).
- **`Core/Keychain/KeychainHelper.swift`** — Three static methods (`save`, `read`, `delete`) wrapping the Security framework. Service: `"com.bankongseton.student"`. Uses `SecItemDelete` before `SecItemAdd` to handle updates.
- **`Core/Network/APIEndpoints.swift`** — Central enum with `baseURL = "https://juley2823.pythonanywhere.com/api"` and path constants.
- **`Core/Network/APIClient.swift`** — `ObservableObject` URLSession wrapper. Reads `auth_token` from Keychain on every authenticated request. Distinct `APIError.cardLost` case triggered by `403 + body["error"] == "CARD_LOST"`. All 7 public methods: `login`, `getBalance`, `getTransactions(limit:offset:)`, `getBudget`, `setBudget`, `reportLostCard`, `logout`.
- **`Core/Auth/AuthManager.swift`** — `@MainActor ObservableObject`. `@Published var isLoggedIn` bootstrapped from Keychain. `clearAll()` deletes all 9 Keychain keys. `handleCardLost()` calls `clearAll()` and flips `isLoggedIn = false`.

### Codable Models (4 Swift files)
- **`Models/LoginModels.swift`** — `LoginRequest`, `Student`, `LoginResponse`, `GenericSuccessResponse`
- **`Models/BalanceModels.swift`** — `BalanceResponse` (maps `money_card`)
- **`Models/TransactionModels.swift`** — `Transaction` (Hashable, `var id = UUID()`, maps `balance_before`), `TransactionItem`, `TransactionsResponse` (maps `has_more`)
- **`Models/BudgetModels.swift`** — `BudgetResponse`, `BudgetRequest`, `BudgetSetResponse`, `LostCardResponse`

---

## Key Contracts Established (for Plans 02–05)

```swift
// APIError cases
case cardLost       // 403 + body["error"] == "CARD_LOST"
case unauthorized   // 403 other
case httpError(Int)
case decodingError(Error)
case networkError(Error)

// AuthManager
@Published var isLoggedIn: Bool
@Published var studentName: String
func login(token: String, student: Student)
func logout(apiClient: APIClient) async
func handleCardLost()       // clears all 9 Keychain keys + isLoggedIn = false

// Keychain service: "com.bankongseton.student"
// Keys: "auth_token", "student_id", "student_name", "last_balance",
//       "theme_mode", "isCardLost", "budget_alert_month",
//       "budgetAlerted80", "budgetAlerted100"
```

---

## Constraints Satisfied
- ✅ No `₱` symbol anywhere — only `฿`
- ✅ No `NavigationView` — `NavigationStack` used in stubs
- ✅ JWT stored in Keychain (never `UserDefaults`)
- ✅ `APIError.cardLost` is a distinct enum case
- ✅ `AuthManager` is `@MainActor` with `@Published` properties
- ✅ No third-party dependencies
- ✅ `project.pbxproj` covers all 24 final source files

---

## Files Created
1. `mobile/ios/BankongSetonStudent/BankongSetonStudent.xcodeproj/project.pbxproj`
2. `mobile/ios/BankongSetonStudent/App/BankongSetonStudentApp.swift`
3. `mobile/ios/BankongSetonStudent/App/ContentView.swift`
4. `mobile/ios/BankongSetonStudent/Core/Keychain/KeychainHelper.swift`
5. `mobile/ios/BankongSetonStudent/Core/Network/APIEndpoints.swift`
6. `mobile/ios/BankongSetonStudent/Core/Network/APIClient.swift`
7. `mobile/ios/BankongSetonStudent/Core/Auth/AuthManager.swift`
8. `mobile/ios/BankongSetonStudent/Models/LoginModels.swift`
9. `mobile/ios/BankongSetonStudent/Models/BalanceModels.swift`
10. `mobile/ios/BankongSetonStudent/Models/TransactionModels.swift`
11. `mobile/ios/BankongSetonStudent/Models/BudgetModels.swift`
