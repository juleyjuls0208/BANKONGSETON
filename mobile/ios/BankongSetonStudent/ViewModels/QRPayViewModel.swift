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

    func handleScannedURL(_ payload: String, apiClient: APIClient) {
        guard case .scanning = state else {
            return
        }

        guard let token = extractQrToken(from: payload) else {
            state = .error("Invalid QR code. Please scan a payment QR from cashier.")
            return
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

    private func extractQrToken(from payload: String) -> String? {
        let trimmed = payload.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            return nil
        }

        let plain = trimmed.hasSuffix("/") ? String(trimmed.dropLast()) : trimmed
        if isTokenCandidate(plain) {
            return plain
        }

        guard let url = URL(string: trimmed) else {
            return nil
        }

        let segments = url.pathComponents.filter { $0 != "/" }.map {
            $0.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        guard let qrIndex = segments.lastIndex(where: { $0.caseInsensitiveCompare("qr") == .orderedSame }),
              qrIndex + 1 < segments.count else {
            return nil
        }

        let candidate = segments[qrIndex + 1]
        return isTokenCandidate(candidate) ? candidate : nil
    }

    private func isTokenCandidate(_ value: String) -> Bool {
        let tokenPattern = "^[A-Za-z0-9_-]{6,64}$"
        return value.range(of: tokenPattern, options: .regularExpression) != nil
    }

    func handleScannerError(_ message: String) {
        guard case .scanning = state else {
            return
        }
        state = .error(message)
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
