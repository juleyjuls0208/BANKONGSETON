import SwiftUI

// MARK: - TransactionsView
// Stitch-faithful transactions surface with local search/filter derivation,
// explicit state cards, and non-blocking pagination recovery controls.

struct TransactionsView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.accessibilityReduceMotion) private var accessibilityReduceMotion
    @StateObject private var viewModel = TransactionsViewModel()

    var body: some View {
        NavigationStack {
            List {
                styledListRow(top: AppTheme.Spacing.sm, bottom: AppTheme.Spacing.xs) {
                    filterControlsCard
                }

                transactionStateRows
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .background(AppTheme.Palette.background)
            .animation(screenTransitionAnimation, value: transactionStateKey)
            .animation(screenTransitionAnimation, value: viewModel.transactions.count)
            .navigationTitle("Transactions")
            .searchable(
                text: $viewModel.searchQuery,
                placement: .navigationBarDrawer(displayMode: .always),
                prompt: "Search by type, date, or amount"
            )
            .textInputAutocapitalization(.never)
            .autocorrectionDisabled()
            .refreshable {
                await viewModel.loadInitial(apiClient: apiClient, authManager: authManager)
            }
            .task {
                await viewModel.loadInitial(apiClient: apiClient, authManager: authManager)
            }
            .navigationDestination(for: Transaction.self) { transaction in
                ReceiptView(transaction: transaction)
            }
        }
    }

    private var hasActiveSearchOrFilter: Bool {
        !viewModel.searchQuery.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.selectedFilter != .all
    }

    private var screenTransitionAnimation: Animation {
        AppTheme.Motion.animation(
            for: .cardSurface,
            accessibilityReduceMotion: accessibilityReduceMotion
        )
    }

    private var stateCardTransition: AnyTransition {
        if accessibilityReduceMotion {
            return .opacity
        }

        return .asymmetric(
            insertion: .opacity.combined(with: .move(edge: .bottom)),
            removal: .opacity
        )
    }

    private var transactionStateKey: String {
        if viewModel.isLoading && viewModel.allTransactions.isEmpty {
            return "loading"
        }

        if viewModel.initialLoadErrorMessage != nil && viewModel.allTransactions.isEmpty {
            return "initial_error"
        }

        if viewModel.isBaseEmptyState {
            return "base_empty"
        }

        if viewModel.isFilteredEmptyState {
            return "filtered_empty"
        }

        var key = "list_count_\(viewModel.transactions.count)"

        if viewModel.hasPaginationFailureState {
            key += "_pagination_error"
        }

        if viewModel.hasMore {
            key += viewModel.isLoadingMore ? "_loading_more" : "_has_more"
        } else {
            key += "_end"
        }

        return key
    }

    private var filterControlsCard: some View {
        StitchCard(padding: AppTheme.Spacing.md) {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Filter Transactions")
                    .font(AppTheme.Typography.caption)
                    .foregroundStyle(AppTheme.Palette.textSecondary)

                Picker("Transaction Type", selection: $viewModel.selectedFilter) {
                    ForEach(TransactionFilter.allCases, id: \.self) { filter in
                        Text(filterTitle(for: filter))
                            .tag(filter)
                    }
                }
                .pickerStyle(.segmented)
                .accessibilityIdentifier("transactions-filter-picker")
                .accessibilityLabel("Transaction type filter")

                if hasActiveSearchOrFilter {
                    Button {
                        viewModel.clearSearchAndFilter()
                    } label: {
                        Label("Clear Search & Filter", systemImage: "xmark.circle")
                    }
                    .buttonStyle(StitchPrimaryButtonStyle())
                    .accessibilityIdentifier("transactions-clear-search-filter-button")
                    .accessibilityHint("Resets search text and type filter")
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    @ViewBuilder
    private var transactionStateRows: some View {
        if viewModel.isLoading && viewModel.allTransactions.isEmpty {
            styledListRow {
                loadingStateCard
                    .transition(stateCardTransition)
            }
        } else if let initialLoadError = viewModel.initialLoadErrorMessage, viewModel.allTransactions.isEmpty {
            styledListRow {
                initialLoadErrorStateCard(message: initialLoadError)
                    .transition(stateCardTransition)
            }
        } else if viewModel.isBaseEmptyState {
            styledListRow {
                baseEmptyStateCard
                    .transition(stateCardTransition)
            }
        } else if viewModel.isFilteredEmptyState {
            styledListRow {
                filteredEmptyStateCard
                    .transition(stateCardTransition)
            }
        } else {
            ForEach(viewModel.transactions) { transaction in
                styledListRow {
                    Group {
                        if transaction.isNavigable {
                            NavigationLink(value: transaction) {
                                TransactionRowView(transaction: transaction)
                            }
                            .buttonStyle(.plain)
                        } else {
                            TransactionRowView(transaction: transaction)
                        }
                    }
                }
            }

            if viewModel.hasPaginationFailureState, let paginationError = viewModel.paginationErrorMessage {
                styledListRow(top: AppTheme.Spacing.sm, bottom: AppTheme.Spacing.xs) {
                    paginationErrorStateCard(message: paginationError)
                        .transition(stateCardTransition)
                }
            }

            if viewModel.hasMore {
                styledListRow(top: AppTheme.Spacing.sm, bottom: AppTheme.Spacing.xs) {
                    loadMoreCard
                        .transition(stateCardTransition)
                }
            }
        }
    }

    private var loadingStateCard: some View {
        StitchCard {
            HStack(spacing: AppTheme.Spacing.sm) {
                ProgressView()
                Text("Loading transactions…")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
            }
            .frame(maxWidth: .infinity, alignment: .center)
        }
        .accessibilityIdentifier("transactions-state-loading")
    }

    private func initialLoadErrorStateCard(message: String) -> some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Couldn’t Load Transactions")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.danger)

                Text(message)
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Button {
                    Task {
                        await viewModel.loadInitial(apiClient: apiClient, authManager: authManager)
                    }
                } label: {
                    Label("Retry", systemImage: "arrow.clockwise")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("transactions-retry-initial-button")
                .accessibilityHint("Retries loading transactions from the start")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("transactions-state-initial-error")
    }

    private var baseEmptyStateCard: some View {
        StitchCard {
            VStack(spacing: AppTheme.Spacing.sm) {
                Text("No transactions yet")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("Your transaction history will appear here once activity is recorded.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.center)

                Button {
                    Task {
                        await viewModel.loadInitial(apiClient: apiClient, authManager: authManager)
                    }
                } label: {
                    Label("Refresh Transactions", systemImage: "arrow.clockwise")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("transactions-refresh-empty-button")
            }
            .frame(maxWidth: .infinity)
        }
        .accessibilityIdentifier("transactions-state-base-empty")
    }

    private var filteredEmptyStateCard: some View {
        StitchCard {
            VStack(spacing: AppTheme.Spacing.sm) {
                Text("No matching transactions")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("Try a different search term or reset your filter to see all transactions.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.center)

                Button {
                    viewModel.clearSearchAndFilter()
                } label: {
                    Label("Clear Search & Filter", systemImage: "xmark.circle")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("transactions-clear-no-match-button")
            }
            .frame(maxWidth: .infinity)
        }
        .accessibilityIdentifier("transactions-state-filtered-empty")
    }

    private func paginationErrorStateCard(message: String) -> some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Couldn’t load more transactions.")
                    .font(AppTheme.Typography.bodyStrong)
                    .foregroundStyle(AppTheme.Palette.danger)

                Text(message)
                    .font(AppTheme.Typography.caption)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Button {
                    Task {
                        await viewModel.loadMore(apiClient: apiClient, authManager: authManager)
                    }
                } label: {
                    Label("Retry Load More", systemImage: "arrow.clockwise")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("transactions-retry-pagination-button")
                .accessibilityHint("Retries loading the next page without losing loaded transactions")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("transactions-state-pagination-error")
    }

    private var loadMoreCard: some View {
        StitchCard(padding: AppTheme.Spacing.sm) {
            if viewModel.isLoadingMore {
                HStack(spacing: AppTheme.Spacing.sm) {
                    ProgressView()
                    Text("Loading more transactions…")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .center)
            } else {
                Button {
                    Task {
                        await viewModel.loadMore(apiClient: apiClient, authManager: authManager)
                    }
                } label: {
                    Label("Load More", systemImage: "arrow.down.circle")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("transactions-load-more-button")
                .accessibilityHint("Loads older transaction history")
            }
        }
    }

    private func filterTitle(for filter: TransactionFilter) -> String {
        switch filter {
        case .all:
            return "All"
        case .debit:
            return "Debit"
        case .credit:
            return "Credit"
        }
    }

    private func styledListRow<Content: View>(
        top: CGFloat = AppTheme.Spacing.xs,
        bottom: CGFloat = AppTheme.Spacing.xs,
        @ViewBuilder content: () -> Content
    ) -> some View {
        content()
            .listRowInsets(
                EdgeInsets(
                    top: top,
                    leading: AppTheme.Spacing.lg,
                    bottom: bottom,
                    trailing: AppTheme.Spacing.lg
                )
            )
            .listRowSeparator(.hidden)
            .listRowBackground(AppTheme.Palette.background)
    }
}
