import Foundation

// MARK: - BalanceResponse

struct BalanceResponse: Codable {
    let balance: Double
    let moneyCard: String?

    enum CodingKeys: String, CodingKey {
        case balance
        case moneyCard = "money_card"
    }
}
