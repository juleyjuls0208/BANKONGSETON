package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.ImageButton
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.card.MaterialCardView
import com.google.android.material.snackbar.Snackbar
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class HomeActivity : AppCompatActivity() {

    private lateinit var balanceText: TextView
    private lateinit var balanceCard: MaterialCardView
    private lateinit var transactionsButton: android.widget.Button
    private lateinit var settingsButton: android.widget.Button
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar
    private lateinit var balanceProgressBar: ProgressBar
    private lateinit var refreshButton: ImageButton
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
        balanceProgressBar = findViewById(R.id.balanceProgressBar)
        refreshButton = findViewById(R.id.refreshButton)

        transactionsButton.setOnClickListener {
            startActivity(Intent(this, TransactionsActivity::class.java))
        }

        settingsButton.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }

        swipeRefresh.setOnRefreshListener {
            loadBalance()
        }

        refreshButton.setOnClickListener { loadBalance() }

        loadBalance()
    }

    fun loadBalance() {
        val token = secureStorage.getAuthToken() ?: return

        balanceProgressBar.visibility = View.VISIBLE
        balanceText.visibility = View.INVISIBLE  // hide while loading

        ApiClient.apiService.getBalance("Bearer $token").enqueue(object : Callback<Balance> {
            override fun onResponse(call: Call<Balance>, response: Response<Balance>) {
                balanceProgressBar.visibility = View.GONE
                balanceText.visibility = View.VISIBLE
                progressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false

                if (response.isSuccessful) {
                    response.body()?.let { balance ->
                        balanceText.text = "฿%.2f".format(balance.balance)
                        secureStorage.saveLastBalance(balance.balance)
                    }
                } else {
                    val lastBalance = secureStorage.getLastBalance()
                    if (lastBalance != null) {
                        balanceText.text = "฿%.2f".format(lastBalance)
                    }
                    Snackbar.make(
                        findViewById(android.R.id.content),
                        "Couldn't update balance — check your connection",
                        Snackbar.LENGTH_LONG
                    ).show()
                }
            }

            override fun onFailure(call: Call<Balance>, t: Throwable) {
                balanceProgressBar.visibility = View.GONE
                balanceText.visibility = View.VISIBLE
                progressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false

                val lastBalance = secureStorage.getLastBalance()
                if (lastBalance != null) {
                    balanceText.text = "฿%.2f".format(lastBalance)
                }
                Snackbar.make(
                    findViewById(android.R.id.content),
                    "Couldn't update balance — check your connection",
                    Snackbar.LENGTH_LONG
                ).show()
            }
        })
    }
}
