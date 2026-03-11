package com.bankongseton.student

import android.os.Bundle
import android.os.CountDownTimer
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.button.MaterialButton

class NfcPayOverlayActivity : AppCompatActivity() {

    private lateinit var countdownText: TextView
    private var timer: CountDownTimer? = null
    private var userCancelled = false

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Full-screen: hide action bar, set flags
        supportActionBar?.hide()
        window.setFlags(
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN,
            android.view.WindowManager.LayoutParams.FLAG_FULLSCREEN
        )
        setContentView(R.layout.activity_nfc_pay_overlay)

        countdownText = findViewById(R.id.countdownText)
        val cancelButton = findViewById<MaterialButton>(R.id.cancelButton)

        // Authorize payment in BankoHceService
        BankoHceService.reauthorize()

        startCountdown()

        cancelButton.setOnClickListener {
            cancelPayment()
        }
    }

    override fun onResume() {
        super.onResume()
        // Poll: if payment authorization was cleared by HCE deactivation (terminal tap),
        // it means a successful tap occurred — finish with RESULT_OK
        if (!userCancelled && !BankoHceService.isAuthorized()) {
            timer?.cancel()
            setResult(RESULT_OK)
            finish()
        }
    }

    private fun startCountdown() {
        timer = object : CountDownTimer(30_000L, 1_000L) {
            override fun onTick(millisUntilFinished: Long) {
                countdownText.text = (millisUntilFinished / 1000).toString()
            }
            override fun onFinish() {
                // Timer expired without a tap — dismiss overlay
                BankoHceService.deauthorize()
                setResult(RESULT_CANCELED)
                finish()
            }
        }.start()
    }

    private fun cancelPayment() {
        userCancelled = true
        timer?.cancel()
        BankoHceService.deauthorize()
        setResult(RESULT_CANCELED)
        finish()
    }

    override fun onDestroy() {
        super.onDestroy()
        timer?.cancel()
    }
}
