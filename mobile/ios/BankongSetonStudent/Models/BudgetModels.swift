import Foundation

// MARK: - BudgetResponse

struct BudgetResponse: Codable {
    let monthlyLimit: Double?   // nil when no limit has been set yet
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
    let monthlyLimit: Double?   // server may omit this field

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
