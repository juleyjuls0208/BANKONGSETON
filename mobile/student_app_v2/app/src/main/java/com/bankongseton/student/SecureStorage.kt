package com.bankongseton.student

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecureStorage(context: Context) {
    
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()
    
    private val sharedPreferences: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        "bangko_secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    fun saveAuthToken(token: String) {
        sharedPreferences.edit().putString(KEY_AUTH_TOKEN, token).apply()
    }
    
    fun getAuthToken(): String? {
        return sharedPreferences.getString(KEY_AUTH_TOKEN, null)
    }
    
    fun saveStudentId(studentId: String) {
        sharedPreferences.edit().putString(KEY_STUDENT_ID, studentId).apply()
    }
    
    fun getStudentId(): String? {
        return sharedPreferences.getString(KEY_STUDENT_ID, null)
    }
    
    fun saveDarkMode(enabled: Boolean) {
        sharedPreferences.edit().putBoolean(KEY_DARK_MODE, enabled).apply()
    }
    
    fun isDarkMode(): Boolean {
        return sharedPreferences.getBoolean(KEY_DARK_MODE, false)
    }

    fun saveThemeMode(mode: String) {
        sharedPreferences.edit().putString(KEY_THEME_MODE, mode).apply()
    }

    fun getThemeMode(): String {
        return sharedPreferences.getString(KEY_THEME_MODE, "system") ?: "system"
    }

    // Budget limit in PHP. -1f means no limit set.
    fun getBudgetLimit(): Float {
        return sharedPreferences.getFloat(KEY_BUDGET_LIMIT, -1f)
    }

    fun setBudgetLimit(limit: Float) {
        sharedPreferences.edit().putFloat(KEY_BUDGET_LIMIT, limit).apply()
    }

    fun clearBudgetLimit() {
        sharedPreferences.edit().remove(KEY_BUDGET_LIMIT).apply()
    }

    // Budget month tracking — stores "YYYY-MM" of when budget was last set
    fun getBudgetMonth(): String {
        return sharedPreferences.getString(KEY_BUDGET_MONTH, "") ?: ""
    }

    fun setBudgetMonth(yearMonth: String) {
        sharedPreferences.edit().putString(KEY_BUDGET_MONTH, yearMonth).apply()
    }

    // Lost card report state
    fun setLostCardReported(reported: Boolean) {
        sharedPreferences.edit().putBoolean(KEY_LOST_CARD_REPORTED, reported).apply()
    }

    fun isLostCardReported(): Boolean {
        return sharedPreferences.getBoolean(KEY_LOST_CARD_REPORTED, false)
    }

    fun clearLostCardReported() {
        sharedPreferences.edit().remove(KEY_LOST_CARD_REPORTED).apply()
    }

    fun saveJwtToken(token: String) {
        sharedPreferences.edit().putString(KEY_JWT_TOKEN, token).apply()
    }

    fun getJwtToken(): String? {
        return sharedPreferences.getString(KEY_JWT_TOKEN, null)
    }

    fun clearJwtToken() {
        sharedPreferences.edit().remove(KEY_JWT_TOKEN).apply()
    }

    fun clearAuth() {
        sharedPreferences.edit()
            .remove(KEY_AUTH_TOKEN)
            .remove(KEY_STUDENT_ID)
            .remove(KEY_JWT_TOKEN)
            .apply()
    }
    
    fun isLoggedIn(): Boolean {
        return getAuthToken() != null
    }
    
    companion object {
        private const val KEY_AUTH_TOKEN = "auth_token"
        private const val KEY_STUDENT_ID = "student_id"
        private const val KEY_DARK_MODE = "dark_mode"
        private const val KEY_THEME_MODE = "theme_mode"
        private const val KEY_BUDGET_LIMIT = "budget_limit"
        private const val KEY_BUDGET_MONTH = "budget_month"
        private const val KEY_LOST_CARD_REPORTED = "lost_card_reported"
        private const val KEY_JWT_TOKEN = "jwt_token"
    }
}
