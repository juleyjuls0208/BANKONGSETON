import Foundation

enum LostCardFlowPhase: String {
    case idle
    case loading
    case success
    case error
}

@MainActor
final class LostCardViewModel: ObservableObject {
    @Published private(set) var phase: LostCardFlowPhase = .idle
    @Published private(set) var errorMessage: String?
    @Published private(set) var successMessage: String?

    var isLoading: Bool {
        phase == .loading
    }

    var canReportLostCard: Bool {
        phase == .idle || phase == .error
    }

    var canRetry: Bool {
        phase == .error
    }

    func reportLostCard(apiClient: APIClient, authManager: AuthManager) async {
        errorMessage = nil
        successMessage = nil
        transition(to: .loading, reason: "report_started")

        do {
            let response = try await apiClient.reportLostCard()

            guard response.success else {
                transitionToError(
                    message: response.message ?? "Couldn’t report card loss right now. Tap Retry to try again.",
                    reason: "report_unsuccessful_response"
                )
                return
            }

            KeychainHelper.save("true", forKey: "isCardLost")
            successMessage = response.message ?? "Your card has been reported as lost. Please contact administration."
            transition(to: .success, reason: "report_success")
        } catch APIError.unauthorized {
            transitionToError(
                message: "Session expired while reporting your card. Please sign in again.",
                reason: "report_unauthorized"
            )
            authManager.handleUnauthorized()
        } catch APIError.cardLost {
            successMessage = "Your card is already marked as lost. Please sign in again after contacting administration."
            transition(to: .success, reason: "report_card_already_lost")
            authManager.handleCardLost()
        } catch {
            transitionToError(
                message: "Failed to report card. Please check your connection and tap Retry.",
                reason: "report_unknown_error"
            )
        }
    }

    func retryReport(apiClient: APIClient, authManager: AuthManager) async {
        await reportLostCard(apiClient: apiClient, authManager: authManager)
    }

    func resetToIdle() {
        errorMessage = nil
        successMessage = nil
        transition(to: .idle, reason: "user_reset")
    }

    private func transitionToError(message: String, reason: String) {
        successMessage = nil
        errorMessage = message
        transition(to: .error, reason: reason)
    }

    private func transition(to newPhase: LostCardFlowPhase, reason: String) {
        let previous = phase.rawValue
        phase = newPhase
        log("LostCardFlowPhase transition \(previous) -> \(newPhase.rawValue), reason=\(reason)")
    }

    private func log(_ message: String) {
        print("[LostCardViewModel] \(message)")
    }
}
