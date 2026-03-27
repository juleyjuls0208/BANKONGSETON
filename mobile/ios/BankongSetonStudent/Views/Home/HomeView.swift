import SwiftUI

// MARK: - HomeView
// Displays balance, student name, and 3 most recent transactions.
// No NFC Pay button — iOS cannot emulate HCE (Apple Pay only).

struct HomeView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @StateObject private var viewModel = HomeViewModel()
    @State private var showQrPay = false
    @State private var didConsumePresentedQRSuccess = false
    @AppStorage("qr_payment_success_continuity_tick") private var qrPaymentSuccessContinuityTick = 0

    var body: some View {
        NavigationStack {
            ZStack {
                AppTheme.Palette.background
                    .ignoresSafeArea()

                ScrollView {
                    VStack(alignment: .leading, spacing: AppTheme.Spacing.lg) {
                        creditCardHero
                        qrEntryCard

                        if let error = viewModel.errorMessage {
                            errorCard(message: error)
                        }

                        recentTransactionsSection

                        Spacer(minLength: AppTheme.Spacing.sm)
                    }
                    .padding(.horizontal, AppTheme.Spacing.lg)
                    .padding(.vertical, AppTheme.Spacing.lg)
                }
            }
            .navigationTitle("Home")
            .sheet(isPresented: $showQrPay) {
                QRPayView {
                    handleQRPaySuccessCompletion()
                }
                .environmentObject(apiClient)
            }
            .onChange(of: showQrPay) { _, isPresented in
                if isPresented {
                    didConsumePresentedQRSuccess = false
                }
            }
            .refreshable {
                await viewModel.load(apiClient: apiClient, authManager: authManager)
            }
            .onAppear {
                viewModel.refreshResolvedDisplayName(backendDisplayName: authManager.studentName)
            }
            .onChange(of: authManager.studentName) { _, newValue in
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

    private func handleQRPaySuccessCompletion() {
        guard !didConsumePresentedQRSuccess else {
            print("[HomeView] Ignoring duplicate QR success callback for current presentation")
            return
        }

        didConsumePresentedQRSuccess = true
        qrPaymentSuccessContinuityTick += 1
        print("[HomeView] QR success continuity tick advanced to \(qrPaymentSuccessContinuityTick)")

        Task {
            await viewModel.refreshAfterQRSuccess(apiClient: apiClient, authManager: authManager)
        }
    }

    private var creditCardHero: some View {
        VStack(alignment: .leading, spacing: AppTheme.Spacing.md) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: AppTheme.Spacing.xxs) {
                    Text("Bankong Seton")
                        .font(AppTheme.Typography.caption)
                        .foregroundStyle(AppTheme.Palette.textInverse.opacity(0.85))

                    Text(viewModel.resolvedDisplayName)
                        .font(AppTheme.Typography.bodyStrong)
                        .foregroundStyle(AppTheme.Palette.textInverse)

                    Text("Current Balance")
                        .font(AppTheme.Typography.caption)
                        .foregroundStyle(AppTheme.Palette.textInverse.opacity(0.82))
                }

                Spacer()

                Image(systemName: "creditcard.fill")
                    .font(.system(size: 20, weight: .semibold))
                    .foregroundStyle(AppTheme.Palette.textInverse.opacity(0.9))
            }

            Text("₱\(String(format: "%.2f", viewModel.balance))")
                .font(AppTheme.Typography.display)
                .fontWeight(.bold)
                .foregroundStyle(AppTheme.Palette.textInverse)
                .accessibilityLabel("Current balance \(String(format: "%.2f", viewModel.balance)) pesos")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, AppTheme.Spacing.lg)
        .padding(.vertical, AppTheme.Spacing.xl)
        .background(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [AppTheme.Palette.brandPrimary, AppTheme.Palette.brandSecondary],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
        )
        .overlay(
            RoundedRectangle(cornerRadius: 22, style: .continuous)
                .stroke(AppTheme.Palette.textInverse.opacity(0.08), lineWidth: 1)
        )
        .accessibilityIdentifier("home-credit-card-hero")
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
                    didConsumePresentedQRSuccess = false
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

    private func errorCard(message: String) -> some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                HStack(alignment: .top, spacing: AppTheme.Spacing.xs) {
                    Image(systemName: "exclamationmark.circle.fill")
                        .foregroundStyle(AppTheme.Palette.danger)
                        .padding(.top, 1)

                    Text(message)
                        .font(AppTheme.Typography.caption)
                        .foregroundStyle(AppTheme.Palette.danger)
                        .multilineTextAlignment(.leading)
                }

                Text("Pull to refresh or tap retry.")
                    .font(AppTheme.Typography.caption)
                    .foregroundStyle(AppTheme.Palette.textSecondary)

                Button("Retry") {
                    Task {
                        await viewModel.load(apiClient: apiClient, authManager: authManager)
                    }
                }
                .buttonStyle(.bordered)
                .tint(AppTheme.Palette.brandPrimary)
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
            } else if viewModel.recentTransactions.isEmpty && viewModel.errorMessage == nil {
                StitchCard {
                    Text("No recent transactions.")
                        .font(AppTheme.Typography.body)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                }
            } else {
                StitchCard(padding: 0) {
                    VStack(spacing: 0) {
                        ForEach(Array(viewModel.recentTransactions.enumerated()), id: \.element.id) { index, transaction in
                            Group {
                                if transaction.isNavigable {
                                    NavigationLink(value: transaction) {
                                        TransactionRowView(transaction: transaction)
                                            .padding(.horizontal, AppTheme.Spacing.md)
                                            .padding(.vertical, AppTheme.Spacing.sm)
                                    }
                                    .buttonStyle(.plain)
                                } else {
                                    TransactionRowView(transaction: transaction)
                                        .padding(.horizontal, AppTheme.Spacing.md)
                                        .padding(.vertical, AppTheme.Spacing.sm)
                                }
                            }

                            if index < viewModel.recentTransactions.count - 1 {
                                Divider()
                                    .overlay(AppTheme.Palette.border)
                                    .padding(.horizontal, AppTheme.Spacing.md)
                            }
                        }
                    }
                }
            }
        }
    }
}
