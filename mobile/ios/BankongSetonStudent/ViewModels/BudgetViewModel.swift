import Foundation

@MainActor
final class BudgetViewModel: ObservableObject {
    @Published var limit: Double = 0
    @Published var spent: Double = 0
    @Published var isLoading = false
    @Published var showAlert = false
    @Published var alertMessage = ""

    // Explicit recoverable failure channels.
    @Published private(set) var loadErrorMessage: String?
    @Published private(set) var saveErrorMessage: String?
    @Published private(set) var pendingRetryLimit: Double?

    var percent: Double { limit > 0 ? min((spent / limit) * 100, 100) : 0 }

    var hasLoadFailureState: Bool {
        loadErrorMessage != nil
    }

    var hasSaveFailureState: Bool {
        saveErrorMessage != nil && pendingRetryLimit != nil
    }

    func load(apiClient: APIClient, authManager: AuthManager) async {
        isLoading = true
        loadErrorMessage = nil
        defer { isLoading = false }

        // Load both in parallel but surface partial failures explicitly so they are retryable.
        async let budgetTask: BudgetResponse = apiClient.getBudget()
        async let summaryTask: BudgetSummaryResponse = apiClient.fetchBudgetSummary()

        var failedSegments: [BudgetLoadSegment] = []

        do {
            let budget = try await budgetTask
            limit = budget.monthlyLimit ?? 0
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
            return
        } catch APIError.cardLost {
            authManager.handleCardLost()
            return
        } catch {
            failedSegments.append(.monthlyLimit)
            log("Budget limit segment failed to load")
        }

        do {
            let summary = try await summaryTask
            spent = summary.spent
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
            return
        } catch APIError.cardLost {
            authManager.handleCardLost()
            return
        } catch {
            failedSegments.append(.monthlySpend)
            log("Budget spend segment failed to load")
        }

        if failedSegments.isEmpty {
            checkAlerts()
            return
        }

        loadErrorMessage = loadFailureMessage(for: failedSegments)
    }

    func retryLoad(apiClient: APIClient, authManager: AuthManager) async {
        await load(apiClient: apiClient, authManager: authManager)
    }

    func setBudget(limit newLimit: Double, apiClient: APIClient, authManager: AuthManager) async {
        isLoading = true
        saveErrorMessage = nil
        pendingRetryLimit = newLimit
        defer { isLoading = false }

        do {
            let resp = try await apiClient.setBudget(monthlyLimit: newLimit)
            if resp.success {
                limit = resp.monthlyLimit ?? newLimit
                pendingRetryLimit = nil
                saveErrorMessage = nil
                checkAlerts()
                if !showAlert {
                    alertMessage = "Budget limit saved successfully."
                    showAlert = true
                }
            } else {
                let message = "Couldn’t save budget. Tap Retry Save to try again."
                saveErrorMessage = message
                alertMessage = message
                showAlert = true
            }
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch {
            let message = "Failed to save budget. Check your connection and tap Retry Save."
            saveErrorMessage = message
            alertMessage = message
            showAlert = true
            log("Budget save request failed")
        }
    }

    func retryLastSave(apiClient: APIClient, authManager: AuthManager) async {
        guard let pendingRetryLimit else { return }
        await setBudget(limit: pendingRetryLimit, apiClient: apiClient, authManager: authManager)
    }

    private static let monthPrefixFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM"
        return f
    }()

    private func currentMonthPrefix() -> String {
        BudgetViewModel.monthPrefixFormatter.string(from: Date())
    }

    private func checkAlerts() {
        let alertMonth = KeychainHelper.read(forKey: "budget_alert_month")
        let thisMonth = currentMonthPrefix()
        if alertMonth != thisMonth {
            KeychainHelper.save(thisMonth, forKey: "budget_alert_month")
            KeychainHelper.delete(forKey: "budgetAlerted80")
            KeychainHelper.delete(forKey: "budgetAlerted100")
        }
        if percent >= 80 && KeychainHelper.read(forKey: "budgetAlerted80") == nil {
            KeychainHelper.save("true", forKey: "budgetAlerted80")
            alertMessage = "You've used 80% of your monthly budget"
            showAlert = true
        }
        if percent >= 100 && KeychainHelper.read(forKey: "budgetAlerted100") == nil {
            KeychainHelper.save("true", forKey: "budgetAlerted100")
            alertMessage = "You've exceeded your monthly budget"
            showAlert = true
        }
    }

    private func loadFailureMessage(for failedSegments: [BudgetLoadSegment]) -> String {
        let failedSet = Set(failedSegments)

        if failedSet.contains(.monthlyLimit) && failedSet.contains(.monthlySpend) {
            return "Couldn’t refresh budget details. Pull to refresh or tap Retry."
        }

        if failedSet.contains(.monthlyLimit) {
            return "Couldn’t refresh your budget limit. Pull to refresh or tap Retry."
        }

        return "Couldn’t refresh your spending summary. Pull to refresh or tap Retry."
    }

    private func log(_ message: String) {
        print("[BudgetViewModel] \(message)")
    }
}

private enum BudgetLoadSegment: Hashable {
    case monthlyLimit
    case monthlySpend
}
