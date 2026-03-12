import Foundation

// MARK: - TransactionItem

struct TransactionItem: Codable {
    let name: String
    let price: Double
    let qty: Int
}

// MARK: - Transaction
// Conforms to Hashable for navigationDestination(for: Transaction.self)

struct Transaction: Codable, Identifiable, Hashable {
    var id = UUID()                // local only — not from API
    let timestamp: String
    let type: String
    let amount: Double
    let balanceBefore: Double
    let balance: Double
    let description: String?
    let items: [TransactionItem]?

    enum CodingKeys: String, CodingKey {
        case timestamp, type, amount, description, items, balance
        case balanceBefore = "balance_before"
    }

    // Hashable conformance — id is sufficient since it's unique per instance
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: Transaction, rhs: Transaction) -> Bool {
        lhs.id == rhs.id
    }
}

// MARK: - TransactionsResponse

struct TransactionsResponse: Codable {
    let transactions: [Transaction]
    let count: Int
    let total: Int
    let hasMore: Bool

    enum CodingKeys: String, CodingKey {
        case transactions, count, total
        case hasMore = "has_more"
    }
}
