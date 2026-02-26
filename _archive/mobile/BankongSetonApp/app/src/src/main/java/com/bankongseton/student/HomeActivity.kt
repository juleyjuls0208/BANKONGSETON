package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.card.MaterialCardView
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class HomeActivity : AppCompatActivity() {
    
    private lateinit var balanceText: TextView
    private lateinit var balanceCard: MaterialCardView
    private lateinit var transactionsButton: Button
    private lateinit var settingsButton: Button
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar
    private lateinit var secureStorage: SecureStorage
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_home)
        
        secureStorage = SecureStorage(this)
        
        balanceText = findViewById(R.id.balanceText)
        balanceCard = findViewById(R.id.balanceCard)
        transactionsButton = findViewById(R.id.transactionsButton)
        settingsButton = findViewById(R.id.settingsButton)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        progressBar = findViewById(R.id.progressBar)
        
        transactionsButton.setOnClickListener {
            startActivity(Intent(this, TransactionsActivity::class.java))
        }
        
        settingsButton.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
        
        swipeRefresh.setOnRefreshListener {
            loadBalance()
        }
        
        loadBalance()
    }
    
    private fun loadBalance() {
        val token = secureStorage.getAuthToken() ?: return
        
        progressBar.isVisible = true
        
        ApiClient.apiService.getBalance("Bearer $token").enqueue(object : Callback<Balance> {
            override fun onResponse(call: Call<Balance>, response: Response<Balance>) {
                progressBar.isVisible = false
                swipeRefresh.isRefreshing = false
                
                if (response.isSuccessful) {
                    response.body()?.let { balance ->
                        balanceText.text = "₱%.2f".format(balance.balance)
                    }
                } else {
                    Toast.makeText(
                        this@HomeActivity,
                        "Failed to load balance",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            }
            
            override fun onFailure(call: Call<Balance>, t: Throwable) {
                progressBar.isVisible = false
                swipeRefresh.isRefreshing = false
                Toast.makeText(
                    this@HomeActivity,
                    "Network error: ${t.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        })
    }
}
