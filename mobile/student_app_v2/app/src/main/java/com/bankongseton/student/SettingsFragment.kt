package com.bankongseton.student

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.RadioGroup
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import com.google.android.material.button.MaterialButton
import com.google.android.material.radiobutton.MaterialRadioButton
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * Settings fragment v2 — minimalist.
 * Lives inside MainNavActivity.
 */
class SettingsFragment : Fragment() {

    private lateinit var themeRadioGroup: RadioGroup
    private lateinit var tvCurrentTheme: TextView
    private lateinit var tvStudentId: TextView
    private lateinit var tvMoneyCard: TextView
    private lateinit var logoutButton: MaterialButton
    private lateinit var secureStorage: SecureStorage

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        return inflater.inflate(R.layout.fragment_settings, container, false)
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        secureStorage = SecureStorage(requireContext())

        themeRadioGroup = view.findViewById(R.id.themeRadioGroup)
        tvCurrentTheme   = view.findViewById(R.id.tvCurrentTheme)
        tvStudentId      = view.findViewById(R.id.tvStudentId)
        tvMoneyCard      = view.findViewById(R.id.tvMoneyCard)
        logoutButton     = view.findViewById(R.id.logoutButton)

        // Set current theme
        when (secureStorage.getThemeMode()) {
            "light"  -> {
                themeRadioGroup.check(R.id.themeLight)
                tvCurrentTheme.text = "Light"
            }
            "dark"   -> {
                themeRadioGroup.check(R.id.themeDark)
                tvCurrentTheme.text = "Dark"
            }
            else     -> {
                themeRadioGroup.check(R.id.themeSystem)
                tvCurrentTheme.text = "Follow System"
            }
        }

        themeRadioGroup.setOnCheckedChangeListener { _, checkedId ->
            val mode = when (checkedId) {
                R.id.themeLight  -> "light"
                R.id.themeDark   -> "dark"
                else             -> "system"
            }
            tvCurrentTheme.text = when (checkedId) {
                R.id.themeLight  -> "Light"
                R.id.themeDark   -> "Dark"
                else             -> "Follow System"
            }
            secureStorage.saveThemeMode(mode)
            StudentApp.applyTheme(mode)
        }

        // Load profile info
        loadProfileInfo()

        logoutButton.setOnClickListener { performLogout() }
    }

    private fun loadProfileInfo() {
        val token = secureStorage.getAuthToken() ?: return
        ApiClient.apiService.getProfile("Bearer $token")
            .enqueue(object : Callback<Student> {
                override fun onResponse(call: Call<Student>, response: Response<Student>) {
                    if (response.isSuccessful) {
                        response.body()?.let { s ->
                            tvStudentId.text = s.id
                            tvMoneyCard.text = if (s.moneyCard.length >= 4)
                                "•••• ${s.moneyCard.takeLast(4)}" else s.moneyCard
                        }
                    }
                }
                override fun onFailure(call: Call<Student>, t: Throwable) {}
            })
    }

    private fun performLogout() {
        val token = secureStorage.getAuthToken()
        if (token != null) {
            ApiClient.apiService.logout("Bearer $token")
                .enqueue(object : Callback<MessageResponse> {
                    override fun onResponse(
                        call: Call<MessageResponse>,
                        response: Response<MessageResponse>
                    ) { completeLogout() }
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
        startActivity(Intent(requireContext(), LoginActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        })
    }
}
