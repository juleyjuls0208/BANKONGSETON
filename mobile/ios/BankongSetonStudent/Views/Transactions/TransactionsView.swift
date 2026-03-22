import SwiftUI

// MARK: - TransactionsView
// Paginated transaction list.
// Purchase / NFC / Payment rows → NavigationLink to ReceiptView.
// Top-Up / Load rows → non-tappable (no NavigationLink).

struct TransactionsView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = TransactionsViewModel()

    var body: some View {
        NavigationStack {
            List {
                ForEach(viewModel.transactions) { transaction in
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
                    .listRowInsets(
                        EdgeInsets(
                            top: AppTheme.Spacing.xs,
                            leading: AppTheme.Spacing.lg,
                            bottom: AppTheme.Spacing.xs,
                            trailing: AppTheme.Spacing.lg
                        )
                    )
                    .listRowSeparator(.hidden)
                    .listRowBackground(AppTheme.Palette.background)
                }

                if viewModel.hasMore {
                    StitchCard(padding: AppTheme.Spacing.sm) {
                        if viewModel.isLoadingMore {
                            HStack(spacing: AppTheme.Spacing.sm) {
                                ProgressView()
                                Text("Loading more transactions…")
                                    .font(AppTheme.Typography.body)
                                    .foregroundStyle(AppTheme.Palette.textSecondary)
                            }
                            .frame(maxWidth: .infinity)
                        } else {
                            Button {
                                Task {
                                    await viewModel.loadMore(apiClient: apiClient, authManager: authManager)
                                }
                            } label: {
                                Label("Load More", systemImage: "arrow.down.circle")
                            }
                            .buttonStyle(StitchPrimaryButtonStyle())
                        }
                    }
                    .listRowInsets(
                        EdgeInsets(
                            top: AppTheme.Spacing.sm,
                            leading: AppTheme.Spacing.lg,
                            bottom: AppTheme.Spacing.xs,
                            trailing: AppTheme.Spacing.lg
                        )
                    )
                    .listRowSeparator(.hidden)
                    .listRowBackground(AppTheme.Palette.background)
                }
            }
            .listStyle(.plain)
            .scrollContentBackground(.hidden)
            .background(AppTheme.Palette.background)
            .navigationTitle("Transactions")
            .overlay {
                stateOverlay
            }
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

    @ViewBuilder
    private var stateOverlay: some View {
        if viewModel.isLoading {
            StitchCard {
                HStack(spacing: AppTheme.Spacing.sm) {
                    ProgressView()
                    Text("Loading transactions…")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                }
                .frame(maxWidth: .infinity, alignment: .center)
            }
            .padding(.horizontal, AppTheme.Spacing.lg)
        } else if let error = viewModel.errorMessage {
            StitchCard {
                VStack(spacing: AppTheme.Spacing.xs) {
                    Text("Couldn’t Load Transactions")
                        .font(AppTheme.Typography.headline)
                        .foregroundStyle(AppTheme.Palette.danger)
                        .frame(maxWidth: .infinity, alignment: .leading)

                    Text(error)
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.leading)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            .padding(.horizontal, AppTheme.Spacing.lg)
        } else if viewModel.transactions.isEmpty {
            StitchCard {
                VStack(spacing: AppTheme.Spacing.xs) {
                    Text("No transactions yet")
                        .font(AppTheme.Typography.headline)
                        .foregroundStyle(AppTheme.Palette.textPrimary)
                    Text("Your transaction history will appear here.")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.center)
                }
                .frame(maxWidth: .infinity)
            }
            .padding(.horizontal, AppTheme.Spacing.lg)
        }
    }
}
