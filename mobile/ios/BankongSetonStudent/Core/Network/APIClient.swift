import Foundation

// MARK: - APIError

enum APIError: Error {
    case cardLost          // 403 + body["error"] == "CARD_LOST"
    case unauthorized      // 403 (any other body)
    case httpError(Int)    // non-2xx other than 403
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

    // MARK: - Private Helpers

    private func authenticatedRequest(
        path: String,
        method: String = "GET",
        body: Data? = nil
    ) throws -> URLRequest {
        guard let url = URL(string: APIEndpoints.baseURL + path) else {
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
                // Distinguish CARD_LOST from generic unauthorized
                if let body = try? JSONDecoder().decode([String: String].self, from: data),
                   body["error"] == "CARD_LOST" {
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

    func login(studentId: String, pin: String) async throws -> LoginResponse {
        guard let url = URL(string: APIEndpoints.baseURL + APIEndpoints.login) else {
            throw APIError.invalidURL
        }
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        let body = LoginRequest(studentId: studentId, pin: pin)
        request.httpBody = try encoder.encode(body)
        return try await perform(request)
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
}

// MARK: - BudgetSummaryResponse

struct BudgetSummaryResponse: Decodable {
    let spent: Double

    enum CodingKeys: String, CodingKey {
        case spent = "monthly_spend"
    }
}
