package com.bankongseton.student

import android.os.Bundle
import android.widget.LinearLayout
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.appbar.MaterialToolbar
import com.google.android.material.progressindicator.LinearProgressIndicator
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class TransactionsActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: TransactionsAdapter
    private lateinit var secureStorage: SecureStorage
    private lateinit var emptyStateLayout: LinearLayout
    private lateinit var loadingIndicator: LinearProgressIndicator
    private lateinit var toolbar: MaterialToolbar

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

        recyclerView.layoutManager = LinearLayoutManager(this)
        adapter = TransactionsAdapter()
        recyclerView.adapter = adapter

        loadTransactions()
    }

    private fun loadTransactions() {
        val token = secureStorage.getAuthToken() ?: return

        loadingIndicator.isVisible = true
        emptyStateLayout.isVisible = false

        ApiClient.apiService.getTransactions("Bearer $token", 100)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    loadingIndicator.isVisible = false
                    if (response.isSuccessful) {
                        val transactions = response.body()?.transactions ?: emptyList()
                        adapter.setTransactions(transactions)
                        emptyStateLayout.isVisible = transactions.isEmpty()
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
