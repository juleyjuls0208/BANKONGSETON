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

    private var activeQRAPIBaseURLOverride: String?

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

        activeQRAPIBaseURLOverride = parsedPayload.apiBaseURLOverride
        let resolvedEndpoint = parsedPayload.apiBaseURLOverride ?? APIEndpoints.baseURL
        log(
            "Accepted QR payload source=\(parsedPayload.source), token=\(redact(parsedPayload.token)), endpoint=\(resolvedEndpoint)"
        )
        transition(to: .loading, reason: "scan_accepted_\(parsedPayload.source)")

        Task {
            do {
                let cart = try await apiClient.getQrCart(
                    token: parsedPayload.token,
                    apiBaseURLOverride: parsedPayload.apiBaseURLOverride
                )
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

        let apiBaseURLOverride = activeQRAPIBaseURLOverride

        transition(to: .loading, reason: "confirm_started")

        Task {
            do {
                let response = try await apiClient.confirmQrPayment(
                    token: token,
                    apiBaseURLOverride: apiBaseURLOverride
                )
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
        activeQRAPIBaseURLOverride = nil
        transition(to: .scanning, reason: "user_retry")
    }

    private func transition(to newState: QRPayState, reason: String) {
        let oldState = state.debugLabel
        state = newState
        log("QRPayState transition \(oldState) -> \(newState.debugLabel), reason=\(reason)")
    }

    private func parseScannedPayload(_ payload: String) -> ParsedQRPayload? {
        if let urlToken = extractTokenFromQRURL(payload), isValidToken(urlToken) {
            if let trustedBaseURL = extractTrustedAPIBaseURLOverride(from: payload, token: urlToken) {
                return ParsedQRPayload(
                    token: urlToken,
                    source: "url_direct",
                    apiBaseURLOverride: trustedBaseURL
                )
            }

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

        let reservedTailSegments: Set<String> = [
            "confirm", "generate", "pending", "status", "register", "cancel", "paid"
        ]

        for index in 0..<parts.count {
            let current = parts[index].lowercased()
            guard current == "qr", index + 1 < parts.count else {
                continue
            }

            let tokenWithPossibleTail = parts[index + 1]
            let token = tokenWithPossibleTail
                .split(whereSeparator: { $0 == "?" || $0 == "#" })
                .first
                .map(String.init) ?? ""

            let decodedToken = token.removingPercentEncoding ?? token
            if reservedTailSegments.contains(decodedToken.lowercased()) {
                continue
            }

            return decodedToken
        }

        return nil
    }

    private func extractTrustedAPIBaseURLOverride(from payload: String, token: String) -> String? {
        guard let components = URLComponents(string: payload),
              let scheme = components.scheme?.lowercased(),
              (scheme == "http" || scheme == "https"),
              let host = components.host?.lowercased(),
              !host.isEmpty else {
            return nil
        }

        let segments = components.path
            .split(separator: "/")
            .map(String.init)

        guard let qrIndex = segments.lastIndex(where: { $0.lowercased() == "qr" }),
              qrIndex + 1 < segments.count else {
            return nil
        }

        let encodedToken = segments[qrIndex + 1]
        let decodedToken = encodedToken.removingPercentEncoding ?? encodedToken
        guard decodedToken == token else {
            return nil
        }

        guard isTrustedQRHost(host, scheme: scheme) else {
            log("Ignoring untrusted QR host=\(host). Falling back to default API endpoint.")
            return nil
        }

        let prefixSegments = segments.prefix(qrIndex)
        let prefixPath = prefixSegments.isEmpty ? "" : "/" + prefixSegments.joined(separator: "/")

        var baseURL = "\(scheme)://\(host)"
        if let port = components.port {
            baseURL += ":\(port)"
        }

        return baseURL + prefixPath
    }

    private func isTrustedQRHost(_ host: String, scheme: String) -> Bool {
        let normalizedHost = host.lowercased()
        let defaultAPIHost = URL(string: APIEndpoints.baseURL)?.host?.lowercased()

        if let defaultAPIHost, normalizedHost == defaultAPIHost {
            return scheme == "https"
        }

        if normalizedHost == "localhost" || normalizedHost == "127.0.0.1" || normalizedHost == "::1" {
            return true
        }

        if normalizedHost.hasSuffix(".local") {
            return true
        }

        return isPrivateIPv4Host(normalizedHost)
    }

    private func isPrivateIPv4Host(_ host: String) -> Bool {
        let octets = host.split(separator: ".")
        guard octets.count == 4 else { return false }

        let values = octets.compactMap { Int($0) }
        guard values.count == 4, values.allSatisfy({ (0...255).contains($0) }) else {
            return false
        }

        let first = values[0]
        let second = values[1]

        if first == 10 { return true }
        if first == 172 && (16...31).contains(second) { return true }
        if first == 192 && second == 168 { return true }
        if first == 169 && second == 254 { return true }

        return false
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
    let apiBaseURLOverride: String?

    init(token: String, source: String, apiBaseURLOverride: String? = nil) {
        self.token = token
        self.source = source
        self.apiBaseURLOverride = apiBaseURLOverride
    }
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
