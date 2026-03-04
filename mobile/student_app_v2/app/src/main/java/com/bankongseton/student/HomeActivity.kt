package com.bankongseton.student

import android.app.AlertDialog
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.EditText
import android.widget.ImageButton
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.button.MaterialButton
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
    private lateinit var activateNfcPayButton: MaterialButton
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: ProgressBar
    private lateinit var balanceProgressBar: ProgressBar
    private lateinit var refreshButton: ImageButton
    private lateinit var secureStorage: SecureStorage

    companion object {
        const val REQUEST_NFC_PAY = 1001
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_home)

        secureStorage = SecureStorage(this)

        balanceText = findViewById(R.id.balanceText)
        balanceCard = findViewById(R.id.balanceCard)
        transactionsButton = findViewById(R.id.transactionsButton)
        settingsButton = findViewById(R.id.settingsButton)
        activateNfcPayButton = findViewById(R.id.activateNfcPayButton)
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

        activateNfcPayButton.setOnClickListener {
            val nfcManager = NfcManager.getInstance(this)
            nfcManager.authenticateForPayment(
                activity = this,
                onSuccess = {
                    startActivityForResult(
                        Intent(this, NfcPayOverlayActivity::class.java),
                        REQUEST_NFC_PAY
                    )
                },
                onFailure = { reason ->
                    if (reason == "NEEDS_PIN") {
                        showPinDialog(nfcManager)
                    } else {
                        Toast.makeText(this, "Authentication failed: $reason", Toast.LENGTH_SHORT).show()
                    }
                }
            )
        }

        loadBalance()
    }

    override fun onResume() {
        super.onResume()
        refreshNfcButton()
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_NFC_PAY && resultCode == RESULT_OK) {
            Toast.makeText(this, "Payment successful", Toast.LENGTH_SHORT).show()
            loadBalance()
        }
    }

    private fun refreshNfcButton() {
        val nfcManager = NfcManager.getInstance(this)
        if (nfcManager.isNfcAvailable() && nfcManager.isDeviceRegistered()) {
            activateNfcPayButton.visibility = View.VISIBLE
        } else {
            activateNfcPayButton.visibility = View.GONE
        }
    }

    private fun showPinDialog(nfcManager: NfcManager) {
        val pinInput = EditText(this).apply {
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                    android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
            hint = "Enter NFC PIN"
        }
        AlertDialog.Builder(this)
            .setTitle("Bangko ng Seton Payment")
            .setMessage("Enter your NFC PIN to authorize payment")
            .setView(pinInput)
            .setPositiveButton("Confirm") { _, _ ->
                val pin = pinInput.text.toString()
                if (nfcManager.verifyPin(pin)) {
                    startActivityForResult(
                        Intent(this, NfcPayOverlayActivity::class.java),
                        REQUEST_NFC_PAY
                    )
                } else {
                    Toast.makeText(this, "Incorrect PIN", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
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
