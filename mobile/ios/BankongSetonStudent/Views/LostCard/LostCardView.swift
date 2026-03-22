import SwiftUI

struct LostCardView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) private var dismiss

    @StateObject private var viewModel = LostCardViewModel()

    var body: some View {
        ZStack {
            AppTheme.Palette.background
                .ignoresSafeArea()

            ScrollView {
                VStack(spacing: AppTheme.Spacing.lg) {
                    introCard
                    stateCard
                }
                .padding(.horizontal, AppTheme.Spacing.lg)
                .padding(.vertical, AppTheme.Spacing.lg)
                .accessibilityIdentifier("lost-card-screen-root")
            }
        }
        .navigationTitle("Report Lost Card")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var introCard: some View {
        StitchCard {
            VStack(spacing: AppTheme.Spacing.sm) {
                Image(systemName: "exclamationmark.shield.fill")
                    .font(.system(size: 44, weight: .semibold))
                    .foregroundStyle(AppTheme.Palette.danger)
                    .accessibilityHidden(true)

                Text("Protect your account")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("Report your card as lost to block future transactions. This action cannot be undone from the app.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.center)
            }
            .frame(maxWidth: .infinity)
        }
        .accessibilityIdentifier("lost-card-intro-card")
    }

    @ViewBuilder
    private var stateCard: some View {
        switch viewModel.phase {
        case .idle:
            idleStateCard
        case .loading:
            loadingStateCard
        case .success:
            successStateCard
        case .error:
            errorStateCard
        }
    }

    private var idleStateCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Ready to report")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                Text("When you continue, we will notify the backend and lock your card for security.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Button("Report Lost Card") {
                    Task {
                        await viewModel.reportLostCard(apiClient: apiClient, authManager: authManager)
                    }
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .disabled(!viewModel.canReportLostCard)
                .accessibilityIdentifier("lost-card-report-button")
                .accessibilityHint("Reports this card as lost and blocks new transactions")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("lost-card-state-idle")
        .accessibilityLabel("Lost-card report ready")
    }

    private var loadingStateCard: some View {
        StitchCard {
            HStack(spacing: AppTheme.Spacing.sm) {
                ProgressView()
                Text("Reporting your card loss…")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
            }
            .frame(maxWidth: .infinity, alignment: .center)
        }
        .accessibilityIdentifier("lost-card-state-loading")
        .accessibilityLabel("Reporting lost card")
        .accessibilityHint("Wait while your lost-card report is processed")
    }

    private var successStateCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Card reported")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.success)

                Text(viewModel.successMessage ?? "Your card has been reported as lost. Please contact administration.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Button("Back to Settings") {
                    dismiss()
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .accessibilityIdentifier("lost-card-success-done-button")
                .accessibilityHint("Returns to Settings after successful card report")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("lost-card-state-success")
        .accessibilityLabel("Lost-card report succeeded")
    }

    private var errorStateCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Couldn’t report card")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.danger)

                Text(viewModel.errorMessage ?? "Failed to report card. Please try again.")
                    .font(AppTheme.Typography.body)
                    .foregroundStyle(AppTheme.Palette.textSecondary)
                    .multilineTextAlignment(.leading)

                Button("Retry Report") {
                    Task {
                        await viewModel.retryReport(apiClient: apiClient, authManager: authManager)
                    }
                }
                .buttonStyle(StitchPrimaryButtonStyle())
                .disabled(!viewModel.canRetry)
                .accessibilityIdentifier("lost-card-retry-button")
                .accessibilityHint("Retries reporting your card as lost")

                Button("Back to Settings") {
                    dismiss()
                }
                .font(AppTheme.Typography.bodyStrong)
                .frame(maxWidth: .infinity)
                .frame(minHeight: 44)
                .foregroundStyle(AppTheme.Palette.textPrimary)
                .background(AppTheme.Palette.surfaceSubtle)
                .clipShape(RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous))
                .overlay(
                    RoundedRectangle(cornerRadius: AppTheme.Radius.md, style: .continuous)
                        .stroke(AppTheme.Palette.border, lineWidth: 1)
                )
                .accessibilityIdentifier("lost-card-error-dismiss-button")
                .accessibilityHint("Returns to Settings without retrying")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("lost-card-state-error")
        .accessibilityLabel("Lost-card report failed")
    }
}
