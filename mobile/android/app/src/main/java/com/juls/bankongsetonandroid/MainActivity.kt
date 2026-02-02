package com.juls.bankongsetonandroid

import android.content.Intent
import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.google.android.material.bottomnavigation.BottomNavigationView
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class MainActivity : AppCompatActivity() {
    
    private lateinit var bottomNavigation: BottomNavigationView
    private lateinit var apiClient: ApiClient
    private val homeFragment = HomeFragment()
    private val transactionsFragment = TransactionsFragment()
    private val profileFragment = ProfileFragment()
    private var activeFragment: Fragment = homeFragment
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        apiClient = ApiClient.getInstance(this)
        bottomNavigation = findViewById(R.id.bottom_navigation)
        
        // Add all fragments initially
        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .add(R.id.fragment_container, homeFragment, "HOME")
                .add(R.id.fragment_container, transactionsFragment, "TRANSACTIONS")
                .add(R.id.fragment_container, profileFragment, "PROFILE")
                .hide(transactionsFragment)
                .hide(profileFragment)
                .commit()
        }
        
        bottomNavigation.setOnItemSelectedListener { item ->
            val selectedFragment: Fragment = when (item.itemId) {
                R.id.nav_home -> homeFragment
                R.id.nav_transactions -> transactionsFragment
                R.id.nav_profile -> profileFragment
                else -> homeFragment
            }
            
            if (selectedFragment != activeFragment) {
                supportFragmentManager.beginTransaction()
                    .hide(activeFragment)
                    .show(selectedFragment)
                    .commit()
                activeFragment = selectedFragment
            }
            true
        }
        
        bottomNavigation.selectedItemId = R.id.nav_home
    }
    
    override fun onResume() {
        super.onResume()
        // Check card status when app comes to foreground
        validateCardStatus()
    }
    
    private fun validateCardStatus() {
        // Quick balance check to verify card is not lost
        apiClient.getBalance().enqueue(object : Callback<BalanceResponse> {
            override fun onResponse(call: Call<BalanceResponse>, response: Response<BalanceResponse>) {
                if (response.code() == 403) {
                    // Card is lost - force logout
                    handleCardLost()
                }
                // If successful or other errors, continue normally (fragments will handle)
            }
            
            override fun onFailure(call: Call<BalanceResponse>, t: Throwable) {
                // Network errors are handled by fragments, ignore here
            }
        })
    }
    
    private fun handleCardLost() {
        // Clear session
        apiClient.clearToken()
        
        // Show message
        Toast.makeText(
            this, 
            "Your card has been reported as lost. Please contact admin to get a replacement.",
            Toast.LENGTH_LONG
        ).show()
        
        // Go back to login
        val intent = Intent(this, LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
}