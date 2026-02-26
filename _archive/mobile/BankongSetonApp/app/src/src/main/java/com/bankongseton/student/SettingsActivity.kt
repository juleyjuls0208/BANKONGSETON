package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import com.google.android.material.switchmaterial.SwitchMaterial
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class SettingsActivity : AppCompatActivity() {
    
    private lateinit var darkModeSwitch: SwitchMaterial
    private lateinit var logoutButton: Button
    private lateinit var secureStorage: SecureStorage
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Settings"
        
        secureStorage = SecureStorage(this)
        
        darkModeSwitch = findViewById(R.id.darkModeSwitch)
        logoutButton = findViewById(R.id.logoutButton)
        
        // Set current dark mode state
        darkModeSwitch.isChecked = secureStorage.isDarkMode()
        
        darkModeSwitch.setOnCheckedChangeListener { _, isChecked ->
            secureStorage.saveDarkMode(isChecked)
            AppCompatDelegate.setDefaultNightMode(
                if (isChecked) AppCompatDelegate.MODE_NIGHT_YES
                else AppCompatDelegate.MODE_NIGHT_NO
            )
        }
        
        logoutButton.setOnClickListener {
            performLogout()
        }
    }
    
    private fun performLogout() {
        val token = secureStorage.getAuthToken()
        
        if (token != null) {
            ApiClient.apiService.logout("Bearer $token")
                .enqueue(object : Callback<MessageResponse> {
                    override fun onResponse(
                        call: Call<MessageResponse>,
                        response: Response<MessageResponse>
                    ) {
                        // Clear local data regardless of server response
                        completeLogout()
                    }
                    
                    override fun onFailure(call: Call<MessageResponse>, t: Throwable) {
                        // Clear local data even on failure
                        completeLogout()
                    }
                })
        } else {
            completeLogout()
        }
    }
    
    private fun completeLogout() {
        secureStorage.clearAuth()
        
        val intent = Intent(this, LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
        finish()
    }
    
    override fun onSupportNavigateUp(): Boolean {
        finish()
        return true
    }
}
