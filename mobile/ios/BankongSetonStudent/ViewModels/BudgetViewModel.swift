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

        // Load both in parallel but handle errors independently so a
        // summary failure doesn't wipe out the limit (and vice versa).
        async let budgetTask: BudgetResponse = apiClient.getBudget()
        async let summaryTask: BudgetSummaryResponse = apiClient.fetchBudgetSummary()

        do {
            let budget = try await budgetTask
            limit = budget.monthlyLimit ?? 0
        } catch APIError.unauthorized {
            authManager.handleUnauthorized(); return
        } catch APIError.cardLost {
            authManager.handleCardLost(); return
        } catch {}

        do {
            let summary = try await summaryTask
            spent = summary.spent
        } catch APIError.unauthorized {
            authManager.handleUnauthorized(); return
        } catch APIError.cardLost {
            authManager.handleCardLost(); return
        } catch {}

        checkAlerts()
    }

    func setBudget(limit newLimit: Double, apiClient: APIClient, authManager: AuthManager) async {
        isLoading = true
        defer { isLoading = false }
        do {
            let resp = try await apiClient.setBudget(monthlyLimit: newLimit)
            if resp.success {
                limit = resp.monthlyLimit ?? newLimit
                checkAlerts()
                if !showAlert {
                    alertMessage = "Budget limit saved successfully."
                    showAlert = true
                }
            } else {
                alertMessage = "Could not save budget. Please try again."
                showAlert = true
            }
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch {
            alertMessage = "Failed to save budget. Check your connection and try again."
            showAlert = true
        }
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
