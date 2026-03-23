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

// MARK: - Transaction filter semantics

enum TransactionFilter: String, CaseIterable, Codable {
    case all
    case qrPay = "qr_pay"
    case cardPay = "card_pay"
    case load
}

enum TransactionDirection: String, Codable {
    case debit
    case credit
}

// MARK: - Transaction convenience helpers

extension Transaction {
    private static let debitTypeSignals: [String] = [
        "purchase", "payment", "debit", "expense"
    ]

    private static let creditTypeSignals: [String] = [
        "load", "top up", "topup", "credit", "refund", "deposit"
    ]

    private static let qrPayTypeSignals: [String] = [
        "qr", "scan to pay"
    ]

    private static let cardPayTypeSignals: [String] = [
        "purchase", "payment", "debit", "expense", "card"
    ]

    var normalizedTypeValue: String {
        let lowercased = type.lowercased()
            .replacingOccurrences(of: "_", with: " ")
            .replacingOccurrences(of: "-", with: " ")

        return lowercased
            .split(whereSeparator: { $0.isWhitespace })
            .joined(separator: " ")
    }

    var normalizedDirection: TransactionDirection {
        let normalizedType = normalizedTypeValue

        if Self.debitTypeSignals.contains(where: { normalizedType.contains($0) }) {
            return .debit
        }

        if Self.creditTypeSignals.contains(where: { normalizedType.contains($0) }) {
            return .credit
        }

        if amount < 0 {
            return .debit
        }

        return .credit
    }

    var isDebitLike: Bool {
        normalizedDirection == .debit
    }

    var isCreditLike: Bool {
        normalizedDirection == .credit
    }

    var normalizedFilterCategory: TransactionFilter {
        let normalizedType = normalizedTypeValue

        if Self.creditTypeSignals.contains(where: { normalizedType.contains($0) }) {
            return .load
        }

        if Self.qrPayTypeSignals.contains(where: { normalizedType.contains($0) }) {
            return .qrPay
        }

        if Self.cardPayTypeSignals.contains(where: { normalizedType.contains($0) }) {
            return .cardPay
        }

        if isCreditLike {
            return .load
        }

        return .cardPay
    }

    var isNavigable: Bool {
        let normalizedType = normalizedTypeValue
        let isPurchaseFamily = normalizedType.contains("purchase") || normalizedType.contains("payment")
        let hasItems = !(items ?? []).isEmpty

        return isPurchaseFamily || hasItems
    }

    func matchesFilter(_ filter: TransactionFilter) -> Bool {
        switch filter {
        case .all:
            return true
        case .qrPay, .cardPay, .load:
            return normalizedFilterCategory == filter
        }
    }

    func matchesSearchQuery(_ query: String) -> Bool {
        let normalizedQuery = query
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()

        if normalizedQuery.isEmpty {
            return true
        }

        return searchableText.contains(normalizedQuery)
    }

    private var searchableText: String {
        [
            timestamp,
            type,
            description ?? "",
            String(format: "%.2f", abs(amount)),
            String(format: "%.2f", balance),
        ]
        .joined(separator: " ")
        .lowercased()
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
