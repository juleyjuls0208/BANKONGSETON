package com.juls.bankongsetonandroid

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class TransactionsFragment : Fragment() {
    
    private lateinit var recyclerView: RecyclerView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var adapter: TransactionAdapter
    private val transactions = mutableListOf<Transaction>()
    private lateinit var apiClient: ApiClient
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_transactions, container, false)
        
        apiClient = ApiClient.getInstance(requireContext())
        
        recyclerView = view.findViewById(R.id.transactions_recycler)
        swipeRefresh = view.findViewById(R.id.swipe_refresh)
        
        recyclerView.layoutManager = LinearLayoutManager(context)
        
        adapter = TransactionAdapter(transactions)
        recyclerView.adapter = adapter
        
        // Setup SwipeRefreshLayout
        swipeRefresh.setColorSchemeColors(
            android.graphics.Color.WHITE
        )
        swipeRefresh.setProgressBackgroundColorSchemeColor(
            android.graphics.Color.parseColor("#1C1C1E")
        )
        swipeRefresh.setOnRefreshListener {
            loadTransactions()
        }
        
        loadTransactions()
        
        return view
    }
    
    override fun onHiddenChanged(hidden: Boolean) {
        super.onHiddenChanged(hidden)
        if (!hidden) {
            // Fragment is now visible, refresh data
            loadTransactions()
        }
    }
    
    private fun loadTransactions() {
        apiClient.getTransactions().enqueue(object : Callback<TransactionsResponse> {
            override fun onResponse(
                call: Call<TransactionsResponse>,
                response: Response<TransactionsResponse>
            ) {
                if (response.isSuccessful && response.body() != null) {
                    transactions.clear()
                    transactions.addAll(response.body()!!.transactions)
                    adapter.notifyDataSetChanged()
                } else if (response.code() == 403) {
                    // Card is lost - force logout
                    handleCardLost()
                }
                swipeRefresh.isRefreshing = false
            }
            
            override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                Toast.makeText(context, "Error loading transactions", Toast.LENGTH_SHORT).show()
                swipeRefresh.isRefreshing = false
            }
        })
    }
    
    private fun handleCardLost() {
        // Clear session
        apiClient.clearToken()
        
        // Show message
        Toast.makeText(
            context, 
            "Your card has been reported as lost. Please contact admin to get a replacement.",
            Toast.LENGTH_LONG
        ).show()
        
        // Go back to login
        val intent = android.content.Intent(requireContext(), LoginActivity::class.java)
        intent.flags = android.content.Intent.FLAG_ACTIVITY_NEW_TASK or android.content.Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        requireActivity().finish()
    }
}
