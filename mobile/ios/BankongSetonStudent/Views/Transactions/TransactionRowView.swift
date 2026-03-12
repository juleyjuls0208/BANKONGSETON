import SwiftUI

// MARK: - TransactionRowView
// Color-coded row for a single transaction.
// Red for Purchase/NFC Purchase, green for Top-Up.

struct TransactionRowView: View {
    let transaction: Transaction

    var amountColor: Color {
        switch transaction.type.lowercased() {
        case "purchase", "nfc purchase": return Color(hex: "#F44336")  // red
        case "top-up", "topup":          return Color(hex: "#4CAF50")  // green
        default:                          return .primary
        }
    }

    var isPurchase: Bool {
        ["purchase", "nfc purchase"].contains(transaction.type.lowercased())
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: isPurchase ? "arrow.down.circle.fill" : "arrow.up.circle.fill")
                .foregroundColor(amountColor)
                .font(.title2)

            VStack(alignment: .leading, spacing: 2) {
                Text(transaction.type)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text(transaction.timestamp)
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()

            VStack(alignment: .trailing, spacing: 2) {
                Text("₱\(String(format: "%.2f", transaction.amount))")
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

// MARK: - Color(hex:) extension

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red:   Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}
