package com.bankongseton.student

import android.os.Bundle
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
        
        loadTransactions()
    }
    
    private fun loadTransactions() {
        val token = secureStorage.getAuthToken() ?: return
        
        ApiClient.apiService.getTransactions("Bearer $token", 50)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    if (response.isSuccessful) {
                        response.body()?.let {
                            adapter.setTransactions(it.transactions)
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
