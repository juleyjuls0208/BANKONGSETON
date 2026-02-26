package com.bankongseton.student

import android.os.Bundle
import android.view.View
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class TransactionsActivity : AppCompatActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: TransactionsAdapter
    private lateinit var secureStorage: SecureStorage

    private var currentOffset = 0
    private var isLoading = false
    private var hasMore = true
    private val pageSize = 20

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_transactions)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Transaction History"

        secureStorage = SecureStorage(this)

        recyclerView = findViewById(R.id.recyclerView)
        recyclerView.layoutManager = LinearLayoutManager(this)

        adapter = TransactionsAdapter()
        recyclerView.adapter = adapter

        recyclerView.addOnScrollListener(object : RecyclerView.OnScrollListener() {
            override fun onScrolled(recyclerView: RecyclerView, dx: Int, dy: Int) {
                super.onScrolled(recyclerView, dx, dy)
                val layoutManager = recyclerView.layoutManager as LinearLayoutManager
                val totalItemCount = layoutManager.itemCount
                val lastVisibleItem = layoutManager.findLastVisibleItemPosition()
                if (!isLoading && hasMore && lastVisibleItem >= totalItemCount - 4) {
                    loadTransactions(currentOffset)
                }
            }
        })

        loadTransactions()
    }

    private fun loadTransactions(offset: Int = 0) {
        if (isLoading || !hasMore) return
        val token = secureStorage.getAuthToken() ?: return
        isLoading = true

        ApiClient.apiService.getTransactions("Bearer $token", pageSize, offset)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    isLoading = false
                    if (response.isSuccessful) {
                        response.body()?.let { body ->
                            if (offset == 0) {
                                adapter.setTransactions(body.transactions)
                                // Empty state: show friendly message if list is empty
                                if (body.transactions.isEmpty()) {
                                    findViewById<TextView>(R.id.emptyStateText)?.let {
                                        it.text = "No transactions yet"
                                        it.visibility = View.VISIBLE
                                    }
                                    recyclerView.visibility = View.GONE
                                } else {
                                    findViewById<TextView>(R.id.emptyStateText)?.visibility =
                                        View.GONE
                                    recyclerView.visibility = View.VISIBLE
                                }
                            } else {
                                adapter.appendTransactions(body.transactions)
                            }
                            hasMore = body.hasMore ?: false
                            currentOffset = offset + body.transactions.size
                        }
                    } else {
                        Toast.makeText(
                            this@TransactionsActivity,
                            "Failed to load transactions",
                            Toast.LENGTH_SHORT
                        ).show()
                    }
                }

                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    isLoading = false
                    Toast.makeText(
                        this@TransactionsActivity,
                        "Network error: ${t.message}",
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
