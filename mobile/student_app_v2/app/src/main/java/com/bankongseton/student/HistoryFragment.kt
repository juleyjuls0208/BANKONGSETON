package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import com.google.android.material.bottomsheet.BottomSheetDialog
import com.google.android.material.chip.Chip
import com.google.android.material.chip.ChipGroup
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.textfield.TextInputEditText
import com.google.gson.Gson
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

/**
 * History fragment v2 — filter chips + transaction list
 * Lives inside MainNavActivity.
 */
class HistoryFragment : Fragment() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var adapter: TransactionsAdapter
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var chipGroupFilter: ChipGroup
    private lateinit var loadingIndicator: LinearProgressIndicator
    private lateinit var emptyStateLayout: LinearLayout

    private lateinit var secureStorage: SecureStorage

    private var allTransactions: List<Transaction> = emptyList()
    private var activeFilter = "All" // "All", "Purchase", "Load"

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_history, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        secureStorage = SecureStorage(requireContext())

        recyclerView   = view.findViewById(R.id.recyclerView)
        swipeRefresh   = view.findViewById(R.id.swipeRefresh)
        chipGroupFilter = view.findViewById(R.id.chipGroupFilter)
        loadingIndicator = view.findViewById(R.id.loadingIndicator)
        emptyStateLayout = view.findViewById(R.id.emptyStateLayout)

        recyclerView.layoutManager = LinearLayoutManager(requireContext())
        adapter = TransactionsAdapter()
        recyclerView.adapter = adapter

        swipeRefresh.setOnRefreshListener { loadTransactions() }

        setupFilterChips()
        loadTransactions()
    }

    private fun setupFilterChips() {
        listOf("All", "QR Pay", "Card Pay", "Load").forEach { label ->
            val chip = Chip(requireContext()).apply {
                text = label
                isCheckable = true
                isChecked = label == "All"
            }
            chip.setOnCheckedChangeListener { _, isChecked ->
                if (isChecked) {
                    activeFilter = when (label) {
                        "QR Pay"  -> "qr"
                        "Card Pay" -> "card"
                        "Load"    -> "Load"
                        else      -> "All"
                    }
                    applyFilters()
                }
            }
            chipGroupFilter.addView(chip)
        }
    }

    private fun applyFilters() {
        val filtered = when (activeFilter) {
            "All"    -> allTransactions
            "qr"      -> allTransactions.filter { it.type.lowercase().contains("qr") }
            "card"    -> allTransactions.filter { it.type.lowercase() in listOf("purchase","debit","payment","nfc") }
            "Load"    -> allTransactions.filter { it.type.lowercase() in listOf("load","top_up","topup","credit") }
            else      -> allTransactions
        }
        adapter.setTransactions(filtered)
        emptyStateLayout.visibility = if (filtered.isEmpty()) View.VISIBLE else View.GONE
    }

    private fun loadTransactions() {
        val token = secureStorage.getAuthToken()
        if (token == null) {
            redirectToLogin()
            return
        }

        loadingIndicator.visibility = View.VISIBLE
        emptyStateLayout.visibility = View.GONE

        ApiClient.apiService.getTransactions("Bearer $token", limit = 50)
            .enqueue(object : Callback<TransactionsResponse> {
                override fun onResponse(
                    call: Call<TransactionsResponse>,
                    response: Response<TransactionsResponse>
                ) {
                    loadingIndicator.visibility = View.GONE
                    swipeRefresh.isRefreshing = false

                    if (response.isSuccessful) {
                        allTransactions = response.body()?.transactions ?: emptyList()
                        applyFilters()
                        return
                    }

                    when (response.code()) {
                        401, 403 -> redirectToLogin("Session expired")
                        404      -> {
                            allTransactions = emptyList()
                            applyFilters()
                        }
                        else     -> {
                            emptyStateLayout.visibility = View.VISIBLE
                            Toast.makeText(requireContext(), "Failed (${response.code()})", Toast.LENGTH_SHORT).show()
                        }
                    }
                }

                override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                    loadingIndicator.visibility = View.GONE
                    swipeRefresh.isRefreshing = false
                    emptyStateLayout.visibility = View.VISIBLE
                    Toast.makeText(requireContext(), "Network error", Toast.LENGTH_LONG).show()
                }
            })
    }

    private fun redirectToLogin(msg: String? = null) {
        secureStorage.clearAuth()
        msg?.let { Toast.makeText(requireContext(), it, Toast.LENGTH_SHORT).show() }
        startActivity(Intent(requireContext(), LoginActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        })
    }
}
