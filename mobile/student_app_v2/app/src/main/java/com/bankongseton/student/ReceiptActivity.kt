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
        findViewById<TextView>(R.id.receiptTotal).text = "฿%.2f".format(transaction.amount)
        findViewById<TextView>(R.id.receiptBalanceBefore).text = "฿%.2f".format(transaction.balanceBefore)
        findViewById<TextView>(R.id.receiptBalanceAfter).text = "฿%.2f".format(transaction.balance)

        // Line items
        val itemsContainer = findViewById<LinearLayout>(R.id.receiptItemsContainer)
        transaction.items?.forEach { item ->
            val row = layoutInflater.inflate(R.layout.item_receipt_line, itemsContainer, false)
            row.findViewById<TextView>(R.id.lineItemName).text = item.name
            row.findViewById<TextView>(R.id.lineItemUnitPrice).text = "฿%.2f".format(item.price)
            row.findViewById<TextView>(R.id.lineItemQty).text = "x${item.qty}"
            row.findViewById<TextView>(R.id.lineItemTotal).text = "฿%.2f".format(item.price * item.qty)
            itemsContainer.addView(row)
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
