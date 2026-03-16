package com.bankongseton.student

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.button.MaterialButton
import com.google.android.material.card.MaterialCardView
import com.google.android.material.progressindicator.CircularProgressIndicator
import com.google.android.material.progressindicator.LinearProgressIndicator
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

class HomeActivity : AppCompatActivity() {

    private lateinit var balanceText: TextView
    private lateinit var balanceProgressBar: LinearProgressIndicator
    private lateinit var tvGreeting: TextView
    private lateinit var tvStudentName: TextView
    private lateinit var tvCardHint: TextView
    private lateinit var transactionsButton: LinearLayout
    private lateinit var btnSeeAllTransactions: MaterialButton
    private lateinit var settingsButton: MaterialButton
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var progressBar: android.widget.ProgressBar
    private lateinit var activateNfcPayButton: LinearLayout
    private lateinit var bannerLostCard: MaterialCardView
    private lateinit var recentTransactionsContainer: LinearLayout
    private lateinit var emptyRecentState: LinearLayout
    private lateinit var secureStorage: SecureStorage
    private lateinit var nfcManager: NfcManager

    // Budget views
    private lateinit var budgetCard: MaterialCardView
    private lateinit var budgetProgress: CircularProgressIndicator
    private lateinit var tvBudgetPercent: TextView
    private lateinit var tvBudgetSpend: TextView
    private lateinit var btnSetBudget: MaterialButton

    private val nfcPayLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            Toast.makeText(this, "Payment sent — tap terminal", Toast.LENGTH_SHORT).show()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_home)

        secureStorage = SecureStorage(this)
        nfcManager = NfcManager.getInstance(this)

        balanceText = findViewById(R.id.balanceText)
        balanceProgressBar = findViewById(R.id.balanceProgressBar)
        tvGreeting = findViewById(R.id.tvGreeting)
        tvStudentName = findViewById(R.id.tvStudentName)
        tvCardHint = findViewById(R.id.tvCardHint)
        transactionsButton = findViewById(R.id.transactionsButton)
        btnSeeAllTransactions = findViewById(R.id.btnSeeAllTransactions)
        settingsButton = findViewById(R.id.settingsButton)
        swipeRefresh = findViewById(R.id.swipeRefresh)
        progressBar = findViewById(R.id.progressBar)
        activateNfcPayButton = findViewById(R.id.activateNfcPayButton)
        bannerLostCard = findViewById(R.id.bannerLostCard)
        recentTransactionsContainer = findViewById(R.id.recentTransactionsContainer)
        emptyRecentState = findViewById(R.id.emptyRecentState)

        budgetCard = findViewById(R.id.budgetCard)
        budgetProgress = findViewById(R.id.budgetProgress)
        tvBudgetPercent = findViewById(R.id.tvBudgetPercent)
        tvBudgetSpend = findViewById(R.id.tvBudgetSpend)
        btnSetBudget = findViewById(R.id.btnSetBudget)

        // Greet by time of day
        tvGreeting.text = timeGreeting()

        // Show stored name immediately while API loads
        secureStorage.getStudentId()?.let { tvStudentName.text = it }

        transactionsButton.setOnClickListener {
            startActivity(Intent(this, TransactionsActivity::class.java))
        }

        btnSeeAllTransactions.setOnClickListener {
            startActivity(Intent(this, TransactionsActivity::class.java))
        }

        settingsButton.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }

        activateNfcPayButton.setOnClickListener {
            onNfcPayClicked()
        }

        btnSetBudget.setOnClickListener {
            showBudgetDialog()
        }

        swipeRefresh.setOnRefreshListener {
            loadBalance()
            loadRecentTransactions()
            loadBudget()
        }

        loadBalance()
        loadRecentTransactions()
        loadBudget()
        updateNfcButtonVisibility()
    }

    override fun onResume() {
        super.onResume()
        updateNfcButtonVisibility()
        checkBudgetMonthReset()
        loadBudget()
        checkLostCardStatus()
    }

    // ── Greeting ──────────────────────────────────────────────────────────────

    private fun timeGreeting(): String {
        return when (Calendar.getInstance().get(Calendar.HOUR_OF_DAY)) {
            in 0..11 -> "Good morning"
            in 12..16 -> "Good afternoon"
            else -> "Good evening"
        }
    }

    // ── Budget ────────────────────────────────────────────────────────────────

    /**
     * Check if we've entered a new calendar month since the budget was last set.
     * If so, clear the stored limit and prompt the user to set a new one.
     */
    private fun checkBudgetMonthReset() {
        val currentMonth = java.text.SimpleDateFormat("yyyy-MM", java.util.Locale.getDefault())
            .format(java.util.Date())
        val storedMonth = secureStorage.getBudgetMonth()
        val hasLimit = secureStorage.getBudgetLimit() >= 0f

        if (hasLimit && storedMonth.isNotEmpty() && storedMonth != currentMonth) {
            // New month — reset budget
            secureStorage.clearBudgetLimit()
            secureStorage.setBudgetMonth("")
            android.app.AlertDialog.Builder(this)
                .setTitle("New Month — Set Your Budget")
                .setMessage("Your monthly budget has been reset for $currentMonth. Would you like to set a new spending limit?")
                .setPositiveButton("Set Budget") { _, _ -> showBudgetDialog() }
                .setNegativeButton("Later", null)
                .show()
        }
    }

    /**
     * Check lost card status from the API and update the banner accordingly.
     * On card_replaced FCM (handled in FCMService), HomeActivity will be refreshed.
     */
    private fun checkLostCardStatus() {
        val token = secureStorage.getAuthToken() ?: return
        ApiClient.apiService.getLostCardStatus("Bearer $token")
            .enqueue(object : retrofit2.Callback<LostCardStatusResponse> {
                override fun onResponse(
                    call: retrofit2.Call<LostCardStatusResponse>,
                    response: retrofit2.Response<LostCardStatusResponse>
                ) {
                    val body = response.body() ?: return
                    if (body.reported && body.processed) {
                        // Admin processed replacement — hide banner and notify
                        bannerLostCard.isVisible = false
                        secureStorage.clearLostCardReported()
                        android.widget.Toast.makeText(
                            this@HomeActivity,
                            "Your replacement card has been activated!",
                            android.widget.Toast.LENGTH_LONG
                        ).show()
                    } else {
                        bannerLostCard.isVisible = body.reported
                    }
                }

                override fun onFailure(
                    call: retrofit2.Call<LostCardStatusResponse>,
                    t: Throwable
                ) {
                    // Non-fatal — keep existing banner state
                }
            })
    }

    private fun loadBudget() {
        budgetCard.isVisible = true

        val limit = secureStorage.getBudgetLimit()
        if (limit < 0f) {
            budgetProgress.progress = 0
            tvBudgetPercent.text = "0%"
            tvBudgetSpend.text = getString(R.string.budget_no_limit)
            btnSetBudget.text = getString(R.string.budget_set_limit)
            return
        }

        val token = secureStorage.getAuthToken() ?: return
        ApiClient.apiService.getTransactions("Bearer $token", 200)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    if (!response.isSuccessful) return
                    val transactions = response.body()?.transactions ?: return
                    val spent = calcMonthlySpend(transactions)
                    updateBudgetUI(spent, limit)
                }

                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    updateBudgetUI(0.0, limit)
                }
            })
    }

    private fun calcMonthlySpend(transactions: List<Transaction>): Double {
        val cal = Calendar.getInstance()
        val currentMonth = cal.get(Calendar.MONTH)
        val currentYear = cal.get(Calendar.YEAR)
        val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
        return transactions
            .filter { tx ->
                if (tx.type.lowercase() !in listOf("purchase", "debit", "payment", "nfc")) return@filter false
                try {
                    val date = sdf.parse(tx.timestamp) ?: return@filter false
                    val txCal = Calendar.getInstance().apply { time = date }
                    txCal.get(Calendar.MONTH) == currentMonth && txCal.get(Calendar.YEAR) == currentYear
                } catch (_: Exception) { false }
            }
            .sumOf { it.amount }
    }

    private fun updateBudgetUI(spent: Double, limit: Float) {
        val pct = if (limit > 0) ((spent / limit) * 100).coerceIn(0.0, 100.0).toInt() else 0
        budgetProgress.progress = pct
        tvBudgetPercent.text = "$pct%"
        tvBudgetSpend.text = "₱%.2f / ₱%.2f".format(spent, limit)
        btnSetBudget.text = "Change"

        val color = if (pct >= 90)
            getColor(com.google.android.material.R.color.design_default_color_error)
        else
            getColor(R.color.md_theme_light_primary)
        budgetProgress.setIndicatorColor(color)
    }

    private fun showBudgetDialog() {
        val current = secureStorage.getBudgetLimit()
        val input = EditText(this).apply {
            hint = "Monthly limit (₱)"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                    android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
            if (current > 0f) setText("%.0f".format(current))
        }
        val builder = AlertDialog.Builder(this)
            .setTitle("Set Monthly Budget")
            .setView(input)
            .setPositiveButton("Save") { _, _ ->
                val value = input.text.toString().toFloatOrNull()
                if (value != null && value > 0) {
                    secureStorage.setBudgetLimit(value)
                    // Record the month this budget was set
                    val currentMonth = java.text.SimpleDateFormat("yyyy-MM", java.util.Locale.getDefault())
                        .format(java.util.Date())
                    secureStorage.setBudgetMonth(currentMonth)
                    loadBudget()
                } else {
                    Toast.makeText(this, "Enter a valid amount", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
        if (current > 0f) {
            builder.setNeutralButton("Remove") { _, _ ->
                secureStorage.clearBudgetLimit()
                loadBudget()
            }
        }
        builder.show()
    }

    // ── Recent Transactions (home screen preview) ─────────────────────────────

    private fun loadRecentTransactions() {
        val token = secureStorage.getAuthToken() ?: return

        ApiClient.apiService.getTransactions("Bearer $token", 5)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    swipeRefresh.isRefreshing = false
                    if (!response.isSuccessful) return
                    val transactions = response.body()?.transactions ?: emptyList()
                    renderRecentTransactions(transactions)
                }

                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    swipeRefresh.isRefreshing = false
                }
            })
    }

    private fun renderRecentTransactions(transactions: List<Transaction>) {
        recentTransactionsContainer.removeAllViews()
        if (transactions.isEmpty()) {
            emptyRecentState.isVisible = true
            return
        }
        emptyRecentState.isVisible = false

        val inflater = LayoutInflater.from(this)
        transactions.forEach { tx ->
            val row = inflater.inflate(R.layout.item_transaction, recentTransactionsContainer, false)

            row.findViewById<TextView>(R.id.typeText).text = formatTransactionType(tx.type)
            row.findViewById<TextView>(R.id.timestampText).text = formatTimestamp(tx.timestamp)
            row.findViewById<TextView>(R.id.balanceText).text = "Balance ₱%.2f".format(tx.balance)

            val amountView = row.findViewById<TextView>(R.id.amountText)
            val isDebit = tx.type.lowercase() in listOf("purchase", "debit", "payment", "nfc")
            amountView.text = if (isDebit) "−₱%.2f".format(tx.amount) else "+₱%.2f".format(tx.amount)
            amountView.setTextColor(
                if (isDebit) getColor(R.color.md_theme_light_error)
                else getColor(R.color.positive_green)
            )

            recentTransactionsContainer.addView(row)
        }
    }

    private fun formatTransactionType(type: String): String = when (type.lowercase()) {
        "purchase" -> "Canteen Purchase"
        "top_up", "topup", "credit" -> "Top Up"
        "nfc" -> "NFC Payment"
        "refund" -> "Refund"
        else -> type.replaceFirstChar { it.uppercaseChar() }
    }

    private fun formatTimestamp(raw: String): String {
        return try {
            val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
            val date = sdf.parse(raw) ?: return raw
            SimpleDateFormat("MMM d, h:mm a", Locale.US).format(date)
        } catch (_: Exception) { raw }
    }

    // ── NFC ───────────────────────────────────────────────────────────────────

    private fun updateNfcButtonVisibility() {
        val show = nfcManager.isNfcAvailable() && nfcManager.isNfcEnabled()
        activateNfcPayButton.isVisible = show
    }

    private fun onNfcPayClicked() {
        if (!nfcManager.isNfcEnabled()) {
            Toast.makeText(this, "Please enable NFC in device settings", Toast.LENGTH_LONG).show()
            return
        }
        if (!nfcManager.isDeviceRegistered()) {
            showSetupPinDialog()
            return
        }
        nfcManager.authenticateForPayment(
            this,
            onSuccess = {
                nfcPayLauncher.launch(Intent(this, NfcPayOverlayActivity::class.java))
            },
            onFailure = { reason ->
                if (reason == "NEEDS_PIN") showPinDialog()
                else Toast.makeText(this, reason, Toast.LENGTH_LONG).show()
            }
        )
    }

    private fun showSetupPinDialog() {
        val input = EditText(this).apply {
            hint = "Enter 4–6 digit PIN"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                    android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
        }
        AlertDialog.Builder(this)
            .setTitle("Set Up NFC Pay")
            .setMessage("Choose a PIN to secure your NFC payments.")
            .setView(input)
            .setPositiveButton("Set Up") { _, _ ->
                val pin = input.text.toString()
                val token = secureStorage.getAuthToken() ?: return@setPositiveButton
                nfcManager.registerDevice(pin, token) { success, message ->
                    Toast.makeText(this, message, Toast.LENGTH_LONG).show()
                    if (success) nfcPayLauncher.launch(Intent(this, NfcPayOverlayActivity::class.java))
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun showPinDialog() {
        val input = EditText(this).apply {
            hint = "Enter PIN"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                    android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
        }
        AlertDialog.Builder(this)
            .setTitle("NFC Pay — Enter PIN")
            .setView(input)
            .setPositiveButton("Pay") { _, _ ->
                if (nfcManager.verifyPin(input.text.toString())) {
                    nfcPayLauncher.launch(Intent(this, NfcPayOverlayActivity::class.java))
                } else {
                    Toast.makeText(this, "Incorrect PIN", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    // ── Balance ───────────────────────────────────────────────────────────────

    private fun loadBalance() {
        val token = secureStorage.getAuthToken() ?: return

        balanceProgressBar.isVisible = true
        balanceText.visibility = android.view.View.INVISIBLE

        ApiClient.apiService.getBalance("Bearer $token").enqueue(object : Callback<Balance> {
            override fun onResponse(call: Call<Balance>, response: Response<Balance>) {
                balanceProgressBar.isVisible = false
                swipeRefresh.isRefreshing = false

                if (response.isSuccessful) {
                    response.body()?.let { balance ->
                        balanceText.text = "₱%.2f".format(balance.balance)
                        balanceText.isVisible = true
                        // Show last 4 of card number
                        val card = balance.moneyCard
                        if (card.length >= 4) {
                            tvCardHint.text = "•••• ${card.takeLast(4)}"
                        }
                    }
                } else {
                    balanceText.text = "—"
                    balanceText.isVisible = true
                }
            }

            override fun onFailure(call: Call<Balance>, t: Throwable) {
                balanceProgressBar.isVisible = false
                balanceText.text = "—"
                balanceText.isVisible = true
                swipeRefresh.isRefreshing = false
                Toast.makeText(this@HomeActivity, "Network error", Toast.LENGTH_SHORT).show()
            }
        })
    }
}
