package com.bankongseton.student

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

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
        private val typeText: TextView = itemView.findViewById(R.id.typeText)
        private val timestampText: TextView = itemView.findViewById(R.id.timestampText)
        private val amountText: TextView = itemView.findViewById(R.id.amountText)
        private val balanceText: TextView = itemView.findViewById(R.id.balanceText)
        private val itemsContainer: LinearLayout = itemView.findViewById(R.id.itemsContainer)
        private val itemsText: TextView = itemView.findViewById(R.id.itemsText)
        private val expandIcon: ImageView = itemView.findViewById(R.id.expandIcon)
        
        private var isExpanded = false
        
        fun bind(transaction: Transaction) {
            typeText.text = transaction.type
            timestampText.text = transaction.timestamp
            amountText.text = "₱%.2f".format(transaction.amount)
            balanceText.text = "Balance: ₱%.2f".format(transaction.balance)
            
            // Check if transaction has items
            val hasItems = transaction.items != null && transaction.items.isNotEmpty()
            
            if (hasItems) {
                expandIcon.visibility = View.VISIBLE
                
                // Build items string
                val itemsStr = transaction.items!!.joinToString("\n") {
                    "• ${it.name} (x${it.qty}) - ₱%.2f".format(it.price * it.qty)
                }
                itemsText.text = itemsStr
                
                // Toggle expansion on click
                itemView.setOnClickListener {
                    isExpanded = !isExpanded
                    itemsContainer.visibility = if (isExpanded) View.VISIBLE else View.GONE
                    expandIcon.rotation = if (isExpanded) 180f else 0f
                }
            } else {
                expandIcon.visibility = View.GONE
                itemsContainer.visibility = View.GONE
                itemView.setOnClickListener(null)
            }
        }
    }
}
