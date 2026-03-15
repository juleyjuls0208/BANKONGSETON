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
    let balanceBefore: Double?     // not always returned by server
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

// MARK: - Transaction convenience helpers

extension Transaction {
    /// Navigable = any purchase-family type OR has item detail to show.
    /// Type strings vary by server version ("purchase", "nfc purchase", "nfc"),
    /// so check broadly with contains *and* fall back to items presence.
    var isNavigable: Bool {
        let t = type.lowercased()
        let isPurchase = t.contains("purchase") || t == "nfc" || t == "payment" || t == "debit"
        let hasItems = !(items ?? []).isEmpty
        return isPurchase || hasItems
    }
}

struct TransactionsResponse: Codable {
    let transactions: [Transaction]
    let count: Int
    let total: Int?       // not always returned by server
    let hasMore: Bool?    // not always returned by server

    enum CodingKeys: String, CodingKey {
        case transactions, count, total
        case hasMore = "has_more"
    }
}
