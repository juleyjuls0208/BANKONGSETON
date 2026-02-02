package com.juls.bankongsetonandroid

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginActivity : AppCompatActivity() {
    
    private lateinit var studentIdInput: EditText
    private lateinit var loginButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var apiClient: ApiClient
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        apiClient = ApiClient.getInstance(this)
        
        // Check if already logged in
        if (apiClient.isLoggedIn()) {
            goToMain()
            return
        }
        
        setContentView(R.layout.activity_login)
        
        studentIdInput = findViewById(R.id.student_id_input)
        loginButton = findViewById(R.id.login_button)
        progressBar = findViewById(R.id.progress_bar)
        
        loginButton.setOnClickListener {
            val studentId = studentIdInput.text.toString().trim()
            
            if (studentId.isEmpty()) {
                Toast.makeText(this, "Please enter your Student ID", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            
            login(studentId)
        }
    }
    
    private fun login(studentId: String) {
        setLoading(true)
        
        apiClient.login(studentId).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                setLoading(false)
                
                if (response.isSuccessful) {
                    val loginResponse = response.body()
                    if (loginResponse != null) {
                        // Save token
                        apiClient.saveToken(loginResponse.token)
                        
                        // Save student info
                        val prefs = getSharedPreferences("banko_prefs", MODE_PRIVATE)
                        prefs.edit().apply {
                            putString("student_name", loginResponse.student.name)
                            putString("student_id", loginResponse.student.id)
                            apply()
                        }
                        
                        Toast.makeText(
                            this@LoginActivity,
                            "Welcome, ${loginResponse.student.name}!",
                            Toast.LENGTH_SHORT
                        ).show()
                        
                        goToMain()
                    }
                } else {
                    // Parse error message from API
                    val errorMessage = try {
                        val errorBody = response.errorBody()?.string()
                        if (errorBody != null && errorBody.contains("error")) {
                            // Extract error message from JSON
                            val startIndex = errorBody.indexOf("\"error\":\"") + 9
                            val endIndex = errorBody.indexOf("\"", startIndex)
                            if (startIndex > 8 && endIndex > startIndex) {
                                errorBody.substring(startIndex, endIndex)
                            } else {
                                "Login failed"
                            }
                        } else {
                            "Login failed"
                        }
                    } catch (e: Exception) {
                        "Login failed"
                    }
                    
                    Toast.makeText(
                        this@LoginActivity,
                        errorMessage,
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
            
            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                setLoading(false)
                Toast.makeText(
                    this@LoginActivity,
                    "Connection error: ${t.message}",
                    Toast.LENGTH_LONG
                ).show()
            }
        })
    }
    
    private fun setLoading(loading: Boolean) {
        progressBar.isVisible = loading
        loginButton.isEnabled = !loading
        studentIdInput.isEnabled = !loading
    }
    
    private fun goToMain() {
        startActivity(Intent(this, MainActivity::class.java))
        finish()
    }
}
