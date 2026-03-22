import Foundation

// MARK: - TransactionsViewModel
// Canonical source + derived display state with split initial/pagination failure channels.

@MainActor
final class TransactionsViewModel: ObservableObject {
    // Canonical paginated source list.
    @Published private(set) var allTransactions: [Transaction] = []

    // Derived list currently displayed in the UI.
    @Published private(set) var transactions: [Transaction] = []

    // Local query/filter controls that deterministically recompute `transactions`.
    @Published var searchQuery = "" {
        didSet { recomputeDisplayedTransactions() }
    }

    @Published var selectedFilter: TransactionFilter = .all {
        didSet { recomputeDisplayedTransactions() }
    }

    // Shared loading channels.
    @Published var isLoading = false
    @Published var isLoadingMore = false
    @Published var hasMore = true

    // Split failure channels.
    @Published private(set) var initialLoadErrorMessage: String?
    @Published private(set) var paginationErrorMessage: String?

    // Legacy compatibility channel used by existing TransactionsView overlay (initial only).
    @Published private(set) var errorMessage: String?

    // Derived-state observability markers.
    var isBaseEmptyState: Bool {
        !isLoading && initialLoadErrorMessage == nil && allTransactions.isEmpty
    }

    var isFilteredEmptyState: Bool {
        !isLoading && initialLoadErrorMessage == nil && !allTransactions.isEmpty && transactions.isEmpty
    }

    var hasPaginationFailureState: Bool {
        paginationErrorMessage != nil && !allTransactions.isEmpty
    }

    private let pageSize = 20
    private var offset = 0

    private enum FetchContext {
        case initial
        case pagination
    }

    func loadInitial(apiClient: APIClient, authManager: AuthManager) async {
        offset = 0
        allTransactions = []
        transactions = []
        hasMore = true

        initialLoadErrorMessage = nil
        paginationErrorMessage = nil
        errorMessage = nil

        isLoading = true
        defer { isLoading = false }

        await fetchPage(apiClient: apiClient, authManager: authManager, context: .initial)
    }

    func loadMore(apiClient: APIClient, authManager: AuthManager) async {
        guard hasMore && !isLoading && !isLoadingMore else { return }

        paginationErrorMessage = nil
        isLoadingMore = true
        defer { isLoadingMore = false }

        await fetchPage(apiClient: apiClient, authManager: authManager, context: .pagination)
    }

    func clearSearchAndFilter() {
        searchQuery = ""
        selectedFilter = .all
    }

    private func fetchPage(apiClient: APIClient, authManager: AuthManager, context: FetchContext) async {
        do {
            let resp = try await apiClient.getTransactions(limit: pageSize, offset: offset)
            let fetchedCount = resp.transactions.count

            allTransactions.append(contentsOf: resp.transactions)
            offset += fetchedCount
            hasMore = resolveHasMore(response: resp, fetchedCount: fetchedCount)

            // Re-derive display list from canonical source after every data mutation.
            recomputeDisplayedTransactions()

            if context == .initial {
                initialLoadErrorMessage = nil
                errorMessage = nil
            }
            paginationErrorMessage = nil
        } catch APIError.unauthorized {
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            authManager.handleCardLost()
        } catch {
            switch context {
            case .initial:
                initialLoadErrorMessage = "Failed to load transactions."
                errorMessage = initialLoadErrorMessage
                hasMore = false
            case .pagination:
                paginationErrorMessage = "Couldn’t load more transactions. Tap Load More to retry."
            }
        }
    }

    private func resolveHasMore(response: TransactionsResponse, fetchedCount: Int) -> Bool {
        if let explicitHasMore = response.hasMore {
            return explicitHasMore
        }

        if let total = response.total {
            return offset < total
        }

        // Defensive continuity fallback when backend omits `has_more`.
        // Assume more pages only when a full page arrives.
        return fetchedCount == pageSize
    }

    private func recomputeDisplayedTransactions() {
        transactions = allTransactions.filter { transaction in
            transaction.matchesFilter(selectedFilter) && transaction.matchesSearchQuery(searchQuery)
        }
    }
}
