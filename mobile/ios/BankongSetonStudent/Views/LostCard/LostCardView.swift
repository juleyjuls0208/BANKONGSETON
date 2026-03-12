import SwiftUI

struct LostCardView: View {
    @EnvironmentObject var apiClient: APIClient
    @EnvironmentObject var authManager: AuthManager

    @State private var isLoading = false
    @State private var isSuccess = false
    @State private var errorMessage: String?

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            // Warning icon
            Image(systemName: "exclamationmark.triangle.fill")
                .font(.system(size: 64))
                .foregroundColor(.orange)

            // Warning text
            Text("Report your card as lost. This will block your card from being used.")
                .font(.body)
                .multilineTextAlignment(.center)
                .foregroundColor(.secondary)
                .padding(.horizontal, 32)

            if isSuccess {
                // Success confirmation
                Text("Your card has been reported as lost. Please contact administration.")
                    .font(.callout)
                    .multilineTextAlignment(.center)
                    .foregroundColor(.green)
                    .padding(.horizontal, 32)
            } else {
                // Report button
                Button("Report Lost Card") {
                    Task {
                        isLoading = true
                        errorMessage = nil
                        do {
                            let resp = try await apiClient.reportLostCard()
                            if resp.success {
                                KeychainHelper.save("true", forKey: "isCardLost")
                                isSuccess = true
                            }
                        } catch APIError.cardLost {
                            authManager.handleCardLost()
                        } catch {
                            errorMessage = "Failed to report card. Please try again."
                        }
                        isLoading = false
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
                .disabled(isLoading || isSuccess)

                if isLoading {
                    ProgressView()
                }

                if let msg = errorMessage {
                    Text(msg)
                        .font(.callout)
                        .foregroundColor(.red)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 32)
                }
            }

            Spacer()
        }
        .navigationTitle("Report Lost Card")
        .navigationBarTitleDisplayMode(.inline)
    }
}
