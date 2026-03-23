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
            log("Ignoring duplicate scan while state is \(state.debugLabel)")
            return
        }

        let trimmedPayload = payload.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedPayload.isEmpty else {
            transition(
                to: .error("We couldn't read that QR code. Please try scanning again."),
                reason: "empty_scan_payload"
            )
            return
        }

        guard let parsedPayload = parseScannedPayload(trimmedPayload) else {
            transition(
                to: .error("This QR is invalid for payment. Ask the cashier for a new QR, then tap Retry."),
                reason: "invalid_scan_payload"
            )
            return
        }

        log("Accepted QR payload source=\(parsedPayload.source), token=\(redact(parsedPayload.token))")
        transition(to: .loading, reason: "scan_accepted_\(parsedPayload.source)")

        Task {
            do {
                let cart = try await apiClient.getQrCart(token: parsedPayload.token)
                transition(to: .confirming(cart: cart, token: parsedPayload.token), reason: "cart_loaded")
            } catch APIError.httpError(404), APIError.httpError(410) {
                transition(
                    to: .error("QR code has expired. Ask the cashier to generate a new one."),
                    reason: "cart_fetch_expired"
                )
            } catch APIError.unauthorized {
                transition(
                    to: .error("Session expired. Please log out and log in again."),
                    reason: "cart_fetch_unauthorized"
                )
            } catch APIError.networkError(let error) {
                transition(
                    to: .error("Network error: \(error.localizedDescription)"),
                    reason: "cart_fetch_network_error"
                )
            } catch {
                transition(
                    to: .error("Failed to load cart. Please try again."),
                    reason: "cart_fetch_unknown_error"
                )
            }
        }
    }

    func handleScannerFailure(_ message: String) {
        guard case .scanning = state else {
            log("Ignoring scanner failure callback while state is \(state.debugLabel)")
            return
        }

        transition(to: .error(message), reason: "scanner_failure")
    }

    func confirm(token: String, apiClient: APIClient) {
        guard case let .confirming(_, activeToken) = state else {
            log("Ignoring confirm action while state is \(state.debugLabel)")
            return
        }

        guard activeToken == token else {
            log("Ignoring confirm action due to mismatched token")
            return
        }

        transition(to: .loading, reason: "confirm_started")

        Task {
            do {
                let response = try await apiClient.confirmQrPayment(token: token)
                transition(to: .success(newBalance: response.newBalance), reason: "confirm_success")
            } catch APIError.httpError(402) {
                transition(
                    to: .error("Insufficient balance. Please top up your card."),
                    reason: "confirm_insufficient_balance"
                )
            } catch APIError.httpError(404), APIError.httpError(410) {
                transition(
                    to: .error("QR code has expired. Ask the cashier to generate a new one."),
                    reason: "confirm_expired"
                )
            } catch APIError.unauthorized {
                transition(
                    to: .error("Session expired. Please log out and log in again."),
                    reason: "confirm_unauthorized"
                )
            } catch APIError.networkError(let error) {
                transition(
                    to: .error("Network error: \(error.localizedDescription)"),
                    reason: "confirm_network_error"
                )
            } catch {
                transition(
                    to: .error("Payment failed. Please try again."),
                    reason: "confirm_unknown_error"
                )
            }
        }
    }

    func reset() {
        transition(to: .scanning, reason: "user_retry")
    }

    private func transition(to newState: QRPayState, reason: String) {
        let oldState = state.debugLabel
        state = newState
        log("QRPayState transition \(oldState) -> \(newState.debugLabel), reason=\(reason)")
    }

    private func parseScannedPayload(_ payload: String) -> ParsedQRPayload? {
        if let urlToken = extractTokenFromQRURL(payload), isValidToken(urlToken) {
            return ParsedQRPayload(token: urlToken, source: "url")
        }

        if isValidToken(payload) {
            return ParsedQRPayload(token: payload, source: "token")
        }

        return nil
    }

    private func extractTokenFromQRURL(_ payload: String) -> String? {
        let path: String

        if let parsedURL = URL(string: payload), let scheme = parsedURL.scheme, !scheme.isEmpty {
            path = parsedURL.path
        } else {
            path = payload
        }

        let parts = path
            .split(separator: "/")
            .map(String.init)

        for index in 0..<parts.count {
            let current = parts[index].lowercased()
            guard current == "qr", index > 0, parts[index - 1].lowercased() == "api", index + 1 < parts.count else {
                continue
            }

            let tokenWithPossibleTail = parts[index + 1]
            let token = tokenWithPossibleTail
                .split(whereSeparator: { $0 == "?" || $0 == "#" })
                .first
                .map(String.init) ?? ""

            return token.removingPercentEncoding ?? token
        }

        return nil
    }

    private func isValidToken(_ token: String) -> Bool {
        let pattern = #"^[A-Za-z0-9_-]{6,128}$"#
        return token.range(of: pattern, options: .regularExpression) != nil
    }

    private func redact(_ token: String) -> String {
        guard token.count > 4 else { return "****" }
        let prefix = token.prefix(2)
        let suffix = token.suffix(2)
        return "\(prefix)…\(suffix)"
    }

    private func log(_ message: String) {
        print("[QRPayViewModel] \(message)")
    }
}

private struct ParsedQRPayload {
    let token: String
    let source: String
}

private extension QRPayState {
    var debugLabel: String {
        switch self {
        case .scanning:
            return "scanning"
        case .loading:
            return "loading"
        case .confirming:
            return "confirming"
        case .success:
            return "success"
        case .error:
            return "error"
        }
    }
}
