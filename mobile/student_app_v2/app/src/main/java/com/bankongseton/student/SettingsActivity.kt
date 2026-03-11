package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.RadioGroup
import androidx.appcompat.app.AppCompatActivity
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class SettingsActivity : AppCompatActivity() {

    private lateinit var themeRadioGroup: RadioGroup
    private lateinit var logoutButton: Button
    private lateinit var secureStorage: SecureStorage

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = "Settings"

        secureStorage = SecureStorage(this)

        themeRadioGroup = findViewById(R.id.themeRadioGroup)
        logoutButton = findViewById(R.id.logoutButton)

        // Set current theme selection
        when (secureStorage.getThemeMode()) {
            "light"  -> themeRadioGroup.check(R.id.themeLight)
            "dark"   -> themeRadioGroup.check(R.id.themeDark)
            else     -> themeRadioGroup.check(R.id.themeSystem)
        }

        themeRadioGroup.setOnCheckedChangeListener { _, checkedId ->
            val mode = when (checkedId) {
                R.id.themeLight  -> "light"
                R.id.themeDark   -> "dark"
                else             -> "system"
            }
            secureStorage.saveThemeMode(mode)
            StudentApp.applyTheme(mode)
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
                        completeLogout()
                    }

                    override fun onFailure(call: Call<MessageResponse>, t: Throwable) {
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
