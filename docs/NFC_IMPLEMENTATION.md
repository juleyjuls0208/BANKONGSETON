# NFC Phone Payments Implementation Guide

## Overview

This guide explains how to implement Host Card Emulation (HCE) for NFC payments in the Bangko ng Seton Android app. HCE allows students to use their phone as a virtual money card.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Android Phone                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  HCE Service (Background)                           │   │
│  │  ├─ Listens for NFC reader tap                     │   │
│  │  ├─ Sends encrypted token via APDU                 │   │
│  │  └─ Requires biometric/PIN for high-value          │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ NFC (APDU Commands)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    POS Terminal / Arduino                   │
│  ├─ Reads NFC token from phone                             │
│  ├─ Sends token to backend API                             │
│  └─ Processes payment response                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ HTTP/HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend Server                         │
│  ├─ Validates token against registered devices             │
│  ├─ Checks security (PIN/biometric verified)               │
│  ├─ Processes payment on linked money card                 │
│  └─ Returns success/failure                                │
└─────────────────────────────────────────────────────────────┘
```

## Android Implementation

### 1. Add NFC Permissions (AndroidManifest.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <!-- NFC Permissions -->
    <uses-permission android:name="android.permission.NFC" />
    <uses-feature android:name="android.hardware.nfc.hce" android:required="true" />
    
    <!-- Biometric Permission -->
    <uses-permission android:name="android.permission.USE_BIOMETRIC" />

    <application ...>
        
        <!-- HCE Service -->
        <service
            android:name=".nfc.BankoHceService"
            android:exported="true"
            android:permission="android.permission.BIND_NFC_SERVICE">
            <intent-filter>
                <action android:name="android.nfc.cardemulation.action.HOST_APDU_SERVICE" />
            </intent-filter>
            <meta-data
                android:name="android.nfc.cardemulation.host_apdu_service"
                android:resource="@xml/apdu_service" />
        </service>
        
    </application>
</manifest>
```

### 2. Create APDU Service Configuration (res/xml/apdu_service.xml)

```xml
<?xml version="1.0" encoding="utf-8"?>
<host-apdu-service xmlns:android="http://schemas.android.com/apk/res/android"
    android:description="@string/nfc_service_description"
    android:requireDeviceUnlock="true">
    
    <!-- Custom AID for Bangko ng Seton -->
    <aid-group
        android:category="payment"
        android:description="@string/nfc_aid_description">
        <!-- Custom AID: F0 42 41 4E 4B 4F (BANKO in hex) -->
        <aid-filter android:name="F042414E4B4F" />
    </aid-group>
</host-apdu-service>
```

### 3. Create HCE Service (nfc/BankoHceService.kt)

```kotlin
package com.juls.bankongsetonandroid.nfc

import android.content.Intent
import android.nfc.cardemulation.HostApduService
import android.os.Bundle
import android.util.Log

class BankoHceService : HostApduService() {
    
    companion object {
        private const val TAG = "BankoHCE"
        
        // APDU Commands
        private val SELECT_AID = byteArrayOf(
            0x00.toByte(), // CLA
            0xA4.toByte(), // INS (SELECT)
            0x04.toByte(), // P1
            0x00.toByte(), // P2
            0x06.toByte(), // Length
            0xF0.toByte(), 0x42.toByte(), 0x41.toByte(), // AID: F042414E4B4F
            0x4E.toByte(), 0x4B.toByte(), 0x4F.toByte()
        )
        
        private val SELECT_OK = byteArrayOf(0x90.toByte(), 0x00.toByte())
        private val UNKNOWN_CMD = byteArrayOf(0x00.toByte(), 0x00.toByte())
        
        // Current token (set by app when user authenticates)
        @Volatile
        var currentToken: String? = null
        
        @Volatile
        var biometricVerified: Boolean = false
    }
    
    override fun processCommandApdu(commandApdu: ByteArray?, extras: Bundle?): ByteArray {
        if (commandApdu == null) {
            return UNKNOWN_CMD
        }
        
        Log.d(TAG, "Received APDU: ${commandApdu.toHex()}")
        
        // Handle SELECT AID command
        if (commandApdu.size >= 7 && commandApdu[1] == 0xA4.toByte()) {
            Log.d(TAG, "SELECT AID received")
            return SELECT_OK
        }
        
        // Handle GET TOKEN command (custom: 0x00 0xCA)
        if (commandApdu.size >= 2 && 
            commandApdu[0] == 0x00.toByte() && 
            commandApdu[1] == 0xCA.toByte()) {
            
            return getTokenResponse()
        }
        
        return UNKNOWN_CMD
    }
    
    private fun getTokenResponse(): ByteArray {
        val token = currentToken
        
        if (token == null) {
            Log.w(TAG, "No token available")
            return byteArrayOf(0x6A.toByte(), 0x82.toByte()) // File not found
        }
        
        // Build response: token + biometric flag + SW1SW2
        val tokenBytes = token.toByteArray()
        val biometricFlag = if (biometricVerified) 0x01.toByte() else 0x00.toByte()
        
        val response = ByteArray(tokenBytes.size + 3)
        System.arraycopy(tokenBytes, 0, response, 0, tokenBytes.size)
        response[tokenBytes.size] = biometricFlag
        response[tokenBytes.size + 1] = 0x90.toByte() // SW1: Success
        response[tokenBytes.size + 2] = 0x00.toByte() // SW2: Success
        
        Log.d(TAG, "Sending token response")
        biometricVerified = false // Reset after use
        
        return response
    }
    
    override fun onDeactivated(reason: Int) {
        Log.d(TAG, "HCE deactivated: $reason")
    }
    
    private fun ByteArray.toHex(): String = 
        joinToString("") { "%02X".format(it) }
}
```

### 4. Create NFC Manager (nfc/NfcManager.kt)

```kotlin
package com.juls.bankongsetonandroid.nfc

import android.app.Activity
import android.content.Context
import android.nfc.NfcAdapter
import android.nfc.cardemulation.CardEmulation
import android.widget.Toast
import androidx.biometric.BiometricManager
import androidx.biometric.BiometricPrompt
import androidx.core.content.ContextCompat
import androidx.fragment.app.FragmentActivity
import com.juls.bankongsetonandroid.ApiClient
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class NfcManager(private val context: Context) {
    
    private val nfcAdapter: NfcAdapter? = NfcAdapter.getDefaultAdapter(context)
    private val apiClient = ApiClient.getInstance(context)
    
    /**
     * Check if device supports NFC HCE
     */
    fun isNfcSupported(): Boolean {
        return nfcAdapter != null
    }
    
    fun isNfcEnabled(): Boolean {
        return nfcAdapter?.isEnabled == true
    }
    
    fun isHceSupported(): Boolean {
        if (nfcAdapter == null) return false
        
        val cardEmulation = CardEmulation.getInstance(nfcAdapter)
        return cardEmulation != null
    }
    
    /**
     * Register device for NFC payments
     */
    fun registerDevice(
        deviceName: String,
        onSuccess: (String) -> Unit,
        onError: (String) -> Unit
    ) {
        val deviceId = getDeviceId()
        
        apiClient.registerNfcDevice(deviceId, deviceName)
            .enqueue(object : Callback<NfcRegistrationResponse> {
                override fun onResponse(
                    call: Call<NfcRegistrationResponse>,
                    response: Response<NfcRegistrationResponse>
                ) {
                    if (response.isSuccessful) {
                        val token = response.body()?.token
                        if (token != null) {
                            // Store token securely
                            saveToken(token)
                            BankoHceService.currentToken = token
                            onSuccess("Device registered for NFC payments")
                        } else {
                            onError("Invalid response from server")
                        }
                    } else {
                        onError(response.errorBody()?.string() ?: "Registration failed")
                    }
                }
                
                override fun onFailure(call: Call<NfcRegistrationResponse>, t: Throwable) {
                    onError("Network error: ${t.message}")
                }
            })
    }
    
    /**
     * Prepare for NFC payment with biometric authentication
     */
    fun preparePayment(
        activity: FragmentActivity,
        amount: Double,
        onReady: () -> Unit,
        onError: (String) -> Unit
    ) {
        // Load stored token
        val token = loadToken()
        if (token == null) {
            onError("Device not registered for NFC payments")
            return
        }
        
        BankoHceService.currentToken = token
        
        // Require biometric for amounts >= 100
        if (amount >= 100.0) {
            authenticateBiometric(activity, 
                onSuccess = {
                    BankoHceService.biometricVerified = true
                    onReady()
                },
                onError = onError
            )
        } else {
            onReady()
        }
    }
    
    /**
     * Biometric authentication
     */
    private fun authenticateBiometric(
        activity: FragmentActivity,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        val biometricManager = BiometricManager.from(context)
        
        when (biometricManager.canAuthenticate(BiometricManager.Authenticators.BIOMETRIC_STRONG)) {
            BiometricManager.BIOMETRIC_SUCCESS -> {
                showBiometricPrompt(activity, onSuccess, onError)
            }
            BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE -> {
                onError("No biometric hardware available")
            }
            BiometricManager.BIOMETRIC_ERROR_HW_UNAVAILABLE -> {
                onError("Biometric hardware unavailable")
            }
            BiometricManager.BIOMETRIC_ERROR_NONE_ENROLLED -> {
                onError("No biometric enrolled. Please set up fingerprint or face unlock")
            }
            else -> {
                onError("Biometric authentication not available")
            }
        }
    }
    
    private fun showBiometricPrompt(
        activity: FragmentActivity,
        onSuccess: () -> Unit,
        onError: (String) -> Unit
    ) {
        val executor = ContextCompat.getMainExecutor(context)
        
        val biometricPrompt = BiometricPrompt(activity, executor,
            object : BiometricPrompt.AuthenticationCallback() {
                override fun onAuthenticationSucceeded(result: BiometricPrompt.AuthenticationResult) {
                    super.onAuthenticationSucceeded(result)
                    onSuccess()
                }
                
                override fun onAuthenticationError(errorCode: Int, errString: CharSequence) {
                    super.onAuthenticationError(errorCode, errString)
                    onError(errString.toString())
                }
                
                override fun onAuthenticationFailed() {
                    super.onAuthenticationFailed()
                    // Don't call onError - user can retry
                }
            })
        
        val promptInfo = BiometricPrompt.PromptInfo.Builder()
            .setTitle("Authenticate Payment")
            .setSubtitle("Verify your identity for NFC payment")
            .setNegativeButtonText("Cancel")
            .build()
        
        biometricPrompt.authenticate(promptInfo)
    }
    
    // Token storage (use EncryptedSharedPreferences in production)
    private fun saveToken(token: String) {
        context.getSharedPreferences("nfc_prefs", Context.MODE_PRIVATE)
            .edit()
            .putString("nfc_token", token)
            .apply()
    }
    
    private fun loadToken(): String? {
        return context.getSharedPreferences("nfc_prefs", Context.MODE_PRIVATE)
            .getString("nfc_token", null)
    }
    
    private fun getDeviceId(): String {
        // Use Android ID or generate a unique ID
        return android.provider.Settings.Secure.getString(
            context.contentResolver,
            android.provider.Settings.Secure.ANDROID_ID
        )
    }
}

// API Response classes
data class NfcRegistrationResponse(
    val token: String,
    val device_id: String,
    val message: String
)
```

### 5. Add API Endpoints to ApiClient.kt

```kotlin
// Add these to the BankoApiService interface

@POST("api/nfc/register")
fun registerNfcDevice(
    @Header("Authorization") token: String,
    @Body request: NfcRegisterRequest
): Call<NfcRegistrationResponse>

@POST("api/nfc/validate")
fun validateNfcPayment(
    @Body request: NfcValidateRequest
): Call<NfcValidateResponse>

@DELETE("api/nfc/device/{deviceId}")
fun deactivateNfcDevice(
    @Header("Authorization") token: String,
    @Path("deviceId") deviceId: String
): Call<Map<String, String>>

// Request/Response classes
data class NfcRegisterRequest(
    val device_id: String,
    val device_name: String
)

data class NfcValidateRequest(
    val token: String,
    val amount: Double,
    val biometric_verified: Boolean,
    val pin: String? = null
)

data class NfcValidateResponse(
    val valid: Boolean,
    val money_card: String?,
    val message: String
)
```

### 6. UI Integration

Add NFC setup to the Profile screen:

```kotlin
// In ProfileFragment.kt

private fun setupNfcSection() {
    val nfcManager = NfcManager(requireContext())
    
    if (!nfcManager.isNfcSupported()) {
        nfcCard.visibility = View.GONE
        return
    }
    
    if (!nfcManager.isNfcEnabled()) {
        nfcStatus.text = "NFC is disabled. Enable in Settings."
        nfcToggle.isChecked = false
        return
    }
    
    // Check if already registered
    val isRegistered = checkNfcRegistration()
    
    nfcToggle.isChecked = isRegistered
    nfcStatus.text = if (isRegistered) 
        "NFC payments enabled" 
    else 
        "Tap to enable phone payments"
    
    nfcToggle.setOnCheckedChangeListener { _, isChecked ->
        if (isChecked) {
            nfcManager.registerDevice(
                deviceName = Build.MODEL,
                onSuccess = { message ->
                    Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
                    nfcStatus.text = "NFC payments enabled"
                },
                onError = { error ->
                    Toast.makeText(context, error, Toast.LENGTH_LONG).show()
                    nfcToggle.isChecked = false
                }
            )
        } else {
            // Deactivate NFC device
            deactivateNfcDevice()
        }
    }
}
```

## Backend API Endpoints

The backend already includes NFC endpoints in `backend/nfc_payments.py`. Add these routes to `admin_dashboard.py`:

```python
from backend.nfc_payments import get_nfc_manager

@app.route('/api/nfc/register', methods=['POST'])
def register_nfc_device():
    """Register a device for NFC payments"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    # Validate session token and get student info
    
    data = request.get_json()
    device_id = data.get('device_id')
    device_name = data.get('device_name', 'Unknown Device')
    
    nfc_manager = get_nfc_manager()
    success, virtual_card, message = nfc_manager.register_device(
        student_id=student_id,
        money_card=money_card,
        device_id=device_id,
        device_name=device_name
    )
    
    if success:
        return jsonify({
            'token': virtual_card.token,
            'device_id': device_id,
            'message': message
        })
    else:
        return jsonify({'error': message}), 400

@app.route('/api/nfc/validate', methods=['POST'])
def validate_nfc_payment():
    """Validate an NFC payment from terminal"""
    data = request.get_json()
    
    nfc_manager = get_nfc_manager()
    valid, money_card, message = nfc_manager.validate_payment(
        token=data.get('token'),
        amount=data.get('amount', 0),
        pin=data.get('pin'),
        biometric_verified=data.get('biometric_verified', False)
    )
    
    return jsonify({
        'valid': valid,
        'money_card': money_card,
        'message': message
    })
```

## Security Considerations

### 1. Token Security
- Tokens are generated with cryptographic randomness
- Tokens expire after 7 days (configurable)
- Tokens are bound to specific device IDs

### 2. High-Value Transaction Protection
- Transactions ≥₱100 require biometric OR PIN
- Biometric verification happens on-device
- PIN is verified server-side

### 3. Device Binding
- Each device can only be registered to one student
- Maximum 2 devices per student
- Devices can be remotely deactivated

### 4. Fraud Prevention
- Rapid transaction detection
- Location mismatch alerts
- Automatic card suspension on suspicious activity

## Testing

### Test NFC on Emulator
1. Use Android Studio's built-in NFC emulation
2. Or use a physical device with NFC reader

### Test Flow
1. Register device for NFC payments
2. Prepare payment (triggers biometric if needed)
3. Tap phone to NFC reader
4. Verify transaction in app

## Troubleshooting

### NFC Not Working
1. Ensure NFC is enabled in device settings
2. Check that app has NFC permissions
3. Verify HCE service is running

### Token Invalid
1. Token may have expired - re-register device
2. Check network connectivity
3. Verify device ID hasn't changed

### Biometric Fails
1. Ensure biometric is enrolled on device
2. Try PIN fallback for high-value transactions
3. Check BiometricPrompt compatibility

## Dependencies

Add to `app/build.gradle.kts`:

```kotlin
dependencies {
    // Biometric authentication
    implementation("androidx.biometric:biometric:1.1.0")
    
    // Security (for encrypted storage)
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
}
```

---

*Last Updated: February 2026*
