package com.bankongseton.student

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import retrofit2.Call
import retrofit2.Callback
import retrofit2.Response
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class QRPayActivity : AppCompatActivity() {

    private lateinit var previewView: PreviewView
    private lateinit var tvScanHint: TextView
    private lateinit var confirmPanel: View
    private lateinit var tvCashier: TextView
    private lateinit var itemsContainer: LinearLayout
    private lateinit var tvTotal: TextView
    private lateinit var btnConfirm: com.google.android.material.button.MaterialButton
    private lateinit var btnCancel: com.google.android.material.button.MaterialButton
    private lateinit var progressConfirm: android.widget.ProgressBar
    private lateinit var secureStorage: SecureStorage
    private lateinit var cameraExecutor: ExecutorService
    private var scannedToken: String? = null
    private var scanning = true

    private val cameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) startCamera() else {
            Toast.makeText(this, "Camera permission required", Toast.LENGTH_LONG).show()
            finish()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_qr_pay)

        secureStorage = SecureStorage(this)
        cameraExecutor = Executors.newSingleThreadExecutor()

        previewView = findViewById(R.id.previewView)
        tvScanHint = findViewById(R.id.tvScanHint)
        confirmPanel = findViewById(R.id.confirmPanel)
        tvCashier = findViewById(R.id.tvCashier)
        itemsContainer = findViewById(R.id.itemsContainer)
        tvTotal = findViewById(R.id.tvTotal)
        btnConfirm = findViewById(R.id.btnConfirm)
        btnCancel = findViewById(R.id.btnCancel)
        progressConfirm = findViewById(R.id.progressConfirm)

        btnCancel.setOnClickListener { setResult(RESULT_CANCELED); finish() }

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
            == PackageManager.PERMISSION_GRANTED) {
            startCamera()
        } else {
            cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            val preview = Preview.Builder().build().also {
                it.setSurfaceProvider(previewView.surfaceProvider)
            }
            val analyzer = ImageAnalysis.Builder()
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
                .also { analysis ->
                    analysis.setAnalyzer(cameraExecutor) { imageProxy ->
                        processImage(imageProxy)
                    }
                }
            try {
                cameraProvider.unbindAll()
                cameraProvider.bindToLifecycle(this, CameraSelector.DEFAULT_BACK_CAMERA, preview, analyzer)
            } catch (e: Exception) {
                Toast.makeText(this, "Camera error: ${e.message}", Toast.LENGTH_SHORT).show()
            }
        }, ContextCompat.getMainExecutor(this))
    }

    @androidx.annotation.OptIn(androidx.camera.core.ExperimentalGetImage::class)
    private fun processImage(imageProxy: ImageProxy) {
        if (!scanning) { imageProxy.close(); return }
        val mediaImage = imageProxy.image ?: run { imageProxy.close(); return }
        val image = InputImage.fromMediaImage(mediaImage, imageProxy.imageInfo.rotationDegrees)
        val options = BarcodeScannerOptions.Builder()
            .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
            .build()
        val scanner = BarcodeScanning.getClient(options)
        scanner.process(image)
            .addOnSuccessListener { barcodes ->
                for (barcode in barcodes) {
                    val rawValue = barcode.rawValue ?: continue
                    // Extract token from URL last path segment
                    val token = rawValue.trimEnd('/').substringAfterLast('/')
                    if (token.isNotEmpty() && rawValue.contains("/api/qr/")) {
                        scanning = false
                        runOnUiThread { fetchCart(token) }
                        break
                    }
                }
            }
            .addOnCompleteListener { imageProxy.close() }
    }

    private fun fetchCart(token: String) {
        scannedToken = token
        val jwt = secureStorage.getJwtToken() ?: run {
            showError("Not logged in with a valid session. Please log out and log in again.")
            return
        }
        ApiClient.apiService.getQrCart("Bearer $jwt", token)
            .enqueue(object : Callback<QrCartResponse> {
                override fun onResponse(call: Call<QrCartResponse>, response: Response<QrCartResponse>) {
                    when (response.code()) {
                        200 -> response.body()?.let { showConfirmation(it) }
                        404, 410 -> showError("QR code has expired. Ask the cashier to generate a new one.")
                        401 -> showError("Session expired. Please log out and log in again.")
                        else -> showError("Failed to load cart (${response.code()}). Try again.")
                    }
                }
                override fun onFailure(call: Call<QrCartResponse>, t: Throwable) {
                    showError("Network error: ${t.message}")
                }
            })
    }

    private fun showConfirmation(cart: QrCartResponse) {
        previewView.isVisible = false
        tvScanHint.isVisible = false
        confirmPanel.isVisible = true

        tvCashier.text = "Cashier: ${cart.cashier}"
        tvTotal.text = "₱%.2f".format(cart.total)

        itemsContainer.removeAllViews()
        val inflater = LayoutInflater.from(this)
        cart.items.forEach { item ->
            val row = inflater.inflate(R.layout.item_receipt_line, itemsContainer, false)
            row.findViewById<TextView>(R.id.itemName).text = item.name
            row.findViewById<TextView>(R.id.itemQty).text = "×${item.qty}"
            row.findViewById<TextView>(R.id.itemPrice).text = "₱%.2f".format(item.price * item.qty)
            itemsContainer.addView(row)
        }

        btnConfirm.setOnClickListener { confirmPayment() }
    }

    private fun confirmPayment() {
        val token = scannedToken ?: return
        val jwt = secureStorage.getJwtToken() ?: return
        setLoading(true)
        ApiClient.apiService.confirmQrPayment("Bearer $jwt", QrConfirmRequest(token))
            .enqueue(object : Callback<QrConfirmResponse> {
                override fun onResponse(call: Call<QrConfirmResponse>, response: Response<QrConfirmResponse>) {
                    setLoading(false)
                    when (response.code()) {
                        200 -> {
                            Toast.makeText(this@QRPayActivity, "Payment successful!", Toast.LENGTH_SHORT).show()
                            setResult(RESULT_OK)
                            finish()
                        }
                        402 -> showError("Insufficient balance. Please top up your card.")
                        404, 410 -> showError("QR code has expired. Ask the cashier to generate a new one.")
                        401 -> showError("Session expired. Please log out and log in again.")
                        else -> showError("Payment failed (${response.code()}). Try again.")
                    }
                }
                override fun onFailure(call: Call<QrConfirmResponse>, t: Throwable) {
                    setLoading(false)
                    showError("Network error: ${t.message}")
                }
            })
    }

    private fun setLoading(loading: Boolean) {
        progressConfirm.isVisible = loading
        btnConfirm.isEnabled = !loading
        btnCancel.isEnabled = !loading
    }

    private fun showError(message: String) {
        AlertDialog.Builder(this)
            .setTitle("Payment Error")
            .setMessage(message)
            .setPositiveButton("OK") { _, _ -> finish() }
            .setCancelable(false)
            .show()
    }

    override fun onDestroy() {
        super.onDestroy()
        cameraExecutor.shutdown()
    }
}
