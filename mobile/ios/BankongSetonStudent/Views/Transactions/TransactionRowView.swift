import SwiftUI

// MARK: - TransactionRowView
// Color-coded row for a single transaction.
// Debit types (purchases, nfc, payment) are red; credits (top-up, load) are green.

struct TransactionRowView: View {
    let transaction: Transaction

    // A "debit" if the type sounds like money leaving, OR amount is negative.
    private var isDebit: Bool {
        let t = transaction.type.lowercased()
        let debitType = t.contains("purchase") || t == "nfc" || t == "payment" || t == "debit"
        return debitType || transaction.amount < 0
    }

    private var amountColor: Color {
        isDebit ? Color(hex: "#F44336") : Color(hex: "#4CAF50")
    }

    // Always show positive amount — sign is conveyed by color + icon.
    private var displayAmount: String {
        "₱\(String(format: "%.2f", abs(transaction.amount)))"
    }

    private var displayLabel: String {
        let t = transaction.type.lowercased()
        switch t {
        case "purchase":     return "Canteen Purchase"
        case "nfc purchase": return "NFC Purchase"
        case "nfc":          return "NFC Payment"
        case "load", "top-up", "topup", "credit": return "Top Up"
        default:             return transaction.type.prefix(1).uppercased() + transaction.type.dropFirst()
        }
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: isDebit ? "arrow.down.circle.fill" : "arrow.up.circle.fill")
                .foregroundColor(amountColor)
                .font(.title2)

            VStack(alignment: .leading, spacing: 2) {
                Text(displayLabel)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(transaction.timestamp)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 2) {
                Text(isDebit ? "−\(displayAmount)" : "+\(displayAmount)")
                    .foregroundColor(amountColor)
                    .fontWeight(.semibold)
                Text("₱\(String(format: "%.2f", transaction.balance))")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .padding(.vertical, 4)
    }
}

