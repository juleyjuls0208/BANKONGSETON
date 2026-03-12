import SwiftUI

// MARK: - HomeView
// Displays balance, student name, and 3 most recent transactions.
// No NFC Pay button — iOS cannot emulate HCE (Apple Pay only).

struct HomeView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = HomeViewModel()

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 24) {

                    // MARK: Balance Card
                    VStack(spacing: 8) {
                        Text(authManager.studentName)
                            .font(.subheadline)
                            .foregroundColor(.white.opacity(0.85))
                        Text("₱\(String(format: "%.2f", viewModel.balance))")
                            .font(.system(size: 44, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                        Text("Current Balance")
                            .font(.caption)
                            .foregroundColor(.white.opacity(0.75))
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 32)
                    .background(
                        LinearGradient(
                            colors: [Color(hex: "#1565C0"), Color(hex: "#1E88E5")],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .cornerRadius(20)
                    .padding(.horizontal)

                    // MARK: Error message
                    if let error = viewModel.errorMessage {
                        Text(error)
                            .foregroundColor(.red)
                            .font(.subheadline)
                            .multilineTextAlignment(.center)
                            .padding(.horizontal)
                    }

                    // MARK: Recent Transactions
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Recent Transactions")
                            .font(.headline)
                            .padding(.horizontal)

                        if viewModel.isLoading {
                            HStack {
                                Spacer()
                                ProgressView()
                                Spacer()
                            }
                            .padding()
                        } else if viewModel.recentTransactions.isEmpty && viewModel.errorMessage == nil {
                            Text("No recent transactions.")
                                .foregroundColor(.secondary)
                                .font(.subheadline)
                                .padding(.horizontal)
                        } else {
                            ForEach(viewModel.recentTransactions) { transaction in
                                TransactionRowView(transaction: transaction)
                                    .padding(.horizontal)
                                Divider()
                                    .padding(.leading)
                            }
                        }
                    }

                    Spacer(minLength: 20)
                }
                .padding(.top)
            }
            .navigationTitle("Home")
            .refreshable {
                await viewModel.load(apiClient: apiClient, authManager: authManager)
            }
            .task {
                await viewModel.load(apiClient: apiClient, authManager: authManager)
            }
        }
    }
}
