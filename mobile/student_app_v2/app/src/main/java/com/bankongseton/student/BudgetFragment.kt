package com.bankongseton.student

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.fragment.app.Fragment
import com.google.android.material.button.MaterialButton
import com.google.android.material.progressindicator.CircularProgressIndicator
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

/**
 * Budget fragment v2 — dedicated budget screen with circular progress.
 * Lives inside MainNavActivity.
 */
class BudgetFragment : Fragment() {

    private lateinit var budgetProgress: CircularProgressIndicator
    private lateinit var tvBudgetPercent: TextView
    private lateinit var tvBudgetSpend: TextView
    private lateinit var tvBudgetRemaining: TextView
    private lateinit var tvBudgetMonth: TextView
    private lateinit var tvNoLimitCard: TextView
    private lateinit var cardNoLimit: View
    private lateinit var btnSetBudget: MaterialButton
    private lateinit var spendListContainer: LinearLayout

    private lateinit var secureStorage: SecureStorage

    private val monthFmt = SimpleDateFormat("MMMM yyyy", Locale.getDefault())

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_budget, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        secureStorage = SecureStorage(requireContext())

        budgetProgress    = view.findViewById(R.id.budgetProgress)
        tvBudgetPercent   = view.findViewById(R.id.tvBudgetPercent)
        tvBudgetSpend     = view.findViewById(R.id.tvBudgetSpend)
        tvBudgetRemaining = view.findViewById(R.id.tvBudgetRemaining)
        tvBudgetMonth     = view.findViewById(R.id.tvBudgetMonth)
        cardNoLimit       = view.findViewById(R.id.cardNoLimit)
        btnSetBudget       = view.findViewById(R.id.btnSetBudget)
        spendListContainer = view.findViewById(R.id.spendListContainer)

        // Show current month
        tvBudgetMonth.text = monthFmt.format(Calendar.getInstance().time)

        btnSetBudget.setOnClickListener { showBudgetDialog() }
        checkBudgetMonthReset()
        loadBudget()
    }

    override fun onResume() {
        super.onResume()
        loadBudget()
    }

    private fun checkBudgetMonthReset() {
        val currentMonth = SimpleDateFormat("yyyy-MM", Locale.getDefault())
            .format(Calendar.getInstance().time)
        val storedMonth = secureStorage.getBudgetMonth()
        val hasLimit = secureStorage.getBudgetLimit() >= 0f

        if (hasLimit && storedMonth.isNotEmpty() && storedMonth != currentMonth) {
            secureStorage.clearBudgetLimit()
            secureStorage.setBudgetMonth("")
            AlertDialog.Builder(requireContext())
                .setTitle("New Month — Set Your Budget")
                .setMessage("Your budget has been reset for ${monthFmt.format(Calendar.getInstance().time)}.")
                .setPositiveButton("Set Budget") { _, _ -> showBudgetDialog() }
                .setNegativeButton("Later", null)
                .show()
        }
    }

    private fun loadBudget() {
        val limit = secureStorage.getBudgetLimit()

        if (limit < 0f) {
            // No limit
            budgetProgress.progress = 0
            tvBudgetPercent.text = "—"
            tvBudgetSpend.text = "No limit set"
            tvBudgetRemaining.text = ""
            tvBudgetMonth.text = SimpleDateFormat("MMMM yyyy", Locale.getDefault())
                .format(Calendar.getInstance().time)
            cardNoLimit.visibility = View.VISIBLE
            btnSetBudget.text = getString(R.string.budget_set_limit)
            return
        }

        cardNoLimit.visibility = View.GONE
        btnSetBudget.text = "Change Budget"

        val token = secureStorage.getAuthToken() ?: return
        ApiClient.apiService.getTransactions("Bearer $token", limit = 200)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    if (!response.isSuccessful) return
                    val spent = calcMonthlySpend(response.body()?.transactions ?: emptyList())
                    updateBudgetUI(spent, limit)
                }
                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    updateBudgetUI(0.0, limit)
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

    private fun updateBudgetUI(spent: Double, limit: Float) {
        val pct = if (limit > 0) ((spent / limit) * 100).coerceIn(0.0, 100.0).toInt() else 0
        budgetProgress.progress = pct
        tvBudgetPercent.text = "$pct%"
        tvBudgetSpend.text = "₱%.0f / ₱%.0f".format(spent, limit)
        tvBudgetRemaining.text = "₱%.0f remaining".format((limit - spent).coerceAtLeast(0.0))

        val color = when {
            pct >= 90 -> requireContext().getColor(com.google.android.material.R.color.design_default_color_error)
            pct >= 70 -> requireContext().getColor(android.R.color.holo_orange_light)
            else      -> requireContext().getColor(R.color.md_theme_light_primary)
        }
        budgetProgress.setIndicatorColor(color)
    }

    private fun showBudgetDialog() {
        val current = secureStorage.getBudgetLimit()
        val input = EditText(requireContext()).apply {
            hint = "Monthly limit (₱)"
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                    android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL
            if (current > 0f) setText("%.0f".format(current))
        }
        val builder = AlertDialog.Builder(requireContext())
            .setTitle("Set Monthly Budget")
            .setView(input)
            .setPositiveButton("Save") { _, _ ->
                val value = input.text.toString().toFloatOrNull()
                if (value != null && value > 0) {
                    secureStorage.setBudgetLimit(value)
                    val currentMonth = SimpleDateFormat("yyyy-MM", Locale.getDefault())
                        .format(Calendar.getInstance().time)
                    secureStorage.setBudgetMonth(currentMonth)
                    loadBudget()
                } else {
                    Toast.makeText(requireContext(), "Enter a valid amount", Toast.LENGTH_SHORT).show()
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
}
