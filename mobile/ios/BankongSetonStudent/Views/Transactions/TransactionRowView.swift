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
        isDebit ? AppTheme.Palette.danger : AppTheme.Palette.success
    }

    // Always show positive amount — sign is conveyed by color + icon.
    private var displayAmount: String {
        "₱\(String(format: "%.2f", abs(transaction.amount)))"
    }

    private var displayLabel: String {
        let t = transaction.type.lowercased()
        switch t {
        case "purchase":
            return "Canteen Purchase"
        case "nfc purchase":
            return "NFC Purchase"
        case "nfc":
            return "NFC Payment"
        case "load", "top-up", "topup", "credit":
            return "Top Up"
        default:
            return transaction.type.prefix(1).uppercased() + transaction.type.dropFirst()
        }
    }

    var body: some View {
        StitchCard(padding: AppTheme.Spacing.md) {
            HStack(spacing: AppTheme.Spacing.md) {
                ZStack {
                    Circle()
                        .fill(amountColor.opacity(0.14))

                    Image(systemName: isDebit ? "arrow.down.circle.fill" : "arrow.up.circle.fill")
                        .font(AppTheme.Typography.headline)
                        .foregroundStyle(amountColor)
                }
                .frame(width: 40, height: 40)

                VStack(alignment: .leading, spacing: AppTheme.Spacing.xxs) {
                    Text(displayLabel)
                        .font(AppTheme.Typography.bodyStrong)
                        .foregroundStyle(AppTheme.Palette.textPrimary)

                    Text(transaction.timestamp)
                        .font(AppTheme.Typography.caption)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                }

                Spacer(minLength: AppTheme.Spacing.sm)

                VStack(alignment: .trailing, spacing: AppTheme.Spacing.xxs) {
                    Text(isDebit ? "−\(displayAmount)" : "+\(displayAmount)")
                        .font(AppTheme.Typography.bodyStrong)
                        .foregroundStyle(amountColor)

                    Text("Balance \(String(format: "₱%.2f", transaction.balance))")
                        .font(AppTheme.Typography.caption)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                }
            }
        }
    }
}
