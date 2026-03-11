package com.bankongseton.student

import android.animation.ObjectAnimator
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.card.MaterialCardView
import java.text.SimpleDateFormat
import java.util.Locale

class TransactionsAdapter : RecyclerView.Adapter<TransactionsAdapter.TransactionViewHolder>() {

    private var transactions = listOf<Transaction>()

    fun setTransactions(transactions: List<Transaction>) {
        this.transactions = transactions
        notifyDataSetChanged()
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): TransactionViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_transaction, parent, false)
        return TransactionViewHolder(view)
    }

    override fun onBindViewHolder(holder: TransactionViewHolder, position: Int) {
        holder.bind(transactions[position])
    }

    override fun getItemCount() = transactions.size

    class TransactionViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val iconChip: MaterialCardView = itemView.findViewById(R.id.iconChip)
        private val expandIcon: ImageView = itemView.findViewById(R.id.expandIcon)
        private val typeText: TextView = itemView.findViewById(R.id.typeText)
        private val timestampText: TextView = itemView.findViewById(R.id.timestampText)
        private val amountText: TextView = itemView.findViewById(R.id.amountText)
        private val balanceText: TextView = itemView.findViewById(R.id.balanceText)
        private val itemsContainer: LinearLayout = itemView.findViewById(R.id.itemsContainer)
        private val itemsText: TextView = itemView.findViewById(R.id.itemsText)
        private val chevronIcon: ImageView = itemView.findViewById(R.id.chevronIcon)

        private var isExpanded = false

        fun bind(transaction: Transaction) {
            val ctx = itemView.context
            val isDebit = transaction.type.lowercase() in
                    listOf("purchase", "debit", "payment", "nfc")

            // Type label
            typeText.text = formatType(transaction.type)

            // Timestamp
            timestampText.text = formatTimestamp(transaction.timestamp)

            // Balance after
            balanceText.text = "Balance ₱%.2f".format(transaction.balance)

            // Amount — color-coded
            amountText.text = if (isDebit) "−₱%.2f".format(transaction.amount)
                              else "+₱%.2f".format(transaction.amount)
            amountText.setTextColor(
                if (isDebit) ctx.getColor(R.color.md_theme_light_error)
                else ctx.getColor(R.color.positive_green)
            )

            // Icon chip background color
            val chipBg = if (isDebit)
                ctx.getColorStateList(R.color.md_theme_light_errorContainer)
            else
                ctx.getColorStateList(R.color.positive_green_container)
            iconChip.setCardBackgroundColor(chipBg)

            val iconTint = if (isDebit)
                ctx.getColor(R.color.md_theme_light_onErrorContainer)
            else
                ctx.getColor(R.color.positive_green)
            expandIcon.setColorFilter(iconTint)

            // Expandable receipt items
            val hasItems = !transaction.items.isNullOrEmpty()
            chevronIcon.isVisible = hasItems
            itemsContainer.isVisible = false
            isExpanded = false
            chevronIcon.rotation = 0f

            if (hasItems) {
                val itemsStr = transaction.items!!.joinToString("\n") {
                    "• ${it.name} ×${it.qty}  ₱%.2f".format(it.price * it.qty)
                }
                itemsText.text = itemsStr

                itemView.setOnClickListener {
                    isExpanded = !isExpanded
                    itemsContainer.isVisible = isExpanded
                    ObjectAnimator.ofFloat(
                        chevronIcon, "rotation",
                        if (isExpanded) 0f else 180f,
                        if (isExpanded) 180f else 0f
                    ).setDuration(200).start()
                }
            } else {
                itemsContainer.isVisible = false
                itemView.setOnClickListener(null)
            }
        }

        private fun formatType(type: String): String = when (type.lowercase()) {
            "purchase" -> "Canteen Purchase"
            "top_up", "topup", "credit" -> "Top Up"
            "nfc" -> "NFC Payment"
            "refund" -> "Refund"
            else -> type.replaceFirstChar { it.uppercaseChar() }
        }

        private fun formatTimestamp(raw: String): String {
            return try {
                val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
                val date = sdf.parse(raw) ?: return raw
                SimpleDateFormat("MMM d, h:mm a", Locale.US).format(date)
            } catch (_: Exception) { raw }
        }
    }
}
