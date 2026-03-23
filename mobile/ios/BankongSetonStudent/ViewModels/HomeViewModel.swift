import Foundation
import os

// MARK: - HomeViewModel
// Loads balance and 3 most recent transactions for the Home screen.

@MainActor
final class HomeViewModel: ObservableObject {
    @Published var balance: Double = 0
    @Published var recentTransactions: [Transaction] = []
    @Published var isLoading = false
    @Published var errorMessage: String?

    private let logger = Logger(
        subsystem: Bundle.main.bundleIdentifier ?? "com.bankongseton.student",
        category: "HomeViewModel"
    )
    private var activeLoadToken = UUID()

    init() {
        if let cached = KeychainHelper.read(forKey: "last_balance"),
           let value = Double(cached) {
            balance = value
        }
    }

    func load(apiClient: APIClient, authManager: AuthManager) async {
        let loadToken = UUID()
        activeLoadToken = loadToken

        isLoading = true
        errorMessage = nil
        defer {
            if activeLoadToken == loadToken {
                isLoading = false
            }
        }

        async let balanceResult: Result<BalanceResponse, Error> = {
            do {
                return .success(try await apiClient.getBalance())
            } catch {
                return .failure(error)
            }
        }()

        async let transactionsResult: Result<TransactionsResponse, Error> = {
            do {
                return .success(try await apiClient.getTransactions(limit: 3, offset: 0))
            } catch {
                return .failure(error)
            }
        }()

        let (balanceResponse, txResponse) = await (balanceResult, transactionsResult)
        guard activeLoadToken == loadToken else { return }

        var messages: [String] = []

        switch balanceResponse {
        case .success(let bal):
            balance = bal.balance
            KeychainHelper.save(String(format: "%.2f", bal.balance), forKey: "last_balance")
        case .failure(let error):
            if isCancellationError(error) {
                logger.debug("Balance load cancelled")
                break
            }
            if handleAuthErrorIfNeeded(error, authManager: authManager) { return }
            logger.error("Balance load failed: \(String(describing: error), privacy: .public)")
            messages.append(userMessage(for: error, source: "balance"))
        }

        switch txResponse {
        case .success(let txs):
            recentTransactions = txs.transactions
        case .failure(let error):
            if isCancellationError(error) {
                logger.debug("Transactions load cancelled")
                break
            }
            if handleAuthErrorIfNeeded(error, authManager: authManager) { return }
            logger.error("Transactions load failed: \(String(describing: error), privacy: .public)")
            messages.append(userMessage(for: error, source: "transactions"))
        }

        if !messages.isEmpty {
            errorMessage = messages.joined(separator: "\n")
        }
    }

    private func isCancellationError(_ error: Error) -> Bool {
        if error is CancellationError {
            return true
        }

        if let urlError = error as? URLError, urlError.code == .cancelled {
            return true
        }

        guard let apiError = error as? APIError,
              case .networkError(let underlyingError) = apiError else {
            return false
        }

        if underlyingError is CancellationError {
            return true
        }

        if let urlError = underlyingError as? URLError, urlError.code == .cancelled {
            return true
        }

        let nsError = underlyingError as NSError
        return nsError.domain == NSURLErrorDomain && nsError.code == NSURLErrorCancelled
    }

    private func handleAuthErrorIfNeeded(_ error: Error, authManager: AuthManager) -> Bool {
        guard let apiError = error as? APIError else { return false }
        switch apiError {
        case .unauthorized:
            authManager.handleUnauthorized()
            return true
        case .cardLost:
            authManager.handleCardLost()
            return true
        default:
            return false
        }
    }

    private func userMessage(for error: Error, source: String) -> String {
        guard let apiError = error as? APIError else {
            return "Failed to load \(source). Pull to refresh."
        }

        switch apiError {
        case .networkError:
            return "Couldn’t load \(source) due to a network issue. Check connection and pull to refresh."
        case .decodingError:
            return "Couldn’t read \(source) from the server response. Pull to refresh."
        case .httpError(let code):
            if code >= 500 {
                return "Server is temporarily unavailable while loading \(source). Pull to refresh shortly."
            }
            return "Failed to load \(source) (\(code)). Pull to refresh."
        case .invalidURL:
            return "App configuration error while loading \(source). Please contact support."
        case .loginRejected(let message):
            return message
        case .unauthorized, .cardLost:
            return ""
        }
    }
}
