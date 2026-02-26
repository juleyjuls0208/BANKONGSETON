package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import com.google.android.material.textfield.TextInputLayout
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginActivity : AppCompatActivity() {
    
    private lateinit var studentIdInput: EditText
    private lateinit var studentIdLayout: TextInputLayout
    private lateinit var loginButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var secureStorage: SecureStorage
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)
        
        secureStorage = SecureStorage(this)
        
        studentIdInput = findViewById(R.id.studentIdInput)
        studentIdLayout = findViewById(R.id.studentIdLayout)
        loginButton = findViewById(R.id.loginButton)
        progressBar = findViewById(R.id.progressBar)
        
        loginButton.setOnClickListener {
            val studentId = studentIdInput.text.toString().trim()
            
            if (studentId.isEmpty()) {
                studentIdLayout.error = "Student ID required"
                return@setOnClickListener
            }
            
            studentIdLayout.error = null
            performLogin(studentId)
        }
    }
    
    private fun performLogin(studentId: String) {
        setLoading(true)
        
        val request = LoginRequest(studentId)
        
        ApiClient.apiService.login(request).enqueue(object : Callback<LoginResponse> {
            override fun onResponse(call: Call<LoginResponse>, response: Response<LoginResponse>) {
                setLoading(false)
                
                if (response.isSuccessful) {
                    response.body()?.let { loginResponse ->
                        // Save auth data
                        secureStorage.saveAuthToken(loginResponse.token)
                        secureStorage.saveStudentId(loginResponse.student.id)
                        
                        // Go to home
                        startActivity(Intent(this@LoginActivity, HomeActivity::class.java))
                        finish()
                    }
                } else {
                    Toast.makeText(
                        this@LoginActivity,
                        "Login failed: ${response.message()}",
                        Toast.LENGTH_LONG
                    ).show()
                }
            }
            
            override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                setLoading(false)
                Toast.makeText(
                    this@LoginActivity,
                    "Network error: ${t.message}",
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
}
