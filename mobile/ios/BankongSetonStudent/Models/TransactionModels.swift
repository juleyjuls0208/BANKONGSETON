import Foundation

// MARK: - TransactionItem

struct TransactionItem: Codable {
    let name: String
    let price: Double
    let qty: Int

    enum CodingKeys: String, CodingKey {
        case name
        case price
        case qty
        case quantity
        case itemName = "item_name"
        case unitPrice = "unit_price"
    }

    init(name: String, price: Double, qty: Int) {
        self.name = name
        self.price = price
        self.qty = qty
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        name =
            (try? container.decode(String.self, forKey: .name)) ??
            (try? container.decode(String.self, forKey: .itemName)) ??
            "Unknown item"

        price =
            Self.decodeDouble(from: container, key: .price) ??
            Self.decodeDouble(from: container, key: .unitPrice) ??
            0

        qty =
            Self.decodeInt(from: container, key: .qty) ??
            Self.decodeInt(from: container, key: .quantity) ??
            1
    }

    private static func decodeDouble(from container: KeyedDecodingContainer<CodingKeys>, key: CodingKeys) -> Double? {
        if let value = try? container.decode(Double.self, forKey: key) { return value }
        if let value = try? container.decode(Int.self, forKey: key) { return Double(value) }
        if let value = try? container.decode(String.self, forKey: key) {
            return Double(value.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        return nil
    }

    private static func decodeInt(from container: KeyedDecodingContainer<CodingKeys>, key: CodingKeys) -> Int? {
        if let value = try? container.decode(Int.self, forKey: key) { return value }
        if let value = try? container.decode(Double.self, forKey: key) { return Int(value) }
        if let value = try? container.decode(String.self, forKey: key),
           let intValue = Int(value.trimmingCharacters(in: .whitespacesAndNewlines)) {
            return intValue
        }
        return nil
    }
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

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = UUID()
        timestamp = (try? container.decode(String.self, forKey: .timestamp)) ?? ""
        type = (try? container.decode(String.self, forKey: .type)) ?? ""
        amount = Self.decodeDouble(from: container, key: .amount) ?? 0
        balanceBefore = Self.decodeDouble(from: container, key: .balanceBefore)
        balance = Self.decodeDouble(from: container, key: .balance) ?? 0
        description = try? container.decodeIfPresent(String.self, forKey: .description)
        items = try? container.decodeIfPresent([TransactionItem].self, forKey: .items)
    }

    // Hashable conformance — id is sufficient since it's unique per instance
    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }

    static func == (lhs: Transaction, rhs: Transaction) -> Bool {
        lhs.id == rhs.id
    }

    private static func decodeDouble(from container: KeyedDecodingContainer<CodingKeys>, key: CodingKeys) -> Double? {
        if let value = try? container.decode(Double.self, forKey: key) { return value }
        if let value = try? container.decode(Int.self, forKey: key) { return Double(value) }
        if let value = try? container.decode(String.self, forKey: key) {
            return Double(value.trimmingCharacters(in: .whitespacesAndNewlines))
        }
        return nil
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
