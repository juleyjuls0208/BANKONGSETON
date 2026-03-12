import Foundation

// MARK: - HomeViewModel
// Loads balance and 3 most recent transactions for the Home screen.

@MainActor
final class HomeViewModel: ObservableObject {
    @Published var balance: Double = 0
    @Published var recentTransactions: [Transaction] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    init() {
        if let cached = KeychainHelper.read(forKey: "last_balance"),
           let value = Double(cached) {
            balance = value
        }
    }

    func load(apiClient: APIClient, authManager: AuthManager) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        do {
            async let balanceResp = apiClient.getBalance()
            async let txResp = apiClient.getTransactions(limit: 3, offset: 0)
            let (bal, txs) = try await (balanceResp, txResp)
            balance = bal.balance
            KeychainHelper.save(String(format: "%.2f", bal.balance), forKey: "last_balance")
            recentTransactions = txs.transactions
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch {
            errorMessage = "Failed to load data. Pull to refresh."
        }
    }
}
