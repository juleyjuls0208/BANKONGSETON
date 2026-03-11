package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    
    private lateinit var secureStorage: SecureStorage
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        secureStorage = SecureStorage(this)
        
        // Check if user is logged in
        if (secureStorage.isLoggedIn()) {
            // Go to home
            startActivity(Intent(this, HomeActivity::class.java))
        } else {
            // Go to login
            startActivity(Intent(this, LoginActivity::class.java))
        }
        
        finish()
    }
}
