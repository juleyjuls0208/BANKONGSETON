package com.bankongseton.student

import android.app.AlertDialog
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import com.google.android.material.button.MaterialButton
import com.google.android.material.switchmaterial.SwitchMaterial
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class SettingsActivity : AppCompatActivity() {
    
    private lateinit var darkModeSwitch: SwitchMaterial
    private lateinit var logoutButton: Button
    private lateinit var secureStorage: SecureStorage
    
    // NFC section views
    private lateinit var nfcSection: LinearLayout
    private lateinit var nfcStatusText: TextView
    private lateinit var setupNfcButton: MaterialButton
    private lateinit var removeNfcButton: MaterialButton
    private lateinit var nfcManager: NfcManager
    
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
        
        // NFC section setup
        nfcSection = findViewById(R.id.nfcSection)
        nfcStatusText = findViewById(R.id.nfcStatusText)
        setupNfcButton = findViewById(R.id.setupNfcButton)
        removeNfcButton = findViewById(R.id.removeNfcButton)
        nfcManager = NfcManager.getInstance(this)
        
        // Show NFC section only on NFC-capable devices
        if (nfcManager.isNfcAvailable()) {
            nfcSection.visibility = View.VISIBLE
        }
        // else: stays gone — non-NFC devices see nothing
        
        refreshNfcSection()
        
        setupNfcButton.setOnClickListener {
            showPinDialog { pin ->
                val authToken = secureStorage.getAuthToken() ?: ""
                nfcManager.registerDevice(pin, authToken) { success, message ->
                    runOnUiThread {
                        if (success) {
                            refreshNfcSection()
                        } else {
                            Toast.makeText(this, "Registration failed. Please try again.", Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        }
        
        removeNfcButton.setOnClickListener {
            val authToken = secureStorage.getAuthToken() ?: ""
            nfcManager.unregisterDevice(authToken) { success, _ ->
                runOnUiThread {
                    if (success) {
                        refreshNfcSection()
                    } else {
                        Toast.makeText(this, "Could not remove NFC device. Please try again.", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        }
    }
    
    private fun refreshNfcSection() {
        if (nfcManager.isDeviceRegistered()) {
            nfcStatusText.text = "✓ NFC Payment Ready"
            setupNfcButton.visibility = View.GONE
            removeNfcButton.visibility = View.VISIBLE
        } else {
            nfcStatusText.text = "Not set up"
            setupNfcButton.visibility = View.VISIBLE
            removeNfcButton.visibility = View.GONE
        }
    }
    
    private fun showPinDialog(onPinEntered: (String) -> Unit) {
        val input = EditText(this).apply {
            inputType = android.text.InputType.TYPE_CLASS_NUMBER or
                android.text.InputType.TYPE_NUMBER_VARIATION_PASSWORD
            hint = "4–6 digit PIN"
        }
        AlertDialog.Builder(this)
            .setTitle("Set NFC Payment PIN")
            .setMessage("Create a PIN to secure your NFC payments.")
            .setView(input)
            .setPositiveButton("Set Up") { _, _ ->
                val pin = input.text.toString()
                if (pin.length in 4..6 && pin.all { it.isDigit() }) {
                    onPinEntered(pin)
                } else {
                    Toast.makeText(this, "PIN must be 4–6 digits.", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    override fun onResume() {
        super.onResume()
        refreshNfcSection()
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
