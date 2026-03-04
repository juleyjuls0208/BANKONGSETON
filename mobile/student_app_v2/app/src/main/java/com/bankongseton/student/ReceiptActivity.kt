package com.bankongseton.student

import android.os.Bundle
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.google.gson.Gson
import java.text.SimpleDateFormat
import java.util.Locale

class ReceiptActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_receipt)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Receipt"

        val json = intent.getStringExtra("transaction_json") ?: run { finish(); return }
        val transaction = Gson().fromJson(json, Transaction::class.java)

        // Summary fields
        findViewById<TextView>(R.id.receiptDate).text = formatDate(transaction.timestamp)
        findViewById<TextView>(R.id.receiptTime).text = formatTime(transaction.timestamp)
        // Transaction type label (e.g. "NFC Purchase" or "Purchase")
        val typeLabel = TextView(this)
        typeLabel.text = transaction.type
        typeLabel.textSize = 14f
        typeLabel.setTextColor(android.graphics.Color.GRAY)
        typeLabel.setPadding(0, 0, 0, 8)
        // Insert type label below the time row inside the parent LinearLayout
        val receiptTimeView = findViewById<TextView>(R.id.receiptTime)
        val parentLayout = receiptTimeView.parent.parent as LinearLayout
        val timeRowIndex = parentLayout.indexOfChild(receiptTimeView.parent as android.view.View)
        parentLayout.addView(typeLabel, timeRowIndex + 1)

        findViewById<TextView>(R.id.receiptTotal).text = "฿%.2f".format(transaction.amount)
        findViewById<TextView>(R.id.receiptBalanceBefore).text = "฿%.2f".format(transaction.balanceBefore)
        findViewById<TextView>(R.id.receiptBalanceAfter).text = "฿%.2f".format(transaction.balance)

        // Line items — use null-items fallback for NFC Purchase (or any transaction with no line items)
        val itemsContainer = findViewById<LinearLayout>(R.id.receiptItemsContainer)
        val items = transaction.items
        if (items.isNullOrEmpty()) {
            // Synthetic row for transactions with no line items (e.g. NFC Payment)
            val syntheticItem = TransactionItem(
                name = "NFC Payment",
                price = transaction.amount,
                qty = 1
            )
            val row = layoutInflater.inflate(R.layout.item_receipt_line, itemsContainer, false)
            row.findViewById<TextView>(R.id.lineItemName).text = syntheticItem.name
            row.findViewById<TextView>(R.id.lineItemUnitPrice).text = "฿%.2f".format(syntheticItem.price)
            row.findViewById<TextView>(R.id.lineItemQty).text = "x${syntheticItem.qty}"
            row.findViewById<TextView>(R.id.lineItemTotal).text = "฿%.2f".format(syntheticItem.price * syntheticItem.qty)
            itemsContainer.addView(row)
        } else {
            items.forEach { item ->
                val row = layoutInflater.inflate(R.layout.item_receipt_line, itemsContainer, false)
                row.findViewById<TextView>(R.id.lineItemName).text = item.name
                row.findViewById<TextView>(R.id.lineItemUnitPrice).text = "฿%.2f".format(item.price)
                row.findViewById<TextView>(R.id.lineItemQty).text = "x${item.qty}"
                row.findViewById<TextView>(R.id.lineItemTotal).text = "฿%.2f".format(item.price * item.qty)
                itemsContainer.addView(row)
            }
        }
    }

    private fun formatDate(timestamp: String): String {
        return try {
            val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            val date = sdf.parse(timestamp) ?: return "Invalid date"
            SimpleDateFormat("MMM d, yyyy", Locale.getDefault()).format(date)
        } catch (e: Exception) {
            "Invalid date"
        }
    }

    private fun formatTime(timestamp: String): String {
        return try {
            val sdf = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
            val date = sdf.parse(timestamp) ?: return "Invalid date"
            SimpleDateFormat("h:mm a", Locale.getDefault()).format(date)
        } catch (e: Exception) {
            "Invalid date"
        }
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
