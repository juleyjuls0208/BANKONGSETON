package com.juls.bankongsetonandroid

import android.nfc.cardemulation.HostApduService
import android.os.Bundle
import android.util.Log

/**
 * Host Card Emulation (HCE) Service for NFC Payments
 * 
 * This service allows the phone to act as an NFC card when tapped
 * on the payment terminal (Arduino/RFID reader).
 * 
 * Protocol:
 * 1. Terminal sends SELECT command with our AID
 * 2. Phone responds with virtual card token (48 chars)
 * 3. Terminal verifies token with backend
 * 4. Payment is processed
 */
class BankoHceService : HostApduService() {

    companion object {
        private const val TAG = "BankoHceService"
        
        // Our custom AID: F0 + "BANKONGSETON" in hex
        private val SELECT_AID = byteArrayOf(
            0x00.toByte(), 0xA4.toByte(), 0x04.toByte(), 0x00.toByte(),
            0x0D.toByte(), // Length of AID
            0xF0.toByte(), 0x42.toByte(), 0x41.toByte(), 0x4E.toByte(),
            0x4B.toByte(), 0x4F.toByte(), 0x4E.toByte(), 0x47.toByte(),
            0x53.toByte(), 0x45.toByte(), 0x54.toByte(), 0x4F.toByte(),
            0x4E.toByte()
        )
        
        // Status words
        private val SW_OK = byteArrayOf(0x90.toByte(), 0x00.toByte())
        private val SW_NO_TOKEN = byteArrayOf(0x6A.toByte(), 0x82.toByte())
        private val SW_ERROR = byteArrayOf(0x6F.toByte(), 0x00.toByte())
        
        // Current virtual card token (set by NfcManager when authenticated)
        @Volatile
        var currentToken: String? = null
        
        // Flag to check if payment is authorized (biometric/PIN verified)
        @Volatile
        var isPaymentAuthorized: Boolean = false
    }

    override fun processCommandApdu(commandApdu: ByteArray?, extras: Bundle?): ByteArray {
        if (commandApdu == null || commandApdu.size < 4) {
            Log.e(TAG, "Invalid APDU command received")
            return SW_ERROR
        }
        
        Log.d(TAG, "Received APDU: ${commandApdu.toHexString()}")
        
        // Check if this is a SELECT command
        if (isSelectCommand(commandApdu)) {
            return handleSelectCommand()
        }
        
        // Unknown command
        Log.w(TAG, "Unknown command: ${commandApdu.toHexString()}")
        return SW_ERROR
    }

    override fun onDeactivated(reason: Int) {
        Log.d(TAG, "HCE deactivated, reason: $reason")
        // Reset authorization after each tap
        isPaymentAuthorized = false
    }
    
    private fun isSelectCommand(apdu: ByteArray): Boolean {
        // SELECT APDU: CLA=00, INS=A4, P1=04, P2=00
        return apdu.size >= 4 &&
                apdu[0] == 0x00.toByte() &&
                apdu[1] == 0xA4.toByte() &&
                apdu[2] == 0x04.toByte() &&
                apdu[3] == 0x00.toByte()
    }
    
    private fun handleSelectCommand(): ByteArray {
        // Check if we have a valid token
        val token = currentToken
        if (token == null || token.isEmpty()) {
            Log.w(TAG, "No virtual card token available")
            return SW_NO_TOKEN
        }
        
        // Check if payment is authorized (biometric/PIN verified)
        if (!isPaymentAuthorized) {
            Log.w(TAG, "Payment not authorized - biometric/PIN required")
            return SW_NO_TOKEN
        }
        
        Log.d(TAG, "Sending token response")
        
        // Return token as bytes + SW_OK
        val tokenBytes = token.toByteArray(Charsets.US_ASCII)
        return tokenBytes + SW_OK
    }
    
    private fun ByteArray.toHexString(): String {
        return joinToString("") { "%02X".format(it) }
    }
}
