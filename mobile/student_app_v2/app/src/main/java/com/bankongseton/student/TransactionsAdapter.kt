package com.bankongseton.student

import android.content.Intent
import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.google.gson.Gson

class TransactionsAdapter : RecyclerView.Adapter<TransactionsAdapter.TransactionViewHolder>() {

    private val transactions = mutableListOf<Transaction>()

    fun setTransactions(newTransactions: List<Transaction>) {
        transactions.clear()
        transactions.addAll(newTransactions)
        notifyDataSetChanged()
    }

    fun appendTransactions(newTransactions: List<Transaction>) {
        val start = transactions.size
        transactions.addAll(newTransactions)
        notifyItemRangeInserted(start, newTransactions.size)
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
        private val typeText: TextView = itemView.findViewById(R.id.typeText)
        private val timestampText: TextView = itemView.findViewById(R.id.timestampText)
        private val amountText: TextView = itemView.findViewById(R.id.amountText)
        private val balanceText: TextView = itemView.findViewById(R.id.balanceText)
        private val typeIcon: ImageView = itemView.findViewById(R.id.expandIcon)

        fun bind(transaction: Transaction) {
            typeText.text = transaction.type
            timestampText.text = transaction.timestamp
            amountText.text = "฿%.2f".format(transaction.amount)
            balanceText.text = "Balance: ฿%.2f".format(transaction.balance)

            val isPurchase = transaction.type.equals("Purchase", ignoreCase = true)
                    || transaction.type.equals("NFC Purchase", ignoreCase = true)
            val isTopUp = transaction.type.equals("Top-Up", ignoreCase = true)
                    || transaction.type.equals("TopUp", ignoreCase = true)

            // Color-code amount
            amountText.setTextColor(
                when {
                    isPurchase -> Color.parseColor("#F44336")  // red
                    isTopUp    -> Color.parseColor("#4CAF50")  // green
                    else       -> itemView.context.getColor(android.R.color.tab_indicator_text)
                }
            )

            // Type icon: show for all rows
            typeIcon.visibility = View.VISIBLE
            if (isPurchase) {
                typeIcon.setImageResource(android.R.drawable.arrow_down_float)
            } else {
                typeIcon.setImageResource(android.R.drawable.arrow_up_float)
            }

            // Navigation: Purchase → ReceiptActivity; others → no action
            if (isPurchase) {
                itemView.setOnClickListener {
                    val intent = Intent(itemView.context, ReceiptActivity::class.java)
                    intent.putExtra("transaction_json", Gson().toJson(transaction))
                    itemView.context.startActivity(intent)
                }
            } else {
                itemView.setOnClickListener(null)
                itemView.isClickable = false
            }
        }
    }
}
