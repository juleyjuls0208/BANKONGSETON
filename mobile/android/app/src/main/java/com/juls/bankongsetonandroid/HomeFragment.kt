package com.juls.bankongsetonandroid

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import android.widget.Toast
import androidx.cardview.widget.CardView
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class HomeFragment : Fragment() {
    
    private lateinit var balanceText: TextView
    private lateinit var studentNameText: TextView
    private lateinit var studentIdText: TextView
    private lateinit var balanceCard: CardView
    private lateinit var recentTransactionsRecycler: RecyclerView
    private lateinit var emptyTransactionsText: TextView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private lateinit var apiClient: ApiClient
    private lateinit var adapter: TransactionAdapter
    private val recentTransactions = mutableListOf<Transaction>()
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_home, container, false)
        
        apiClient = ApiClient.getInstance(requireContext())
        
        balanceText = view.findViewById(R.id.balance_text)
        studentNameText = view.findViewById(R.id.student_name_text)
        studentIdText = view.findViewById(R.id.student_id_text)
        balanceCard = view.findViewById(R.id.balance_card)
        recentTransactionsRecycler = view.findViewById(R.id.recent_transactions_recycler)
        emptyTransactionsText = view.findViewById(R.id.empty_transactions_text)
        swipeRefresh = view.findViewById(R.id.swipe_refresh)
        
        // Setup SwipeRefreshLayout
        swipeRefresh.setColorSchemeColors(
            android.graphics.Color.WHITE
        )
        swipeRefresh.setProgressBackgroundColorSchemeColor(
            android.graphics.Color.parseColor("#1C1C1E")
        )
        swipeRefresh.setOnRefreshListener {
            refreshData()
        }
        
        // Setup RecyclerView
        recentTransactionsRecycler.layoutManager = LinearLayoutManager(context)
        adapter = TransactionAdapter(recentTransactions)
        recentTransactionsRecycler.adapter = adapter
        
        loadStudentData()
        refreshData()
        
        return view
    }
    
    override fun onHiddenChanged(hidden: Boolean) {
        super.onHiddenChanged(hidden)
        if (!hidden) {
            // Fragment is now visible, refresh data
            refreshData()
        }
    }
    
    private fun refreshData() {
        loadBalance()
        loadRecentTransactions()
    }
    
    private fun loadStudentData() {
        apiClient.getProfile().enqueue(object : Callback<StudentData> {
            override fun onResponse(call: Call<StudentData>, response: Response<StudentData>) {
                if (response.isSuccessful && response.body() != null) {
                    val student = response.body()!!
                    studentNameText.text = student.name
                    studentIdText.text = student.id
                    studentIdText.visibility = View.VISIBLE
                    android.util.Log.d("HomeFragment", "Student ID set to: ${student.id}")
                } else {
                    android.util.Log.e("HomeFragment", "Failed to load profile: ${response.code()}")
                }
            }
            
            override fun onFailure(call: Call<StudentData>, t: Throwable) {
                Toast.makeText(context, "Error loading profile", Toast.LENGTH_SHORT).show()
                android.util.Log.e("HomeFragment", "Error loading profile", t)
            }
        })
    }
    
    private fun loadBalance() {
        apiClient.getBalance().enqueue(object : Callback<BalanceResponse> {
            override fun onResponse(call: Call<BalanceResponse>, response: Response<BalanceResponse>) {
                if (response.isSuccessful && response.body() != null) {
                    val balance = response.body()!!.balance
                    balanceText.text = String.format("₱%.0f", balance)
                } else if (response.code() == 403) {
                    // Card is lost - force logout
                    handleCardLost()
                }
                swipeRefresh.isRefreshing = false
            }
            
            override fun onFailure(call: Call<BalanceResponse>, t: Throwable) {
                Toast.makeText(context, "Error loading balance", Toast.LENGTH_SHORT).show()
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
    
    private fun loadRecentTransactions() {
        apiClient.getTransactions(4).enqueue(object : Callback<TransactionsResponse> {
            override fun onResponse(
                call: Call<TransactionsResponse>,
                response: Response<TransactionsResponse>
            ) {
                if (response.isSuccessful && response.body() != null) {
                    recentTransactions.clear()
                    recentTransactions.addAll(response.body()!!.transactions)
                    adapter.notifyDataSetChanged()
                    
                    if (recentTransactions.isEmpty()) {
                        emptyTransactionsText.visibility = View.VISIBLE
                        recentTransactionsRecycler.visibility = View.GONE
                    } else {
                        emptyTransactionsText.visibility = View.GONE
                        recentTransactionsRecycler.visibility = View.VISIBLE
                    }
                }
                swipeRefresh.isRefreshing = false
            }
            
            override fun onFailure(call: Call<TransactionsResponse>, t: Throwable) {
                emptyTransactionsText.visibility = View.VISIBLE
                recentTransactionsRecycler.visibility = View.GONE
                swipeRefresh.isRefreshing = false
            }
        })
    }
}

