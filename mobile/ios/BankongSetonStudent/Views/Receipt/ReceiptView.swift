import SwiftUI

// MARK: - ReceiptView
// Stitch-faithful receipt surface for Purchase/NFC transactions.
// Scope guard: no PDF/download/report utility actions belong to S04.

struct ReceiptView: View {
    let transaction: Transaction

    private static let timestampParser: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter
    }()

    private static let dateDisplay: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d, yyyy"
        return formatter
    }()

    private static let timeDisplay: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "h:mm a"
        return formatter
    }()

    private var formattedDate: String {
        guard let date = ReceiptView.timestampParser.date(from: transaction.timestamp) else {
            return transaction.timestamp
        }
        return ReceiptView.dateDisplay.string(from: date)
    }

    private var formattedTime: String {
        guard let date = ReceiptView.timestampParser.date(from: transaction.timestamp) else {
            return "—"
        }
        return ReceiptView.timeDisplay.string(from: date)
    }

    private var lineItems: [TransactionItem] {
        if let items = transaction.items, !items.isEmpty {
            return items
        }

        let label: String = {
            let normalizedType = transaction.type.lowercased()
            if normalizedType.contains("purchase") || normalizedType == "nfc" || normalizedType == "payment" {
                return "Payment"
            }
            if normalizedType.contains("load") || normalizedType.contains("top") || normalizedType == "credit" {
                return "Top Up"
            }
            return transaction.type.isEmpty ? "Transaction" : transaction.type
        }()

        return [TransactionItem(name: label, price: abs(transaction.amount), qty: 1)]
    }

    private var usesSyntheticFallbackItem: Bool {
        transaction.items?.isEmpty ?? true
    }

    private var indexedLineItems: [(index: Int, item: TransactionItem)] {
        Array(lineItems.enumerated()).map { (index: $0.offset, item: $0.element) }
    }

    var body: some View {
        ScrollView {
            VStack(spacing: AppTheme.Spacing.lg) {
                summaryCard
                itemsCard
            }
            .padding(.horizontal, AppTheme.Spacing.lg)
            .padding(.vertical, AppTheme.Spacing.lg)
            .accessibilityIdentifier("receipt-screen-root")
        }
        .background(AppTheme.Palette.background)
        .navigationTitle("Receipt")
        .navigationBarTitleDisplayMode(.inline)
    }

    private var summaryCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Summary")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                receiptSummaryRow(title: "Date", value: formattedDate)
                receiptSummaryRow(title: "Time", value: formattedTime)
                receiptSummaryRow(title: "Type", value: transaction.type.isEmpty ? "—" : transaction.type)
                receiptSummaryRow(title: "Total", value: "₱\(String(format: "%.2f", abs(transaction.amount)))")
                receiptSummaryRow(
                    title: "Balance Before",
                    value: transaction.balanceBefore.map { "₱\(String(format: "%.2f", $0))" } ?? "—"
                )
                receiptSummaryRow(title: "Balance After", value: "₱\(String(format: "%.2f", transaction.balance))")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("receipt-summary-card")
        .accessibilityLabel("Receipt summary")
        .accessibilityHint("Shows receipt date, type, amount, and balance changes")
    }

    private var itemsCard: some View {
        StitchCard {
            VStack(alignment: .leading, spacing: AppTheme.Spacing.sm) {
                Text("Items")
                    .font(AppTheme.Typography.headline)
                    .foregroundStyle(AppTheme.Palette.textPrimary)

                if usesSyntheticFallbackItem {
                    Text("Item details were unavailable, so this receipt shows a synthesized line item from the transaction total.")
                        .font(AppTheme.Typography.caption)
                        .foregroundStyle(AppTheme.Palette.textSecondary)
                        .multilineTextAlignment(.leading)
                        .accessibilityIdentifier("receipt-fallback-item-marker")
                }

                Divider()

                ForEach(indexedLineItems, id: \.index) { line in
                    HStack(spacing: AppTheme.Spacing.sm) {
                        VStack(alignment: .leading, spacing: AppTheme.Spacing.xxs) {
                            Text(line.item.name)
                                .font(AppTheme.Typography.bodyStrong)
                                .foregroundStyle(AppTheme.Palette.textPrimary)

                            Text("Qty \(line.item.qty)")
                                .font(AppTheme.Typography.caption)
                                .foregroundStyle(AppTheme.Palette.textSecondary)
                        }

                        Spacer()

                        Text("₱\(String(format: "%.2f", line.item.price * Double(line.item.qty)))")
                            .font(AppTheme.Typography.bodyStrong)
                            .foregroundStyle(AppTheme.Palette.textPrimary)
                    }
                    .padding(.vertical, AppTheme.Spacing.xxs)
                    .accessibilityIdentifier("receipt-line-item-row-\(line.index)")
                    .accessibilityLabel(
                        "\(line.item.name), quantity \(line.item.qty), line total \(String(format: "%.2f", line.item.price * Double(line.item.qty))) pesos"
                    )
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .accessibilityIdentifier("receipt-items-card")
        .accessibilityHint("Lists purchased items with stable row identity markers")
    }

    private func receiptSummaryRow(title: String, value: String) -> some View {
        HStack(spacing: AppTheme.Spacing.sm) {
            Text(title)
                .font(AppTheme.Typography.caption)
                .foregroundStyle(AppTheme.Palette.textSecondary)

            Spacer()

            Text(value)
                .font(AppTheme.Typography.body)
                .foregroundStyle(AppTheme.Palette.textPrimary)
                .multilineTextAlignment(.trailing)
        }
    }
}
