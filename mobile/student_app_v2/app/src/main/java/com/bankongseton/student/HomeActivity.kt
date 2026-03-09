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
import androidx.lifecycle.lifecycleScope
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.launch
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

    // Budget UI
    private lateinit var budgetCard: MaterialCardView
    private lateinit var budgetProgress: CircularProgressIndicator
    private lateinit var tvBudgetPercent: TextView
    private lateinit var tvBudgetSpend: TextView
    private lateinit var btnSetBudget: MaterialButton
    private var monthlyLimit: Double? = null

    // Lost card banner
    private lateinit var bannerLostCard: MaterialCardView

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

        // Budget views
        budgetCard = findViewById(R.id.budgetCard)
        budgetProgress = findViewById(R.id.budgetProgress)
        tvBudgetPercent = findViewById(R.id.tvBudgetPercent)
        tvBudgetSpend = findViewById(R.id.tvBudgetSpend)
        btnSetBudget = findViewById(R.id.btnSetBudget)

        // Lost card banner
        bannerLostCard = findViewById(R.id.bannerLostCard)

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

        btnSetBudget.setOnClickListener { showSetBudgetDialog() }

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
                        Toast.makeText(this, getString(R.string.nfc_pay_auth_failed, reason), Toast.LENGTH_SHORT).show()
                    }
                }
            )
        }

        loadBalance()
        loadAndDisplayBudget()
    }

    override fun onResume() {
        super.onResume()
        refreshNfcButton()
        // Show lost card banner if card has been reported lost
        if (secureStorage.isCardLost()) {
            bannerLostCard.visibility = View.VISIBLE
        } else {
            bannerLostCard.visibility = View.GONE
        }
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_NFC_PAY && resultCode == RESULT_OK) {
            Toast.makeText(this, getString(R.string.nfc_pay_payment_successful), Toast.LENGTH_SHORT).show()
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
            hint = getString(R.string.nfc_pin_hint)
        }
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.nfc_pay_dialog_title))
            .setMessage(getString(R.string.nfc_pay_dialog_message))
            .setView(pinInput)
            .setPositiveButton(getString(R.string.nfc_pay_confirm_button)) { _, _ ->
                val pin = pinInput.text.toString()
                if (nfcManager.verifyPin(pin)) {
                    startActivityForResult(
                        Intent(this, NfcPayOverlayActivity::class.java),
                        REQUEST_NFC_PAY
                    )
                } else {
                    Toast.makeText(this, getString(R.string.nfc_pay_incorrect_pin), Toast.LENGTH_SHORT).show()
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
                        balanceText.text = "₱%.2f".format(balance.balance)
                        secureStorage.saveLastBalance(balance.balance)
                    }
                } else {
                    val lastBalance = secureStorage.getLastBalance()
                    if (lastBalance != null) {
                        balanceText.text = "₱%.2f".format(lastBalance)
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
                    balanceText.text = "₱%.2f".format(lastBalance)
                }
                Snackbar.make(
                    findViewById(android.R.id.content),
                    "Couldn't update balance — check your connection",
                    Snackbar.LENGTH_LONG
                ).show()
            }
        })
    }

    // ── Budget Tracker ─────────────────────────────────────────────────────────

    private fun loadAndDisplayBudget() {
        val token = secureStorage.getAuthToken() ?: return

        lifecycleScope.launch {
            try {
                val response = ApiClient.apiService.getBudget("Bearer $token")
                if (response.isSuccessful) {
                    monthlyLimit = response.body()?.monthlyLimit
                } else {
                    monthlyLimit = null
                }
            } catch (e: Exception) {
                monthlyLimit = null
            }

            // Now load transactions with callback style (not suspend)
            ApiClient.apiService.getTransactions("Bearer $token")
                .enqueue(object : Callback<TransactionsResponse> {
                    override fun onResponse(
                        call: Call<TransactionsResponse>,
                        response: Response<TransactionsResponse>
                    ) {
                        val transactions = response.body()?.transactions ?: emptyList()
                        updateBudgetUI(transactions)
                    }

                    override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                        updateBudgetUI(emptyList())
                    }
                })
        }
    }

    private fun updateBudgetUI(transactions: List<Transaction>) {
        val limit = monthlyLimit
        if (limit == null || limit <= 0.0) {
            tvBudgetSpend.text = getString(R.string.budget_no_limit)
            tvBudgetPercent.text = "—"
            budgetProgress.progress = 0
            budgetCard.visibility = View.VISIBLE
            return
        }

        val currentMonth = java.text.SimpleDateFormat("yyyy-MM", java.util.Locale.getDefault())
            .format(java.util.Date())

        val spent = transactions
            .filter { it.timestamp.startsWith(currentMonth) }
            .filter { it.type == "Purchase" || it.type == "NFC Purchase" }
            .sumOf { it.amount }

        val percent = ((spent / limit) * 100).toInt().coerceIn(0, 100)

        tvBudgetPercent.text = "$percent%"
        tvBudgetSpend.text = getString(R.string.budget_spent_format, spent, limit)
        budgetProgress.max = 100
        budgetProgress.progress = percent
        budgetCard.visibility = View.VISIBLE

        checkBudgetAlerts(percent, currentMonth)
    }

    private fun checkBudgetAlerts(percent: Int, currentMonth: String) {
        val lastAlertMonth = secureStorage.getBudgetAlertMonth()
        if (lastAlertMonth != currentMonth) {
            // New month — reset flags
            secureStorage.setBudgetAlertMonth(currentMonth)
            secureStorage.setBudgetAlerted80(false)
            secureStorage.setBudgetAlerted100(false)
        }

        if (percent >= 100 && !secureStorage.isBudgetAlerted100()) {
            secureStorage.setBudgetAlerted100(true)
            Snackbar.make(
                findViewById(android.R.id.content),
                getString(R.string.budget_alert_100),
                Snackbar.LENGTH_LONG
            ).show()
        } else if (percent >= 80 && !secureStorage.isBudgetAlerted80()) {
            secureStorage.setBudgetAlerted80(true)
            Snackbar.make(
                findViewById(android.R.id.content),
                getString(R.string.budget_alert_80),
                Snackbar.LENGTH_LONG
            ).show()
        }
    }

    private fun showSetBudgetDialog() {
        val input = EditText(this).apply {
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                    android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
            hint = "e.g. 1000"
            monthlyLimit?.let { setText("%.2f".format(it)) }
        }
        AlertDialog.Builder(this)
            .setTitle(getString(R.string.budget_set_limit))
            .setView(input)
            .setPositiveButton("Save") { _, _ ->
                val value = input.text.toString().toDoubleOrNull()
                if (value != null && value >= 0) {
                    saveBudgetLimit(value)
                } else {
                    Toast.makeText(this, "Enter a valid amount", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun saveBudgetLimit(limit: Double) {
        val token = secureStorage.getAuthToken() ?: return
        lifecycleScope.launch {
            try {
                val response = ApiClient.apiService.setBudget(
                    "Bearer $token",
                    SetBudgetRequest(limit)
                )
                if (response.isSuccessful) {
                    monthlyLimit = limit
                    loadAndDisplayBudget()
                } else {
                    Toast.makeText(
                        this@HomeActivity,
                        "Failed to save budget",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            } catch (e: Exception) {
                Toast.makeText(
                    this@HomeActivity,
                    "Failed to save budget",
                    Toast.LENGTH_SHORT
                ).show()
            }
        }
    }
}
