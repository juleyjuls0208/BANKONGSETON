package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.ProgressBar
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class LoginActivity : AppCompatActivity() {

    private lateinit var studentIdInput: TextInputEditText
    private lateinit var studentIdLayout: TextInputLayout
    private lateinit var loginButton: Button
    private lateinit var progressBar: ProgressBar
    private lateinit var secureStorage: SecureStorage

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_login)

        secureStorage = SecureStorage(this)

        // Already logged in? Skip straight to home.
        if (secureStorage.getAuthToken() != null) {
            goHome()
            return
        }

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

        // Allow IME Done to submit
        studentIdInput.setOnEditorActionListener { _, _, _ ->
            loginButton.performClick()
            true
        }
    }

    private fun performLogin(studentId: String) {
        setLoading(true)

        ApiClient.apiService.login(LoginRequest(studentId))
            .enqueue(object : Callback<LoginResponse> {
                override fun onResponse(
                    call: Call<LoginResponse>,
                    response: Response<LoginResponse>
                ) {
                    setLoading(false)
                    if (response.isSuccessful) {
                        response.body()?.let { loginResponse ->
                            secureStorage.saveAuthToken(loginResponse.token)
                            secureStorage.saveStudentId(loginResponse.student.id)
                            goHome()
                        }
                    } else {
                        studentIdLayout.error = when (response.code()) {
                            401, 404 -> "Student not found"
                            else -> "Login failed (${response.code()})"
                        }
                    }
                }

                override fun onFailure(call: Call<LoginResponse>, t: Throwable) {
                    setLoading(false)
                    studentIdLayout.error = "Network error — check your connection"
                }
            })
    }

    private fun setLoading(loading: Boolean) {
        progressBar.isVisible = loading
        loginButton.isEnabled = !loading
        studentIdInput.isEnabled = !loading
    }

    private fun goHome() {
        startActivity(Intent(this, HomeActivity::class.java))
        finish()
    }
}
