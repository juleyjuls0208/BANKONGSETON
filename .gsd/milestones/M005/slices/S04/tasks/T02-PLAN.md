---
estimated_steps: 7
estimated_files: 6
---

# T02: Build Android QRPayActivity — CameraX scanner, confirmation UI, HomeActivity wiring

**Slice:** S04 — Android + iOS App QR Pay
**Milestone:** M005

## Description

Creates `QRPayActivity.kt` with a full QR scanning + confirmation flow using CameraX and ML Kit. Replaces the hidden NFC Pay button in `activity_home.xml` with an always-visible "Scan QR" quick-action chip. Wires `HomeActivity.kt` to launch `QRPayActivity` and refresh balance on successful payment. Adds CAMERA permission and `QRPayActivity` declaration to `AndroidManifest.xml`. Adds `action_qr_pay` string resource.

**Prerequisite:** T01 must be complete — `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse` data classes and `BangkoApiService.getQrCart()`/`confirmQrPayment()` must exist, and `SecureStorage.getJwtToken()` must be available.

## Steps

1. **`app/src/main/res/layout/activity_qr_pay.xml`** — create new layout file:
   ```xml
   <?xml version="1.0" encoding="utf-8"?>
   <FrameLayout xmlns:android="http://schemas.android.com/apk/res/android"
       android:layout_width="match_parent"
       android:layout_height="match_parent"
       android:background="@android:color/black">

       <!-- Camera preview — fills screen during scanning -->
       <androidx.camera.view.PreviewView
           android:id="@+id/previewView"
           android:layout_width="match_parent"
           android:layout_height="match_parent" />

       <!-- Scanning hint overlay -->
       <TextView
           android:id="@+id/tvScanHint"
           android:layout_width="wrap_content"
           android:layout_height="wrap_content"
           android:layout_gravity="bottom|center_horizontal"
           android:layout_marginBottom="48dp"
           android:text="@string/qr_pay_scanning"
           android:textColor="#FFFFFF"
           android:textSize="16sp"
           android:padding="12dp"
           android:background="#80000000" />

       <!-- Confirmation panel — hidden until QR is scanned -->
       <androidx.core.widget.NestedScrollView
           android:id="@+id/confirmPanel"
           android:layout_width="match_parent"
           android:layout_height="match_parent"
           android:visibility="gone"
           android:background="?attr/colorSurface">

           <LinearLayout
               android:layout_width="match_parent"
               android:layout_height="wrap_content"
               android:orientation="vertical"
               android:padding="24dp">

               <TextView
                   android:id="@+id/tvConfirmTitle"
                   android:layout_width="wrap_content"
                   android:layout_height="wrap_content"
                   android:text="@string/qr_pay_confirm_title"
                   android:textAppearance="?attr/textAppearanceHeadlineSmall"
                   android:layout_marginTop="48dp"
                   android:layout_marginBottom="8dp" />

               <TextView
                   android:id="@+id/tvCashier"
                   android:layout_width="wrap_content"
                   android:layout_height="wrap_content"
                   android:textAppearance="?attr/textAppearanceBodyMedium"
                   android:textColor="?attr/colorOnSurfaceVariant"
                   android:layout_marginBottom="16dp" />

               <!-- Cart items populated programmatically via item_receipt_line.xml -->
               <LinearLayout
                   android:id="@+id/itemsContainer"
                   android:layout_width="match_parent"
                   android:layout_height="wrap_content"
                   android:orientation="vertical"
                   android:layout_marginBottom="16dp" />

               <com.google.android.material.divider.MaterialDivider
                   android:layout_width="match_parent"
                   android:layout_height="1dp"
                   android:layout_marginBottom="12dp" />

               <LinearLayout
                   android:layout_width="match_parent"
                   android:layout_height="wrap_content"
                   android:orientation="horizontal"
                   android:layout_marginBottom="32dp">

                   <TextView
                       android:layout_width="0dp"
                       android:layout_height="wrap_content"
                       android:layout_weight="1"
                       android:text="Total"
                       android:textAppearance="?attr/textAppearanceTitleMedium" />

                   <TextView
                       android:id="@+id/tvTotal"
                       android:layout_width="wrap_content"
                       android:layout_height="wrap_content"
                       android:textAppearance="?attr/textAppearanceTitleMedium"
                       android:textColor="?attr/colorPrimary" />

               </LinearLayout>

               <com.google.android.material.button.MaterialButton
                   android:id="@+id/btnConfirm"
                   android:layout_width="match_parent"
                   android:layout_height="wrap_content"
                   android:text="@string/qr_pay_confirm_button"
                   android:textAllCaps="false" />

               <com.google.android.material.button.MaterialButton
                   android:id="@+id/btnCancel"
                   style="@style/Widget.Material3.Button.OutlinedButton"
                   android:layout_width="match_parent"
                   android:layout_height="wrap_content"
                   android:layout_marginTop="12dp"
                   android:text="@string/nfc_cancel"
                   android:textAllCaps="false" />

               <!-- Loading indicator shown during confirm API call -->
               <ProgressBar
                   android:id="@+id/progressConfirm"
                   style="?android:attr/progressBarStyleSmall"
                   android:layout_width="wrap_content"
                   android:layout_height="wrap_content"
                   android:layout_gravity="center_horizontal"
                   android:layout_marginTop="16dp"
                   android:visibility="gone" />

           </LinearLayout>
       </androidx.core.widget.NestedScrollView>

   </FrameLayout>
   ```

2. **`app/src/main/res/values/strings.xml`** — add three strings inside `<resources>`:
   ```xml
   <string name="action_qr_pay">Scan QR</string>
   <string name="qr_pay_scanning">Point camera at QR code on terminal</string>
   <string name="qr_pay_confirm_title">Confirm Payment</string>
   <string name="qr_pay_confirm_button">Pay Now</string>
   ```

3. **`app/src/main/java/com/bankongseton/student/QRPayActivity.kt`** — create new file:

   ```kotlin
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
   ```

4. **`app/src/main/res/layout/activity_home.xml`** — replace the `activateNfcPayButton` LinearLayout with a `qrPayButton` LinearLayout. Key changes:
   - Change `android:id="@+id/activateNfcPayButton"` to `android:id="@+id/qrPayButton"`
   - Remove `android:visibility="gone"` (QR is always visible — no hardware check needed)
   - Change the icon from `@android:drawable/stat_sys_data_bluetooth` to `@android:drawable/ic_menu_camera`
   - Change `android:contentDescription` from `@string/action_nfc_pay` to `@string/action_qr_pay`
   - Change `app:cardBackgroundColor` from `?attr/colorTertiaryContainer` to `?attr/colorSecondaryContainer`
   - Change the label TextView `android:text` from `@string/action_nfc_pay` to `@string/action_qr_pay`

5. **`HomeActivity.kt`** — update NFC references to QR:
   - Change field declaration `private lateinit var activateNfcPayButton: LinearLayout` to `private lateinit var qrPayButton: LinearLayout`
   - Change `activateNfcPayButton = findViewById(R.id.activateNfcPayButton)` to `qrPayButton = findViewById(R.id.qrPayButton)`
   - Change `activateNfcPayButton.setOnClickListener { onNfcPayClicked() }` to `qrPayButton.setOnClickListener { launchQrPay() }`
   - Remove `updateNfcButtonVisibility()` call from `onCreate()` and `onResume()` (QR is always visible; no hardware check)
   - Add the QR pay launcher below the `nfcPayLauncher` declaration:
     ```kotlin
     private val qrPayLauncher = registerForActivityResult(
         ActivityResultContracts.StartActivityForResult()
     ) { result ->
         if (result.resultCode == Activity.RESULT_OK) {
             loadBalance()
         }
     }
     ```
   - Add `launchQrPay()` method (replaces the NFC pay click handler):
     ```kotlin
     private fun launchQrPay() {
         qrPayLauncher.launch(Intent(this, QRPayActivity::class.java))
     }
     ```
   - Remove (or leave as dead code for S05 to clean up): `nfcManager`, `nfcPayLauncher`, `updateNfcButtonVisibility()`, `onNfcPayClicked()`, `showSetupPinDialog()`, `showPinDialog()` — **do NOT remove NfcManager import yet** (S05 task). Only remove the `activateNfcPayButton` references and the `updateNfcButtonVisibility()` calls.

   **Important:** Keep `private lateinit var nfcManager: NfcManager` and `nfcManager = NfcManager.getInstance(this)` in place for now — removing them requires removing the NFC classes (S05). The `updateNfcButtonVisibility()` calls are the only thing that must be removed.

6. **`AndroidManifest.xml`** — add `CAMERA` permission and `QRPayActivity` declaration:
   - After `<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />`, add:
     ```xml
     <uses-permission android:name="android.permission.CAMERA" />
     <uses-feature android:name="android.hardware.camera" android:required="false" />
     ```
   - After the `SettingsActivity` declaration, add:
     ```xml
     <activity
         android:name=".QRPayActivity"
         android:exported="false"
         android:screenOrientation="portrait" />
     ```

7. **Verify layout references** — confirm `item_receipt_line.xml` has `R.id.itemName`, `R.id.itemQty`, `R.id.itemPrice` (already confirmed in research — the file exists with these exact IDs). No changes needed to that file.

## Must-Haves

- [ ] `activity_qr_pay.xml` exists with `previewView`, `confirmPanel`, `itemsContainer`, `tvTotal`, `btnConfirm`, `btnCancel`, `progressConfirm`
- [ ] `QRPayActivity.kt` exists; imports CameraX and ML Kit; has `scanning` flag to prevent double-scan; handles 402/404/410/401 error codes with specific dialogs
- [ ] `QRPayActivity.kt` extracts token from URL last path segment (`substringAfterLast('/')`)
- [ ] `QRPayActivity.kt` uses `item_receipt_line.xml` for cart item rows
- [ ] `QRPayActivity.kt` calls `setResult(RESULT_OK)` on success and `finish()`; calls `setResult(RESULT_CANCELED)` on Cancel
- [ ] `activity_home.xml` has `qrPayButton` id (not `activateNfcPayButton`); no `android:visibility="gone"` on that view
- [ ] `HomeActivity.kt` uses `qrPayButton`, `qrPayLauncher`; refreshes balance on `RESULT_OK`; no call to `updateNfcButtonVisibility()`
- [ ] `AndroidManifest.xml` has `CAMERA` permission and `QRPayActivity` declaration
- [ ] `strings.xml` has `action_qr_pay`, `qr_pay_scanning`, `qr_pay_confirm_title`, `qr_pay_confirm_button`

## Verification

```bash
# QRPayActivity declared in manifest
grep -q 'QRPayActivity' mobile/student_app_v2/app/src/main/AndroidManifest.xml && echo "OK: QRPayActivity in manifest"

# CAMERA permission in manifest
grep -q 'android.permission.CAMERA' mobile/student_app_v2/app/src/main/AndroidManifest.xml && echo "OK: CAMERA permission"

# qrPayButton in HomeActivity
grep -q 'qrPayButton' mobile/student_app_v2/app/src/main/java/com/bankongseton/student/HomeActivity.kt && echo "OK: qrPayButton in HomeActivity"

# QRPayActivity.kt exists
test -f mobile/student_app_v2/app/src/main/java/com/bankongseton/student/QRPayActivity.kt && echo "OK: QRPayActivity.kt exists"

# activity_qr_pay.xml exists
test -f mobile/student_app_v2/app/src/main/res/layout/activity_qr_pay.xml && echo "OK: activity_qr_pay.xml exists"
```

## Inputs

- T01 must be complete: `QrCartResponse`, `QrConfirmRequest`, `QrConfirmResponse` exist in `Models.kt`; `SecureStorage.getJwtToken()` is available; `BangkoApiService.getQrCart()` and `confirmQrPayment()` are declared; CameraX + ML Kit in `build.gradle.kts`
- `item_receipt_line.xml` — has `itemName`, `itemQty`, `itemPrice` TextViews (confirmed in research)
- `activity_home.xml` — existing `activateNfcPayButton` LinearLayout becomes `qrPayButton`

## Expected Output

- `QRPayActivity.kt` — full CameraX + ML Kit scanning activity with cart confirmation; handles all error codes
- `activity_qr_pay.xml` — camera preview + confirmation panel layout
- `activity_home.xml` — `qrPayButton` visible by default (no gone)
- `HomeActivity.kt` — wired to `QRPayActivity` via `qrPayLauncher`; balance refreshes on success
- `AndroidManifest.xml` — CAMERA permission + QRPayActivity entry
- `strings.xml` — 4 new QR strings added
