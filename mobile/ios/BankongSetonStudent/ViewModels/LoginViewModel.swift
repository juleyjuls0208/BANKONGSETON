import Foundation

@MainActor
final class LoginViewModel: ObservableObject {
    @Published var studentId: String = ""
    @Published var pin: String = ""
    @Published var isLoading: Bool = false
    @Published var errorMessage: String? = nil

    var canSubmit: Bool {
        !studentId.trimmingCharacters(in: .whitespaces).isEmpty &&
        pin.count >= 4 &&
        !isLoading
    }

    func login(apiClient: APIClient, authManager: AuthManager) async {
        errorMessage = nil
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await apiClient.login(
                studentId: studentId.trimmingCharacters(in: .whitespaces),
                pin: pin
            )
            authManager.login(token: response.token, student: response.student)
        } catch APIError.cardLost {
            errorMessage = "Your card has been reported lost. Please contact the canteen admin."
        } catch APIError.unauthorized {
            errorMessage = "Invalid student ID or PIN. Please try again."
        } catch APIError.httpError(let code) {
            errorMessage = "Server error (\(code)). Please try again later."
        } catch APIError.networkError {
            errorMessage = "Network error. Check your connection and try again."
        } catch APIError.decodingError {
            errorMessage = "Server returned an unexpected response. Please try again or contact support."
        } catch APIError.invalidURL {
            errorMessage = "Configuration error: invalid server address. Please contact support."
        } catch {
            errorMessage = "An unexpected error occurred. Please try again."
        }
    }
}
