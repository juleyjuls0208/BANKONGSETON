import Foundation
import SwiftUI

enum QRPayState {
    case scanning
    case loading
    case confirming(cart: QrCartResponse, token: String)
    case success(newBalance: Double?)
    case error(String)
}

@MainActor
final class QRPayViewModel: ObservableObject {
    @Published var state: QRPayState = .scanning
    @Published var isPresented: Bool = true

    func handleScannedURL(_ urlString: String, apiClient: APIClient) {
        // Extract token from URL last path segment
        guard let url = URL(string: urlString),
              let token = url.pathComponents.last, !token.isEmpty,
              urlString.contains("/api/qr/") else {
            return  // ignore non-QR URLs
        }
        state = .loading
        Task {
            do {
                let cart = try await apiClient.getQrCart(token: token)
                state = .confirming(cart: cart, token: token)
            } catch APIError.httpError(404), APIError.httpError(410) {
                state = .error("QR code has expired. Ask the cashier to generate a new one.")
            } catch APIError.unauthorized {
                state = .error("Session expired. Please log out and log in again.")
            } catch APIError.networkError(let e) {
                state = .error("Network error: \(e.localizedDescription)")
            } catch {
                state = .error("Failed to load cart. Please try again.")
            }
        }
    }

    func confirm(token: String, apiClient: APIClient) {
        state = .loading
        Task {
            do {
                let response = try await apiClient.confirmQrPayment(token: token)
                state = .success(newBalance: response.newBalance)
            } catch APIError.httpError(402) {
                state = .error("Insufficient balance. Please top up your card.")
            } catch APIError.httpError(404), APIError.httpError(410) {
                state = .error("QR code has expired. Ask the cashier to generate a new one.")
            } catch APIError.unauthorized {
                state = .error("Session expired. Please log out and log in again.")
            } catch APIError.networkError(let e) {
                state = .error("Network error: \(e.localizedDescription)")
            } catch {
                state = .error("Payment failed. Please try again.")
            }
        }
    }

    func reset() {
        state = .scanning
    }
}
