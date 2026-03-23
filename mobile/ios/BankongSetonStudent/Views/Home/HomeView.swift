import SwiftUI

// MARK: - HomeView
// Displays balance, student name, and 3 most recent transactions.
// No NFC Pay button — iOS cannot emulate HCE (Apple Pay only).

struct HomeView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.accessibilityReduceMotion) private var accessibilityReduceMotion
    @StateObject private var viewModel = HomeViewModel()
    @State private var showQrPay = false

    private var screenTransitionAnimation: Animation {
        AppTheme.Motion.animation(
            for: .cardSurface,
            accessibilityReduceMotion: accessibilityReduceMotion
        )
    }

    private var stateTransition: AnyTransition {
        if accessibilityReduceMotion {
            return .opacity
        }

        return .asymmetric(
            insertion: .opacity.combined(with: .move(edge: .bottom)),
            removal: .opacity
        )
    }

    private var errorBannerStateKey: String {
        viewModel.errorMessage == nil ? "error_hidden" : "error_visible"
    }

    private var recentTransactionStateKey: String {
        if viewModel.isLoading {
            return "recent_loading"
        }

        if viewModel.recentTransactions.isEmpty && viewModel.errorMessage == nil {
            return "recent_empty"
        }

        return "recent_list_\(viewModel.recentTransactions.count)"
    }

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.Palette.background
                    .ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: AppTheme.Spacing.xl) {
                        balanceCard
                        qrEntryCard

                        if let error = viewModel.errorMessage {
                            StitchCard {
                                HStack(alignment: .top, spacing: AppTheme.Spacing.xs) {
                                    Image(systemName: "exclamationmark.circle.fill")
                                        .foregroundStyle(AppTheme.Palette.danger)
                                        .padding(.top, 1)

                                    Text(error)
                                        .font(AppTheme.Typography.caption)
                                        .foregroundStyle(AppTheme.Palette.danger)
                                        .multilineTextAlignment(.leading)
                                        .frame(maxWidth: .infinity, alignment: .leading)
                                }
                            }
                            .transition(stateTransition)
                        }

                        recentTransactionsSection
                            .id(recentTransactionStateKey)
                            .transition(stateTransition)

                        Spacer(minLength: AppTheme.Spacing.sm)
                    }
                    .animation(screenTransitionAnimation, value: errorBannerStateKey)
                    .animation(screenTransitionAnimation, value: recentTransactionStateKey)
                    .padding(.horizontal, AppTheme.Spacing.lg)
                    .padding(.vertical, AppTheme.Spacing.lg)
                }
            }
            .navigationTitle("Home")
            .sheet(isPresented: $showQrPay) {
                QRPayView {
                    Task {
                        await viewModel.refreshAfterQRSuccess(apiClient: apiClient, authManager: authManager)
                    }
                }
                .environmentObject(apiClient)
            }
            .refreshable {
                await viewModel.load(apiClient: apiClient, authManager: authManager)
            }
            .onAppear {
                viewModel.refreshResolvedDisplayName(backendDisplayName: authManager.studentName)
            }
            .onChange(of: authManager.studentName) { newValue in
                viewModel.refreshResolvedDisplayName(backendDisplayName: newValue)
            }
            .onReceive(NotificationCenter.default.publisher(for: .settingsDisplayNameDidChange)) { _ in
                viewModel.refreshResolvedDisplayName(backendDisplayName: authManager.studentName)
            }
            .task {
                await viewModel.load(apiClient: apiClient, authManager: authManager)
            }
            .navigationDestination(for: Transaction.self) { transaction in
                ReceiptView(transaction: transaction)
            }
        }
    }

    private var balanceCard: some View {
        StitchCard(padding: 0) {
            VStack(spacing: AppTheme.Spacing.xs) {
                Text(viewModel.resolvedDisplayName)
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textInverse.opacity(0.9))

                Text("₱\(String(format: "%.2f", viewModel.balance))")
                    .font(AppTheme.Typography.display)
                    .foregroundStyle(AppTheme.Palette.textInverse)
                    .fontWeight(.bold)
                    .accessibilityLabel("Current balance \(String(format: "%.2f", viewModel.balance)) pesos")

                Text("Current Balance")
                    .font(AppTheme.Typography.caption)
                    .foregroundStyle(AppTheme.Palette.textInverse.opacity(0.82))
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, AppTheme.Spacing.xxl)
            .padding(.horizontal, AppTheme.Spacing.lg)
            .background(
                LinearGradient(
                    colors: [AppTheme.Palette.brandPrimary, AppTheme.Palette.brandSecondary],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
            )
        }
    }

    private var qrEntryCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Pay with QR")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("QR Pay is the only payment method available on iOS. Scan the cashier QR to continue.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Button {
                    showQrPay = true
                } label: {
                    Label("Pay with QR", systemImage: "qrcode.viewfinder")
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("home-qr-pay-button")
                .accessibilityHint("Opens the QR payment scanner")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
    }

    private var recentTransactionsSection: some View {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
            Text("Recent Transactions")
                .font(AppTheme.Typography.headline)
                .foregroundStyle(AppTheme.Palette.textPrimary)

            if viewModel.isLoading {
                StitchCard {
                    HStack(spacing: AppTheme.Spacing.sm) {
                        ProgressView()
                        Text("Loading recent transactions…")
                            .font(AppTheme.Typography.body)
                            .foregroundStyle(AppTheme.Palette.textSecondary)
                    }
                    .frame(maxWidth: .infinity, alignment: .center)
                }
                .transition(stateTransition)
            } else if viewModel.recentTransactions.isEmpty && viewModel.errorMessage == nil {
                StitchCard {
                    Text("No recent transactions.")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                }
                .transition(stateTransition)
            } else {
                ForEach(viewModel.recentTransactions) { transaction in
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
    }
}
