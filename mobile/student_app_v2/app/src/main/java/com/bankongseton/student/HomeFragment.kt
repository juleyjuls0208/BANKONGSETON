package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
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

/**
 * Home fragment v2 — Digital Peso Card
 * Shows balance, budget peek, recent transactions, and QR pay CTA.
 * Lives inside MainNavActivity with bottom navigation.
 */
class HomeFragment : Fragment() {

    private lateinit var tvGreeting: TextView
    private lateinit var tvStudentName: TextView
    private lateinit var tvCardHint: TextView
    private lateinit var balanceText: TextView
    private lateinit var balanceProgressBar: LinearProgressIndicator
    private lateinit var balanceCard: MaterialCardView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var qrPayCard: MaterialCardView
    private lateinit var budgetPeekCard: MaterialCardView
    private lateinit var budgetProgress: CircularProgressIndicator
    private lateinit var tvBudgetPercent: TextView
    private lateinit var tvBudgetSpend: TextView
    private lateinit var recentTransactionsContainer: LinearLayout
    private lateinit var emptyRecentState: LinearLayout
    private lateinit var btnSeeAllTransactions: MaterialButton
    private lateinit var bannerLostCard: MaterialCardView

    private lateinit var secureStorage: SecureStorage
    private val transactionsAdapter = TransactionsAdapter()

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_home, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        secureStorage = SecureStorage(requireContext())

        // Bind views
        tvGreeting         = view.findViewById(R.id.tvGreeting)
        tvStudentName        = view.findViewById(R.id.tvStudentName)
        tvCardHint           = view.findViewById(R.id.tvCardHint)
        balanceText          = view.findViewById(R.id.balanceText)
        balanceProgressBar  = view.findViewById(R.id.balanceProgressBar)
        balanceCard          = view.findViewById(R.id.balanceCard)
        swipeRefresh         = view.findViewById(R.id.swipeRefresh)
        qrPayCard            = view.findViewById(R.id.qrPayCard)
        budgetPeekCard       = view.findViewById(R.id.budgetPeekCard)
        budgetProgress       = view.findViewById(R.id.budgetProgress)
        tvBudgetPercent      = view.findViewById(R.id.tvBudgetPercent)
        tvBudgetSpend        = view.findViewById(R.id.tvBudgetSpend)
        recentTransactionsContainer = view.findViewById(R.id.recentTransactionsContainer)
        emptyRecentState     = view.findViewById(R.id.emptyRecentState)
        btnSeeAllTransactions = view.findViewById(R.id.btnSeeAllTransactions)
        bannerLostCard       = view.findViewById(R.id.bannerLostCard)

        tvGreeting.text = timeGreeting()
        secureStorage.getStudentId()?.let { tvStudentName.text = it }

        swipeRefresh.setOnRefreshListener {
            loadBalance()
            loadRecentTransactions()
            loadBudgetPeek()
        }

        qrPayCard.setOnClickListener {
            startActivity(Intent(requireContext(), QRPayActivity::class.java))
        }

        btnSeeAllTransactions.setOnClickListener {
            // Navigate to history tab
            (activity as? MainNavActivity)?.selectHistoryTab()
        }

        loadBalance()
        loadRecentTransactions()
        loadBudgetPeek()
        checkLostCardStatus()
    }

    override fun onResume() {
        super.onResume()
        loadBalance()
        loadBudgetPeek()
    }

    private fun timeGreeting(): String {
        return when (Calendar.getInstance().get(Calendar.HOUR_OF_DAY)) {
            in 0..11 -> "Good morning"
            in 12..16 -> "Good afternoon"
            else -> "Good evening"
        }
    }

    // ── Balance ──────────────────────────────────────────────────────────────

    private fun loadBalance() {
        val token = secureStorage.getAuthToken() ?: return

        balanceProgressBar.visibility = View.VISIBLE
        balanceText.visibility = View.INVISIBLE

        ApiClient.apiService.getBalance("Bearer $token").enqueue(object : Callback<Balance> {
            override fun onResponse(call: Call<Balance>, response: Response<Balance>) {
                balanceProgressBar.visibility = View.GONE
                swipeRefresh.isRefreshing = false

                if (response.isSuccessful) {
                    response.body()?.let { b ->
                        balanceText.text = "₱%.2f".format(b.balance)
                        balanceText.visibility = View.VISIBLE
                        val card = b.moneyCard
                        if (card.length >= 4) tvCardHint.text = "•••• ${card.takeLast(4)}"
                    }
                } else {
                    balanceText.text = "—"
                    balanceText.visibility = View.VISIBLE
                }
            }

            override fun onFailure(call: Call<Balance>, t: Throwable) {
                balanceProgressBar.visibility = View.GONE
                balanceText.text = "—"
                balanceText.visibility = View.VISIBLE
                swipeRefresh.isRefreshing = false
                Toast.makeText(requireContext(), "Network error", Toast.LENGTH_SHORT).show()
            }
        })
    }

    // ── Budget Peek ────────────────────────────────────────────────────────

    private fun loadBudgetPeek() {
        val limit = secureStorage.getBudgetLimit()
        if (limit < 0f) {
            budgetPeekCard.visibility = View.GONE
            return
        }

        budgetPeekCard.visibility = View.VISIBLE
        val token = secureStorage.getAuthToken() ?: return

        ApiClient.apiService.getTransactions("Bearer $token", limit = 200)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(call: Call<TransactionsResponse>, response: Response<TransactionsResponse>) {
                    if (!response.isSuccessful) return
                    val spent = calcMonthlySpend(response.body()?.transactions ?: emptyList())
                    updateBudgetPeekUI(spent, limit)
                }
                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    updateBudgetPeekUI(0.0, limit)
                }
            })
    }

    private fun calcMonthlySpend(transactions: List<Transaction>): Double {
        val cal = Calendar.getInstance()
        val sdf = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US)
        return transactions
            .filter { tx ->
                if (tx.type.lowercase() !in listOf("purchase","debit","payment","nfc")) false
                else try {
                    val date = sdf.parse(tx.timestamp) ?: return@filter false
                    val txCal = Calendar.getInstance().apply { time = date }
                    txCal.get(Calendar.MONTH) == cal.get(Calendar.MONTH) &&
                            txCal.get(Calendar.YEAR) == cal.get(Calendar.YEAR)
                } catch (_: Exception) { false }
            }
            .sumOf { it.amount }
    }

    private fun updateBudgetPeekUI(spent: Double, limit: Float) {
        val pct = if (limit > 0) ((spent / limit) * 100).coerceIn(0.0, 100.0).toInt() else 0
        budgetProgress.progress = pct
        tvBudgetPercent.text = "$pct%"
        tvBudgetSpend.text = "₱%.0f / ₱%.0f".format(spent, limit)

        val color = if (pct >= 90)
            requireContext().getColor(com.google.android.material.R.color.design_default_color_error)
        else
            requireContext().getColor(R.color.md_theme_light_primary)
        budgetProgress.setIndicatorColor(color)
    }

    // ── Recent Transactions ─────────────────────────────────────────────────

    private fun loadRecentTransactions() {
        val token = secureStorage.getAuthToken() ?: return

        ApiClient.apiService.getTransactions("Bearer $token", limit = 5)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    swipeRefresh.isRefreshing = false
                    if (!response.isSuccessful) return
                    val txns = response.body()?.transactions ?: emptyList()
                    renderRecentTransactions(txns)
                }
                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    swipeRefresh.isRefreshing = false
                }
            })
    }

    private fun renderRecentTransactions(transactions: List<Transaction>) {
        recentTransactionsContainer.removeAllViews()
        if (transactions.isEmpty()) {
            emptyRecentState.visibility = View.VISIBLE
            return
        }
        emptyRecentState.visibility = View.GONE

        val inflater = LayoutInflater.from(requireContext())
        transactions.forEach { tx ->
            val row = inflater.inflate(R.layout.item_transaction, recentTransactionsContainer, false)
            row.findViewById<TextView>(R.id.typeText).text = formatType(tx.type)
            row.findViewById<TextView>(R.id.timestampText).text = formatTimestamp(tx.timestamp)
            row.findViewById<TextView>(R.id.balanceText).text = "₱%.2f".format(tx.balance)

            val amtView = row.findViewById<TextView>(R.id.amountText)
            val isDebit = tx.type.lowercase() in listOf("purchase","debit","payment","nfc")
            amtView.text = if (isDebit) "−₱%.2f".format(tx.amount) else "+₱%.2f".format(tx.amount)
            amtView.setTextColor(
                if (isDebit) requireContext().getColor(R.color.md_theme_light_error)
                else requireContext().getColor(R.color.positive_green)
            )
            recentTransactionsContainer.addView(row)
        }
    }

    private fun formatType(type: String): String = when (type.lowercase()) {
        "purchase" -> "Canteen Purchase"
        "top_up","topup","credit" -> "Top Up"
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

    // ── Lost Card ─────────────────────────────────────────────────────────

    private fun checkLostCardStatus() {
        val token = secureStorage.getAuthToken() ?: return
        ApiClient.apiService.getLostCardStatus("Bearer $token")
            .enqueue(object : Callback<LostCardStatusResponse> {
                override fun onResponse(
                    call: Call<LostCardStatusResponse>,
                    response: Response<LostCardStatusResponse>
                ) {
                    val body = response.body() ?: return
                    if (body.reported && body.processed) {
                        bannerLostCard.visibility = View.GONE
                        secureStorage.clearLostCardReported()
                    } else {
                        bannerLostCard.visibility = if (body.reported) View.VISIBLE else View.GONE
                    }
                }
                override fun onFailure(call: Call<LostCardStatusResponse>, t: Throwable) {}
            })
    }
}
