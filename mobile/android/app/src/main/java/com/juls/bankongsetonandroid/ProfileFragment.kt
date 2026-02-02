package com.juls.bankongsetonandroid

import android.app.AlertDialog
import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.fragment.app.Fragment
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response

class ProfileFragment : Fragment() {
    
    private lateinit var nameText: TextView
    private lateinit var studentIdText: TextView
    private lateinit var idCardText: TextView
    private lateinit var moneyCardText: TextView
    private lateinit var statusText: TextView
    private lateinit var logoutButton: Button
    private lateinit var apiClient: ApiClient
    
    // NFC UI elements
    private lateinit var nfcCard: View
    private lateinit var nfcStatusText: TextView
    private lateinit var nfcSetupButton: Button
    private lateinit var nfcPayButton: Button
    private lateinit var nfcRemoveButton: Button
    private lateinit var nfcManager: NfcManager
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View? {
        val view = inflater.inflate(R.layout.fragment_profile, container, false)
        
        apiClient = ApiClient.getInstance(requireContext())
        nfcManager = NfcManager.getInstance(requireContext())
        
        nameText = view.findViewById(R.id.profile_name)
        studentIdText = view.findViewById(R.id.profile_student_id)
        idCardText = view.findViewById(R.id.profile_id_card)
        moneyCardText = view.findViewById(R.id.profile_money_card)
        statusText = view.findViewById(R.id.profile_status)
        logoutButton = view.findViewById(R.id.logout_button)
        
        // NFC UI
        nfcCard = view.findViewById(R.id.nfc_card)
        nfcStatusText = view.findViewById(R.id.nfc_status_text)
        nfcSetupButton = view.findViewById(R.id.nfc_setup_button)
        nfcPayButton = view.findViewById(R.id.nfc_pay_button)
        nfcRemoveButton = view.findViewById(R.id.nfc_remove_button)
        
        loadProfile()
        updateNfcUI()
        
        logoutButton.setOnClickListener {
            logout()
        }
        
        nfcSetupButton.setOnClickListener {
            showNfcSetupDialog()
        }
        
        nfcPayButton.setOnClickListener {
            authenticateForPayment()
        }
        
        nfcRemoveButton.setOnClickListener {
            confirmRemoveNfc()
        }
        
        return view
    }
    
    private fun updateNfcUI() {
        if (!nfcManager.isNfcAvailable()) {
            nfcStatusText.text = "NFC not available on this device"
            nfcStatusText.setTextColor(resources.getColor(android.R.color.holo_red_light, null))
            nfcSetupButton.visibility = View.GONE
            nfcPayButton.visibility = View.GONE
            nfcRemoveButton.visibility = View.GONE
            return
        }
        
        if (!nfcManager.isNfcEnabled()) {
            nfcStatusText.text = "NFC is disabled. Enable in Settings."
            nfcStatusText.setTextColor(resources.getColor(android.R.color.holo_orange_light, null))
            nfcSetupButton.visibility = View.GONE
            nfcPayButton.visibility = View.GONE
            nfcRemoveButton.visibility = View.GONE
            return
        }
        
        if (nfcManager.isDeviceRegistered()) {
            nfcStatusText.text = "✓ NFC Payment Ready"
            nfcStatusText.setTextColor(resources.getColor(android.R.color.holo_green_light, null))
            nfcSetupButton.visibility = View.GONE
            nfcPayButton.visibility = View.VISIBLE
            nfcRemoveButton.visibility = View.VISIBLE
        } else {
            nfcStatusText.text = "Not set up"
            nfcStatusText.setTextColor(resources.getColor(android.R.color.darker_gray, null))
            nfcSetupButton.visibility = View.VISIBLE
            nfcPayButton.visibility = View.GONE
            nfcRemoveButton.visibility = View.GONE
        }
    }
    
    private fun showNfcSetupDialog() {
        val dialogView = LayoutInflater.from(context).inflate(R.layout.dialog_nfc_setup, null)
        val pinInput = dialogView.findViewById<EditText>(R.id.nfc_pin_input)
        
        AlertDialog.Builder(requireContext())
            .setTitle("Set Up NFC Payment")
            .setMessage("Create a 4-6 digit PIN for NFC payments. This PIN will be used when biometric authentication is not available.")
            .setView(dialogView)
            .setPositiveButton("Set Up") { _, _ ->
                val pin = pinInput.text.toString()
                registerNfcDevice(pin)
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun registerNfcDevice(pin: String) {
        nfcSetupButton.isEnabled = false
        nfcSetupButton.text = "Setting up..."
        
        nfcManager.registerDevice(pin) { success, message ->
            activity?.runOnUiThread {
                nfcSetupButton.isEnabled = true
                nfcSetupButton.text = "Set Up NFC Payment"
                
                if (success) {
                    Toast.makeText(context, "NFC Payment enabled!", Toast.LENGTH_SHORT).show()
                    updateNfcUI()
                } else {
                    Toast.makeText(context, message, Toast.LENGTH_LONG).show()
                }
            }
        }
    }
    
    private fun authenticateForPayment() {
        nfcPayButton.isEnabled = false
        nfcPayButton.text = "Authenticating..."
        
        nfcManager.authenticateForPayment(
            requireActivity(),
            onSuccess = {
                activity?.runOnUiThread {
                    nfcPayButton.isEnabled = true
                    nfcPayButton.text = "Ready to Pay"
                    Toast.makeText(context, "Hold phone near payment terminal", Toast.LENGTH_LONG).show()
                    
                    // Reset button after 30 seconds
                    nfcPayButton.postDelayed({
                        nfcPayButton.text = "Tap to Pay"
                        BankoHceService.isPaymentAuthorized = false
                    }, 30000)
                }
            },
            onFailure = { error ->
                activity?.runOnUiThread {
                    nfcPayButton.isEnabled = true
                    nfcPayButton.text = "Tap to Pay"
                    
                    if (error == "NEEDS_PIN") {
                        showPinDialog()
                    } else {
                        Toast.makeText(context, error, Toast.LENGTH_SHORT).show()
                    }
                }
            }
        )
    }
    
    private fun showPinDialog() {
        val dialogView = LayoutInflater.from(context).inflate(R.layout.dialog_nfc_setup, null)
        val pinInput = dialogView.findViewById<EditText>(R.id.nfc_pin_input)
        
        AlertDialog.Builder(requireContext())
            .setTitle("Enter Payment PIN")
            .setView(dialogView)
            .setPositiveButton("Verify") { _, _ ->
                val pin = pinInput.text.toString()
                if (nfcManager.verifyPin(pin)) {
                    Toast.makeText(context, "Hold phone near payment terminal", Toast.LENGTH_LONG).show()
                    nfcPayButton.text = "Ready to Pay"
                    
                    nfcPayButton.postDelayed({
                        nfcPayButton.text = "Tap to Pay"
                        BankoHceService.isPaymentAuthorized = false
                    }, 30000)
                } else {
                    Toast.makeText(context, "Incorrect PIN", Toast.LENGTH_SHORT).show()
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun confirmRemoveNfc() {
        AlertDialog.Builder(requireContext())
            .setTitle("Remove NFC Payment")
            .setMessage("Are you sure you want to remove NFC payment from this device?")
            .setPositiveButton("Remove") { _, _ ->
                nfcManager.unregisterDevice { success, message ->
                    activity?.runOnUiThread {
                        Toast.makeText(context, message, Toast.LENGTH_SHORT).show()
                        updateNfcUI()
                    }
                }
            }
            .setNegativeButton("Cancel", null)
            .show()
    }
    
    private fun loadProfile() {
        apiClient.getProfile().enqueue(object : Callback<StudentData> {
            override fun onResponse(call: Call<StudentData>, response: Response<StudentData>) {
                if (response.isSuccessful && response.body() != null) {
                    val student = response.body()!!
                    nameText.text = student.name
                    studentIdText.text = student.id
                    idCardText.text = student.id_card
                    moneyCardText.text = student.money_card
                    statusText.text = student.status
                } else if (response.code() == 403) {
                    handleCardLost()
                }
            }
            
            override fun onFailure(call: Call<StudentData>, t: Throwable) {
                Toast.makeText(context, "Error loading profile", Toast.LENGTH_SHORT).show()
            }
        })
    }
    
    private fun handleCardLost() {
        apiClient.clearToken()
        
        Toast.makeText(
            context, 
            "Your card has been reported as lost. Please contact admin to get a replacement.",
            Toast.LENGTH_LONG
        ).show()
        
        val intent = Intent(requireContext(), LoginActivity::class.java)
        intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        startActivity(intent)
    }
    
    private fun logout() {
        apiClient.logout().enqueue(object : Callback<Map<String, String>> {
            override fun onResponse(
                call: Call<Map<String, String>>,
                response: Response<Map<String, String>>
            ) {
                apiClient.clearToken()
                
                val intent = Intent(requireContext(), LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
            }
            
            override fun onFailure(call: Call<Map<String, String>>, t: Throwable) {
                apiClient.clearToken()
                
                val intent = Intent(requireContext(), LoginActivity::class.java)
                intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
                startActivity(intent)
            }
        })
    }
}

