package com.juls.bankongsetonandroid

import android.content.Context
import android.content.SharedPreferences
import android.nfc.NfcAdapter
import android.os.Build
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

/**
 * NFC Manager - Handles virtual card registration and authentication
 * 
 * Features:
 * - Device registration with backend
 * - Secure token storage (encrypted)
 * - Biometric authentication for payments
 * - PIN fallback for devices without biometrics
 */
class NfcManager private constructor(private val context: Context) {

    private val securePrefs: SharedPreferences
    private val apiClient: ApiClient = ApiClient.getInstance(context)
    
    companion object {
        private const val PREFS_NAME = "banko_nfc_secure"
        private const val KEY_VIRTUAL_TOKEN = "virtual_token"
        private const val KEY_DEVICE_REGISTERED = "device_registered"
        private const val KEY_NFC_PIN = "nfc_pin"
        
        @Volatile
        private var instance: NfcManager? = null
        
        fun getInstance(context: Context): NfcManager {
            return instance ?: synchronized(this) {
                instance ?: NfcManager(context.applicationContext).also { instance = it }
            }
        }
    }
    
    init {
        // Create encrypted shared preferences for secure token storage
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        
        securePrefs = EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
    
    // Check if NFC is available on this device
    fun isNfcAvailable(): Boolean {
        val nfcAdapter = NfcAdapter.getDefaultAdapter(context)
        return nfcAdapter != null
    }
    
    // Check if NFC is enabled
    fun isNfcEnabled(): Boolean {
        val nfcAdapter = NfcAdapter.getDefaultAdapter(context)
        return nfcAdapter?.isEnabled == true
    }
    
    // Check if device has biometric capability
    fun hasBiometricCapability(): Boolean {
        val biometricManager = BiometricManager.from(context)
        return when (biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)) {
            BiometricManager.BIOMETRIC_SUCCESS -> true
            else -> false
        }
    }
    
    // Check if device is registered for NFC payments
    fun isDeviceRegistered(): Boolean {
        return securePrefs.getBoolean(KEY_DEVICE_REGISTERED, false) &&
                securePrefs.getString(KEY_VIRTUAL_TOKEN, null) != null
    }
    
    // Get current virtual card token
    fun getVirtualToken(): String? {
        return securePrefs.getString(KEY_VIRTUAL_TOKEN, null)
    }
    
    // Register device for NFC payments
    fun registerDevice(pin: String, callback: (Boolean, String) -> Unit) {
        if (pin.length < 4 || pin.length > 6 || !pin.all { it.isDigit() }) {
            callback(false, "PIN must be 4-6 digits")
            return
        }
        
        val deviceId = getDeviceId()
        val deviceName = "${Build.MANUFACTURER} ${Build.MODEL}"
        
        apiClient.registerNfcDevice(deviceId, deviceName, pin).enqueue(object : Callback<NfcRegistrationResponse> {
            override fun onResponse(
                call: Call<NfcRegistrationResponse>,
                response: Response<NfcRegistrationResponse>
            ) {
                if (response.isSuccessful && response.body() != null) {
                    val token = response.body()!!.virtual_token
                    
                    // Store token securely
                    securePrefs.edit()
                        .putString(KEY_VIRTUAL_TOKEN, token)
                        .putBoolean(KEY_DEVICE_REGISTERED, true)
                        .putString(KEY_NFC_PIN, pin)
                        .apply()
                    
                    // Enable HCE service with token
                    BankoHceService.currentToken = token
                    
                    callback(true, "Device registered successfully")
                } else {
                    val error = response.errorBody()?.string() ?: "Registration failed"
                    callback(false, error)
                }
            }
            
            override fun onFailure(call: Call<NfcRegistrationResponse>, t: Throwable) {
                callback(false, "Network error: ${t.message}")
            }
        })
    }
    
    // Unregister device from NFC payments
    fun unregisterDevice(callback: (Boolean, String) -> Unit) {
        val deviceId = getDeviceId()
        
        apiClient.unregisterNfcDevice(deviceId).enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(
                call: Call<Map<String, String>>,
                response: Response<Map<String, String>>
            ) {
                // Clear local data regardless of server response
                securePrefs.edit().clear().apply()
                BankoHceService.currentToken = null
                BankoHceService.isPaymentAuthorized = false
                
                callback(true, "Device unregistered")
            }
            
            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {
                // Clear local data anyway
                securePrefs.edit().clear().apply()
                BankoHceService.currentToken = null
                callback(true, "Device unregistered locally")
            }
        })
    }
    
    // Authenticate for payment (biometric or PIN)
    fun authenticateForPayment(
        activity: FragmentActivity,
        onSuccess: () -> Unit,
        onFailure: (String) -> Unit
    ) {
        if (!isDeviceRegistered()) {
            onFailure("Device not registered for NFC payments")
            return
        }
        
        // Load token into HCE service
        BankoHceService.currentToken = getVirtualToken()
        
        if (hasBiometricCapability()) {
            // Use biometric authentication
            showBiometricPrompt(activity, onSuccess, onFailure)
        } else {
            // Fallback: request PIN via callback
            onFailure("NEEDS_PIN")
        }
    }
    
    // Verify PIN manually
    fun verifyPin(enteredPin: String): Boolean {
        val storedPin = securePrefs.getString(KEY_NFC_PIN, null)
        if (storedPin != null && storedPin == enteredPin) {
            BankoHceService.isPaymentAuthorized = true
            return true
        }
        return false
    }
    
    private fun showBiometricPrompt(
        activity: FragmentActivity,
        onSuccess: () -> Unit,
        onFailure: (String) -> Unit
    ) {
        val executor = ContextCompat.getMainExecutor(context)
        
        val biometricPrompt = BiometricPrompt(activity, executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    super.onAuthenticationSucceeded(result)
                    BankoHceService.isPaymentAuthorized = true
                    onSuccess()
                }
                
                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    super.onAuthenticationError(errorCode, errString)
                    if (errorCode == BiometricPrompt.ERROR_NEGATIVE_BUTTON) {
                        // User chose PIN fallback
                        onFailure("NEEDS_PIN")
                    } else {
                        onFailure(errString.toString())
                    }
                }
                
                override fun onAuthenticationFailed() {
                    super.onAuthenticationFailed()
                    // Don't call onFailure here - let user retry
                }
            })
        
        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Bangko ng Seton Payment")
            .setSubtitle("Authenticate to enable NFC payment")
            .setNegativeButtonText("Use PIN")
            .build()
        
        biometricPrompt.authenticate(promptInfo)
    }
    
    private fun getDeviceId(): String {
        // Use Android ID as device identifier
        return android.provider.Settings.Secure.getString(
            context.contentResolver,
            android.provider.Settings.Secure.ANDROID_ID
        )
    }
}
