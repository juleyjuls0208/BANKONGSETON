import Foundation

@MainActor
final class BudgetViewModel: ObservableObject {
    @Published var limit: Double = 0
    @Published var spent: Double = 0
    @Published var isLoading = false
    @Published var showAlert = false
    @Published var alertMessage = ""

    var percent: Double { limit > 0 ? min((spent / limit) * 100, 100) : 0 }

    func load(apiClient: APIClient, authManager: AuthManager) async {
        isLoading = true
        defer { isLoading = false }
        async let budgetResp = apiClient.getBudget()
        async let summaryResp = apiClient.fetchBudgetSummary()
        do {
            let (budget, summary) = try await (budgetResp, summaryResp)
            limit = budget.monthlyLimit
            spent = summary.spent
            checkAlerts()
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch { /* swallow other errors — UI shows stale data */ }
    }

    func setBudget(limit newLimit: Double, apiClient: APIClient, authManager: AuthManager) async {
        do {
            let resp = try await apiClient.setBudget(monthlyLimit: newLimit)
            if resp.success {
                limit = resp.monthlyLimit
                checkAlerts()
            }
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch {}
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
}
