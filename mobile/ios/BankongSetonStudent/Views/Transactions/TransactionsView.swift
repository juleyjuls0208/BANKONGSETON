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
                    if transaction.isNavigable {
                        NavigationLink(value: transaction) {
                            TransactionRowView(transaction: transaction)
                        }
                    } else {
                        TransactionRowView(transaction: transaction)
                    }
                }

                // Load More footer
                if viewModel.hasMore {
                    HStack {
                        Spacer()
                        if viewModel.isLoadingMore {
                            ProgressView()
                        } else {
                            Button("Load More") {
                                Task {
                                    await viewModel.loadMore(apiClient: apiClient, authManager: authManager)
                                }
                            }
                            .buttonStyle(.borderless)
                        }
                        Spacer()
                    }
                    .padding(.vertical, 8)
                }
            }
            .listStyle(.plain)
            .navigationTitle("Transactions")
            .overlay {
                if viewModel.isLoading {
                    ProgressView()
                }
            }
            .overlay {
                if let error = viewModel.errorMessage {
                    VStack {
                        Spacer()
                        Text(error)
                            .foregroundColor(.red)
                            .font(.subheadline)
                            .multilineTextAlignment(.center)
                            .padding()
                        Spacer()
                    }
                }
            }
            .overlay {
                if viewModel.transactions.isEmpty && !viewModel.isLoading && viewModel.errorMessage == nil {
                    VStack(spacing: 8) {
                        Text("No transactions yet")
                            .font(.headline)
                            .foregroundColor(.primary)
                        Text("Your transaction history will appear here.")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                }
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
}
