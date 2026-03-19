package com.bankongseton.student

import android.os.Bundle
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.LinearLayout
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.chip.Chip
import com.google.android.material.chip.ChipGroup
import com.google.android.material.progressindicator.LinearProgressIndicator
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

class TransactionsActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: TransactionsAdapter
    private lateinit var secureStorage: SecureStorage
    private lateinit var emptyStateLayout: LinearLayout
    private lateinit var loadingIndicator: LinearProgressIndicator
    private lateinit var toolbar: MaterialToolbar
    private lateinit var chipGroupFilter: ChipGroup

    private var allTransactions: List<Transaction> = emptyList()

    // Filter state
    private var activeTypeFilter: String = "All" // "All", "Purchase", "Load"
    private var activePeriodFilter: String = "All" // "All", "This Month", "Last Month"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_transactions)

        secureStorage = SecureStorage(this)

        toolbar = findViewById(R.id.toolbar)
        setSupportActionBar(toolbar)
        toolbar.setNavigationOnClickListener { finish() }

        recyclerView = findViewById(R.id.recyclerView)
        emptyStateLayout = findViewById(R.id.emptyStateLayout)
        loadingIndicator = findViewById(R.id.loadingIndicator)

        chipGroupFilter = findViewById(R.id.chipGroupFilter)

        recyclerView.layoutManager = LinearLayoutManager(this)
        adapter = TransactionsAdapter()
        recyclerView.adapter = adapter

        setupFilterChips()
        loadTransactions()
    }

    private fun setupFilterChips() {
        // Type chips
        val typeLabels = listOf("All", "Purchases", "Loads")
        typeLabels.forEach { label ->
            val chip = Chip(this).apply {
                text = label
                isCheckable = true
                isChecked = label == "All"
            }
            chip.setOnCheckedChangeListener { _, isChecked ->
                if (isChecked) {
                    activeTypeFilter = when (label) {
                        "Purchases" -> "Purchase"
                        "Loads" -> "Load"
                        else -> "All"
                    }
                    applyFilters()
                }
            }
            chipGroupFilter.addView(chip)
        }

        // Period chips
        val periodLabels = listOf("This Month", "Last Month")
        periodLabels.forEach { label ->
            val chip = Chip(this).apply {
                text = label
                isCheckable = true
                isChecked = false
            }
            chip.setOnCheckedChangeListener { _, isChecked ->
                if (isChecked) {
                    activePeriodFilter = label
                    // Uncheck other period chips
                    for (i in 0 until chipGroupFilter.childCount) {
                        val c = chipGroupFilter.getChildAt(i) as? Chip ?: continue
                        if (c.text in listOf("This Month", "Last Month") && c !== chip) {
                            c.isChecked = false
                        }
                    }
                } else {
                    activePeriodFilter = "All"
                }
                applyFilters()
            }
            chipGroupFilter.addView(chip)
        }
    }

    private fun applyFilters() {
        val cal = Calendar.getInstance()
        val sdf = SimpleDateFormat("yyyy-MM", Locale.US)

        val thisMonth = sdf.format(cal.time)
        cal.add(Calendar.MONTH, -1)
        val lastMonth = sdf.format(cal.time)

        val filtered = allTransactions.filter { txn ->
            val typeMatch = when (activeTypeFilter) {
                "Purchase" -> txn.type.lowercase() in listOf("purchase", "debit", "payment", "nfc")
                "Load" -> txn.type.lowercase() in listOf("load", "top_up", "topup", "credit")
                else -> true
            }

            val periodMatch = when (activePeriodFilter) {
                "This Month" -> txn.timestamp.startsWith(thisMonth)
                "Last Month" -> txn.timestamp.startsWith(lastMonth)
                else -> true
            }

            typeMatch && periodMatch
        }

        adapter.setTransactions(filtered)
        emptyStateLayout.isVisible = filtered.isEmpty()
    }

    private fun loadTransactions() {
        val token = secureStorage.getAuthToken() ?: return

        loadingIndicator.isVisible = true
        emptyStateLayout.isVisible = false

        ApiClient.apiService.getTransactions("Bearer $token", 200)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    loadingIndicator.isVisible = false
                    if (response.isSuccessful) {
                        allTransactions = response.body()?.transactions ?: emptyList()
                        applyFilters()
                    } else {
                        emptyStateLayout.isVisible = true
                        Toast.makeText(
                            this@TransactionsActivity,
                            "Failed to load transactions",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }

                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    loadingIndicator.isVisible = false
                    emptyStateLayout.isVisible = true
                    Toast.makeText(
                        this@TransactionsActivity,
                        "Network error — check your connection",
                        Toast.LENGTH_LONG
                    ).show()
                }
            })
    }

    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
