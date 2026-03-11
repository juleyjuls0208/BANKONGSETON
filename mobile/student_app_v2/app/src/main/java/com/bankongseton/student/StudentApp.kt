package com.bankongseton.student

import android.app.Application
import androidx.appcompat.app.AppCompatDelegate

class StudentApp : Application() {

    override fun onCreate() {
        super.onCreate()
        applyTheme(SecureStorage(this).getThemeMode())
    }

    companion object {
        fun applyTheme(mode: String) {
            val nightMode = when (mode) {
                "light"  -> AppCompatDelegate.MODE_NIGHT_NO
                "dark"   -> AppCompatDelegate.MODE_NIGHT_YES
                else     -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
            }
            AppCompatDelegate.setDefaultNightMode(nightMode)
        }
    }
}
