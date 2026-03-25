import Foundation

// MARK: - APIError

enum APIError: Error {
    case cardLost          // 403 + error message indicates lost card
    case unauthorized      // 401/403 when auth fails
    case loginRejected(String) // login endpoint provided user-facing rejection reason
    case httpError(Int)    // non-2xx other than auth errors
    case decodingError(Error)
    case networkError(Error)
    case invalidURL        // URL construction failed
}

// MARK: - APIClient

final class APIClient: ObservableObject {
    private let session = URLSession.shared
    private let decoder = JSONDecoder()
    private let encoder = JSONEncoder()

    private var token: String? { KeychainHelper.read(forKey: "auth_token") }
    private var jwtToken: String? { KeychainHelper.read(forKey: "jwt_token") }

    // MARK: - Private Helpers

    private func buildURL(baseURL: String, path: String) -> URL? {
        let normalizedBase = baseURL.hasSuffix("/") ? String(baseURL.dropLast()) : baseURL
        let normalizedPath = path.hasPrefix("/") ? path : "/\(path)"
        return URL(string: normalizedBase + normalizedPath)
    }

    private func authenticatedRequest(
        path: String,
        method: String = "GET",
        body: Data? = nil
    ) throws -> URLRequest {
        guard let url = buildURL(baseURL: APIEndpoints.baseURL, path: path) else {
            throw APIError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = body
        return request
    }

    private func jwtRequest(
        path: String,
        method: String = "GET",
        body: Data? = nil,
        baseURLOverride: String? = nil,
        fallbackBaseURL: String = APIEndpoints.baseURL
    ) throws -> URLRequest {
        let candidateBaseURL = baseURLOverride?.trimmingCharacters(in: .whitespacesAndNewlines)
        let targetBaseURL = (candidateBaseURL?.isEmpty == false ? candidateBaseURL : nil) ?? fallbackBaseURL

        guard let url = buildURL(baseURL: targetBaseURL, path: path) else {
            throw APIError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if let jwt = jwtToken {
            request.setValue("Bearer \(jwt)", forHTTPHeaderField: "Authorization")
        }
        request.httpBody = body
        return request
    }

    private func extractErrorMessage(from data: Data) -> String? {
        if let payload = try? decoder.decode([String: String].self, from: data) {
            if let error = payload["error"]?.trimmingCharacters(in: .whitespacesAndNewlines),
               !error.isEmpty {
                return error
            }
            if let message = payload["message"]?.trimmingCharacters(in: .whitespacesAndNewlines),
               !message.isEmpty {
                return message
            }
        }
        return nil
    }

    private func perform<T: Decodable>(_ request: URLRequest) async throws -> T {
        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }
        if let http = response as? HTTPURLResponse {
            if http.statusCode == 401 {
                throw APIError.unauthorized
            }
            if http.statusCode == 403 {
                // Distinguish lost-card responses from generic unauthorized responses.
                if let body = try? JSONDecoder().decode([String: String].self, from: data),
                   let error = body["error"]?.lowercased(),
                   error.contains("lost") {
                    throw APIError.cardLost
                }
                throw APIError.unauthorized
            }
            guard (200..<300).contains(http.statusCode) else {
                throw APIError.httpError(http.statusCode)
            }
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    // MARK: - Public Methods

    func login(studentId: String) async throws -> LoginResponse {
        guard let url = URL(string: APIEndpoints.baseURL + APIEndpoints.login) else {
            throw APIError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body = LoginRequest(studentId: studentId)
        request.httpBody = try encoder.encode(body)

        let data: Data
        let response: URLResponse
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw APIError.networkError(error)
        }

        if let http = response as? HTTPURLResponse {
            if http.statusCode == 401 {
                throw APIError.unauthorized
            }

            if http.statusCode == 403 {
                if let message = extractErrorMessage(from: data),
                   message.lowercased().contains("lost") {
                    throw APIError.cardLost
                }
                if let message = extractErrorMessage(from: data) {
                    throw APIError.loginRejected(message)
                }
                throw APIError.unauthorized
            }

            guard (200..<300).contains(http.statusCode) else {
                if let message = extractErrorMessage(from: data) {
                    throw APIError.loginRejected(message)
                }
                throw APIError.httpError(http.statusCode)
            }
        }

        do {
            return try decoder.decode(LoginResponse.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    func getBalance() async throws -> BalanceResponse {
        let req = try authenticatedRequest(path: APIEndpoints.balance)
        return try await perform(req)
    }

    func getTransactions(limit: Int, offset: Int) async throws -> TransactionsResponse {
        let path = "\(APIEndpoints.transactions)?limit=\(limit)&offset=\(offset)"
        let req = try authenticatedRequest(path: path)
        return try await perform(req)
    }

    func getBudget() async throws -> BudgetResponse {
        let req = try authenticatedRequest(path: APIEndpoints.budget)
        return try await perform(req)
    }

    func setBudget(monthlyLimit: Double) async throws -> BudgetSetResponse {
        let body = BudgetRequest(monthlyLimit: monthlyLimit)
        let bodyData = try encoder.encode(body)
        let req = try authenticatedRequest(path: APIEndpoints.budget, method: "POST", body: bodyData)
        return try await perform(req)
    }

    func reportLostCard() async throws -> LostCardResponse {
        let req = try authenticatedRequest(path: APIEndpoints.lostCard, method: "POST")
        return try await perform(req)
    }

    func logout() async throws -> GenericSuccessResponse {
        let req = try authenticatedRequest(path: APIEndpoints.logout, method: "POST")
        return try await perform(req)
    }

    func fetchBudgetSummary() async throws -> BudgetSummaryResponse {
        let req = try authenticatedRequest(path: APIEndpoints.budgetSummary)
        return try await perform(req)
    }

    func getQrCart(token: String, apiBaseURLOverride: String? = nil) async throws -> QrCartResponse {
        let req = try jwtRequest(
            path: APIEndpoints.qrCart + token,
            baseURLOverride: apiBaseURLOverride,
            fallbackBaseURL: APIEndpoints.qrBaseURL
        )
        return try await perform(req)
    }

    func confirmQrPayment(token: String, apiBaseURLOverride: String? = nil) async throws -> QrConfirmResponse {
        let body = QrConfirmRequest(token: token)
        let bodyData = try encoder.encode(body)
        let req = try jwtRequest(
            path: APIEndpoints.qrConfirm,
            method: "POST",
            body: bodyData,
            baseURLOverride: apiBaseURLOverride,
            fallbackBaseURL: APIEndpoints.qrBaseURL
        )
        return try await perform(req)
    }
}

// MARK: - BudgetSummaryResponse

struct BudgetSummaryResponse: Decodable {
    let spent: Double

    enum CodingKeys: String, CodingKey {
        case spent = "monthly_spend"
    }
}
