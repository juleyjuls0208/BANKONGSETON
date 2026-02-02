package com.juls.bankongsetonandroid

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class ProfileFragment : Fragment() {
    
    private lateinit var nameText: TextView
    private lateinit var studentIdText: TextView
    private lateinit var idCardText: TextView
    private lateinit var moneyCardText: TextView
    private lateinit var statusText: TextView
    private lateinit var logoutButton: Button
    private lateinit var apiClient: ApiClient
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_profile, container, false)
        
        apiClient = ApiClient.getInstance(requireContext())
        
        nameText = view.findViewById(R.id.profile_name)
        studentIdText = view.findViewById(R.id.profile_student_id)
        idCardText = view.findViewById(R.id.profile_id_card)
        moneyCardText = view.findViewById(R.id.profile_money_card)
        statusText = view.findViewById(R.id.profile_status)
        logoutButton = view.findViewById(R.id.logout_button)
        
        loadProfile()
        
        logoutButton.setOnClickListener {
            logout()
        }
        
        return view
    }
    
    private fun loadProfile() {
        apiClient.getProfile().enqueue(object : Callback<StudentData> {
            override fun onResponse(call: Call<StudentData>, response: Response<StudentData>) {
                if (response.isSuccessful && response.body() != null) {
                    val student = response.body()!!
                    nameText.text = student.name
                    studentIdText.text = student.id
                    idCardText.text = student.id_card
                    moneyCardText.text = student.money_card
                    statusText.text = student.status
                } else if (response.code() == 403) {
                    // Card is lost - force logout
                    handleCardLost()
                }
            }
            
            override fun onFailure(call: Call<StudentData>, t: Throwable) {
                Toast.makeText(context, "Error loading profile", Toast.LENGTH_SHORT).show()
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
        val intent = Intent(requireContext(), LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
    }
    
    private fun logout() {
        apiClient.logout().enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(
                call: Call<Map<String, String>>,
                response: Response<Map<String, String>>
            ) {
                apiClient.clearToken()
                
                val intent = Intent(requireContext(), LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
            }
            
            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {
                // Logout anyway on failure
                apiClient.clearToken()
                
                val intent = Intent(requireContext(), LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
            }
        })
    }
}

