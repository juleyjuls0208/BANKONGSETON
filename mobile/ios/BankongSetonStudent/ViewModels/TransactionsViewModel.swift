import Foundation

// MARK: - TransactionsViewModel
// Offset-based pagination: initial load + load-more.

@MainActor
final class TransactionsViewModel: ObservableObject {
    @Published var transactions: [Transaction] = []
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var hasMore = true
    @Published var errorMessage: String?

    private let pageSize = 20
    private var offset = 0

    func loadInitial(apiClient: APIClient, authManager: AuthManager) async {
        offset = 0
        transactions = []
        hasMore = true
        errorMessage = nil
        isLoading = true
        defer { isLoading = false }
        await fetchPage(apiClient: apiClient, authManager: authManager)
    }

    func loadMore(apiClient: APIClient, authManager: AuthManager) async {
        guard hasMore && !isLoadingMore else { return }
        isLoadingMore = true
        defer { isLoadingMore = false }
        await fetchPage(apiClient: apiClient, authManager: authManager)
    }

    private func fetchPage(apiClient: APIClient, authManager: AuthManager) async {
        do {
            let resp = try await apiClient.getTransactions(limit: pageSize, offset: offset)
            transactions.append(contentsOf: resp.transactions)
            offset += resp.transactions.count
            hasMore = resp.hasMore
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch {
            errorMessage = "Failed to load transactions."
        }
    }
}
