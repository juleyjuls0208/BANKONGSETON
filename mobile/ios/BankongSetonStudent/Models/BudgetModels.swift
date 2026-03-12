import Foundation

// MARK: - BudgetResponse

struct BudgetResponse: Codable {
    let monthlyLimit: Double
    let currency: String?

    enum CodingKeys: String, CodingKey {
        case monthlyLimit = "monthly_limit"
        case currency
    }
}

// MARK: - BudgetRequest

struct BudgetRequest: Codable {
    let monthlyLimit: Double

    enum CodingKeys: String, CodingKey {
        case monthlyLimit = "monthly_limit"
    }
}

// MARK: - BudgetSetResponse

struct BudgetSetResponse: Codable {
    let success: Bool
    let monthlyLimit: Double

    enum CodingKeys: String, CodingKey {
        case success
        case monthlyLimit = "monthly_limit"
    }
}

// MARK: - LostCardResponse

struct LostCardResponse: Codable {
    let success: Bool
    let message: String?
}
