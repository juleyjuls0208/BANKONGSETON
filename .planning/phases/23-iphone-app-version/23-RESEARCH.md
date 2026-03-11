# Phase 23: iPhone App Version - Research

**Researched:** 2026-03-09  
**Domain:** SwiftUI iOS app (iOS 16+), JWT auth, Keychain, REST API consumption  
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- SwiftUI only (no UIKit, no React Native, no Flutter)
- Minimum iOS 16 — use `NavigationStack`, not `NavigationView`
- JWT stored in iOS Keychain (never `UserDefaults`)
- No NFC / payment features on iOS (Apple blocks HCE for third parties)
- Zero new backend endpoints — reuse existing REST API exactly as-is
- Budget tracker is client-side derived (fetch transactions + budget limit, compute locally)
- Distribution: ad hoc / direct install (not App Store, no TestFlight required)
- Currency: Thai Baht `฿` symbol throughout UI

### Claude's Discretion
- Exact SwiftUI view decomposition (how to split views into files)
- HTTP client choice (`URLSession` directly or a thin wrapper)
- State management approach (`@StateObject` / `@EnvironmentObject` / `@Observable`)
- Error handling UX (alerts vs inline banners)
- Folder/project structure within the Xcode project

### Deferred Ideas (OUT OF SCOPE)
- Push notifications
- Biometric (Face ID / Touch ID) login
- App Store submission
- iPad layout optimisation
- Dark mode (can be done but not a phase goal)
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| REQ-23-01 | Login screen: student_id + PIN, POST /api/auth/login, store JWT in Keychain | Auth section, Keychain patterns, API contract |
| REQ-23-02 | Home screen: display balance `฿X.XX`, student name, recent 3 transactions | Balance API, transaction model |
| REQ-23-03 | Transaction history: paginated list (offset), tap Purchase → Receipt | Pagination pattern, transaction model, receipt screen |
| REQ-23-04 | Receipt detail: date, time, type, amount, balance before/after, line items | Receipt screen logic from Android |
| REQ-23-05 | Settings: theme toggle (light/dark), logout, lost card report | Settings screen, logout flow |
| REQ-23-06 | Lost Card Report: POST /api/student/lost-card, persist `isCardLost` in Keychain | Lost card API, local flag |
| REQ-23-07 | Budget Tracker: fetch limit + transactions, compute spent, show progress | Budget logic, month filter |
| REQ-23-08 | CARD_LOST 403 handling: clear token, navigate to Login with message | Error handling section |
| REQ-23-09 | JWT auth header: `Authorization: Bearer <token>` on every authenticated request | API client pattern |
| REQ-23-10 | No NFC / payment UI anywhere in the iOS app | Omission checklist |
</phase_requirements>

---

## Summary

The iOS app is a SwiftUI port of the existing Android student app. The backend API is complete and stable — the entire phase is front-end work. The app has 7 screens: Login, Home/Balance, Transaction History, Receipt Detail, Settings, Lost Card Report, and Budget Tracker.

The Android app uses Kotlin + Retrofit + Gson + SharedPreferences (encrypted). The iOS counterpart replaces all of that with SwiftUI + `URLSession` + `Codable` + Keychain. The NFC/HCE payment feature that exists on Android is intentionally omitted on iOS because Apple restricts HCE to Apple Pay.

The biggest iOS-specific concerns are: (1) Keychain access for secure token storage, (2) `NavigationStack` path-based navigation (iOS 16+), (3) async/await network calls with proper `MainActor` UI updates, and (4) the CARD_LOST 403 error path which must clear the session and push the user back to Login from any screen.

**Primary recommendation:** Use a single `AuthManager` (`@Observable` / `ObservableObject`) as the source of truth for auth state, injected via `@EnvironmentObject`. All screens read from it; network errors bubble up through it.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| SwiftUI | iOS 16+ | Declarative UI | Locked decision |
| Foundation (URLSession) | iOS 16+ | HTTP networking | Built-in, no dependency needed |
| Security framework (Keychain) | iOS 16+ | Secure token/flag storage | Apple-recommended for secrets |
| Swift Concurrency (async/await) | Swift 5.5+ / iOS 15+ | Async network calls | Modern Swift standard |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `@Observable` macro | iOS 17+ | Reactive state | Use if min deployment raised to 17; else `ObservableObject` |
| `ObservableObject` + `@StateObject` | iOS 14+ | Reactive state | Use for iOS 16 min target (safe floor) |
| `Codable` | Swift 4+ | JSON decode/encode | All API response models |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `URLSession` directly | Alamofire | Alamofire is nice but adds a dependency; URLSession + async/await is clean enough for ~7 endpoints |
| Security framework Keychain | `KeychainAccess` (pod) | The pod is convenient but adds another dependency; a 60-line `KeychainHelper` covers our needs |
| `ObservableObject` | `@Observable` (iOS 17) | `@Observable` is cleaner but raises min iOS to 17; stick with `ObservableObject` for iOS 16 |

**No third-party dependencies required.** All needs are met by Apple frameworks.

**No Package.swift / CocoaPods / SPM dependencies needed.**

---

## Architecture Patterns

### Recommended Project Structure
```
BankongSetonStudent/
├── App/
│   └── BankongSetonStudentApp.swift   # @main entry, inject EnvironmentObjects
├── Core/
│   ├── Network/
│   │   ├── APIClient.swift            # URLSession wrapper, injects auth header
│   │   └── APIEndpoints.swift         # Endpoint enum / URL builder
│   ├── Keychain/
│   │   └── KeychainHelper.swift       # get/set/delete wrappers
│   └── Auth/
│       └── AuthManager.swift          # ObservableObject, isLoggedIn, token, studentName
├── Models/
│   ├── LoginModels.swift              # LoginRequest, LoginResponse, Student
│   ├── TransactionModels.swift        # Transaction, TransactionItem, TransactionsResponse
│   ├── BudgetModels.swift             # BudgetResponse, BudgetRequest
│   └── BalanceModels.swift            # BalanceResponse
├── Views/
│   ├── Auth/
│   │   └── LoginView.swift
│   ├── Home/
│   │   └── HomeView.swift
│   ├── Transactions/
│   │   ├── TransactionsView.swift
│   │   └── TransactionRowView.swift
│   ├── Receipt/
│   │   └── ReceiptView.swift
│   ├── Budget/
│   │   └── BudgetView.swift
│   ├── Settings/
│   │   └── SettingsView.swift
│   └── LostCard/
│       └── LostCardView.swift
└── ViewModels/
    ├── LoginViewModel.swift
    ├── HomeViewModel.swift
    ├── TransactionsViewModel.swift
    ├── BudgetViewModel.swift
    └── SettingsViewModel.swift
```

### Pattern 1: MVVM with ObservableObject
**What:** Each screen has a `ViewModel: ObservableObject`. Views are pure SwiftUI driven by `@Published` properties.  
**When to use:** All 7 screens.

```swift
// ViewModels/HomeViewModel.swift
@MainActor
final class HomeViewModel: ObservableObject {
    @Published var balance: Double = 0
    @Published var studentName: String = ""
    @Published var recentTransactions: [Transaction] = []
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var isCardLost = false

    private let apiClient: APIClient

    init(apiClient: APIClient) {
        self.apiClient = apiClient
    }

    func loadData() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let resp = try await apiClient.getBalance()
            balance = resp.balance
        } catch APIError.cardLost {
            isCardLost = true          // triggers global logout in AuthManager
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
```

### Pattern 2: NavigationStack with Path
**What:** Root `ContentView` switches between `LoginView` and `MainTabView` based on `AuthManager.isLoggedIn`. Inside the app, `NavigationStack` with a `NavigationPath` drives navigation.  
**When to use:** iOS 16+ required; do NOT use deprecated `NavigationView`.

```swift
// App/BankongSetonStudentApp.swift
@main
struct BankongSetonStudentApp: App {
    @StateObject private var authManager = AuthManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(authManager)
        }
    }
}

// Views/ContentView.swift
struct ContentView: View {
    @EnvironmentObject var authManager: AuthManager

    var body: some View {
        if authManager.isLoggedIn {
            MainTabView()
        } else {
            LoginView()
        }
    }
}
```

### Pattern 3: Keychain Helper
**What:** A lightweight struct wrapping `Security` framework `SecItemAdd`, `SecItemCopyMatching`, `SecItemDelete`.  
**When to use:** Every read/write of token, student_id, last_balance, theme_mode, budget alert flags, isCardLost.

```swift
// Core/Keychain/KeychainHelper.swift
struct KeychainHelper {
    static let service = "com.bankongseton.student"

    static func save(_ value: String, forKey key: String) {
        let data = Data(value.utf8)
        let query: [String: Any] = [
            kSecClass as String:       kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecValueData as String:   data
        ]
        SecItemDelete(query as CFDictionary)           // delete old first
        SecItemAdd(query as CFDictionary, nil)
    }

    static func read(forKey key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String:            kSecClassGenericPassword,
            kSecAttrService as String:      service,
            kSecAttrAccount as String:      key,
            kSecReturnData as String:       true,
            kSecMatchLimit as String:       kSecMatchLimitOne
        ]
        var result: AnyObject?
        guard SecItemCopyMatching(query as CFDictionary, &result) == errSecSuccess,
              let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func delete(forKey key: String) {
        let query: [String: Any] = [
            kSecClass as String:       kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key
        ]
        SecItemDelete(query as CFDictionary)
    }
}
```

### Pattern 4: APIClient with Auth Header Injection
**What:** A class that wraps `URLSession`, reads the token from `KeychainHelper`, and injects `Authorization: Bearer <token>` on every authenticated request.  
**When to use:** All endpoints except `/api/auth/login`.

```swift
// Core/Network/APIClient.swift
enum APIError: Error {
    case cardLost
    case unauthorized
    case httpError(Int)
    case decodingError(Error)
}

final class APIClient {
    static let baseURL = "https://juley2823.pythonanywhere.com/api"
    private let session = URLSession.shared

    private var token: String? { KeychainHelper.read(forKey: "auth_token") }

    private func authenticatedRequest(path: String, method: String = "GET", body: Data? = nil) throws -> URLRequest {
        guard let url = URL(string: Self.baseURL + path) else { fatalError("Bad URL") }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = body
        return request
    }

    func getBalance() async throws -> BalanceResponse {
        let req = try authenticatedRequest(path: "/student/balance")
        let (data, response) = try await session.data(for: req)
        if let http = response as? HTTPURLResponse, http.statusCode == 403 {
            // Check for CARD_LOST
            if let body = try? JSONDecoder().decode([String: String].self, from: data),
               body["error"] == "CARD_LOST" {
                throw APIError.cardLost
            }
            throw APIError.unauthorized
        }
        return try JSONDecoder().decode(BalanceResponse.self, from: data)
    }

    // … similar methods for transactions, budget GET/POST, lost-card, logout
}
```

### Pattern 5: Global CARD_LOST Handling via AuthManager
**What:** `AuthManager` exposes a `handleCardLost()` method. Any ViewModel that catches `APIError.cardLost` calls `authManager.handleCardLost()`, which sets `isCardLost = true`, clears Keychain, and flips `isLoggedIn = false` (sending user to Login).  
**When to use:** Any screen that calls `getBalance()` or `getTransactions()`.

```swift
// Core/Auth/AuthManager.swift
@MainActor
final class AuthManager: ObservableObject {
    @Published var isLoggedIn: Bool
    @Published var studentName: String = ""

    init() {
        isLoggedIn = KeychainHelper.read(forKey: "auth_token") != nil
        studentName = KeychainHelper.read(forKey: "student_name") ?? ""
    }

    func login(token: String, student: Student) {
        KeychainHelper.save(token, forKey: "auth_token")
        KeychainHelper.save(student.name, forKey: "student_name")
        studentName = student.name
        isLoggedIn = true
    }

    func logout(apiClient: APIClient) async {
        _ = try? await apiClient.logout()     // best-effort
        clearAll()
    }

    func handleCardLost() {
        KeychainHelper.save("true", forKey: "isCardLost")
        clearAll()
    }

    private func clearAll() {
        ["auth_token", "student_name", "last_balance",
         "budget_alert_month", "budgetAlerted80", "budgetAlerted100",
         "isCardLost"].forEach { KeychainHelper.delete(forKey: $0) }
        isLoggedIn = false
    }
}
```

### Anti-Patterns to Avoid
- **Storing JWT in `UserDefaults`:** Never. It is readable by any process with the same bundle ID. Use Keychain only.
- **Using `NavigationView`:** Deprecated in iOS 16. Causes broken back-button behavior in some cases. Use `NavigationStack`.
- **Performing network calls on the MainActor synchronously:** Always `async`/`await`; annotate ViewModels `@MainActor` so `@Published` updates are safe.
- **Hardcoding currency symbol in format strings as `₱`:** The Android app uses Philippine Peso `₱` in its format strings (`"₱%.2f"`), but this project uses **Thai Baht `฿`**. The iOS app must use `฿` throughout.
- **Sharing a ViewModel instance across multiple view instances via `.environmentObject`:** ViewModels should be `@StateObject` at their owning view and passed down only as needed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Secure token storage | Custom encryption in UserDefaults | `Security` framework Keychain | Keychain is hardware-backed on modern iPhones; UserDefaults is plaintext |
| JSON parsing | Manual string parsing | `Codable` / `JSONDecoder` | Handles optionals, date formats, nested objects; battle-tested |
| Async HTTP | Custom OperationQueue networking | `async/await` + `URLSession.data(for:)` | Cancellation, back-pressure, and structured concurrency built in |
| Pagination state | Custom index tracker | Standard `offset`/`hasMore` pattern in ViewModel | Straightforward; no library needed |

---

## Common Pitfalls

### Pitfall 1: Currency Symbol — `฿` vs `₱`
**What goes wrong:** The Android source code uses Philippine Peso `₱` in format strings (`"₱%.2f"`). Copying those strings into Swift will produce the wrong currency symbol.  
**Why it happens:** Android was originally built for a different deployment context.  
**How to avoid:** Always use `฿` in all iOS Swift format strings. Define a constant: `let baht = "฿"`.  
**Warning signs:** Any `₱` character in Swift source files.

### Pitfall 2: CARD_LOST 403 Not Handled
**What goes wrong:** The balance endpoint returns HTTP 403 with `{"error": "CARD_LOST"}` when the card is reported lost. If the app only checks status code, it will show a generic "unauthorized" error instead of clearing the session.  
**Why it happens:** 403 is being reused for two semantically different error conditions.  
**How to avoid:** After receiving a 403, decode the body and check `body["error"] == "CARD_LOST"`. Throw a distinct `APIError.cardLost` case.  
**Warning signs:** App gets stuck on Home screen with a 403 error after card is reported lost.

### Pitfall 3: NavigationView Instead of NavigationStack
**What goes wrong:** `NavigationView` is deprecated on iOS 16 and causes layout issues (double navigation bars, broken back behavior in certain configurations).  
**Why it happens:** Many tutorials and copied code snippets still use `NavigationView`.  
**How to avoid:** Use `NavigationStack` everywhere. In iOS 16+ `NavigationStack` supports `navigationDestination(for:)` for type-safe routing.  
**Warning signs:** Compiler deprecation warnings; visual glitches in navigation.

### Pitfall 4: MainActor UI Updates from Background Thread
**What goes wrong:** `@Published` property updates from a non-main thread produce runtime warnings ("Publishing changes from background threads is not allowed") and can cause visual glitches.  
**Why it happens:** `URLSession.data(for:)` resumes on a background executor by default.  
**How to avoid:** Annotate ViewModels with `@MainActor`. All `@Published` assignments then automatically run on the main thread.  
**Warning signs:** Purple runtime warnings in Xcode console about background thread publishing.

### Pitfall 5: Budget Month Filter
**What goes wrong:** Including transactions from previous months in the monthly budget calculation.  
**Why it happens:** Filtering by wrong date format or off-by-one in string comparison.  
**How to avoid:** Use `transaction.timestamp.hasPrefix(currentMonthPrefix)` where `currentMonthPrefix` is formatted as `"yyyy-MM"` (e.g. `"2026-03"`). Mirror the Android implementation exactly.  
**Warning signs:** Budget percentage is much higher than expected; includes transactions from prior months.

### Pitfall 6: Token Not Persisting Across App Launches
**What goes wrong:** User is logged out every time the app restarts.  
**Why it happens:** Token stored in memory or `UserDefaults` (cleared on some reinstalls), not Keychain.  
**How to avoid:** `AuthManager.init()` reads `auth_token` from Keychain to restore session.  
**Warning signs:** Users must log in every app launch.

---

## Code Examples

### Codable Models (mirroring Android Models.kt)

```swift
// Models/TransactionModels.swift
struct Transaction: Codable, Identifiable {
    var id = UUID()                      // local only, not from API
    let timestamp: String
    let type: String
    let amount: Double
    let balanceBefore: Double
    let balance: Double
    let description: String?
    let items: [TransactionItem]?

    enum CodingKeys: String, CodingKey {
        case timestamp, type, amount, description, items, balance
        case balanceBefore = "balance_before"
    }
}

struct TransactionItem: Codable {
    let name: String
    let price: Double
    let qty: Int
}

struct TransactionsResponse: Codable {
    let transactions: [Transaction]
    let count: Int
    let total: Int
    let hasMore: Bool

    enum CodingKeys: String, CodingKey {
        case transactions, count, total
        case hasMore = "has_more"
    }
}
```

### Receipt View — Matching Android ReceiptActivity Logic

Key behaviors from Android to mirror:
- Split `timestamp` (format `"yyyy-MM-dd HH:mm:ss"`) into date (`"MMM d, yyyy"`) and time (`"h:mm a"`)
- Show transaction `type` as a subtitle label
- If `items` is null or empty → show a **synthetic** single line item: name = "NFC Payment" (or equivalent), price = `transaction.amount`, qty = 1
- Only `Purchase` and `NFC Purchase` types are tappable in the transaction list → navigate to receipt
- `Top-Up` rows are NOT tappable (no receipt)

```swift
// Views/Receipt/ReceiptView.swift
struct ReceiptView: View {
    let transaction: Transaction

    var formattedDate: String { /* parse timestamp → "Mar 9, 2026" */ }
    var formattedTime: String { /* parse timestamp → "3:45 PM" */ }

    var lineItems: [TransactionItem] {
        if let items = transaction.items, !items.isEmpty { return items }
        return [TransactionItem(name: "NFC Payment", price: transaction.amount, qty: 1)]
    }

    var body: some View {
        List {
            Section("Summary") {
                LabeledContent("Date", value: formattedDate)
                LabeledContent("Time", value: formattedTime)
                LabeledContent("Type", value: transaction.type)
                LabeledContent("Total", value: "฿\(String(format: "%.2f", transaction.amount))")
                LabeledContent("Balance Before", value: "฿\(String(format: "%.2f", transaction.balanceBefore))")
                LabeledContent("Balance After", value: "฿\(String(format: "%.2f", transaction.balance))")
            }
            Section("Items") {
                ForEach(lineItems, id: \.name) { item in
                    HStack {
                        Text(item.name)
                        Spacer()
                        Text("x\(item.qty)")
                        Text("฿\(String(format: "%.2f", item.price * Double(item.qty)))")
                    }
                }
            }
        }
        .navigationTitle("Receipt")
        .navigationBarTitleDisplayMode(.inline)
    }
}
```

### Budget Tracker Logic

```swift
// ViewModels/BudgetViewModel.swift
@MainActor
final class BudgetViewModel: ObservableObject {
    @Published var limit: Double = 0
    @Published var spent: Double = 0
    @Published var isLoading = false

    var percent: Double { limit > 0 ? min((spent / limit) * 100, 100) : 0 }

    func load(apiClient: APIClient) async {
        isLoading = true
        defer { isLoading = false }
        async let budgetResp = apiClient.getBudget()
        async let txResp = apiClient.getTransactions(limit: 200, offset: 0)  // fetch enough for a month
        do {
            let (budget, txs) = try await (budgetResp, txResp)
            limit = budget.monthlyLimit
            let prefix = currentMonthPrefix()             // "yyyy-MM"
            spent = txs.transactions
                .filter { $0.timestamp.hasPrefix(prefix) }
                .filter { $0.type == "Purchase" || $0.type == "NFC Purchase" }
                .reduce(0) { $0 + $1.amount }
            checkAlerts()
        } catch { /* handle */ }
    }

    private func currentMonthPrefix() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM"
        return formatter.string(from: Date())
    }

    private func checkAlerts() {
        let alertMonth = KeychainHelper.read(forKey: "budget_alert_month")
        let thisMonth = currentMonthPrefix()
        let isNewMonth = alertMonth != thisMonth
        if isNewMonth {
            KeychainHelper.save(thisMonth, forKey: "budget_alert_month")
            KeychainHelper.delete(forKey: "budgetAlerted80")
            KeychainHelper.delete(forKey: "budgetAlerted100")
        }
        if percent >= 80 && KeychainHelper.read(forKey: "budgetAlerted80") == nil {
            KeychainHelper.save("true", forKey: "budgetAlerted80")
            // show in-app alert: "You've used 80% of your monthly budget"
        }
        if percent >= 100 && KeychainHelper.read(forKey: "budgetAlerted100") == nil {
            KeychainHelper.save("true", forKey: "budgetAlerted100")
            // show in-app alert: "You've exceeded your monthly budget"
        }
    }
}
```

### Transaction Row Color Coding (mirroring Android adapter)

```swift
// Views/Transactions/TransactionRowView.swift
struct TransactionRowView: View {
    let transaction: Transaction

    var amountColor: Color {
        switch transaction.type.lowercased() {
        case "purchase", "nfc purchase": return Color(hex: "#F44336")  // red
        case "top-up", "topup":          return Color(hex: "#4CAF50")  // green
        default:                          return .primary
        }
    }

    var isPurchase: Bool {
        ["purchase", "nfc purchase"].contains(transaction.type.lowercased())
    }

    var body: some View {
        HStack {
            Image(systemName: isPurchase ? "arrow.down.circle.fill" : "arrow.up.circle.fill")
                .foregroundColor(amountColor)
            VStack(alignment: .leading) {
                Text(transaction.type).font(.subheadline)
                Text(transaction.timestamp).font(.caption).foregroundColor(.secondary)
            }
            Spacer()
            VStack(alignment: .trailing) {
                Text("฿\(String(format: "%.2f", transaction.amount))")
                    .foregroundColor(amountColor)
                    .fontWeight(.semibold)
                Text("Balance: ฿\(String(format: "%.2f", transaction.balance))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
    }
}
```

---

## Keychain Keys Reference

All keys used by the iOS app (mirrors Android `SecureStorage.kt`):

| Key | Type | Purpose |
|-----|------|---------|
| `auth_token` | String | JWT bearer token |
| `student_id` | String | Student ID (display only) |
| `student_name` | String | Student name for Home screen |
| `last_balance` | String | Cached balance (optional optimistic UI) |
| `theme_mode` | String | `"light"` / `"dark"` / `"system"` |
| `isCardLost` | String (`"true"`) | Whether card has been reported lost |
| `budget_alert_month` | String | `"yyyy-MM"` of last alert (reset monthly) |
| `budgetAlerted80` | String (`"true"`) | Fired 80% alert this month |
| `budgetAlerted100` | String (`"true"`) | Fired 100% alert this month |

---

## API Contract Summary

**Base URL:** `https://juley2823.pythonanywhere.com/api`

| Method | Path | Auth | Request Body | Response |
|--------|------|------|-------------|----------|
| POST | `/auth/login` | ❌ | `{student_id, pin}` | `{token, student: {id, name, ...}}` |
| GET | `/student/balance` | ✅ | — | `{balance, money_card}` or 403 `{error:"CARD_LOST"}` |
| GET | `/student/transactions` | ✅ | `?limit=N&offset=N` | `{transactions[], count, total, has_more}` |
| GET | `/student/budget` | ✅ | — | `{monthly_limit, currency}` |
| POST | `/student/budget` | ✅ | `{monthly_limit: float}` | `{success, monthly_limit}` |
| POST | `/student/lost-card` | ✅ | — | `{success, message}` |
| POST | `/auth/logout` | ✅ | — | `{success}` |

**Auth header on all ✅ requests:** `Authorization: Bearer <token>`

---

## Screens × Features Matrix

| Screen | API calls | Keychain reads | Keychain writes | iOS-only differences vs Android |
|--------|-----------|----------------|-----------------|----------------------------------|
| Login | POST /auth/login | — | auth_token, student_name | Same logic |
| Home | GET /balance | auth_token, isCardLost | last_balance | **No NFC Pay button** (Android has it) |
| Transaction History | GET /transactions | auth_token | — | Same logic |
| Receipt Detail | None (passed via navigation) | — | — | Same logic; use `฿` not `₱` |
| Settings | POST /auth/logout | auth_token, theme_mode, isCardLost | theme_mode | **No NFC settings section** (Android has it) |
| Lost Card Report | POST /lost-card | auth_token | isCardLost | Same logic |
| Budget Tracker | GET /budget, GET /transactions | auth_token, budget alert keys | budget alert keys | Same logic |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `NavigationView` | `NavigationStack` | iOS 16 (2022) | Use `NavigationStack` — `NavigationView` deprecated |
| `@StateObject` + `ObservableObject` | `@Observable` macro | iOS 17 (2023) | Stick with `ObservableObject` for iOS 16 floor |
| Completion handler URLSession | `async/await` URLSession | Swift 5.5 / iOS 15 (2021) | Use `async/await` throughout |
| Manual Keychain CFDictionary | Same (no better alternative) | — | A small `KeychainHelper` struct is the right abstraction |

---

## Open Questions

1. **Student model fields from `/auth/login`**
   - What we know: Android parses `student.name` and `student.student_id`
   - What's unclear: Full shape of the `student` object (other fields like photo, class, etc.)
   - Recommendation: Decode only the fields we display; mark the rest as optional in `Codable` model

2. **Pagination depth for Budget Tracker**
   - What we know: Budget uses current-month transactions; `/transactions` paginates with `limit`/`offset`
   - What's unclear: How many transactions a student can have in one month (could exceed a single page)
   - Recommendation: Fetch with `limit=200&offset=0` on Budget screen (sufficient for monthly view); document this assumption

3. **Lost Card banner on Home screen**
   - What we know: Android shows a banner if `isCardLost` is set
   - What's unclear: Exact banner wording / colour in the design spec
   - Recommendation: Use a yellow/orange `InfoBanner` component with "Your card has been reported lost" — planner can refine

---

## Sources

### Primary (HIGH confidence)
- Android source code read directly: `Models.kt`, `ApiClient.kt`, `LoginActivity.kt`, `HomeActivity.kt`, `TransactionsActivity.kt`, `SettingsActivity.kt`, `SecureStorage.kt`, `ReceiptActivity.kt`, `TransactionsAdapter.kt`
- Backend source code read directly: `backend/api/api_server.py` (all student endpoints)
- `.planning/phases/23-iphone-app-version/23-CONTEXT.md` (locked decisions)
- `.planning/REQUIREMENTS.md`

### Secondary (MEDIUM confidence)
- Apple Keychain documentation patterns — standard pattern in use since iOS 2; well established
- SwiftUI `NavigationStack` — released iOS 16, widely documented

### Tertiary (LOW confidence)
- Budget transaction fetch depth assumption (limit=200) — inferred, not verified against real data volume

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all Apple frameworks, no third-party dependencies needed
- Architecture: HIGH — direct port of confirmed Android patterns to SwiftUI idioms
- API contract: HIGH — read directly from backend source
- Pitfalls: HIGH — currency bug and CARD_LOST handling identified directly from source
- Budget logic: HIGH — read directly from Android implementation

**Research date:** 2026-03-09  
**Valid until:** 2026-06-09 (stable — backend API is locked, Apple framework APIs are stable)
