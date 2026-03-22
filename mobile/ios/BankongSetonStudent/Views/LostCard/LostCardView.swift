import SwiftUI

struct LostCardView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager
    @Environment(\.dismiss) private var dismiss

    @StateObject private var viewModel = LostCardViewModel()

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 64))
                .foregroundColor(.orange)

            Text("Report your card as lost. This will block your card from being used.")
                .font(.body)
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)
                .padding(.horizontal, 8)

            stateSurface
                .frame(maxWidth: .infinity)

            Spacer()
        }
        .padding(.horizontal, 24)
        .navigationTitle("Report Lost Card")
        .navigationBarTitleDisplayMode(.inline)
    }

    @ViewBuilder
    private var stateSurface: some View {
        switch viewModel.phase {
        case .idle:
            Button("Report Lost Card") {
                Task {
                    await viewModel.reportLostCard(apiClient: apiClient, authManager: authManager)
                }
            }
            .buttonStyle(.borderedProminent)
            .tint(.red)
            .disabled(!viewModel.canReportLostCard)
            .accessibilityIdentifier("lost-card-report-button")

        case .loading:
            VStack(spacing: 12) {
                ProgressView()
                Text("Reporting your card loss…")
                    .font(.callout)
                    .foregroundColor(.secondary)
            }
            .accessibilityIdentifier("lost-card-state-loading")

        case .success:
            VStack(spacing: 16) {
                Text(viewModel.successMessage ?? "Your card has been reported as lost. Please contact administration.")
                    .font(.callout)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.green)

                Button("Back to Settings") {
                    dismiss()
                }
                .buttonStyle(.borderedProminent)
                .accessibilityIdentifier("lost-card-success-done-button")
            }
            .accessibilityIdentifier("lost-card-state-success")

        case .error:
            VStack(spacing: 16) {
                Text(viewModel.errorMessage ?? "Failed to report card. Please try again.")
                    .font(.callout)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.red)

                Button("Retry Report") {
                    Task {
                        await viewModel.retryReport(apiClient: apiClient, authManager: authManager)
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
                .disabled(!viewModel.canRetry)
                .accessibilityIdentifier("lost-card-retry-button")

                Button("Back to Settings") {
                    dismiss()
                }
                .buttonStyle(.bordered)
                .accessibilityIdentifier("lost-card-error-dismiss-button")
            }
            .accessibilityIdentifier("lost-card-state-error")
        }
    }
}
