package com.juls.bankongsetonandroid

import android.graphics.Color
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import java.text.SimpleDateFormat
import java.util.*

class TransactionAdapter(
    private val transactions: List<Transaction>
) : RecyclerView.Adapter<TransactionAdapter.ViewHolder>() {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_transaction, parent, false)
        return ViewHolder(view)
    }
    
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val transaction = transactions[position]
        holder.bind(transaction)
    }
    
    override fun getItemCount(): Int = transactions.size
    
    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val timestampText: TextView = itemView.findViewById(R.id.transaction_timestamp)
        private val typeText: TextView = itemView.findViewById(R.id.transaction_type)
        private val amountText: TextView = itemView.findViewById(R.id.transaction_amount)
        private val iconText: TextView = itemView.findViewById(R.id.transaction_icon)
        
        fun bind(transaction: Transaction) {
            // Format timestamp for better readability
            timestampText.text = formatTimestamp(transaction.timestamp)
            typeText.text = transaction.type
            
            // Set icon based on transaction type
            when (transaction.type.lowercase()) {
                "load" -> {
                    iconText.text = "💰"
                    amountText.setTextColor(Color.parseColor("#4CAF50"))
                    amountText.text = "+${String.format("₱%.0f", transaction.amount)}"
                }
                "purchase" -> {
                    iconText.text = "🏢"
                    amountText.setTextColor(Color.parseColor("#FFFFFF"))
                    amountText.text = String.format("₱%.0f", transaction.amount)
                }
                else -> {
                    iconText.text = "💳"
                    amountText.setTextColor(Color.parseColor("#FFFFFF"))
                    amountText.text = String.format("₱%.0f", transaction.amount)
                }
            }
        }
        
        private fun formatTimestamp(timestamp: String): String {
            return try {
                // Try to parse and format the timestamp to MM/dd/yy
                val inputFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                val outputFormat = SimpleDateFormat("MM/dd/yy", Locale.getDefault())
                val date = inputFormat.parse(timestamp)
                date?.let { outputFormat.format(it) } ?: timestamp
            } catch (e: Exception) {
                // If parsing fails, return original timestamp
                timestamp
            }
        }
    }
}
