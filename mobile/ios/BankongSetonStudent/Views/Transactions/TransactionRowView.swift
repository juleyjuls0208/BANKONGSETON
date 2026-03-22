import SwiftUI

// MARK: - TransactionRowView
// Color-coded row for a single transaction.
// Debit rows are red, credit rows are green.

struct TransactionRowView: View {
    let transaction: Transaction

    private var isDebit: Bool {
        transaction.isDebitLike
    }

    private var amountColor: Color {
        isDebit ? AppTheme.Palette.danger : AppTheme.Palette.success
    }

    // Always show positive amount — sign is conveyed by color + icon.
    private var displayAmount: String {
        "₱\(String(format: "%.2f", abs(transaction.amount)))"
    }

    private var displayLabel: String {
        let normalizedType = transaction.normalizedTypeValue

        switch normalizedType {
        case "purchase":
            return "Canteen Purchase"
        case "payment":
            return "Payment"
        case "load", "top up", "topup", "credit":
            return "Top Up"
        default:
            return transaction.type.prefix(1).uppercased() + transaction.type.dropFirst()
        }
    }

    private var signedAmountText: String {
        isDebit ? "−\(displayAmount)" : "+\(displayAmount)"
    }

    private var accessibilityAmountText: String {
        isDebit ? "Debit \(displayAmount)" : "Credit \(displayAmount)"
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
                    Text(signedAmountText)
                        .font(AppTheme.Typography.bodyStrong)
                        .foregroundStyle(amountColor)

                    Text("Balance \(String(format: "₱%.2f", transaction.balance))")
                        .font(AppTheme.Typography.caption)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                }
            }
            .accessibilityElement(children: .combine)
            .accessibilityLabel("\(displayLabel). \(accessibilityAmountText). Balance \(String(format: "₱%.2f", transaction.balance)).")
            .accessibilityHint(transaction.isNavigable ? "Opens the transaction receipt" : "Transaction is not navigable")
        }
    }
}
